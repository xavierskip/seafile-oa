# coding:utf-8
import os
from django.db import models
from django.db.models import F, Q
from django.db.models.signals import post_delete
from django.utils import timezone
from django.utils.html import format_html
from django.dispatch import receiver
from django.core.urlresolvers import reverse
from seaserv import seafile_api
from office.settings import HASHIDS
from office.utils import find_at


class BasisManager(models.Manager):
    pass
    # def update_or_create(self, defaults=None, **kwargs):
    #     """ New in Django 1.7
    #     :param defaults: fields what you update
    #     :param kwargs: fields what you create object
    #     :return: obj, [create: True | update: False]
    #     """
    #     defaults = defaults or {}
    #     try:
    #         obj = self.model.objects.get(**kwargs)
    #         for key, value in defaults.iteritems():
    #             setattr(obj, key, value)
    #         obj.save()
    #         return obj, True
    #     except self.model.DoesNotExist:
    #         defaults.update(kwargs)
    #         obj = self.model(**defaults)
    #         obj.save()
    #         return obj, False


# abstract Model
class TimeStampedModel(models.Model):
    """
    abstract base class, 提供创建时间和修改时间两个通用的field
    """
    created = models.DateTimeField(u'生成时间', auto_now_add=True)
    modified = models.DateTimeField(u'修改时间', auto_now=True)

    class Meta:
        abstract = True


class Tag(models.Model):
    name = models.CharField(max_length=32)


class DocumentManager(BasisManager):
    def user_distribute(self, username,commit):
        """
        :param commit: bool
        :return: query_set
        """
        return self.filter(
            distribution__uid = username,
            distribution__commit__isnull = commit
        )

    def user_todo(self, username,commit):
        """
        :param commit: bool
        :return: query_set
        """
        return self.filter(
            member__uid = username,
            member__commit__isnull = commit
        )

class Document(models.Model):
    STATE_CHOICES = (
        (0, u'紧急'),  # urgent
        (1, u'普通'),  # common
        (2, u'无关'),  # unrelated
    )
    reference = models.CharField(u'文号', max_length=32, unique=True, null=True, blank=True, default=None)
    title = models.CharField(u'文题', max_length=256)
    issue = models.CharField(u'发文单位', max_length=128)
    generated = models.DateField(u'成文时间', default=timezone.now)
    registered = models.DateField(u'登记时间', default=timezone.now)
    urgent = models.PositiveSmallIntegerField(u'状态', choices=STATE_CHOICES, default=1)
    note = models.TextField(u'备注', max_length=512, null=True, blank=True)
    tags = models.ManyToManyField(Tag)
    folder = models.CharField(max_length=128, null=True, blank=True, default=None)  # len 32 gen by gen_folder_name()
    repo_id = models.CharField(max_length=36, null=True, blank=True, default=None)  # len 36

    objects = DocumentManager()

    class Meta:
        verbose_name = u'文件'
        verbose_name_plural = u'文件'

    def __unicode__(self):
        # reference can be None
        return u'%s%s' % (u'%s：' % self.reference if self.reference else '', self.title)

    def commit_progress(self):
        """
        show commit progress
        :return: str "done/all"
        """
        done = self.member_set.filter(commit__isnull=False).count()
        count = self.member_set.count()
        if count == 0:
            return 0
        else:
            return '%s/%s' % (done, count)

    def delete(self, using=None):
        # print 'delete %s' %self
        seafile_api.del_file(self.repo_id, '', self.folder, 'Admin site')
        return super(Document, self).delete(using)

    def get_absolute_url(self):
        return reverse('office.views.document_page', args=[HASHIDS.encode(self.id)])

    def assigned(self):
        # return True
        return bool(self.distribution.commit_id)
    assigned.boolean = True
    assigned.short_description = u'办'
    assigned.admin_order_field = 'registered'

    def preview(self):
        """ use in list_display """
        url = self.get_absolute_url()
        # format UnicodeEncodeError
        # http://stackoverflow.com/questions/3235386/python-using-format-on-a-unicode-escaped-string
        return format_html(u'<a href="{0}" target="_blank">{1}</a>', url, u'打开')
    preview.short_description = u'浏览'
    preview.allow_tags = True  # avoid XSS should format_html()
    preview.admin_order_field = 'registered'

    def print_form_num(self):
        """ show in form for print page"""
        return int(Document.objects.filter(
            registered__year = self.registered.year,
            id__lt = self.id
        ).count()) + 1


class Attachment(models.Model):
    doc = models.ForeignKey(Document)
    file = models.CharField(max_length=1024, verbose_name=u'文件名', help_text='drop and drag')
    created = models.DateTimeField(u'生成时间', auto_now_add=True)

    def __unicode__(self):
        return self.file if len(unicode(self.file)) < 20 else os.path.basename(unicode(self.file))

    @property
    def repo(self):
        """ belong to the repo
        """
        return self.doc.repo_id

    @property
    def path(self):
        """ Root repo absolute path """
        return os.path.join(self.doc.folder, self.file)

    @property
    def file_obj(self):
        return seafile_api.get_dirent_by_path(self.repo, self.path)

    def get_absolute_url(self):
        return reverse('view_lib_file', args=[self.repo, '/%s' % self.path])
        # virtual repo
        # return reverse('view_lib_file', args=[self.repo, '/%s' % self.file])

    def delete(self, *args, **kwargs):
        seafile_api.del_file(self.repo, self.doc.folder, self.file, 'Django')
        return super(Attachment, self).delete(*args, **kwargs)


