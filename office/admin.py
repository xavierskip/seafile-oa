# coding:utf-8
from django.contrib.admin import AdminSite, ModelAdmin, TabularInline, StackedInline, SimpleListFilter
from django.contrib.admin.views import main
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.views.decorators.cache import never_cache
from django.core.urlresolvers import reverse, reverse_lazy
from django.forms import TextInput, Textarea, ModelForm
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.db.models import Count
from django.db import models
from office.models import Document, Attachment, Commit, Distribution, Issue, BlockHole, Info
from office.forms import DocumentAdminForm
from seaserv import seafile_api
from seaserv.service import SearpcError
import posixpath
import uuid
import re


def gen_folder_name():
    """ Generate a unique folder name
    """
    return uuid.uuid4().hex


def seafile_mkdir(repo_id, parent_dir, dir_path, username):
    """ mkdir with a path
    """
    for d in dir_path.split('/'):
        if d == '':  # pass path like '/a/b/' or 'a/b/'
            continue
        try:
            seafile_api.post_dir(repo_id, parent_dir, d, username)
        except SearpcError as e:
            # todo: log it
            print('{}/{} {}'.format(parent_dir, d, e))
            pass
        parent_dir = posixpath.join(parent_dir, d)
    return parent_dir


def login_redirect(viewname="office.views.home"):
    tup = reverse('auth_login'), REDIRECT_FIELD_NAME, reverse(viewname)
    return HttpResponseRedirect('%s?%s=%s' % tup)


def get_issue_symbol(s):
    """return the china chars from str startswith"""
    r = re.match(u'^[\u4E00-\u9FA5]+', s)
    return r.group() if r else None


def auto_issue_symbol(obj):
    """prepare fill out Issue for automatically
    obj: Document model
    """
    if obj.reference:
        symbol = get_issue_symbol(obj.reference)
        if symbol:
            Issue.objects.update_or_create(defaults={'organization': obj.issue}, symbol=symbol)


# Convenient to testing
def after_document_save(obj, username, folder):
    """use for Admin site response_add
    :param obj: Instance of Document model
    :param username:
    :param folder:
    :return:
    """
    root_repo_id = Info.objects.root_repo
    # distribution document
    Distribution.objects.create(doc=obj, uid=username)
    auto_issue_symbol(obj)
    seaobj = seafile_api.get_dirent_by_path(root_repo_id, folder)
    if seaobj:
        o = BlockHole.objects.get(folder=folder)
        o.delete()
    else:  # create document folder if docuemnt don't have attachment
        seafile_mkdir(root_repo_id, '', folder, username)
    obj.repo_id = root_repo_id
    obj.save()


class DigitalFilter(SimpleListFilter):
    title = u'数字化'
    parameter_name = 'digital'

    def lookups(self, request, model_admin):
        return (
            ('False', u'有电子版'),
            ('True', u'无电子版')
        )

    def queryset(self, request, queryset):
        """
        note: only handle the value returned by lookups()
        """
        if self.value() == 'False':
            return queryset.filter(attachment__doc__isnull=False)
        if self.value() == 'True':
            return queryset.filter(attachment__doc__isnull=True)


class IssueFilter(SimpleListFilter):
    title = u"发文单位"
    parameter_name = 'issue'

    def lookups(self, request, model_admin):
        limit = 50
        q = Document.objects.values('issue').annotate(Count('issue')).order_by(Count('issue').desc(), 'issue')
        return [(i['issue'], "%s(%s)" %(i['issue'], i['issue__count'])) for i in q[:limit]]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(issue=self.value())


class MyAdminSite(AdminSite):
    site_header = u'文件管理'
    site_title = u'文件管理'
    index_title = u'登记台'
    site_url = '/oa/'

    @never_cache
    def login(self, request, extra_context=None):
        return login_redirect('admin:index')

    def has_permission(self, request):
        """
        Returns True if the given HttpRequest has permission to view
        *at least one* page in the admin site.
        """
        try:
            return request.user.is_officer
        except AttributeError:
            return False


class ModelAdminCustom(ModelAdmin):
    def __init__(self, *args, **kwargs):
        """ Django 1.9 don't need this
        Changed admin EMPTY_CHANGELIST_VALUE from (None) to -
        http://stackoverflow.com/a/28175877/1265727
        """
        super(ModelAdminCustom, self).__init__(*args, **kwargs)
        main.EMPTY_CHANGELIST_VALUE = '-'

    # todo: log it without foreign key
    # the LogEntry model need ForeignKey(settings.AUTH_USER_MODEL)
    def log_addition(self, request, object):
        pass

    def log_change(self, request, object, message):
        pass

    def log_deletion(self, request, object, object_repr):
        pass


