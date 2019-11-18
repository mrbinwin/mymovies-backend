from django.http import JsonResponse
from django.views import View

from api.models import SearchRequest
from utils.rutracker_parser import RutrackerParser, ParseException


class TorrentSearch(View):
    def get(self, request, title, original_title, year):
        data = {
            'success': False,
            'title': title,
            'original_title': title,
            'year': year,
            'torrents': []
        }
        try:
            parser = RutrackerParser()
            torrents = parser.parse(title, original_title, year)
            data['success'] = True
            data['torrents'] = torrents
        except ParseException as e:
            data['error'] = str(e)

        search_request = SearchRequest(
            ip=request.META['REMOTE_ADDR'],
            user_agent=request.META['HTTP_USER_AGENT'],
            search_query="%s / %s / %d" % (title, original_title, year)
        )
        search_request.save()

        return JsonResponse(data)
