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
	# get all images that start with localhost:32000, output the results into image_ls file
	# echo "sudo microk8s ctr images ls name~='localhost:32000' | awk {'print $1'} > images.txt"
	# loop over file, remove each image
	# echo "cat images.txt | while read line || [[ -n $line ]];"
	# echo "do"
    # echo "	microk8s ctr images rm $line"
	# echo "done;"
	# echo "rm images.txt"
	echo "comments"

build-image:
	@echo "Building Container..."
	@docker build . -t microsvc
	@echo "Tagging image..."
	@docker tag microsvc localhost:32000/microsvc
	@echo "Pushing to microk8s local registry"
	@docker push localhost:32000/microsvc

deploy: build-image 
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
	MACHINE_IP=$$(hostname -I | awk '{print $$1}'); sed -i "s/machine-ip/$$MACHINE_IP/g" manifests/kafka.yaml
	@kubectl create -f ./manifests/kafka.yaml
	# Query
	@echo "Creating the Query..."
	@kubectl create -f ./manifests/query.yaml
	# Command
	@echo "Creating the Command..."
	@kubectl create -f ./manifests/command.yaml

db-client:
	@kubectl run -it --rm --image=mysql --restart=Never mysql-client -- mysql --host mysql --password=pass

destroy: 
	@echo "Destroying the Query..."
	@kubectl delete -f ./manifests/query.yaml --ignore-not-found=true --wait=true 
	@echo "Destroying the Command..."
	@kubectl delete -f ./manifests/command.yaml --ignore-not-found=true --wait=true
	@echo "Destroying Mongo Database..."
	@kubectl delete -f ./manifests/mongo.yaml --ignore-not-found=true --wait=true
	@echo "Destroying Redis Cache..."
	@kubectl delete -f ./manifests/redis.yaml --ignore-not-found=true --wait=true
	@echo "Destroying Kafka..."
	@kubectl delete -f ./manifests/kafka.yaml --ignore-not-found=true --wait=true
	@echo "Destroying Persistent Volume..."
	@kubectl delete -f ./manifests/volume.yaml --ignore-not-found=true --wait=true
	@echo "Destroying Secrets..."
	@kubectl delete -f ./manifests/secrets.yaml --ignore-not-found=true --wait=true
	@echo "Destroying the volume data..."
	@sudo rm -rfd /mnt/data

api-run: 
	@uvicorn microsvc.query:app --reload --host 0.0.0.0

api-redeploy: build-image
	@kubectl rollout restart deploy microsvc-deployment

api-test:
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