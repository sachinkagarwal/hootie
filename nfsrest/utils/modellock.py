def LockUser(user):
    """
    Set the "locked" property of User.Profile to true
    """
    user.profile.locked = True
    user.save()

def isLocked(user):
    """
    Return true if user is locked
    """
    return user.profile.locked

def UnlockUser(user):
    """
    Release the lock by setting locked to False
    """
    user.profile.locked = False
    user.save()
