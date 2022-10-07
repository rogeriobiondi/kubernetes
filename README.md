# Kubernetes - FASTAPI Microservice/API + Mongo

## Instructions:

### Pre-reqs

- Docker and Local Kubernetes Installation
https://ubuntu.com/tutorials/install-a-local-kubernetes-with-microk8s?&_ga=2.95357212.1448209.1665159994-1843409535.1663600026#1-overview


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

The `postman` directory contains a test postman collection.


### Destroy and release resources:

```
make destroy
```

### Run locally (development)

Execute in three separate windows:

```
make query-run
```

```
make command-run
```

```
make moderator-run
```

## Stress test

1) Instale ferramentas de suporte:

```
sudo apt install influxdb-client
```

``` 
make stress
```

1) Create a datasource in Grafana:
- Select `InfluxDB` as datasource
- URL: http://localhost:8086
- Database: k6
- User and Password: Empty
Click in Save & Test

2) Access Grafana: Dashboards:import the dashboard (json file) or provide the ID `10660`
http://localhost:3000

3) Start the tests:

```
cd stress
k6 run -o influxdb=http://localhost:8086/k6 script.js
```



