import json
import re
import time
from http import client

import requests
from bs4 import BeautifulSoup as get_soup

session = requests.Session()
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.97 Safari/537.36'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.97 Safari/537.36',
}

address = '123.31.45.40'
port = '1808'

username = "n743116"
password = "107987"

http_proxy = f"http://{username}:{password}@{address}:{port}"
https_proxy = f"https://{username}:{password}@{address}:{port}"
ftp_proxy = f"ftp://{username}:{password}@{address}:{port}"

proxyDict = {
    "http": http_proxy,
    # "https": https_proxy,
    # "ftp": ftp_proxy
}
# proxyDict = None


def get_req(url, headers=None, params=None, proxies=None, timeout=3, type=None):
    try:
        res = session.get(url=url, headers=headers, params=params, timeout=timeout, proxies=proxyDict)
        if res.ok or res.status_code in [502, 503]:
            if type == 'json':
                return res.json()
            elif type == 'text':
                text = res.text
                return removeCharacters(text)
            elif type == 'content':
                return res.content
            return res
        if not res.ok:
            return None
    except requests.exceptions.HTTPError as httpErr:
        print("Http Error:", httpErr)
    except requests.exceptions.ConnectionError as connErr:
        print("Error Connecting:", connErr)
    except requests.exceptions.Timeout as timeOutErr:
        print("Timeout Error:", timeOutErr)
    except requests.exceptions.RequestException as reqErr:
        print("Something Else:", reqErr)
    return


def post_req(url, headers, data=None, timeout=3, type=None, type_send='data', proxies=None):
    res = None
    try:
        if type_send == 'data':
            res = session.post(url=url, headers=headers, data=data, timeout=timeout, proxies=proxyDict)
        elif type_send == 'json':
            res = session.post(url=url, headers=headers, json=data, timeout=timeout, proxies=proxyDict)
        if res.ok or res.status_code in [502, 503]:
            if type == 'json':
                return res.json()
            elif type == 'text':
                return removeCharacters(res.text)
            elif type == 'content':
                return res.content
            return res
        if not res.ok:
            return None
    except requests.exceptions.HTTPError as httpErr:
        print("Http Error:", httpErr)
    except requests.exceptions.ConnectionError as connErr:
        print("Error Connecting:", connErr)
    except requests.exceptions.Timeout as timeOutErr:
        print("Timeout Error:", timeOutErr)
    except requests.exceptions.RequestException as reqErr:
        print("Something Else:", reqErr)
    return None


def js_to_json(code):
    if not code:
        return None
    code = code.replace(':!', ':')
    COMMENT_RE = r'/\*(?:(?!\*/).)*?\*/|//[^\n]*'
    SKIP_RE = r'\s*(?:{comment})?\s*'.format(comment=COMMENT_RE)
    INTEGER_TABLE = (
        (r'(?s)^(0[xX][0-9a-fA-F]+){skip}:?$'.format(skip=SKIP_RE), 16),
        (r'(?s)^(0+[0-7]+){skip}:?$'.format(skip=SKIP_RE), 8),
    )

    def fix_kv(m):
        v = m.group(0)
        if v in ('true', 'false', 'null'):
            return v
        elif v.startswith('/*') or v.startswith('//') or v == ',':
            return ""

        if v[0] in ("'", '"'):
            v = re.sub(r'(?s)\\.|"', lambda m: {
                '"': '\\"',
                "\\'": "'",
                '\\\n': '',
                '\\x': '\\u00',
            }.get(m.group(0), m.group(0)), v[1:-1])

        for regex, base in INTEGER_TABLE:
            im = re.match(regex, v)
            if im:
                i = int(im.group(1), base)
                return '"%d":' % i if v.endswith(':') else '%d' % i

        return '"%s"' % v

    return re.sub(r'''(?sx)
        "(?:[^"\\]*(?:\\\\|\\['"nurtbfx/\n]))*[^"\\]*"|
        '(?:[^'\\]*(?:\\\\|\\['"nurtbfx/\n]))*[^'\\]*'|
        {comment}|,(?={skip}[\]}}])|
        (?:(?<![0-9])[eE]|[a-df-zA-DF-Z_])[.a-zA-Z_0-9]*|
        \b(?:0[xX][0-9a-fA-F]+|0+[0-7]+)(?:{skip}:)?|
        [0-9]+(?={skip}:)
        '''.format(comment=COMMENT_RE, skip=SKIP_RE), fix_kv, code)


def search_regex(pattern, string, flags=0, group=None):
    mobj = None
    if isinstance(pattern, str):
        mobj = re.search(pattern, string, flags)
    else:
        for p in pattern:
            mobj = re.search(p, string, flags)
            if mobj:
                break
    if mobj:
        if group is None:
            return next(g for g in mobj.groups() if g is not None)
        else:
            return mobj.group(group)
    else:
        return None


