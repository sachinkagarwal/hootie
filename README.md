# Introduction

Linux commands do not come with a HTTP RESTful API. Conventionally, system resources - like storage, networking, user permissions etc. - are configurable with CLI (command line interface) commands and configuration files. This was ideal when human system administrators did most of the configuration but it is inadequate for today's automation focused devops world.

So how do you put a RESTful API in front of the command line? The Hootie project is a Vignette for this - it shows how to wrap up a fleet of Linux NFS kernel servers in a HTTP API. Django rest framework is used to create the RESTFul API and Django's admin interface is used to build a GUI for administering Kernel NFS servers running on multiple hosts. Python Fabric is used by the Django system to administer multiple Linux servers running the NFS daemon to export NFS volumes to clients. 

Here is a picture illustrating the system's architecture.


# Quick start

* Clone the Hootie master branch from 
    ```
    git clone https://github.com/sachinkagarwal/hootie.git
    ```

A Hootie-all-in-one Vagrantfile is included in the infra directory. Install Vagrant, and then simply run
```
cd hootie/infra
vagrant up
```

This will setup a single Vagrant VM with Hootie and a nfs kernel server at 192.168.50.2 (private address space).

 * Log into the Vagrant VM (vagrant ssh) 
 * Create a root-path directory that will be the base directory on which subdirectories will be created and exported.
 * On the host machine, open a browser and log into the the django admin website at http://192.168.50.2:8080/admin (User, password: admin,admin) to add a NFS server via the GUI (simply specify its IP addres 192.168.50.2). Next, add a "rootpath", specifying the directory created above and with 192.168.50.2 as the containing NFS server; also specify the "capacity" of this rootpath.

Then you can skip to the usage section below (replace localhost with 192.168.50.2, port 8080).


# Detailed Installation Instructions

These instructions are for debian-based systems (e.g. Debian, Ubuntu, etc.).

1. On each NFS server 
    * Create a sudo-enabled system account (lets call it sysact) with a home directory and use visudo to give it password-less sudo capability. In this version of hootie a password-based ssh login into this account is required. 
    * Install 
    ```
    sudo apt-get update
    sudo apt-get install -y \
    nfs-kernel-server \
    openssh-server

    ```
    * Create the root_path(s) - base directories - on each NFS-server where subdirectories corresponding to NFS volumes will be created.
2. On the Hootie server
    
    * Create a sudo-enabled system account (lets call it sysact) with a home directory and use visudo to give it password-less sudo capability.  
    * Install
    ```
    sudo apt-get update
    sudo apt-get install -y \
    python-pip python-dev build-essential \
    supervisor redis-server \
    git python-virtualenv \

    ```
    * Create a default SSH-keypair and use ssh-copy-id to copy the public key into each NFS server.
    ```
    # Avoiding passphrase prompts
    cat /dev/zero | ssh-keygen -q -N ""
    ```

    * Clone the Hootie master branch from 
    ```
    git clone https://github.com/sachinkagarwal/hootie.git
    ```
    * Add environment variable credentials for fabric in the .bashrc, something like.
    ```
    export FABAC_USER=vagrant
    export FABAC_PASS=vagrant
    export FABAC_KEY=/home/vagrant/.ssh/id_rsa
    ```
    * Install the requirements.txt python packages
    ```
    cd hootie
    pip install -r requirements.txt
    ```
    
    * Create RQ-worker processes

    Use something like supervisor in a production envinronment.
    ```
    nohup bash -c "python /home/vagrant/hootie/nfsrest/manage.py rqworker queue1 queue2 queue3 queue4 queue5"  1>/dev/null 2>/dev/null &
    nohup bash -c "python /home/vagrant/hootie/nfsrest/manage.py rqworker queue1 queue2 queue3 queue4 queue5"  1>/dev/null 2>/dev/null &

    ```
 

    * Run the Django server
    Launch the Django server (these are testing/development instructions,  for production consider uWSGI and nginx frontends).

    ```
    cd .. # Back to nfsrest directory

     # Migrations
    python manage.py makemigrations
    python manage.py migrate
    # Create a superuser
    python manage.py createsuperuser
    python manage.py runserver 0.0.0.0:8080
   
    ```
