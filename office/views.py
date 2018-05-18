# coding:utf-8
"""
the function argument hashid preprocessed in MIDDLEWARE_CLASSES
"""
from django.core.urlresolvers import reverse, reverse_lazy
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from seahub.contacts.signals import mail_sended
from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, render_to_response, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from seahub.views.ajax import delete_dirent, check_folder_permission
from seahub.share.views import ajax_private_share_dir, share_to_user, share_to_group
from django.utils import timezone, dateparse
from seahub.utils import send_perm_audit_msg, is_valid_username, is_org_context
from office.models import Document, Member, Distribution, Commit, Info, Attachment, Issue, BlockHole
from office.accounts import OfficeUser, MyError
from office.admin import seafile_mkdir
from office.forms import CommitForm
from office.settings import HASHIDS
from office.utils import find_at
from office.ajax import get_file_op_url
from seaserv import seafile_api
from seaserv.service import SearpcError
import seaserv
import json

PER_PAGE = 10
LOGIN_JUMP = reverse_lazy('office_jump')


# handle paginator
def get_paginator_page(query_set, page, per_page=20):
    """
    :return: instance of django.core.paginator.Paginator
    """
    paginator = Paginator(query_set, per_page)
    try:
        p = paginator.page(page)  # 获取某页对应的记录
    except PageNotAnInteger:  # 如果页码不是个整数
        p = paginator.page(1)  # 取第一页的记录
    except EmptyPage:  # 如果页码太大，没有相应的记录
        p = paginator.page(paginator.num_pages)  # 取最后一页的记录
    return p


def remove_share_repo(repo_id, from_email, to_email):  # todo: useless, abandon
    seaserv.remove_share(repo_id, from_email, to_email)
    send_perm_audit_msg('delete-repo-perm', from_email, to_email, repo_id, '/', 'rw')


def share_repo(request, repo_id, emails_set, groups=''):  # todo: useless, abandon
    """ share sub repo
    :param request:
    :param repo_id: repo id
    :param emails_set: type set
    :param groups: type set
    :return: json HttpResponse
    """
    root_user = Info.objects.root_user
    request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'  # need ajax request
    if len(emails_set) == 1 and list(emails_set)[0] == root_user:  # share to yourself
        return HttpResponse(json.dumps({
            "shared_success": list(emails_set),
        }))
    else:
        request.user = OfficeUser.objects.get(email=root_user)  # repo belong root_user
        post = request.POST.copy()
        post['repo_id'] = repo_id
        post['perm'] = request.POST.get('perm', 'rw')
        post['path'] = '/'  # sub/virtual repo path for share
        post['emails'] = ','.join(emails_set)
        post['groups'] = ','.join(groups)
        request.POST = post
        return ajax_private_share_dir(request)


# request GET
def login_jump(request):
    url = '?'.join([reverse('auth_login'), request.META['QUERY_STRING']])
    return render(request, 'login_jump.html', {
        'url': url,
    })


def home(request):
    """ root path home page """
    if request.user.is_anonymous():
        return redirect('officeHistory')
    else:
        return index(request)


# @login_required(login_url=LOGIN_JUMP)
def index(request):
    """ all you own office """
    page = request.GET.get('page')
    username = request.GET.get('user') if request.GET.get('user') else request.user.username
    query_set = Document.objects.filter(member__uid=username).order_by('-member__modified')
    doc_page = get_paginator_page(query_set, page, PER_PAGE)
    return render(request, 'office_index.html', {
        'document_page': doc_page,
        'banner': u'文件列表',
        'username': username
    })


@login_required(login_url=LOGIN_JUMP)
def user_index(request, username):
    if is_valid_username(username):
        get_copy = request.GET.copy()
        get_copy['user'] = username
        request.GET = get_copy
        return index(request)
    else:
        raise Http404("user does not exist")


# @login_required(login_url=LOGIN_JUMP)
def history(request):
    """  all documents page """
    page = request.GET.get('page')
    query_set = Document.objects.all().order_by('-registered', '-id')
    doc_page = get_paginator_page(query_set, page, PER_PAGE)
    return render(request, 'office_history.html', {
        'document_page': doc_page,
        'banner': u'文件历史',

    })


@login_required(login_url=LOGIN_JUMP)
def distribute_doc(request, distributed=True):
    """admin to be distribute"""
    page = request.GET.get('page')
    query_set = Document.objects.user_distribute(
        request.user.username,
        distributed
    ).order_by('-distribution__modified')
    doc_page = get_paginator_page(query_set, page, PER_PAGE)
    return render(request, 'office_distribution.html', {
        'document_page': doc_page,
        'distributed': distributed,
        'banner': u'分发文件',
    })


@login_required(login_url=LOGIN_JUMP)
def todo_doc(request, todo=True):
    """ document commitsed or no """
    page = request.GET.get('page')
    query_set = Document.objects.user_todo(
        request.user.username,
        todo
    ).order_by('-distribution__modified')
    doc_page = get_paginator_page(query_set, page, PER_PAGE)
    return render(request, 'office_todo.html', {
        'document_page': doc_page,
        'todo': todo,
        'banner': u'我的文件',
    })


