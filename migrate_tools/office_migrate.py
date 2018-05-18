#!/usr/bin/env python
#-*- coding: utf-8 -*-
import os
import sys
import time
import platform
import json
import uuid
import shutil

REPO = sys.argv[1]
print(REPO)

def gen_folder_name():
    """ Generate a unique folder name
    """
    # return timezone.now().strftime('%Y/%m/%d')
    return uuid.uuid4().hex


def creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime


def cmp(a, b):
    return int(creation_date(a) - creation_date(b))


def epoch2date(t):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))

def ls(path, all=False):
    names = os.listdir(path)
    if not all:
        names = filter(lambda x: not x.startswith('.'), names)
    return map(lambda x: os.path.join(REPO,x), names)

def reference_title(name):
    rt = name.split('：')
    if len(rt) == 1:
        return None, rt[0]
    else:
        return rt[0], rt[1]

def guess_main_file(paths):
    count_dict = {}
    exts = ['.pdf','.doc','.other']
    for k in exts:
        count_dict[k] = []
    filenams = map(lambda x: os.path.basename(x), paths)
    if len(filenams) == 1:
        return os.path.splitext(filenams[0])
    for i,f in enumerate(filenams):    
        name, ext = os.path.splitext(f)
        ext = ext.lower()
        if ext == '.docx':
            ext = '.doc'
        try:
            count_dict[ext].append(i)
        except KeyError, e:
            count_dict['.other'].append(i)
    for k in exts:
        index = count_dict[k]
        if index:
            name = filenams[index[0]]
            return os.path.splitext(name)

def get_document_info(path):
    files_path = ls(path)
    DATE = epoch2date(creation_date(path)).split()[0]
    UUID = gen_folder_name()
    name, ext = guess_main_file(files_path)
    #
    reference, title = reference_title(name)
    issue = 'ADMIN'
    generated = DATE
    registered = DATE
    folder = UUID
    attachments = map(lambda x: os.path.basename(x), files_path)
    return {
    'reference': reference,
    'title': title,
    'issue': issue,
    'generated': generated,
    'registered': registered,
    'folder': folder,
    'attachments': attachments
    }


def main():
    folder_paths = ls(REPO)
    sorter_paths = sorted(folder_paths, cmp)
    uuid_paths = []
    documents = {}
    for f in sorter_paths:
        print('[%s] %s' %(epoch2date(creation_date(f)), f))
        info = get_document_info(f)
        uuid_folder = info['folder']
        documents[uuid_folder] = info
        os.rename(f, os.path.join(REPO, uuid_folder))
        uuid_paths.append(uuid_folder)

    with open('folder.json','w') as f:
        json.dump(uuid_paths, f)
    with open('document.json','w') as f:
        json.dump(documents, f)

if __name__ == '__main__':
    main()


