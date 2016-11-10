from .models import Volume
from .models import RootPath
from rest_framework import serializers
from django.contrib.auth.models import User


class VolumeSerializer(serializers.ModelSerializer):
    fullpath = serializers.ReadOnlyField(source='path')
    fileserver = serializers.ReadOnlyField(source='nfsserver')
    owner = serializers.ReadOnlyField(source='owner.username')
    class Meta:
        model = Volume
        fields = ('pk', 'root_path','sub_path','fileserver','fullpath',
                'allowed_hosts','size_GB','options','owner',)


class RootPathSerializer(serializers.ModelSerializer):
    server_path = serializers.ReadOnlyField(source='fullpath')
    class Meta:
        model = RootPath
        fields = ('pk','server_path')


class UserSerializer(serializers.ModelSerializer):
    volumes = serializers.PrimaryKeyRelatedField(many=True, queryset=Volume.objects.all())

    class Meta:
        model = User
        fields = ('id', 'username', 'volumes')
