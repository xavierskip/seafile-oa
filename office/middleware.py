from office.settings import HASHIDS

def hashid_decode(hashid):
    numbers = HASHIDS.decode(hashid)
    return numbers[0] if len(numbers) == 1 else numbers

class HashidsMiddleware(object):
    """
    auto decode the hashid if it in the view_kwargs
    """
    def process_view(self, request, view_func, view_args, view_kwargs):
        if 'hashid' in view_kwargs.keys():
            hashid = view_kwargs['hashid']
            view_kwargs['hashid'] = hashid_decode(hashid)
        return None