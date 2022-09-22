# Kubernetes - Sample Deployments

Kubernetes deployment templates.


## Flask Microservice/API + MySQL

```
git checkout flask-mysql
```


## Pre-reqs:

- Ubuntu Operating System
- GNU Make
- Kubectl  - https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/
- Microk8s - https://microk8s.io/
    - You'll need to enable dns and local registry.
    - The target `make install` has the commands for installation.

## Instructions:

### Configuration

```
make configure
```

### Deploy

```
# Deploy services
make deploy

# Check if all pods are ready before going to the next step
kubectl get all
```

### Create Tunnel for Microservice

```
make api-tunnel
```

### Testing the Microservice

```
make api-test
```

### Destroy and release resources:

```
make deploy
```
