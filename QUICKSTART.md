# Quick Start Guide

Get uFawkesPipe up and running in 5 minutes!

## Prerequisites

- Docker 20.10+
- Docker Compose v2.0+
- 4GB+ RAM available
- DockerHub account

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/paruff/uFawkesPipe.git
cd uFawkesPipe
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env  # or vim, code, etc.
```

**Required settings in `.env`:**
```bash
DOCKERHUB_USERNAME=your-dockerhub-username
DOCKERHUB_TOKEN=your-dockerhub-token
JENKINS_ADMIN_PASSWORD=your-secure-password
```

**Get DockerHub token:**
1. Go to https://hub.docker.com/settings/security
2. Click "New Access Token"
3. Copy the token to `.env`

### 3. Start the Platform

```bash
# Initialize (first time only)
make init

# Start all services
make start

# Watch the logs
make logs
```

Wait 2-3 minutes for services to start. You'll see:
```
Jenkins is fully up and running
```

### 4. Access Services

- **Jenkins**: http://localhost:8080/jenkins
  - Username: `admin`
  - Password: (from `.env`)
  
- **SonarQube**: http://localhost:9000
  - Username: `admin`
  - Password: `admin` (change on first login)

## Create Your First Pipeline

### Option 1: Use Example Job

Jenkins comes with a pre-configured example pipeline:

1. Navigate to Jenkins → `pipelines/example-polyglot-pipeline`
2. Click "Build with Parameters"
3. Enter your repository URL and branch
4. Click "Build"

### Option 2: Create Custom Pipeline

1. **Add `.fawkespipe.yml` to your repository**

   Example for Node.js:
   ```yaml
   app:
     name: my-app
     type: service
     language: nodejs
   
   build:
     builder: cnb
     image:
       namespace: myorg
       name: my-app
   
   stages:
     lint:
       enabled: true
       commands:
         - language: nodejs
           cmd: npm run lint
     
     test:
       enabled: true
       commands:
         - language: nodejs
           cmd: npm test
     
     push:
       enabled: true
   ```

2. **Copy standard Jenkinsfile**
   ```bash
   cp uFawkesPipe/Jenkinsfile your-repo/Jenkinsfile
   git add Jenkinsfile .fawkespipe.yml
   git commit -m "Add CI/CD configuration"
   git push
   ```

3. **Create Pipeline in Jenkins**
   - Jenkins → New Item
   - Name: `my-app`
   - Type: Pipeline
   - Pipeline → Definition: Pipeline script from SCM
   - SCM: Git
   - Repository URL: `https://github.com/yourorg/your-repo`
   - Script Path: `Jenkinsfile`
   - Save

4. **Run the Pipeline**
   - Click "Build Now"
   - Watch the pipeline execute through all stages
   - Images are pushed to DockerHub

## Webhook Integration

### GitHub Webhook

1. Go to your repository → Settings → Webhooks → Add webhook
2. Configure:
   - **Payload URL**: `http://your-jenkins:8080/jenkins/github-webhook/`
   - **Content type**: `application/json`
   - **Events**: Just the push event
   - **Active**: ✓
3. Push code → Pipeline auto-triggers!

### Manual Webhook Trigger

```bash
curl -X POST "http://localhost:8080/jenkins/generic-webhook-trigger/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/user/repo",
    "branch": "main",
    "webhook_secret": "changeme"
  }'
```

## Common Commands

```bash
# Start platform
make start

# Stop platform
make stop

# View logs
make logs

# View specific service logs
make logs-jenkins
make logs-sonar

# Check service status
make status

# Restart services
make restart

# Backup Jenkins data
make backup

# Update to latest images
make update

# Clean everything (⚠️ destroys data)
make clean
```

## Verify Installation

Run the validation script:
```bash
./validate.sh
```

## Troubleshooting

### Jenkins won't start
```bash
# Check logs
make logs-jenkins

# Increase memory if needed (edit docker-compose.yml)
# JAVA_OPTS=-Xmx4g

# Reset Jenkins (⚠️ destroys data)
docker-compose down
docker volume rm ufp_jenkins_home
make start
```

### Can't access Jenkins
- Ensure port 8080 is not in use: `lsof -i :8080`
- Check firewall rules
- Verify Docker networking: `docker network ls`

### SonarQube won't start
```bash
# Increase vm.max_map_count (Linux only)
sudo sysctl -w vm.max_map_count=262144

# Check logs
make logs-sonar
```

### Pipeline fails to build image
- Verify Docker socket is mounted: `ls -la /var/run/docker.sock`
- Check DockerHub credentials in `.env`
- Ensure sufficient disk space: `df -h`

## Next Steps

- 📚 Read the [Full Documentation](README.md)
- 🔌 Set up [Webhooks and APIs](docs/webhook-api.md)
- ☸️ Plan [Kubernetes Promotion](docs/kubernetes-promotion.md)
- 📝 Review [Example Configs](examples/)

## Learn More

- Pipeline stages and configuration
- Multi-language support (Java, Python, Go, Node.js, Ruby)
- Security scanning (SAST, dependency scanning, image scanning)
- Kubernetes deployment
- Custom pipeline libraries

## Support

- 📖 Documentation: https://github.com/paruff/uFawkesPipe
- 🐛 Issues: https://github.com/paruff/uFawkesPipe/issues
- 💬 Discussions: https://github.com/paruff/uFawkesPipe/discussions

---

**Happy building! 🚀**