# @login_required(login_url=LOGIN_JUMP)
def document_page(request, hashid):
    """show document detail"""
    doc = Document.objects.get(id=hashid)
    try:
        pre_id = int(Document.objects.filter(id__gt=hashid)[0].id)
    except IndexError:
        pre_id = None
    try:
        next_id = int(Document.objects.filter(id__lt=hashid).order_by('-id')[0].id)
    except IndexError:
        next_id = None
    doc_distr = doc.distribution
    if request.user.username == doc_distr.uid and doc_distr.commit is None:
        return render(request, 'distribute_doc.html', {
            'doc': doc,
            'pre_id': pre_id,
            'next_id': next_id,
        })
    else:
        members_query = doc.member_set.all().order_by('commit__created')
        # note: some with empty commit
        valid_commits = [doc_distr.commit] if doc_distr.commit else []
        valid_commits.extend([m.commit for m in members_query if m.commit])
        invalid_commits = set(doc.commit_set.all()) - set(valid_commits)
        try:
            need_commit = not bool(doc.member_set.get(uid=request.user.username).commit)
        except ObjectDoesNotExist:
            need_commit = False
        return render(request, 'commit_doc.html', {
            'doc': doc,
            'pre_id': pre_id,
            'next_id': next_id,
            'valid_commits': valid_commits,
            'invalid_commits': invalid_commits,
            'need_commit': need_commit,
        })


def print_form(request, hashid):
    """render processing from"""
    doc = Document.objects.get(id=hashid)
    return render(request, 'doc_form.html', {
        'doc': doc,
    })


# requests POST
def commit_handler(request, doc, commit_update=None):
    """ create or update commit process
    :return: commit obj
    """
    commit = request.POST['commit'].strip()  # claear the whitespace
    if commit == '':
        raise MyError(u'empty commit')
    old_set = find_at(commit_update.content) if commit_update else set()
    new_set = find_at(commit)
    Member.objects.merge(doc, new_set, old_set)
    if commit_update:  # create or update
        commit_update.content = commit
        commit_update.save()
        return commit_update
    else:
        return Commit.objects.create(doc=doc, uid=request.user.username, content=commit)


def distribution_document(request, hashid):
    """ document_root distribute document """
    doc = Document.objects.get(id=hashid)
    distribute = doc.distribution  # distribution to be created when create the document in admin site
    if distribute.uid != request.user.username:
        return HttpResponseForbidden('you don\'t own this document')
    if distribute.commit:
        return HttpResponseForbidden('you already committed')
    else:
        try:
            distribute.commit = commit_handler(request, doc)
            distribute.save()
        except MyError as e:
            return HttpResponse(e.msg, status=403)
        return HttpResponseRedirect(reverse(document_page, args=(HASHIDS.encode(hashid),)))


def commit_document(request, hashid):
    """commit"""
    doc = Document.objects.get(id=hashid)
    try:
        member = Member.objects.get(doc=doc, uid=request.user.username)
    except Member.DoesNotExist:
        return HttpResponseForbidden('you don\'t own this document')
    if member.commit:
        return HttpResponseForbidden('you already committed')
    else:
        try:
            commit_obj = commit_handler(request, doc)
            member.refresh_from_db()  # Member.objects.merge in commit_handler() will change the Member.count
            member.commit = commit_obj
            member.save()
        except MyError as e:
            return HttpResponse(e.msg, status=403)
        return HttpResponseRedirect(reverse(document_page, args=(HASHIDS.encode(hashid),)))


def update_commit(request, hashid):
    commit = Commit.objects.get(id=hashid)
    if commit.uid != request.user.username:
        return HttpResponseForbidden('you don\'t own this commit')
    if request.method == "GET":
        content_type = 'application/json; charset=utf-8'
        url = reverse(update_commit, args=(HASHIDS.encode(hashid),))
        return HttpResponse(json.dumps({'commit': commit.content, 'url': url}), content_type=content_type)
    if request.method == "POST":
        try:
            commit_handler(request, commit.doc, commit)
        except MyError as e:
            return HttpResponse(e.msg, status=403)
        return HttpResponseRedirect(reverse(document_page, args=(HASHIDS.encode(commit.doc_id),)))


# ajax
# need check permission
def get_upload_url(request):
    """get the url for update file with seafile
    get_file_op_url() need request.GET 'op_type' 'path' and argument 'repo_id'
    """
    content_type = 'application/json; charset=utf-8'

    if not request.user.is_office_manager:
        return HttpResponse(json.dumps({"error": "Permission denied"}),
                            status=403,
                            content_type=content_type)
    get_copy = request.GET.copy()  # QueryDict instance is immutable
    path = request.GET['folder']
    if request.GET.get('repo'):
        repo_id = request.GET.get('repo')
    else:
        repo_id = Info.objects.root_repo
        seaobj = seafile_api.get_dirent_by_path(repo_id, path)
        if not seaobj:
            seafile_mkdir(repo_id, '', path, request.user.username)
            BlockHole.objects.create(folder=path)
    get_copy['path'] = path
    # get_copy['op_type'] = request.GET.get('op_type', 'upload')
    get_copy['op_type'] = 'upload'
    request.GET = get_copy  # Update Request
    # request.user = OfficeUser.objects.get(email=Info.objects.root_user)  # Update user
    http_response = get_file_op_url(request, repo_id)
    if http_response.status_code == 200:  # store upload file
        j = json.loads(http_response.content)
        j['parent_dir'] = path
        http_response.content = json.dumps(j)
    return http_response


