# Kubernetes Promotion Path

This document describes how to promote uFawkesPipe from single-node Docker Compose to Kubernetes.

## Overview

uFawkesPipe is designed for easy development on a single node with Docker Compose, but can be promoted to Kubernetes for production use. This guide shows the migration path.

## Architecture Comparison

### Development (Docker Compose)
- Single node deployment
- Docker volumes for persistence
- Bridge networking
- Suitable for: Local dev, small teams, testing

### Production (Kubernetes)
- Multi-node cluster
- PersistentVolumeClaims for storage
- Service mesh networking
- Suitable for: Production, high availability, scale

## Step 1: Prepare Kubernetes Cluster

You'll need:
- Kubernetes 1.24+ cluster
- `kubectl` configured
- Storage provisioner (for PVCs)
- Ingress controller (nginx, traefik, etc.)

```bash
# Verify cluster access
kubectl cluster-info
kubectl get nodes
```

## Step 2: Create Namespace

```bash
kubectl create namespace ufawkespipe
kubectl config set-context --current --namespace=ufawkespipe
```

## Step 3: Deploy Jenkins on Kubernetes

See the `k8s/` directory for complete manifests:

- `jenkins-pvc.yaml` - PersistentVolumeClaim
- `jenkins-deployment.yaml` - StatefulSet
- `jenkins-service.yaml` - Service
- `jenkins-ingress.yaml` - Ingress
- `jenkins-rbac.yaml` - ServiceAccount and RBAC

### Quick Deploy

```bash
# Create secrets
kubectl create secret generic dockerhub-credentials \
  --from-literal=username=your-username \
  --from-literal=token=your-token \
  -n ufawkespipe

# Apply all manifests
kubectl apply -f k8s/

# Watch deployment
kubectl get pods -n ufawkespipe -w
```

## Step 4: Configure Jenkins Kubernetes Plugin

Once Jenkins is running on K8s, configure the Kubernetes plugin to use pods as build agents:

1. Navigate to Manage Jenkins → Configure System
2. Add Kubernetes Cloud:
   - Name: `kubernetes`
   - Kubernetes URL: `https://kubernetes.default.svc`
   - Kubernetes Namespace: `ufawkespipe`
   - Jenkins URL: `http://jenkins:8080/jenkins`

## Migration Checklist

- [ ] Kubernetes cluster provisioned
- [ ] Storage provisioner configured
- [ ] Ingress controller installed
- [ ] Secrets created
- [ ] Custom Jenkins image built and pushed
- [ ] PVCs created
- [ ] Jenkins StatefulSet deployed
- [ ] Services and Ingress configured
- [ ] Test pipeline runs successfully

## References

- [Jenkins on Kubernetes](https://www.jenkins.io/doc/book/installing/kubernetes/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
