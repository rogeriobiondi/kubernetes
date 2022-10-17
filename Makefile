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

image-test:
	@docker run -ti --rm localhost:32000/job bash

image-build:
	@echo "Building Container..."
	@docker rmi -f job
	@docker rmi -f localhost:32000/job
	@docker build . -t job
	@echo "Tagging image..."
	@docker tag job localhost:32000/job
	@echo "Pushing to microk8s local registry"
	@docker push localhost:32000/job
	
job-run:
	@python -m app.job