def delete_file(request):
    """ajax for admin site add page to clear the upload file
    delete_dirent() should POST request
    """
    req_get = request.GET.copy()
    req_get['parent_dir'] = request.GET['folder']
    req_get['name'] = request.GET['filename']
    if request.GET.get('repo'):
        repo_id = request.GET.get('repo')
    else:
        repo_id = Info.objects.root_repo
    request.GET = req_get
    request.method = 'POST'
    return delete_dirent(request, repo_id)


# @login_required
def get_organization(request):
    symbol = request.GET['symbol']
    r = Issue.objects.filter(symbol=symbol).values('organization')
    if r:
        return HttpResponse(json.dumps(r[0]), content_type='application/json')
    else:
        return HttpResponse(json.dumps({'error': 'not found'}), content_type='application/json')


# search view, GET or POST
# @login_required(login_url=LOGIN_JUMP)
def search_doc(request):
    if request.method == 'GET':
        # use html5 date widget if it's chrome
        chrome = 'Chrome' in request.META.get('HTTP_USER_AGENT')
        return render(request, 'office_search.html', {
            'chrome': chrome,
        })
    if request.method == 'POST':
        max_result = 100
        docs = []
        count = 0
        tips = u'没有找到符合条件的结果。'
        kwargs = {}
        field_lookup = ['reference', 'title', 'issue']
        for field in field_lookup:
            v = request.POST.get(field)
            if v:
                lookup = '__'.join([field, 'icontains'])
                kwargs[lookup] = v
        # replace('/','-') is use for admin date widget
        reg_date = request.POST.get('reg_date').replace('/', '-')
        from_date = request.POST.get('from_date').replace('/', '-')
        to_date = request.POST.get('to_date').replace('/', '-')
        if reg_date:
            kwargs['registered'] = dateparse.parse_date(reg_date)
        else:
            if from_date or to_date:
                if from_date:
                    lookup = '__'.join(['registered', 'gte'])
                    kwargs[lookup] = dateparse.parse_date(from_date)
                if to_date:
                    lookup = '__'.join(['registered', 'lte'])
                    kwargs[lookup] = dateparse.parse_date(to_date)
        # print kwargs
        if request.POST.get('related'):
            kwargs['member__uid'] = request.user.username
        if kwargs:
            docs = Document.objects.filter(**kwargs).order_by('-registered', '-id')
            count = docs.count()
            if count > max_result:
                docs = []
                count = False
                tips = u'返回了太多的结果，请确定了更精确的范围再来检索。'
        return render(request, 'search_result.html', {
            'docs': docs,
            'count': count,
            'tips': tips,
        })
        # return HttpResponse(json.dumps({'success': True}), content_type = 'application/json; charset=utf-8')


# below for test
def display_meta(request):
    raise KeyError
    test1 = request.GET.get('test')
    if test1:
        return HttpResponse('test: %s' % test1)
    else:
        values = request.META.items()
        values.sort()
        html = []
        for k, v in values:
            html.append('<tr><td>%s</td><td>%s</td></tr>' % (k, v))
        return HttpResponse('<table>%s</table>' % '\n'.join(html))


@login_required(login_url=LOGIN_JUMP)
def test(request, page=13):
    if request.method == 'GET':
        # return HttpResponseRedirect(reverse('auth_login'), {'redirect_if_logged_in': 'myhome'})
        try:
            title = request.GET['title']
        except Exception, e:
            # raise False
            title = "another title!"
        list = ['fe', '32', 423, 'e23']
        d = {'name': 'test@test.org'}
        # return render(request, 'test.html', {'list':lists, 'site_title':title})
        # raise KeyError
        return render_to_response('test/test.html', {
            'list': list,
            'site_title': title,
            'd': d,
            'CommitForm': CommitForm,
        }, context_instance=RequestContext(request))
    if request.method == 'POST':
        content_type = 'application/json; charset=utf-8'
        err_msg = 'test fail'
        return HttpResponse(json.dumps({"error": err_msg}), status=200,
                            content_type=content_type)


@login_required(login_url=LOGIN_JUMP)
def test_paginator(request):
    limit = 3  # 每页显示的记录数
    items = Attachment.objects.all()
    paginator = Paginator(items, limit)  # 实例化一个分页对象

    page = request.GET.get('page')  # 获取页码
    try:
        items = paginator.page(page)  # 获取某页对应的记录
    except PageNotAnInteger:  # 如果页码不是个整数
        items = paginator.page(1)  # 取第一页的记录
    except EmptyPage:  # 如果页码太大，没有相应的记录
        items = paginator.page(paginator.num_pages)  # 取最后一页的记录

    return render_to_response('test/test_paginator.html', {'items': items})