class AttachmentInline(TabularInline):
    model = Attachment
    verbose_name = u'电子文件'
    verbose_name_plural = u'电子文件'
    extra = 0
    fields = ('file',)
    # fieldsets = (
    #     (u'附件', {
    #         'description': u'可拖拽文件到此页面上传。',
    #         'fields': ('file', )
    #     }),
    # )
    formfield_overrides = {
        models.CharField: {
            'widget': TextInput(attrs={
                'readonly': 'True',
                'size': '100'
            })
        }
    }


class CommentInline(StackedInline):
    model = Commit


class DocumentAdmin(ModelAdminCustom):
    def reg_date(self, obj):
        return obj.registered.strftime("%Y.%m.%d")
    reg_date.short_description = u'日期'
    reg_date.admin_order_field = 'registered'

    def pagination_print(modeladmin, request, queryset):
        ids = [i.id for i in queryset]
        return render(request, 'doc_forms.html', {
            'ids': ids,
        })
    pagination_print.short_description = u'打印处理单'

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '100'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 100})},
    }
    form = DocumentAdminForm
    # change/add forms
    # exclude = (fields...)
    # fields = ()
    fieldsets = (
        (u'文件登记', {
            # 'classes': ['wide'],
            'description': u'深色字段的内容必填，浅色字段的内容可以为空。拖拽文件到页面即可上传文件，根据文件名自动填写信息。',
            'fields': ('reference', 'title', 'issue', 'generated', 'registered')
        }),
        (u'备注其他', {
            'description': u'状态分为三个等级。无关、普通、紧急，默认为「普通」。',
            'classes': ['collapse'],
            'fields': ('urgent', 'note')
        }),
        (u'hide', {
            'classes': ['hide'],  # defined by the default admin site css are collapse and wide.
            'fields': ('repo_id', 'folder')
        }),
    )
    # filter_horizontal = ('tags',)
    # filter_vertical = ('tags',)
    inlines = [AttachmentInline]
    # save_as = True

    # change list page
    # actions_selection_counter = True
    # filter_horizontal = [ManyToManyField,]
    # filter_vertical = [ManyToManyField,]
    list_per_page = 50
    list_display = ('title', 'reference', 'issue', 'reg_date', 'assigned', 'preview')
    # list_display_links = ['title', 'reference']
    # list_editable = ['generated']
    # list_select_related = True
    actions = ['pagination_print']
    actions_on_top = False
    actions_on_bottom = True
    date_hierarchy = 'registered'
    list_filter = ('registered', IssueFilter, DigitalFilter)
    search_fields = ('reference', 'title', 'issue', 'attachment__file')

    add_form_template = 'admin/document_form.html'
    change_form_template = 'admin/document_form.html'

    def response_add(self, request, obj, post_url_continue=None):
        """is called after the admin form is submitted and just after
        the object and all the related instances have been created and saved
        """
        uid = request.user.username
        folder = request.POST['folder']
        after_document_save(obj, uid, folder)
        return super(DocumentAdmin, self).response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        auto_issue_symbol(obj)  # auto update issue_symbol
        return super(DocumentAdmin, self).response_change(request, obj)

    def add_view(self, request, form_url='', extra_context=None):
        if not extra_context:
            extra_context = {}
        extra_context.update({
            'uuid_folder': gen_folder_name(),
        })
        return super(DocumentAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if not extra_context:
            extra_context = {}
        extra_context.update({
            'uuid_folder': gen_folder_name(),
        })
        return super(DocumentAdmin, self).change_view(request, object_id, form_url, extra_context)

    def delete_model(self, request, obj):
        return super(DocumentAdmin, self).delete_model(request, obj)

    # def get_action_choices(self, request, **kwargs):
    #     choices = super(DocumentAdmin, self).get_action_choices(request)
    #     choices.pop(0)  # clear default_choices
    #     # choices.reverse()  # change choices order
    #     return choices

    def changelist_view(self,request, **kwargs):
        choices = self.get_action_choices(request)
        choices.pop(0)  # clear default_choices
        action_form = self.action_form(auto_id=None)
        action_form.fields['action'].choices = choices
        action_form.fields['action'].initial = 'pagination_print'
        extra_context = {'action_form': action_form}
        return super(DocumentAdmin, self).changelist_view(request, extra_context)


class InfoAdmin(ModelAdminCustom):
    list_display = ('key', 'value')

site = MyAdminSite()
site.register(Document, DocumentAdmin)
site.register(Info, InfoAdmin)
