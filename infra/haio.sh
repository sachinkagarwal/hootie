#/bin.bash

# Packages for NFS server
sudo apt-get update
    sudo apt-get install -y \
    nfs-kernel-server \
    openssh-server

# Packages for hootie server
sudo apt-get install -y \
    python-pip python-dev build-essential \
    supervisor redis-server \
    git python-virtualenv \
    fabric \

#Start supervisor
service supervisor start

# Become vagrant User
su - vagrant

#Create SSH keys
cat /dev/zero | ssh-keygen -q -N ""   

# Clone hootie
git clone https://github.com/sachinkagarwal/hootie.git

#pip Packages
cd hootie
#virtualenv hootie
#source hootie/bin/activate
sudo pip install -r requirements.txt


#Start 2 RQ workers
cd nfsrest/fab
fab add_supervisor_process:rqworker1,/home/vagrant/hootie/nfsrest/manage.py,vagrant,vagrant,"queue1 queue2 queue3 queue4 queue5"

fab add_supervisor_process:rqworker2,/home/vagrant/hootie/nfsrest/manage.py,vagrant,vagrant,"queue1 queue2 queue3 queue4 queue5"

ps -aux | grep rqworker1
ps -aux | grep rqworker2

#Create Django sqllite DB 
cd ..
python manage.py migrate
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin')" | python manage.py shell
 
python manage.py runserver 0.0.0.0:8080
