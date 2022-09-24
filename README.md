# Kubernetes - FASTAPI Microservice/API + Mongo

## Instructions:

### Deploy

```
# Deploy services
make deploy

# Check if all pods are ready before going to the next step
kubectl get all
```

### Testing the Microservice

You may access the test page in the browser:
http://localhost:30030/docs

or run the test:

```
make api-test
```

### Destroy and release resources:

```
make destroy
```
