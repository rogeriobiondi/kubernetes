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
	@pyenv install 3.10.4
	@pyenv virtualenv 3.10.4 k8s
	@pyenv local k8s