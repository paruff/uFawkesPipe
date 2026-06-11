# Kubernetes Manifests for uFawkesPipe

This directory contains Kubernetes manifests for deploying uFawkesPipe to a Kubernetes cluster.

## Files

- `jenkins-pvc.yaml` - PersistentVolumeClaim for Jenkins data
- `jenkins-rbac.yaml` - ServiceAccount and RBAC for Jenkins
- `jenkins-deployment.yaml` - StatefulSet for Jenkins
- `jenkins-service.yaml` - Service for Jenkins
- `jenkins-ingress.yaml` - Ingress for Jenkins (requires ingress controller)

## Deployment

1. Create namespace:

   ```bash
   kubectl create namespace ufawkespipe
   ```

2. Create secrets:

   ```bash
   kubectl create secret generic dockerhub-credentials \
     --from-literal=username=your-username \
     --from-literal=token=your-token \
      -n ufawkespipe

    kubectl create secret generic jenkins-admin \
      --from-literal=username=admin \
      --from-literal=password=your-secure-password \
      -n ufawkespipe
   ```

3. Apply manifests:

   ```bash
   kubectl apply -f k8s/
   ```

4. Check status:
   ```bash
   kubectl get pods -n ufawkespipe
   kubectl get svc -n ufawkespipe
   kubectl get ingress -n ufawkespipe
   ```

## Notes

- Update `jenkins-ingress.yaml` with your domain
- Adjust storage class in `jenkins-pvc.yaml` for your cluster
- The Jenkins image (`ufawkespipe/jenkins:latest`) needs to be built and pushed to a registry
- For production, enable TLS in ingress and use cert-manager
- **Security Warning**: The deployment uses Docker socket mounting which grants root access to the host. For production environments, consider:
  - Docker-in-Docker (DinD) sidecar containers
  - Kaniko for building images without Docker
  - Kubernetes-native builders (Tekton, BuildKit)
  - See: https://jpetazzo.github.io/2015/09/03/do-not-use-docker-in-docker-for-ci/

## Building and Pushing Custom Image

```bash
cd uFawkesPipe
docker build -t your-registry/ufp-jenkins:latest -f jenkins/Dockerfile jenkins/
docker push your-registry/ufp-jenkins:latest

# Update jenkins-deployment.yaml with your image
```
