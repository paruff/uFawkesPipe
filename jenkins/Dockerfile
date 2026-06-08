FROM jenkins/jenkins:lts

USER root

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install Docker CLI for Docker-in-Docker
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    docker.io=5:24.0.7-1~ubuntu.22.04~jammy \
    curl=7.81.0-1ubuntu1.16 \
    git=1:2.34.1-1ubuntu1.12 \
    python3=3.10.6-1~22.04.2 \
    python3-pip=22.0.2+dfsg-1ubuntu0.4 \
    nodejs=12.22.9+dfsg-1ubuntu0.4 \
    npm=8.5.1+ds-1 \
    maven=3.6.3-5build0.22.04.1 \
    gradle=4.4.1-1ubuntu1.3 \
    jq=1.6+dfsg-3 \
    unzip=6.0-26ubuntu3.1 \
    gpg=2.2.27-3ubuntu2.1 \
    lsb-release=11.1.0ubuntu2 \
    && rm -rf /var/lib/apt/lists/*

# Install Pack CLI for Cloud Native Buildpacks
RUN curl -sSL "https://github.com/buildpacks/pack/releases/download/v0.32.1/pack-v0.32.1-linux.tgz" | tar -C /usr/local/bin/ --no-same-owner -xzv pack

# Install OWASP Dependency-Check CLI
RUN curl -sSL "https://github.com/jeremylong/DependencyCheck/releases/download/v9.0.9/dependency-check-9.0.9-release.zip" -o /tmp/dc.zip && \
    unzip /tmp/dc.zip -d /opt/ && \
    ln -s /opt/dependency-check/bin/dependency-check.sh /usr/local/bin/dependency-check && \
    rm /tmp/dc.zip

# Install hadolint for Dockerfile linting
RUN curl -sSL -o /usr/local/bin/hadolint https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64 && \
    chmod +x /usr/local/bin/hadolint

# Install trivy for container scanning
RUN curl -fsSL https://aquasecurity.github.io/trivy-repo/deb/public.key | gpg --dearmor -o /usr/share/keyrings/trivy-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/trivy-archive-keyring.gpg] https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | tee /etc/apt/sources.list.d/trivy.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends trivy && \
    rm -rf /var/lib/apt/lists/*

USER jenkins

# Install Jenkins plugins
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

# Copy Jenkins Configuration as Code
ENV CASC_JENKINS_CONFIG=/var/jenkins_home/casc.yaml

# Skip setup wizard
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"

USER root
# Ensure jenkins user can access Docker socket
RUN usermod -aG docker jenkins || true

USER jenkins

# Set working directory
WORKDIR /var/jenkins_home
