# Kubernetes - Sample Deployments

Kubernetes deployment templates.


## Pre-reqs:

- Ubuntu Operating System
- GNU Make
- Kubectl  - https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/
- Microk8s - https://microk8s.io/
    - You'll need to enable dns and local registry.
        - https://microk8s.io/docs/registry-built-in
    - The target `make install` has the commands for installation.

## Templates:

## Flask Microservice/API + MySQL

```
git checkout flask-mysql
``` 

## FastAPI + MySQL

```
git checkout fastapi-mysql
``` 

## FastAPI + MongoDB

```
git checkout fastapi-mongodb
``` 
