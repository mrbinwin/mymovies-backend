from django.http import JsonResponse, HttpResponse
from django.views import View

from utils.rutracker_parser import RutrackerParser, ParseException


class TorrentFile(View):
    def get(self, request, id):
        try:
            parser = RutrackerParser()
            file_data = parser.downloadFile(id)
            response = HttpResponse(file_data, content_type='application/x-bittorrent; charset=Windows-1251')
            response['Content-Disposition'] = 'attachment; filename="movie.torrent"'
            return response

        except ParseException as e:
            return HttpResponse(status=204)
