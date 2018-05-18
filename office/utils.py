from seahub.base.templatetags.seahub_tags import email2nickname
from seahub.utils import is_valid_username
from seahub.base.accounts import User  # don't use OfficeUser to avoid circular reference
import re


ATTPL = u'\{\S+?\}\((\S+?)\)'
at_pattern = re.compile(ATTPL, flags=re.U)


def check_user(name):
    if not is_valid_username(name):
        return False
    try:
        User.objects.get(email=name)
        return True
    except User.DoesNotExist:
        return False

# handle commit and distribute document
def find_at(s=''):
    """find email user name flag
    return: type set
    """
    names = re.findall(ATTPL, s)
    users = filter(check_user, names)
    return set(users)


def emailrepl(matchobj):
    value = matchobj.group(1)
    if check_user(value):
        return u'<span class="at">%s</span>' % email2nickname(value)
    else:
        return matchobj.group(0)