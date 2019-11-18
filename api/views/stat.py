from django.http import JsonResponse, HttpResponse
from django.views import View

from api.models import SearchRequest


class Stat(View):
    def get(self, request):
        search_requests = list(SearchRequest.objects.all()[:1000].values('id', 'ip', 'create_date', 'user_agent', 'search_query'))
        return JsonResponse(search_requests, safe=False)
