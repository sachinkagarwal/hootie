import logging

from django.contrib.auth.models import User
from django.http import Http404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions, status
from rest_framework.exceptions import APIException
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
import django_rq
from time import sleep
from utils.modellock import *
from utils.volumemaker import PostHelper
from .models import RootPath, Volume
from .serializers import RootPathSerializer, VolumeSerializer

logger = logging.getLogger(__name__)

class VolumeList(APIView):
    """
    List (GET) all volumes, create (POST) a volume.
    """
    permission_classes = (permissions.IsAuthenticated,)

    @csrf_exempt
    def get(self, request, format=None):
        """
        List all volumes, or create a new volume.
        """
        if request.method == 'GET':
            if request.user.is_superuser:
                volumes = Volume.objects.all()
            else:
                volumes = Volume.objects.filter(owner=request.user)
            serializer = VolumeSerializer(volumes, many=True)
            return Response(serializer.data)

    def post(self, request, format=None):
        """
        Post - create a new NFS volume.
        Checks whether quota is exceeded before creating it.
        """
        serializer = VolumeSerializer(data=request.data)
        if serializer.is_valid():
            postjobData = {
                "username": request.user.username, #since request object cannot be passed (cannot be pickled)
                "root_path_pk":int(serializer.validated_data["root_path"].pk),
                "sub_path":serializer.validated_data["sub_path"],
                "options":serializer.validated_data["options"],
                "allowed_hosts":serializer.validated_data["allowed_hosts"],
                "size_GB":serializer.validated_data["size_GB"]
            }
            queueName = "queue"+str(serializer.validated_data['root_path'].pk)
            queue = django_rq.get_queue(queueName)
            job = queue.enqueue(PostHelper, postjobData, timeout=5)
            ctr = 0
            while ctr < 5:
                sleep(1) 
                if job.is_failed == True:
                    return Response(
                            {"error": "Job failed" + str(job)}, status.HTTP_500_INTERNAL_SERVER_ERROR)
                if job.result:
                    if job.result == 1:
                        return Response({"error":"None"}, status=status.HTTP_201_CREATED)
                    else:
                         if job.result < 0:
                             return Response({"error":"Internal Error code = " + str(job.result)}, 
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)  
                ctr = ctr + 1
            # If we haven't got a successful response, exit    
            return Response(
                    {"error": "Timeout - exceeded"}, status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    


class VolumeDetail(APIView):
    """
    Display (GET), or delete (DELETE) a volume.
    """

    permission_classes = (permissions.IsAuthenticated,)
    def get_object(self, id, owner):
        """
        Check if the supplied id exists
        """
        try:
            volume = Volume.objects.get(id=id)
            if (volume.owner == owner) or (owner.is_superuser):
                return volume
            else:
                raise Http404
                #Raising a 403 will leak information as it will
                #confirm that the bogus ID is a real NFS volume
                #belonging to someone else.
        except Volume.DoesNotExist:
            raise Http404

    def get(self, request, id, format=None):
        volume = self.get_object(id, request.user)
        serializer = VolumeSerializer(volume)
        return Response(serializer.data)

#Commented for simplicity; with this function we'll need a different serializer
#Without the PUT the only way to change export properties is though the admin interface
#Note that the backend fabric functionality for doing updates is implemented
#so it works in the backend.
#    def put(self,request,id,format=None):
#        volume = self.get_object(id,request.user)
#        serializer = VolumeSerializer(volume,data = request.data)
#        if serializer.is_valid():
#            serializer.save()
#            return Response(serializer.data)
#        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, format=None):
        volume = self.get_object(id, request.user)
        volume.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RootPathList(APIView):
    """
    List rootpaths. Their pk's are used while creating volumes above.
    The rootpaths determine the NFS server and the path on that server
    that is the prefix-path of the NFS volume.
    For example, an NFS server may have a SSD disk mounted at
    /exports/nfs-ssd (a rootpath) and another HDD
    mounted at /exports/nfs-hdd.
    Rootpaths are created/updated/deleted via the admin interface
    by the admin user only.
    """
    def get(self, request, format=None):
        """
        List all root_paths
        """
        if request.method == 'GET':
            rootpaths = RootPath.objects.all()
            serializer = RootPathSerializer(rootpaths, many=True)
            return Response(serializer.data)

#Currently user management happens via the admin interface; this can be included here later.
