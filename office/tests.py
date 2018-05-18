# coding:utf-8
from django.test import TestCase
from django.conf import settings
from seaserv import seafile_api
from office.models import *
from django.db import IntegrityError
import pprint


# Create your tests here.
def open_db_log():
    import logging
    l = logging.getLogger('django.db.backends')
    l.setLevel(logging.DEBUG)
    l.addHandler(logging.StreamHandler())


def create_repo(name, username, passwd=None):
    repo_id = seafile_api.create_repo(name=name, desc=name, username=username, passwd=passwd)
    Info.objects.create(key='repo_id', value=repo_id)
    return repo_id


def inti_rope():
    name = getattr(settings, 'OFFICE_REPO_NAME', 'root')
    username = Info.objects.root_user
    passwd = getattr(settings, 'OFFICE_REPO_PASSWD', None)
    repo_id = create_repo(name, username, passwd)
    return repo_id



def toHex(input):
    hash = ''
    alphabet = '0123456789abcdef'
    alphabet_length = len(alphabet)
    while input:
        hash = alphabet[input%alphabet_length] + hash
        input = int(input/alphabet_length)
    return hash


#
# from hashids import Hashids
# h=Hashids(salt='d8h3uh48fef', alphabet='0123456789abcdefg')
# a={}
# for i in range(99999):
#     a.update({h.encode(i):''})
#
# print len(a.keys())
# if __name__ == '__main__':
#     test()
def insert_document(docs_list, docs_json):
    root_repo_id = Info.objects.root_repo
    UID = 'bgs@bgs.org'
    for key in docs_list:
        info = docs_json[key]
        try:
            d = Document.objects.create(
                reference = info['reference'],
                title = info['title'],
                issue = info['issue'],
                generated = info['generated'],
                registered = info['registered'],
                folder = info['folder'],
            )
        except IntegrityError:
            try:
                d = Document.objects.create(
                    reference = info['reference']+'(conflict)',
                    title = info['title'],
                    issue = info['issue'],
                    generated = info['generated'],
                    registered = info['registered'],
                    folder = info['folder'],
                )
            except IntegrityError:
                pprint.pprint(info)
                continue
        # d.repo_id = seafile_api.create_virtual_repo(root_repo_id, d.folder, str(d), str(d), UID)
        d.repo_id = root_repo_id
        d.save()
        for i in info['attachments']:
            a = Attachment(doc=d, file=i)
            a.save()
        c = Commit.objects.create(doc=d, uid=UID, content='done.')
        Distribution.objects.create(doc=d, uid=UID, commit=c)


def insert_database(folder, document):
    """

    :param folder: a path to a json file
    :param document: a path to a json file
    :return:
    """
    import json
    with open(folder) as f:
        docs_list = json.load(f)
    with open(document) as f:
        docs_json = json.load(f)
    insert_document(docs_list, docs_json)