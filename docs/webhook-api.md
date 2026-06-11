# Webhook and API Documentation

uFawkesPipe exposes multiple APIs and webhooks that allow external planes to trigger and interact with pipelines.

## Overview

The platform provides:

1. **Generic Webhook Trigger** - Trigger any job via HTTP POST
2. **GitHub Webhooks** - Automatic pipeline triggers from GitHub
3. **Jenkins REST API** - Full programmatic control
4. **Build Status API** - Query pipeline status

## 1. Generic Webhook Trigger

The Generic Webhook Trigger plugin allows external systems to trigger Jenkins jobs via HTTP POST requests.

### Endpoint

```
POST http://your-jenkins:8080/jenkins/generic-webhook-trigger/invoke
```

### Authentication

Use webhook secret configured in `.env`:

```bash
WEBHOOK_SECRET=your-random-secret-string
```

### Request Format

**Headers:**

```
Content-Type: application/json
```

**Body:**

```json
{
  "repo_url": "https://github.com/user/repo",
  "branch": "main",
  "commit_sha": "abc123",
  "webhook_secret": "your-random-secret-string",
  "trigger_reason": "manual",
  "triggered_by": "external-plane"
}
```

### Example: Trigger Pipeline

```bash
curl -X POST "http://localhost:8080/jenkins/generic-webhook-trigger/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/myorg/myapp",
    "branch": "main",
    "webhook_secret": "changeme"
  }'
```

### Response

Success (200):

```json
{
  "jobs": {
    "my-pipeline": {
      "triggered": true,
      "url": "http://localhost:8080/jenkins/job/my-pipeline/42/"
    }
  }
}
```

Error (400/401):

```json
{
  "message": "Invalid webhook secret"
}
```

## 2. GitHub Webhooks

Configure GitHub to automatically trigger pipelines on push, pull request, or other events.

### Setup in GitHub

1. Go to repository Settings → Webhooks → Add webhook
2. Configure:
   - **Payload URL**: `http://your-jenkins:8080/jenkins/github-webhook/`
   - **Content type**: `application/json`
   - **Secret**: (optional, for signature verification)
   - **Events**: Choose "Just the push event" or "Let me select individual events"
   - **Active**: ✓ Enabled

### Supported Events

- `push` - Code pushed to repository
- `pull_request` - Pull request opened/updated
- `release` - Release published
- `create` - Branch or tag created

### Webhook Payload

GitHub sends a JSON payload with event details:

```json
{
  "ref": "refs/heads/main",
  "repository": {
    "name": "myapp",
    "full_name": "myorg/myapp",
    "clone_url": "https://github.com/myorg/myapp.git"
  },
  "pusher": {
    "name": "developer",
    "email": "dev@example.com"
  },
  "commits": [
    {
      "id": "abc123...",
      "message": "Fix bug",
      "author": {
        "name": "Developer"
      }
    }
  ]
}
```

### Pipeline Configuration

In your Jenkins pipeline job:

1. Enable "GitHub hook trigger for GITScm polling"
2. Configure Git SCM with repository URL
3. Jenkins will automatically trigger on matching webhooks

## 3. Jenkins REST API

Jenkins provides a comprehensive REST API for programmatic access.

### Authentication

**API Token:**

1. Jenkins → User → Configure → API Token → Generate
2. Use in requests: `username:api-token`

**Basic Auth:**

```bash
curl -u admin:your-api-token ...
```

### Common Endpoints

#### Get Job Info

```bash
curl -u admin:token \
  "http://localhost:8080/jenkins/job/my-job/api/json"
```

Response:

```json
{
  "name": "my-job",
  "url": "http://localhost:8080/jenkins/job/my-job/",
  "buildable": true,
  "builds": [...],
  "lastBuild": {
    "number": 42,
    "url": "http://localhost:8080/jenkins/job/my-job/42/"
  }
}
```

#### Trigger Build

```bash
curl -X POST -u admin:token \
  "http://localhost:8080/jenkins/job/my-job/build"
```

#### Trigger Build with Parameters

```bash
curl -X POST -u admin:token \
  "http://localhost:8080/jenkins/job/my-job/buildWithParameters?BRANCH=develop&TAG=v1.0.0"
```

#### Get Build Status

```bash
curl -u admin:token \
  "http://localhost:8080/jenkins/job/my-job/42/api/json"
```

Response:

```json
{
  "number": 42,
  "result": "SUCCESS",
  "duration": 120000,
  "timestamp": 1234567890,
  "url": "http://localhost:8080/jenkins/job/my-job/42/",
  "building": false,
  "artifacts": [...]
}
```

#### Get Build Console Output

```bash
curl -u admin:token \
  "http://localhost:8080/jenkins/job/my-job/42/consoleText"
```

#### Stop Build

```bash
curl -X POST -u admin:token \
  "http://localhost:8080/jenkins/job/my-job/42/stop"
```

#### Get Queue Info

```bash
curl -u admin:token \
  "http://localhost:8080/jenkins/queue/api/json"
```

## 4. Build Status Badges

Generate build status badges for README files:

### Badge URL

```
http://localhost:8080/jenkins/buildStatus/icon?job=my-job
```

### Markdown

```markdown
![Build Status](http://localhost:8080/jenkins/buildStatus/icon?job=my-job)
```

### HTML

```html
<img
  src="http://localhost:8080/jenkins/buildStatus/icon?job=my-job"
  alt="Build Status"
/>
```

## 5. Multibranch Pipeline Webhooks

For multibranch pipelines, use the Multibranch Scan Webhook Trigger plugin:

### Endpoint

```
POST http://localhost:8080/jenkins/multibranch-webhook-trigger/invoke?token=my-token
```

### Example