class Commit(TimeStampedModel):
    doc = models.ForeignKey(Document, verbose_name='document')
    uid = models.CharField(max_length=255)
    content = models.TextField(max_length=1024)

    objects = BasisManager()

    def __unicode__(self):
        return u"%s:%s" % (self.uid, self.doc_id)


class MemberManager(BasisManager):
    def users(self, docid):
        return self.values_list('uid', flat=True).filter(doc=docid)

    def users_set(self, docid):
        return set(self.users(docid))

    def user_add(self, doc_obj, uid):
        try:
            member = self.get(doc=doc_obj, uid=uid)
            member.count = F('count') + 1
            member.save()
        except Member.DoesNotExist:
            member = self.create(doc=doc_obj, uid=uid)
        return member

    def user_minus(self, doc_obj, uid):
        """
        remove the Member when the count is 1, else count minus 1
        """
        member = self.get(doc=doc_obj, uid=uid)
        if member.count <= 1:
            member.delete(with_commit=False)
        else:
            member.count = F('count') - 1
            member.save()
        return member

    def merge(self, doc_obj, new_members, old_members=set()):
        """
        :param doc_obj: "Document" instance
        :param new_members: type is set, new member
        :return:
        """
        for u in (new_members - old_members):
            self.user_add(doc_obj, u)
        for u in (old_members - new_members):
            self.user_minus(doc_obj, u)


class Member(TimeStampedModel):
    doc = models.ForeignKey(Document)
    uid = models.CharField(max_length=255)
    commit = models.OneToOneField(Commit, null=True, verbose_name='comment')
    count = models.IntegerField(default=1)

    objects = MemberManager()

    def __unicode__(self):
        return u"%s:%s" % (self.uid, self.doc_id)

    def get_absolute_url(self):
        return reverse('office.views.document_page', args=[int(self.doc_id)])

    def delete(self, using=None, with_commit=True):
        if self.commit:
            content = self.commit.content
            remove_set = find_at(content)
            Member.objects.merge(self.doc, set(), remove_set)
        if with_commit:
            self.commit.delete()
        super(Member, self).delete(using)


class Distribution(TimeStampedModel):
    doc = models.OneToOneField(Document)
    uid = models.CharField(max_length=255)
    commit = models.OneToOneField(Commit, null=True, verbose_name='comment')

    def __unicode__(self):
        return u"%s:%s" % (self.doc_id, self.uid)

    def get_absolute_url(self):
        return reverse('office.views.document_page', args=[int(self.doc_id)])


class Issue(models.Model):
    symbol = models.CharField(max_length=32, primary_key=True)
    organization = models.CharField(max_length=256)

    objects = BasisManager()


class InfoManager(BasisManager):
    def key2value(self, key):
        return self.values_list('value', flat=True).get(key=key)

    def value2key(self, value):
        return set(self.values_list('key', flat=True).filter(value=value))

    # def get_admins(self):
    #     kvs = self.filter(Q(key='root') | Q(key='admin'))
    #     return set([k.value for k in kvs])

    @property
    def root_repo(self):
        return self.key2value('root_repo')

    def get_download(self):
        return self.key2value('download')

    # @property
    # def root_user(self):  # todo: remove it
    #     return self.key2value('repo_user')


class Info(models.Model):
    key = models.CharField(max_length=32, primary_key=True)
    value = models.CharField(max_length=256)

    objects = InfoManager()

    class Meta:
        verbose_name = u'设置'
        verbose_name_plural = u'设置'

    def __unicode__(self):
        return u'%s' % self.key


class BlockHole(models.Model):
    # to save the folder name for upload files at admin site add view page
    # MySQL does not allow unique CharFields to have a max_length > 255
    folder = models.CharField(max_length=128, unique=True)

    def __unicode__(self):
        return self.folder

# abandon
# def del_root_repo_dirent(path):
#     """delete file from root repo
#     """
#     repo_id = Info.objects.root_repo
#     parent_dir, filename = os.path.split(path)
#     # print repo_id, path
#     return seafile_api.del_file(repo_id, parent_dir, filename, Info.objects.root_user)


# Signal use for QuerySet.delete()
# for delete obj in admin site
@receiver(post_delete, sender=Document)
def del_document_handler(sender, **kwargs):
    obj = kwargs['instance']
    print sender, obj
    seafile_api.del_file(obj.repo_id, '', obj.folder, 'Django')

# Do not need to delete each file that has also been deleted with folder
# @receiver(post_delete, sender=Attachment)
# def del_attachment_handler(sender, **kwargs):
#     obj = kwargs['instance']
#     print sender, obj
#     seafile_api.del_file(obj.repo, obj.doc.folder, obj.file, 'Django')
