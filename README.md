MyMovies-Backend
=====================

[Django](https://www.djangoproject.com/) based backend for [MyMovies](https://github.com/MrBinWin/mymovies) Android app.
It's a REST API that can search torrents by movie title and release year.

Endpoints
---

`/api/search/<title>/<original_title>/<int:year>` - get list of torrents by movie title in Russian, original title and release year

`/api/download/<int:id>` - download torrent metadata file by torrent id

`/api/stat` - the API usage statictics

Installation
---

After installation the following settings are need to be adjusted:
 - ALLOWED_HOSTS - url or IP address of the current server
 - RUTRACKER_USERNAME
 - RUTRACKER_PASSWORD
 - RUTRACKER_RUCAPTCHA_KEY - rucaptcha.com API key
 - RUTRACKER_PROXY_ENABLED - True if rutracker.org is blocked in your country
 - RUTRACKER_PROXIES
