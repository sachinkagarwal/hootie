from time import sleep
from traceback import format_exc

from django import db
from django.contrib.auth.models import User
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from api.models import *

from .capquotanums import *
from .modellock import *


def PostHelper(jobdata):
    """
    This method embodies the work that needs to be serialized in the queue
    corresponding to the selected RootPath; this work will be spun off into
    the specified RootPath queue, ensuring that not more than one post request
    is modifying the rootpath model (otherwise allocated quota might exceed
    available quota for the root path)
    """
    try: 
        user = User.objects.get(username=jobdata["username"])
        rootpath = RootPath.objects.get(pk=jobdata["root_path_pk"])
        #Get user lock to serialize a particular user's requests
        if isLocked(user):
            #In real code you may want to wait for and retry a couple of times before returning       
            return -1
            #return Response({"error": "User Locked"}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        LockUser(user)
        #Quota check
        if user_quota_exceeded(user, jobdata['size_GB']):    
            return -2
            #return Response({"error":"Quota Exceeded"}, status.HTTP_400_BAD_REQUEST)
        #Capacity check
        #In real code we need a lock for roothpath capacity too -
        #otherwise roothpath may get overprovisioned
        #when multiple users provision at the same time.
        if rootpath_capacity_exceeded(
                rootpath,
                jobdata['size_GB']):
            UnlockUser(jobdata["user"])   
            return -3
            #return Response(
            #    {"error":"Rootpath capacity inadequate"},
            #    status.HTTP_400_BAD_REQUEST)
        
        newVol = Volume(
            owner = user,
            root_path = rootpath,
            sub_path =  jobdata['sub_path'],
            options =  jobdata['options'],
            allowed_hosts =  jobdata['allowed_hosts'],
            size_GB =  jobdata['size_GB']           
        )
        newVol.save()
        UnlockUser(user)
       
        return 1
        #return Response({"error":"None"}, status=status.HTTP_201_CREATED)
    except:
        return format_exc()
        #return Response(
        #    {"error": format_exc()}, status.HTTP_500_INTERNAL_SERVER_ERROR)
