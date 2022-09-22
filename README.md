# Kubernetes - FASTAPI Microservice/API + MySQL

## Instructions:

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
