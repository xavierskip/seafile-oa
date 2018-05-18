from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from office.settings import HASHIDS
from office.utils import at_pattern, emailrepl
from office.models import Document, Info
import datetime

register = template.Library()


@register.filter(name='mention', is_safe=True)
def mention(text):
    return mark_safe(at_pattern.sub(emailrepl, text))


@register.filter(name='anonymousview')
def anonymous_viewfile(url):
    n = url.index('/file/')+6
    return "/d/%s/files/?p=/%s" %(Info.objects.get_download(), url[n:])


@register.filter(name='antispider')
def anti_spider(number):
    return HASHIDS.encode(int(number))  # must be int type otherwise return ''


@register.filter(name='xss', is_safe=False)
def xss(s):
    return u"%s<script>alert('filter xss test')</script>" % s


@register.filter(name='big1', is_safe=True, needs_autoescape=True)
def initial_letter_filter(text, autoescape=False):
    first, other = text[0], text[1:]
    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x
    result = '<strong>%s</strong>%s' % (esc(first), esc(other))
    return mark_safe(result)


@register.simple_tag(takes_context=True)
def current_time(context, format_string='%Y-%m-%d %H:%M:%S'):
    return "<time>%s</time>" % datetime.datetime.now().strftime(format_string)


@register.assignment_tag(takes_context=True)
def distribute_count(context, commit=True):
    request = context['request']
    username = request.user.username
    return Document.objects.user_distribute(username, commit).count()


@register.assignment_tag(takes_context=True)
def todo_count(context, commit=True):
    request = context['request']
    username = request.user.username
    return Document.objects.user_todo(username, commit).count()