```bash
curl -X POST \
  "http://localhost:8080/jenkins/multibranch-webhook-trigger/invoke?token=my-secret-token"
```

## Integration Examples

### Python Client

```python
import requests

class UfawkesPipeClient:
    def __init__(self, base_url, username, api_token):
        self.base_url = base_url
        self.auth = (username, api_token)

    def trigger_build(self, job_name, parameters=None):
        """Trigger a Jenkins build"""
        if parameters:
            url = f"{self.base_url}/job/{job_name}/buildWithParameters"
            response = requests.post(url, auth=self.auth, params=parameters)
        else:
            url = f"{self.base_url}/job/{job_name}/build"
            response = requests.post(url, auth=self.auth)

        return response.status_code == 201

    def get_build_status(self, job_name, build_number):
        """Get build status"""
        url = f"{self.base_url}/job/{job_name}/{build_number}/api/json"
        response = requests.get(url, auth=self.auth)
        return response.json()

    def wait_for_build(self, job_name, build_number, timeout=600):
        """Wait for build to complete"""
        import time
        start = time.time()

        while time.time() - start < timeout:
            status = self.get_build_status(job_name, build_number)
            if not status['building']:
                return status['result']
            time.sleep(5)

        return 'TIMEOUT'

# Usage
client = UfawkesPipeClient(
    'http://localhost:8080/jenkins',
    'admin',
    'your-api-token'
)

# Trigger build
client.trigger_build('my-app', {'BRANCH': 'develop'})

# Check status
status = client.get_build_status('my-app', 42)
print(f"Build status: {status['result']}")
```

### Node.js Client

```javascript
const axios = require("axios");

class UfawkesPipeClient {
  constructor(baseUrl, username, apiToken) {
    this.baseUrl = baseUrl;
    this.auth = {
      username: username,
      password: apiToken,
    };
  }

  async triggerBuild(jobName, parameters = {}) {
    const hasParams = Object.keys(parameters).length > 0;
    const endpoint = hasParams ? "buildWithParameters" : "build";
    const url = `${this.baseUrl}/job/${jobName}/${endpoint}`;

    try {
      const response = await axios.post(url, null, {
        auth: this.auth,
        params: parameters,
      });
      return response.status === 201;
    } catch (error) {
      console.error("Failed to trigger build:", error);
      return false;
    }
  }

  async getBuildStatus(jobName, buildNumber) {
    const url = `${this.baseUrl}/job/${jobName}/${buildNumber}/api/json`;
    const response = await axios.get(url, { auth: this.auth });
    return response.data;
  }
}

// Usage
const client = new UfawkesPipeClient(
  "http://localhost:8080/jenkins",
  "admin",
  "your-api-token",
);

(async () => {
  // Trigger build
  await client.triggerBuild("my-app", { BRANCH: "develop" });

  // Check status
  const status = await client.getBuildStatus("my-app", 42);
  console.log(`Build status: ${status.result}`);
})();
```

### Bash/cURL Script

```bash
#!/bin/bash

JENKINS_URL="http://localhost:8080/jenkins"
JENKINS_USER="admin"
JENKINS_TOKEN="your-api-token"
JOB_NAME="my-app"

# Trigger build with parameters
trigger_build() {
  local branch=$1
  curl -X POST \
    -u "${JENKINS_USER}:${JENKINS_TOKEN}" \
    "${JENKINS_URL}/job/${JOB_NAME}/buildWithParameters?BRANCH=${branch}"
}

# Get last build number
get_last_build() {
  curl -s -u "${JENKINS_USER}:${JENKINS_TOKEN}" \
    "${JENKINS_URL}/job/${JOB_NAME}/api/json" | \
    jq -r '.lastBuild.number'
}

# Get build status
get_build_status() {
  local build_number=$1
  curl -s -u "${JENKINS_USER}:${JENKINS_TOKEN}" \
    "${JENKINS_URL}/job/${JOB_NAME}/${build_number}/api/json" | \
    jq -r '.result'
}

# Wait for build to complete
wait_for_build() {
  local build_number=$1
  echo "Waiting for build ${build_number}..."

  while true; do
    status=$(get_build_status "${build_number}")
    if [ "${status}" != "null" ]; then
      echo "Build completed with status: ${status}"
      return 0
    fi
    sleep 5
  done
}

# Main
trigger_build "main"
build_number=$(get_last_build)
wait_for_build "${build_number}"
```

## Security Considerations

1. **Use HTTPS** in production to encrypt credentials
2. **API Tokens** - Use API tokens instead of passwords
3. **Webhook Secrets** - Always validate webhook signatures
4. **IP Allowlisting** - Restrict webhook sources by IP
5. **Rate Limiting** - Implement rate limiting for webhook endpoints
6. **CSRF Protection** - Jenkins CSRF protection is enabled by default

## Monitoring Webhooks

View webhook delivery logs in Jenkins:

- Jenkins → Manage Jenkins → System Log
- GitHub → Repository → Settings → Webhooks → Recent Deliveries

## Troubleshooting

### Webhook not triggering pipeline

1. Check Jenkins logs: `docker-compose logs jenkins`
2. Verify webhook URL is accessible from GitHub/external system
3. Check webhook secret matches
4. Verify job configuration has webhook trigger enabled

### Authentication failures

1. Verify username and API token are correct
2. Check user has necessary permissions
3. Ensure CSRF protection is handled (use crumb API)

### Timeout issues

1. Increase timeout in webhook configuration
2. Check network connectivity
3. Verify Jenkins is not overloaded

## References

- [Jenkins REST API](https://www.jenkins.io/doc/book/using/remote-access-api/)
- [Generic Webhook Trigger Plugin](https://plugins.jenkins.io/generic-webhook-trigger/)
- [GitHub Webhooks](https://docs.github.com/en/developers/webhooks-and-events/webhooks)