def parse_json(json_string, transform_source=None, fatal=True):
    if transform_source:
        json_string = transform_source(json_string)
    if not json_string:
        return None
    try:
        return json.loads(json_string)
    except ValueError as ve:
        errmsg = '%s: Failed to parse JSON ' % ve
        print('loi load json')
        print(errmsg)
        return None


def removeCharacters(value):
    value = str(value)
    return re.sub('\s+', ' ', value)


class extractPhimMoi():
    def __init__(self, *args, **kwargs):
        self._url = kwargs.get('url')
        self._headers = HEADERS
        self._regex_url = '''(?x)
                ^((http[s]?|fpt):)\/?\/         # check protpcol
                ((?:www.|m.)phimmoi\.net)\/     # check host
                (?P<slug>.*)\/.*?$              # get slug
                $
        '''

        self._api_script = "https://episode.pmcontent.com/episodeinfo-v1.2.php"

    def run(self):
        return self.real_extract()

    def real_extract(self):
        mobj = re.match(self._regex_url, self._url)
        if not mobj:
            return 'Invalid url.'
        slug = mobj.group('slug')
        content = get_req(url=self._url, headers=self._headers, type='text')
        soup = get_soup(content, 'html5lib')
        title = soup.title
        a_data = soup.findAll('a', attrs={'data-episodeid': True, 'data-number': True, 'data-part': True})
        if not a_data:
            item = re.findall(r'''(?x)
                            currentEpisode\.episodeId=.*?\'(?P<episodeid>.*?)\'.*?
                            currentEpisode\.number=.*?\'(?P<number>.*?)\'.*?
                            currentEpisode\.part=.*?\'(?P<part>.*?)\'.*?
                            currentEpisode\.language=.*?\'(?P<language>.*?)\'.*?
                            ''', content)
            for i in item:
                if i:
                    a_data.append({
                        'data-episodeid': i[0],
                        'data-number': i[1],
                        'data-part': i[2],
                        'data-language': i[3]
                    })
        f = {}
        for a in a_data:
            if not a:
                continue
            episodeid = a.get('data-episodeid')
            number = a.get('data-number')
            part = a.get('data-part')
            filmid = slug.split('-')[-1]
            language = a.get('data-language')
            try:
                c = a.get('title') + ' ' + language
            except AttributeError:
                c = language
            print(c)
            content = get_req(url=self._api_script, headers=self._headers, type='text', params={
                'episodeid': episodeid,
                'number': number,
                'part': part,
                'filmid': filmid,
                'filmslug': slug,
                'type': 'javascript',
                '_h':'4'
            })
            all_server = parse_json(search_regex(r'\"thirdParty\"\:(\[.+?\])\}', content), transform_source=js_to_json)
            if all_server:
                for server in all_server:
                    if not server:
                        continue
                    name = server.get('displayName') or ''
                    embed = server.get('embed')
                    if 'GPT' in name:
                        server['media'] = self.extract_gpt(embed)
                    elif 'PZC' in name:
                        server['media'] = self.extract_pzc(embed)
                f.update({
                    removeCharacters(c): all_server
                })
        return {
            'title': removeCharacters(title.text),
            'slug': slug,
            'sources': f
        }
        # return json.dumps({
        #     'title': removeCharacters(title.text),
        #     'slug': slug,
        #     'sources': f
        # }, indent=4, ensure_ascii=False)

    def extract_pzc(self, url_pzc):
        if not url_pzc:
            return
        content = get_req(url=url_pzc, headers={
            'User-Agent': USER_AGENT,
            'Referer': self._url,
            'Upgrade-Insecure-Requests': '1',
            'Host': 'pzc.phimmoi.net'
        }, type='text')
        return search_regex(
            [r'VIDEO_URL=\"(?P<data>.*?)\"',
             r'VIDEO_URL=swapServer\(\"(?P<data>.+?)\"\)'],
            content, group='data'
        )

    def extract_gpt(self, url_gpt):
        if not url_gpt:
            return
        self._headers.update({
            'x-requested-with': 'XMLHttpRequest',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': self._url
        })
        api_gpt = 'https://gpt2.phimmoi.net/getLinkStreamMd5/'
        api = re.sub(r'(.+(?:\=|\/))', api_gpt, url_gpt)
        data = get_req(url=api, headers=self._headers, type='json')
        if data:
            return data
        return


a = extractPhimMoi(url='http://www.phimmoi.net/phim/nga-re-tu-than-3-bo-mac-cho-chet-186/xem-phim-3769.html')
print(a.run())
