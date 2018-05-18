# from django.contrib.auth import REDIRECT_FIELD_NAME
from seahub.auth import REDIRECT_FIELD_NAME

def helper(request):
    return {
        "REDIRECT_FIELD_NAME": REDIRECT_FIELD_NAME,
    }

def test_helper(request):
    return {
        'test': 'test',
    }