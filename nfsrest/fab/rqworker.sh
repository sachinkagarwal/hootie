#!/bin/bash

#Change this to whatever virtualenv you are using
# $1: Path of Django's environment's activate script
# $2: django manage.py command (including full path)
# $3: ids of queues this worker pulls jobs from (space separated)
source /usr/local/bin/virtualenvwrapper.sh; source $1; python $2 rqworker $3
