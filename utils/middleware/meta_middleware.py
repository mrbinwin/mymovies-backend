from django.utils.deprecation import MiddlewareMixin


class MetaMiddleware(MiddlewareMixin):

    def process_request(self, request):
        """
        Setup request.META['REMOTE_ADDR']

        """
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            request.META['REMOTE_ADDR'] = request.META['HTTP_X_FORWARDED_FOR'].split(",")[0].strip()
        return None