3. NFS Server and Rootpath Setup 
 * Create a root-path directory on the NFS server that will be the base directory on which subdirectories will be created and exported.
 * Log into the the django admin website and add a NFS server via the GUI (simply specify its DNS name or IP address). Next, add a "rootpath", specifying the directory created above and with the added NFS server as its containing server, also specify the "capacity" of this rootpath.

Repeat step 3 for each rootpath and nfs server.

# Usage

* Log into the Django admin interface
* Add an NFS server (by specifying its DNS Name)
* Add a root_path (specify which NFS server it belongs to, the directory path on that server, and the maximum capacity)


```
# Get root paths' pks
$> http GET http://localhost:8080/api/v1.0/rootpaths/HTTP/1.0 200 OK
Allow: GET, HEAD, OPTIONS
Content-Type: application/json
Date: Tue, 08 Nov 2016 11:36:08 GMT
Server: WSGIServer/0.1 Python/2.7.12
Vary: Accept, Cookie
X-Frame-Options: SAMEORIGIN

[
    {
        "pk": 1, 
        "server_path": "localhost:/home/sachin/temp"
    }
]

$> 
# Create NFS volume
$> http POST http://localhost:8080/api/v1.0/volumes/ \
> options="ro,sync" \
> root_path=1 \
> sub_path=_my_home_directory \
> size_GB=2 \
> allowed_hosts="192.168.20.2" \
> --json \
> --auth johndoe:johndoe
HTTP/1.0 201 CREATED
Allow: GET, POST, HEAD, OPTIONS
Content-Type: application/json
Date: Tue, 08 Nov 2016 11:27:11 GMT
Server: WSGIServer/0.1 Python/2.7.12
Vary: Accept
X-Frame-Options: SAMEORIGIN

{
    "error": "None"
}

# List users' volumes, error - auth credentials
$> http GET http://localhost:8080/api/v1.0/volumes/
HTTP/1.0 401 UNAUTHORIZED
Allow: GET, POST, HEAD, OPTIONS
Content-Type: application/json
Date: Tue, 08 Nov 2016 11:27:29 GMT
Server: WSGIServer/0.1 Python/2.7.12
Vary: Accept, Cookie
WWW-Authenticate: Basic realm="api"
X-Frame-Options: SAMEORIGIN

{
    "detail": "Authentication credentials were not provided."
}

# List users' volumes
$> http GET http://localhost:8080/api/v1.0/volumes/ --auth johndoe:johndoe
HTTP/1.0 200 OK
Allow: GET, POST, HEAD, OPTIONS
Content-Type: application/json
Date: Tue, 08 Nov 2016 11:27:45 GMT
Server: WSGIServer/0.1 Python/2.7.12
Vary: Accept
X-Frame-Options: SAMEORIGIN

[
    {
        "allowed_hosts": "192.168.20.2", 
        "fileserver": "localhost", 
        "fullpath": "/home/sachin/temp/_my_home_directory", 
        "options": "ro,sync", 
        "owner": "johndoe", 
        "pk": 5, 
        "root_path": 1, 
        "size_GB": 2, 
        "sub_path": "_my_home_directory"
    }
]

# Peek inside /etc/exports - the NFS config file
$> cat /etc/exports 
# /etc/exports: the access control list for filesystems which may be exported
#		to NFS clients.  See exports(5).
#
/home/sachin/temp/_my_home_directory 192.168.20.2(ro,sync)

# Delete a volume by specifying the volume's PK
$> http DELETE http://localhost:8080/api/v1.0/volumes/5/ --auth johndoe:johndoe
HTTP/1.0 204 NO CONTENT
Allow: GET, DELETE, HEAD, OPTIONS
Content-Length: 0
Date: Tue, 08 Nov 2016 11:29:40 GMT
Server: WSGIServer/0.1 Python/2.7.12
Vary: Accept
X-Frame-Options: SAMEORIGIN

# List volumes
$> http GET http://localhost:8080/api/v1.0/volumes/ --auth johndoe:johndoe
HTTP/1.0 200 OK
Allow: GET, POST, HEAD, OPTIONS
Content-Type: application/json
Date: Tue, 08 Nov 2016 11:29:48 GMT
Server: WSGIServer/0.1 Python/2.7.12
Vary: Accept
X-Frame-Options: SAMEORIGIN

[]

# Peek inside /etc/exports - the NFS config file
$> cat /etc/exports
# /etc/exports: the access control list for filesystems which may be exported
#		to NFS clients.  See exports(5).
#

$> 

```
