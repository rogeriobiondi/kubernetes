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
	# MySQL
	@echo "Creating MySQL Database..."
	@kubectl create -f ./manifests/mysql.yaml
	@echo "Waiting for the database creation... (1 minute)"
	@sleep 60
	@echo "Setting up the database..."
	@kubectl run -it --rm --image=mysql --restart=Never mysql-client -- mysql --host mysql --password=pass -e "CREATE DATABASE IF NOT EXISTS microdb; USE microdb; CREATE TABLE IF NOT EXISTS users(user_id INT PRIMARY KEY AUTO_INCREMENT, user_name VARCHAR(255), user_email VARCHAR(255), user_password VARCHAR(255)); "
	# API
	@echo "Creating the API..."
	@kubectl create -f ./manifests/api.yaml

db-client:
	@kubectl run -it --rm --image=mysql --restart=Never mysql-client -- mysql --host mysql --password=pass

destroy: 
	@echo "Destroying the API..."
	@kubectl delete -f ./manifests/api.yaml --ignore-not-found=true --wait=true 
	@echo "Destroying MySQL Database..."
	@kubectl delete -f ./manifests/mysql.yaml --ignore-not-found=true --wait=true
	@echo "Destroying Persistent Volume..."
	@kubectl delete -f ./manifests/volume.yaml --ignore-not-found=true --wait=true
	@echo "Destroying Secrets..."
	@kubectl delete -f ./manifests/secrets.yaml --ignore-not-found=true --wait=true
	@echo "Destroying the volume data..."
	@sudo rm -rfd /mnt/data

api-run: 
	@uvicorn microsvc.main:app --reload

api-redeploy: build-image
	@kubectl rollout restart deploy microsvc-deployment

api-tunnel:
	@kubectl port-forward service/microsvc-service 8000 8000

db-tunnel:
	@kubectl port-forward service/mysql 3306 3306

api-test:
	@curl http://localhost:5000/create -H "Content-Type: application/json" -d '{"name": "Rogerio", "email": "rogerio@email.com", "pwd": "pass"}'
