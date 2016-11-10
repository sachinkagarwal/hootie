from api.models import Volume,RootPath
from django.contrib.auth.models import User
from django import db

def user_allocated(user):
    """
    Return the currently  allocated volume sizes for user.
    """
    userVols = Volume.objects.filter(owner=user)
    if userVols.count() > 0:
        return userVols.aggregate(alSize=db.models.Sum('size_GB'))['alSize']
    else:
        return 0

def total_allocated():
    """
    Return the sum of quotas of all users
    """

    return User.profile.objects.all().aggregate(qSize=db.models.Sum('quota_GB'))['qSize']

def total_capacity():
    """
    Return the sum of installed capacity across all rootpaths
    """
    return RootPath.objects.all().aggregate(
        capSize=db.models.Sum('capacity_GB'))['capSize']

def rootpath_capacity_exceeded(rootpath,newSize):
    """
    Return True if rootpath is already allocated to the extent
    it cannot accomadate newSize, otherwise return False
    """
    vols_in_rootpath = Volume.objects.filter(root_path=rootpath)
    rootpathallocsum = 0
    if vols_in_rootpath.count() > 0:
        rootpathallocsum = vols_in_rootpath.aggregate(
            alSize=db.models.Sum('size_GB'))['alSize']
    if rootpathallocsum + newSize > rootpath.capacity_GB:
        return True
    return False

def user_quota_exceeded(user,newSize):
    """
    Return True if the user's quota_GB (as specified in its Profile)
    is not enough to provision the new volume of size enewSize
    """
    if user.profile.quota_GB < user_allocated(user) + newSize:
        return True
    else:
        return False
        
