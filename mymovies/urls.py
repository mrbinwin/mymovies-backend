from django.urls import include, path
from api import views as api_views

api_patterns = [
    path('search/<title>/<original_title>/<int:year>', api_views.torrent.TorrentSearch.as_view(), name='search'),
    path('download/<int:id>', api_views.file.TorrentFile.as_view(), name='download'),
    path('stat', api_views.stat.Stat.as_view(), name='stat'),
]

urlpatterns = [
    path('api/', include(
        (api_patterns, 'api'),
        namespace='api'
    )),
]