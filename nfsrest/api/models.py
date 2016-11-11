from django.db import models
from django.contrib.auth.models import User
from modelshelper import *
from fabric.api import execute
from django.core.exceptions import ValidationError
from django.core.validators import *

class BaseModel(models.Model):
    """
    Abstract base model (other models inherit from this)
    """
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    class Meta:
        abstract = True

class NFSServer(BaseModel):
    """
    Most basic representation of a NFS server
    """
    dns_name = models.CharField(max_length=200)
    def __unicode__(self):
        return self.dns_name

class RootPath(BaseModel):
    """
    The path on which NFS volumes will be created.
    There could be multiple such paths per nfs_server.
    """
    nfs_server = models.ForeignKey('NFSServer')
    path = models.CharField(max_length=200)
    capacity_GB = models.IntegerField(default=1, validators=[MinValueValidator(1)])

    def __unicode__(self):
        return self.nfs_server.dns_name + ":" + self.path
    
    @property
    def fullpath(self):
        return self.__unicode__()


class Volume(BaseModel):
    """
    Representation of a NFS volume.
    Corresponds to an entry in the /etc/exports file on the NFS server
    As well as to the /var/lib/etab entries
    """
    owner = models.ForeignKey(User, related_name='volumes')
    root_path = models.ForeignKey('RootPath')
    sub_path = models.CharField(max_length=200)
    options = models.CharField(max_length=200) #NFS options
    allowed_hosts = models.CharField(max_length=200, default="*") #NFS allowed_hosts
    size_GB = models.IntegerField(validators=[MinValueValidator(1)])

    def __unicode__(self):
        return self.path+"__"+ self.root_path.nfs_server.dns_name

    @property
    def path(self):
        return os.path.join(self.root_path.path, self.sub_path)
    
    @property
    def nfsserver(self):
        return self.root_path.nfs_server.dns_name

    #Note for the save and delete methods
    def save(self, *args, **kwargs):
        """
        Overriding save to create/re-export
        a volume
        """
        execute(CreateOrExport, self.root_path.path, self.sub_path,
                self.allowed_hosts,self.options,
                hosts = [self.root_path.nfs_server.dns_name])
        #Insert test here to confirm before DB update
        super(Volume,self).save(*args,**kwargs)

class Lock(models.Model):
    lock_name=models.CharField(max_length=100,primary_key=True)
    is_locked = models.BooleanField(default=False)

    def __unicode__(self):
        return self.lock_name



# Pre-delete NFS volume via signals. This approach is needed
# for bulk deletes to work (e.g. via querysets/Admin)
from django.db.models.signals import pre_delete
from django.dispatch import receiver

@receiver(pre_delete, sender=Volume)
def volume_post_delete_handler(sender, **kwargs):
    """
    Call the fabric methods to actually delete the NFS etab entry.
    """
    volume = kwargs['instance']
    execute(UnExport,os.path.join(volume.root_path.path,volume.sub_path),
            True,
            hosts = [volume.root_path.nfs_server.dns_name])

#Extending the user class
from django.contrib.auth.models import User


class Profile(BaseModel):
    user = models.OneToOneField(User,unique=True,primary_key=True)
    quota_GB = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    locked = models.BooleanField(default=False)
#Todos 
#(1) put in validation code for when quota_GB
#is reduced and becomes lesser than the already allocated
#(sum of volume sizes of a user). This should be an error
#(2) need validation that quota_GB does not exceed total 
#RootPath capacity

def create_user_profile(sender, **kwargs):
    if kwargs["created"]:
        Profile.objects.get_or_create(user=kwargs["instance"])

from django.db.models import signals
signals.post_save.connect(create_user_profile, sender=User,dispatch_uid='autocreate_nuser')
