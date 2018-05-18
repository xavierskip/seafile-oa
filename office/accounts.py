# coding:utf-8
# base on seahub.base.accounts
from seaserv import ccnet_threaded_rpc
from seahub.base.accounts import User, UserManager
from seahub.base.accounts import AuthBackend as seafileAuthBackend
from seahub.base.templatetags.seahub_tags import email2nickname
from office.models import Info


class MyError(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.__repr__() + self.msg


class OfficeUserManager(UserManager):

    def get(self, email=None, id=None):
        if not email and not id:
            raise User.DoesNotExist, 'User matching query does not exits.'

        if email:
            emailuser = ccnet_threaded_rpc.get_emailuser(email)
        if id:
            emailuser = ccnet_threaded_rpc.get_emailuser_by_id(id)
        if not emailuser:
            raise User.DoesNotExist, 'User matching query does not exits.'

        user = OfficeUser(emailuser.email) # replace Origin
        user.pk = emailuser.id  # fit with admin site log, django.contrib.admin templatetags.log.AdminLogNode

        user.id = emailuser.id
        user.enc_password = emailuser.password
        user.is_staff = emailuser.is_staff
        user.is_active = emailuser.is_active
        user.ctime = emailuser.ctime
        user.org = emailuser.org
        user.source = emailuser.source
        user.role = emailuser.role

        return user


class OfficeUser(User):
    objects = OfficeUserManager()  # replace Origin

    def __init__(self, email):
        super(OfficeUser, self).__init__(email)
        self.nickname = email2nickname(self.username)
        self.__office_role = self.get_roles()

    def __repr__(self):
        return '<%s:%s>' % (self.__class__, self.username)

    def get_roles(self):
        """
        office_manager: set in db
        office_admin: user.is_staff
        """
        return Info.objects.value2key(self.username)

    # for django.contrib.admin
    # used in base.html #user-tools
    # {% firstof user.get_short_name user.get_username %}
    def get_short_name(self):
        return self.nickname

    def get_username(self):
        return self.username

    @property
    def is_officer(self):
        return self.is_office_admin or self.is_office_manager

    @property
    def is_office_manager(self):
        return 'office_manager' in self.__office_role

    @property
    def is_office_admin(self):
        return self.is_staff

    # for admin site
    # office_manager user has all permission as the super user
    def has_perm(self, perm, obj=None):
        model = perm.split('.')[-1].split('_')[-1]
        # print('has_perm', locals(), self.__office_role)
        if self.is_office_admin and model == 'info':
            return True
        elif self.is_office_manager and model != 'info':
            return True
        else:
            return False

    def has_perms(self, perm_list, obj=None):
        for perm in perm_list:
            if not self.has_perm(perm, obj):
                return False
        return True

    def has_module_perms(self, app_label):
        """
        for admin site
        """
        # print('module_perms', locals(), self.__office_role)
        return self.is_officer


class AuthBackend(seafileAuthBackend):
    def get_user(self, username):
        # seahub.base.accounts.AuthBackend use get_user_with_import() to get the user
        # if you use LDAP you need user get_user_with_import()
        # get_user_with_import() from seafile/python/seaserv/api.py
        try:
            user = OfficeUser.objects.get(email=username)
        except OfficeUser.DoesNotExist:
            user = None
        return user

    # def authenticate(self, username=None, password=None):
    #     try:
    #         user = OfficeUser.objects.get(email=username)
    #         if user.check_password(password):
    #             return user
    #     except OfficeUser.DoesNotExist:
    #         return None

    # def get_group_permissions(self, user_obj, obj=None):
    #     raise MyError('todo')
    #
    # def get_all_permissions(self, user_obj, obj=None):
    #     raise MyError('todo')
    #
    # def has_perm(self, user_obj, perm, obj=None):
    #     raise MyError('todo')
    #
    # def has_module_perms(self, user_obj, app_label):
    #     raise MyError('todo')
