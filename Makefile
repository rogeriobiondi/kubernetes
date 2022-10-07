install:
	@sudo snap install microk8s --classic --channel=1.21
	@sudo usermod -a -G microk8s $USER
	@newgrp microk8s
	@mkdir /home/$USER/.kube
	@microk8s config > /home/$USER/.kube/config	
	@sudo chown -f -R $USER ~/.kube	

configure: 
	@microk8s enable dns
	@microk8s enable registry

create-env:
	# @pyenv install 3.10.4
	@pyenv virtualenv 3.10.4 k8s
	@pyenv local k8s

clean-registry:
	@echo "Run these commands in your terminal:"
	@echo ""
	@echo ""
	@echo "microk8s ctr images ls name~='localhost:32000' | awk {'print \$$1'} > images.txt"
	@echo "cat images.txt | while read line || [[ -n \$$line ]];"
	@echo "do"
	@echo "	microk8s ctr images rm \$$line"
	@echo "done;"
	@echo "rm images.txt"
	@echo ""
	@echo ""

image-build:
	@echo "Building Container..."
	@docker build . -t status
	@echo "Tagging image..."
	@docker tag status localhost:32000/status
	@echo "Pushing to microk8s local registry"
	@docker push localhost:32000/status

image-test:
	@docker run -ti --rm --env LOG_LEVEL=DEBUG localhost:32000/microsvc bash 

stress:
	@cd stress
	@echo "Stress Test Infrastructure is starting..." 
	@echo "Grafana console: http://localhost:3000" 
	@echo "Follow steps of README.md to configure and start the tests."
	@docker-compose up
	@sudo rm -rfd grafana influxdb

deploy: image-build
	# Secrets
	@echo "Creating Secrets..."
	@kubectl create -f ./manifests/secrets.yaml
	# Persistent Volume
	@echo "Creating Persistent Volume..."
	@kubectl create -f ./manifests/volume.yaml
	# Mongo
	@echo "Creating Mongo Database..."
	@kubectl create -f ./manifests/mongo.yaml
	# Redis
	@echo "Creating Redis Cache..."
	@kubectl create -f ./manifests/redis.yaml
	# Kafka
	cp manifests/kafka.yaml manifests/kafka-local.yaml
	MACHINE_IP=$$(hostname -I | awk '{print $$1}'); sed -i "s/machine-ip/$$MACHINE_IP/g" manifests/kafka-local.yaml
	@kubectl create -f ./manifests/kafka-local.yaml
	# Query
	@echo "Creating the Query..."
	@kubectl create -f ./manifests/query.yaml
	# Command
	@echo "Creating the Command..."
	@kubectl create -f ./manifests/command.yaml
	# Moderator
	@echo "Creating the Moderator..."
	@kubectl create -f ./manifests/moderator.yaml

db-client:
	@kubectl run -it --rm --image=mysql --restart=Never mysql-client -- mysql --host mysql --password=pass

destroy: 
	@echo "Destroying the Query..."
	@kubectl delete -f ./manifests/query.yaml --ignore-not-found=true --wait=true 
	@echo "Destroying the Command..."
	@kubectl delete -f ./manifests/command.yaml --ignore-not-found=true --wait=true
	@echo "Destroying the Moderator..."
	@kubectl delete -f ./manifests/moderator.yaml --ignore-not-found=true --wait=true
	@echo "Destroying Mongo Database..."
	@kubectl delete -f ./manifests/mongo.yaml --ignore-not-found=true --wait=true
	@echo "Destroying Redis Cache..."
	@kubectl delete -f ./manifests/redis.yaml --ignore-not-found=true --wait=true
	@echo "Destroying Kafka..."
	@kubectl delete -f ./manifests/kafka-local.yaml --ignore-not-found=true --wait=true
	@echo "Destroying Persistent Volume..."
	@kubectl delete -f ./manifests/volume.yaml --ignore-not-found=true --wait=true
	@echo "Destroying Secrets..."
	@kubectl delete -f ./manifests/secrets.yaml --ignore-not-found=true --wait=true
	@echo "Destroying the volume data..."
	@sudo rm -rfd /mnt/data

query-run: 
	@uvicorn app.query:app --reload --host 0.0.0.0

command-run:
	@python -m app.command

moderator-run:
	@python -m app.moderator

redeploy:image-build
	@kubectl rollout restart deploy query
	@kubectl rollout restart deploy command
	@kubectl rollout restart deploy moderator
	@sleep 10
	@kubectl get pods


query-test:
	@curl -X 'POST' \
		'http://localhost:30333/' \
		-H 'accept: application/json' \
		-H 'Content-Type: application/json' \
		-d '{ "name": "Jane Doe", "email": "jdoe@example.com", "pwd": "pass"}'

redis-cli:
	@redis-cli -p 30379

mongosh:
	# Installation
	# https://www.mongodb.com/docs/mongodb-shell/
	@mongosh mongodb://localhost:32017 -u user -p pass