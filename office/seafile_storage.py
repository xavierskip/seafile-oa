from django.conf import settings
from django.core.files.storage import Storage

class SeafileStorage(Storage):

    def __init__(self, option=None):
        if not option:
            option = settings.SEAFILE_STORAGE_OPTIONS
        else:
            pass

    def _open(self, name, mode='rb'):
        pass

    def _save(self):
        pass

    def delete(self, name):
        pass

    def exists(self, name):
        pass

    def listdir(self, path):
        pass

    def size(self, name):
        pass

    def url(self, name):
        pass
