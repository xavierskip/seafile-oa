# coding:utf-8
"""
seahub removed ajax api

rm ajax get file op url
https://github.com/haiwen/seahub/commit/06bc49d17bd8cf088d9c17d4d1f2d80cd866644a
https://github.com/haiwen/seahub/commits/06bc49d17bd8cf088d9c17d4d1f2d80cd866644a/seahub/views/ajax.py
"""
import json

from seahub.auth.decorators import login_required_ajax
from django.http import HttpResponse
from seaserv import seafile_api
from seahub.views import check_folder_permission, get_system_default_repo_id
from seahub.utils import gen_file_upload_url


def get_repo(repo_id):
    return seafile_api.get_repo(repo_id)


@login_required_ajax
def get_file_op_url(request, repo_id):
    """Get file upload/update url for AJAX.
    """
    content_type = 'application/json; charset=utf-8'

    op_type = request.GET.get('op_type') # value can be 'upload', 'update', 'upload-blks', 'update-blks'
    path = request.GET.get('path')
    if not (op_type and path):
        err_msg = _(u'Argument missing')
        return HttpResponse(json.dumps({"error": err_msg}), status=400,
                            content_type=content_type)

    repo = get_repo(repo_id)
    if not repo:
        err_msg = _(u'Library does not exist')
        return HttpResponse(json.dumps({"error": err_msg}), status=400,
                            content_type=content_type)

    # permission checking
    if check_folder_permission(request, repo.id, path) != 'rw':
        err_msg = _(u'Permission denied')
        return HttpResponse(json.dumps({"error": err_msg}), status=403,
                            content_type=content_type)

    username = request.user.username
    if op_type == 'upload':
        if request.user.is_staff and get_system_default_repo_id() == repo.id:
            # Set username to 'system' to let fileserver release permission
            # check.
            username = 'system'

    if op_type.startswith('update'):
        token = seafile_api.get_fileserver_access_token(repo_id, 'dummy',
                                                        op_type, username)
    else:
        token = seafile_api.get_fileserver_access_token(repo_id, 'dummy',
                                                        op_type, username,
                                                        use_onetime=False)

    url = gen_file_upload_url(token, op_type + '-aj')

    return HttpResponse(json.dumps({"url": url}), content_type=content_type)