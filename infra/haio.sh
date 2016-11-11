#/bin.bash

# Packages for NFS server
sudo apt-get update
    sudo apt-get install -y \
    nfs-kernel-server \
    openssh-server

# Packages for hootie server
sudo apt-get install -y \
    python-pip python-dev build-essential \
    redis-server \
    git python-virtualenv \
    fabric \

# REmove supervisor, will reinstall via pip
sudo apt-get remove supervisor --purge

cat << EOF > /home/vagrant/installasvagrant.sh
#!/bin/bash
cd /home/vagrant

#Environment variables
cat << EF >> /home/vagrant/.bashrc
export FABAC_USER=vagrant
export FABAC_PASS=vagrant
export FABAC_KEY=/home/vagrant/.ssh/id_rsa
EF
#Create SSH keys
cat /dev/zero | ssh-keygen -q -N ""
#Setup autologin
cd /home/vagrant/.ssh   
cat id_rsa.pub >> authorized_keys
chmod 600 authorized_keys
# Clone hootie
cd /home/vagrant
git clone https://github.com/sachinkagarwal/hootie.git 
sleep 5
#pip Packages
cd hootie
#virtualenv hootie
#source hootie/bin/activate
sudo pip install -r requirements.txt

# Start 2 RQ workers
# Use something like supervisor for a production environment
nohup bash -c "python /home/vagrant/hootie/nfsrest/manage.py rqworker queue1 queue2 queue3 queue4 queue5"  1>/dev/null 2>/dev/null &
nohup bash -c "python /home/vagrant/hootie/nfsrest/manage.py rqworker queue1 queue2 queue3 queue4 queue5"  1>/dev/null 2>/dev/null &

#A root path directory
mkdir -p /home/vagrant/nfsrootpath

#Create Django sqllite DB 
cd /home/vagrant/hootie/nfsrest
python manage.py migrate
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin')" | python manage.py shell
 
python manage.py runserver 0.0.0.0:8080

EOF

chmod 755 /home/vagrant/installasvagrant.sh
chown vagrant:vagrant /home/vagrant/installasvagrant.sh
su -c /home/vagrant/installasvagrant.sh - vagrant
