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


## Local installation

### Microk8s

```bash
# Create and connecting to the vm
multipass launch -n k8s -m 8G -c 2 -d 10G
multipass shell k8s

# K8s installation
sudo snap install microk8s --classic --channel=1.21
sudo usermod -a -G microk8s $USER
sudo chown -f -R $USER ~/.kube

# exit and restart
exit
multipass restart k8s
multipass shell k8s

# Status
microk8s status
microk8s enable dns

# stop and start
microk8s stop
microk8s start

# Using kubectl with microk8s
microk8s kubectl get nodes

NAME   STATUS   ROLES    AGE   VERSION
k8s    Ready    <none>   11m   v1.21.3-3+90fd5f3d2aea0a

# Exit 
exit
```


### Installing Kubectl in Linux

```bash
# Copy the configuration from microk8s to kubectl
mkdir ~/.kube/config
chmod go-r ~/.kube/config
multipass exec k8s -- microk8s config > ~/.kube/config

# Linux Installation
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo mv kubectl /usr/local/bin/
sudo chmod a+x /usr/local/bin/kubectl

# Test
kubectl get nodes
```

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
git checkout fastapi-mongo
``` 

## FastAPI + MongoDB + Redis

```
git checkout fastapi-mongo-redis
``` 

## CQRS + Kafka

```
git checkout cqrs-kafka
``` 

## Job and Cronjob

```
git checkout cronjob
``` 