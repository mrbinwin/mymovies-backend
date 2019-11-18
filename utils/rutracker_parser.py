try:
    from PIL import Image
except ImportError:
    import Image

from captcha_solver import CaptchaSolver
import html
from io import BytesIO
from lxml import html as lhtml
import pickle
import requests
from requests.exceptions import ConnectionError

from mymovies.settings import RUTRACKER_PROXY_ENABLED, RUTRACKER_PROXIES, RUTRACKER_RUCAPTCHA_KEY, RUTRACKER_USERNAME, RUTRACKER_PASSWORD


class ParseException(Exception):
    pass


def handle_requests_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConnectionError as e:
            raise ParseException('Error. Connection error')

    return wrapper


class RutrackerParser:

    INDEX_PAGE = 'https://rutracker.org/forum/index.php'
    LOGIN_PAGE = 'https://rutracker.org/forum/login.php'
    SEARCH_PAGE = 'https://rutracker.org/forum/tracker.php?nm=%s'
    DOWNLOAD_PAGE = 'https://rutracker.org/forum/dl.php?t=%s'

    USERNAME = RUTRACKER_USERNAME
    PASSWORD = RUTRACKER_PASSWORD
    COOKIE_FILE = 'tmp/rutracker.cookie'
    RUCAPTCHA_KEY = RUTRACKER_RUCAPTCHA_KEY

    PROXIES = RUTRACKER_PROXY_ENABLED
    if PROXIES:
        PROXIES = RUTRACKER_PROXIES
    TIMEOUT = 15

    _session = None

    @handle_requests_exceptions
    def parse(self, title: str, original_title: str, year: int):
        query = '%s %d' % (title, year)
        if title != original_title:
            query = '%s %s %d' % (title, original_title, year)

        url = RutrackerParser.SEARCH_PAGE % query
        data = {
            'f[]': -1,      # forums
            'o': 10,        # sort by seeds
            's': 2,         # sort DESC
            'pn': '',    # query from query string
            'nm': query,        #
            'oop': 1        # open torrents only
        }

        response = self._send_post(url, data=data)
        if self._check_and_auth(response.text):
            response = self._send_post(url, data=data)
        else:
            raise ParseException('Error. Can not login')

        if self._validate_search_results_page(response.text):
            return self._parse_search_results(response.text)
        else:
            raise ParseException('Error. Search results page is not valid')

        raise ParseException('Unknown error')

    def downloadFile(self, id: int):
        response = self._send_get(RutrackerParser.INDEX_PAGE)
        if not self._check_and_auth(response.text):
            raise ParseException('Error. Can not login')

        response = self._send_get(RutrackerParser.DOWNLOAD_PAGE % id)
        if not response.ok:
            raise ParseException('Error. HTTP %d' % response.status_code)

        return response.content


    """
    Login rutracker.org
    
    """
    @handle_requests_exceptions
    def _auth(self):
        data = {
            'login_username': RutrackerParser.USERNAME,
            'login_password': RutrackerParser.PASSWORD,
            'login': 'ВХОД',
            'redirect': 'index.php'
        }

        response = self._send_post(RutrackerParser.LOGIN_PAGE, data=data)
        captcha_data = self._check_and_get_captcha(response.text)
        if captcha_data['is_shown']:
            data['cap_sid'] = captcha_data['captcha_id'],
            data[captcha_data['captcha_check_code']] = captcha_data['resolved_captcha']
            response = self._send_post(RutrackerParser.LOGIN_PAGE, data=data)
            captcha_data = self._check_and_get_captcha(response.text)

        if captcha_data['is_shown']:
            data['cap_sid'] = captcha_data['captcha_id'],
            data[captcha_data['captcha_check_code']] = captcha_data['resolved_captcha']
            response = self._send_post(RutrackerParser.LOGIN_PAGE, data=data)
            captcha_data = self._check_and_get_captcha(response.text)

        if captcha_data['is_shown']:
            data['cap_sid'] = captcha_data['captcha_id'],
            data[captcha_data['captcha_check_code']] = captcha_data['resolved_captcha']
            response = self._send_post(RutrackerParser.LOGIN_PAGE, data=data)
            captcha_data = self._check_and_get_captcha(response.text)

        if captcha_data['is_shown']:
            raise ParseException('Error. Can not solve captcha')

        return self._check_auth(response.text)

    """
    Check if we are logged in rutracker.org
    :returns boolean
    
    """
    @handle_requests_exceptions
    def _check_auth(self, content: str):
        return content.find('name="login_username"') == -1

    """
    Check if we are logged in rutracker.org and login if needed
    :returns boolean

    """
    @handle_requests_exceptions
    def _check_and_auth(self, content: str):
        if self._check_auth(content):
            return True
        return self._auth()

    """
    Check if captcha is shown and if so resolve it
    
    """
    def _check_and_get_captcha(self, content: str):
        result = {
            'is_shown': False
        }
        if content.find('name="cap_sid"') == -1:
            return result

        tree = lhtml.fromstring(content)
        captcha_image_wrapper = tree.xpath('//img[@alt="pic"][@width=120][@height=72]')
        if not len(captcha_image_wrapper):
            raise ParseException('Error. Captcha parsing')
        captcha_image_url = captcha_image_wrapper[0].attrib['src']

        captcha_id_wrapper = tree.xpath('//input[@name="cap_sid"]')
        if not len(captcha_id_wrapper):
            raise ParseException('Error. Captcha parsing')
        captcha_id = captcha_id_wrapper[0].attrib['value']

        captcha_check_code_wrapper = tree.xpath('//input[@class="reg-input"]')
        if not len(captcha_check_code_wrapper):
            raise ParseException('Error. Captcha parsing')
        captcha_check_code = captcha_check_code_wrapper[0].attrib['name']
        resolved_captcha = self._resolve_captcha(captcha_image_url)
        result = {
            'is_shown': True,
            'resolved_captcha': resolved_captcha,
            'captcha_id': captcha_id,
            'captcha_check_code': captcha_check_code
        }
        return result


    def _get_session(self):
        if self._session is not None:
            return self._session
        self._session = requests.Session()
        if RutrackerParser.PROXIES:
            self._session.proxies.update(RutrackerParser.PROXIES)
        try:
            with open(RutrackerParser.COOKIE_FILE, 'rb') as f:
                self._session.cookies.update(pickle.load(f))
        except FileNotFoundError:
            pass
        return self._session

    def _parse_search_results(self, content):
        result = []
        tree = lhtml.fromstring(content)
        search_results = tree.xpath('//div[@id="search-results"]//tr[@class="tCenter hl-tr"]')
        if not len(search_results):
            return result
        search_results = search_results[:7]
        for search_result in search_results:
            name_wrapper = search_result.xpath('.//div[contains(@class, "t-title")]/a[@data-topic_id]')
            if not len(name_wrapper):
                continue
            id = int(name_wrapper[0].attrib['data-topic_id'])
            name = html.unescape(name_wrapper[0].text)
            size_wrapper = search_result.xpath('.//td[contains(@class, "tor-size")]/a')
            if not len(size_wrapper):
                continue
            size = html.unescape(size_wrapper[0].text)
            seeds_wrapper = search_result.xpath('.//b[@class="seedmed"]')
            seeds = 0 if not len(seeds_wrapper) else int(seeds_wrapper[0].text)
            result.append({
                'id': id,
                'name': name,
                'size': size,
                'seeds': seeds
            })
        return result

    def _resolve_captcha(self, image_url):
        image_bytes = requests.get(image_url).content
        image = Image.open(BytesIO(image_bytes))
        w, h = image.size
        image = image.crop((0, 0, w, h - 12))
        image.save('tmp/captcha.jpg')

        image_bytes = BytesIO()
        image.save(image_bytes, format='JPEG')
        image_bytes = image_bytes.getvalue()

        solver = CaptchaSolver('rucaptcha', api_key=RutrackerParser.RUCAPTCHA_KEY)
        result = solver.solve_captcha(image_bytes)
        return result

    def _send_get(self, url):
        response = self._get_session().get(url, timeout=RutrackerParser.TIMEOUT)
        if not response.ok:
            raise ParseException('Error. HTTP %d' % response.status_code)
        with open(RutrackerParser.COOKIE_FILE, 'wb') as f:
            pickle.dump(self._get_session().cookies, f)
        return response

    def _send_post(self, url, data):
        response = self._get_session().post(url, data=data, timeout=RutrackerParser.TIMEOUT)
        if not response.ok:
            raise ParseException('Error. HTTP %d' % response.status_code)
        with open(RutrackerParser.COOKIE_FILE, 'wb') as f:
            pickle.dump(self._get_session().cookies, f)
        return response

    def _validate_search_results_page(self, content: str):
        return content.find('div id="search-results"') != -1
