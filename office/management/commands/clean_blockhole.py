from django.core.management.base import NoArgsCommand
from seaserv import seafile_api
from office.models import BlockHole,Info

class Command(NoArgsCommand):
    help = '''
    remove the folder of the repo and database info
    '''

    def handle_noargs(self, **options):
        repo_id = Info.objects.root_repo
        for bh in BlockHole.objects.all():
            seafile_api.del_file(repo_id, '', bh.folder, 'django')
            bh.delete()
            self.stdout.write("[remove]%s" %bh.folder, ending='\n')