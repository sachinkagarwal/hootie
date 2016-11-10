from django.contrib import admin
from .models import *
import utils.capquotanums as cqnums
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django import forms
from traceback import format_exc

# Register your models here.
class VolumeAdmin(admin.ModelAdmin):
    standard_fields = ['root_path','sub_path','size_GB','options','allowed_hosts']
    superuser_fields = ['owner']

    def get_queryset(self,request):
        """
        Limit queryset to volumes owned by user.
        """
        qs = super(VolumeAdmin,self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

    def save_model(self,request,obj,form,change):
        """
        Set the owner of to the standard user who is making 
        the request from Django admin.
        """
        if not request.user.is_superuser:
            obj.owner = request.user
        super(self.__class__,self).save_model(request,obj,form,change)

    def get_form(self,request,obj=None, **kwargs):
        """
        Fields for the detail/edit form depend on the type of user.
        The superuser can create a volume for anyone, a standard user
        can only create a volume for itself.
        """
        if request.user.is_superuser:
            self.fields = self.standard_fields + self.superuser_fields
        else:
            self.fields = self.standard_fields
        return super(VolumeAdmin, self).get_form(request,obj, **kwargs)



admin.site.register(Volume,VolumeAdmin)

admin.site.register(NFSServer)
admin.site.register(RootPath)


#Code for bringing extended user attributes to Django admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.admin.views.main import ChangeList
from .models import Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = '__all__' 

class ProfileInline(admin.StackedInline):
    form = ProfileForm
    model = Profile
    can_delete = False
    list_display=[]
    verbose_name_plural = 'Quota Information'


class UserChangeList(ChangeList):
    def get_results(self, *args, **kwargs):
        super(UserChangeList,self).get_results(*args, **kwargs)


admin.site.unregister(User)
class UserAdmin(UserAdmin):
    def save_model(self, request, obj, form, change):
        if request.user.is_superuser:
            obj.is_staff = True
            obj.save()

    inlines = (ProfileInline,)
    list_display = ('username','email','quota_GB','allocated_GB','isLocked' )
    
    def allocated_GB(self,obj):
        try:
            return cqnums.user_allocated(obj)
        except:
            print format_exc()
            return 0
    
    def quota_GB(self,obj):
        return obj.profile.quota_GB

    def isLocked(self,obj):
        return obj.profile.locked

    def get_changelist(self, request):
        return UserChangeList

admin.site.register(User, UserAdmin)


