from .setup import *


def post_image(string_html):
    info = post_req(url='https://htmlcsstoimage.com/demo_run', data={
        'html': string_html
    }, type='json', headers=HEADERS)
    return info.get('url') or "https://i.pinimg.com/736x/fd/66/08/fd66082804374294aaae4379e0c2abe7.jpg"


class extractTKB_PTIT():
    def __init__(self, *args, **kwargs):
        self._masv = kwargs.get('masv')
        self._headers = HEADERS
        self._default_html = '''<!doctype html>
    <html lang="en">
    <head>
        <style type="text/css">
            body {
                font-size: medium;
                font-family: 'Lora', serif;
                line-height: 40px;
            !important;
            }

            td {
                font-weight: bold;
                padding-left: 3px;
                padding-right: 3px;
            }
        </style>
    </head>
    <body>
    <div class="pl-1 pr-1">%s %s</div>
    </body>
    </html>
    '''
        self.lst_day = {
            'monday': "thứ hai",
            'tuesday': 'thứ ba',
            'wednesday': "thứ tư",
            'thursday': 'thứ năm',
            'friday': 'thứ sáu',
            'saturday': 'thứ bảy',
            'sunday': 'chủ nhật'
        }

        self.time_tiet = {
            '1': '07h30',
            '2': '08h30',
            '3': '9h30',
            '4': '10h30',
            '5': '12h30',
            '6': '13h30',
            '7': '14h30',
            '8': '15h30',
            '9': '16h30',
            '10': '17h30',
            '11': '19h30',
            '12': '20h30'
        }
        self._regex_masv = r'(?x)^(?:b|B)[\d]{2}(?:dc|DC).*?[\d]{3}$'
        self._regex_data = r'''(?x)
        \<span\s+id=\"ctl00_ContentPlaceHolder1_ctl00_lblContentMaSV\".*?\>(?P<masv>.*?)\<\/span\>.*?
        \<span\s+id=\"ctl00_ContentPlaceHolder1_ctl00_lblContentTenSV\".*?\>(?P<name>.*?)\<\/span\>.+?
        \<span\s+id=\"ctl00_ContentPlaceHolder1_ctl00_lblContentLopSV\".*?\>(?P<class>.*?)\<\/span\>.+?
        '''

    def get_text(self):
        now = datetime.datetime.now(tz=timezone("Asia/Saigon"))
        weekday_today = now.strftime('%A').lower()

        def extract_ddrivetip(maLop, tenMH, maMH, Thu, TC, Phong, tbd, st, giaoVien,
                              ngaybd, ngaykt, thecolor, thewidth, num, tkbTuan=None):
            nums = num.split('-')
            giaoVien = giaoVien.lower()
            if self.lst_day.get(weekday_today) == Thu.lower():
                return {
                    nums[0]: maMH,
                    nums[1]: tenMH,
                    nums[2]: Phong,
                    nums[3]: Thu,
                    nums[4]: tbd,
                    "Thời gian bắt đầu": self.time_tiet.get(tbd),
                    nums[5]: st,
                    nums[6]: ' '.join(giaoVien.split('_')),
                    nums[9]: maLop
                }

        data = []
        _masv, _name, _class = [None] * 3
        if self._masv:
            if not re.match(self._regex_masv, self._masv):
                return {
                    'messages': [
                        {'text': f" {self._masv} Là cái gì vậy bạn  ?????? 😜😜."}
                    ]
                }
            content = get_req(
                url=f"http://qldt.ptit.edu.vn/Default.aspx?page=thoikhoabieu&id={self._masv.upper()}",
                headers=HEADERS,
                type='text'
            )
            if """window.onload=function(){alert('Server đang tải lại dữ liệu. Vui lòng trở lại sau 15 phút!');}""" in content:
                return {
                    "messages": [
                        {
                            "attachment": {
                                "type": "image",
                                "payload": {
                                    "url": "https://i.postimg.cc/Qx10M7Cz/Capture.png"
                                }
                            }
                        },
                        {
                            'text':"Server đang tải lại dữ liệu bạn nhỏ ạ 😕"
                        }
                    ],
                }
            soup = get_soup(content, 'html5lib')
            span_captcha = soup.find('span', attrs={'id': 'ctl00_ContentPlaceHolder1_ctl00_lblCapcha'})
            if span_captcha:
                text_captcha = span_captcha.text
                input_VIEWSTATE = soup.find('input', attrs={'name': "__VIEWSTATE"})
                input_VIEWSTATEGENERATOR = soup.find('input', attrs={'name': "__VIEWSTATEGENERATOR"})
                url_post = f"http://qldt.ptit.edu.vn/Default.aspx?page=thoikhoabieu&id={self._masv.upper()}"
                post_req(url=url_post, headers=self._headers, type='text', data={
                    'ctl00$ContentPlaceHolder1$ctl00$txtCaptcha': text_captcha,
                    "ctl00$ContentPlaceHolder1$ctl00$btnXacNhan": "Vào website",
                    "__EVENTTARGET": "",
                    "__EVENTARGUMENT": "",
                    "__VIEWSTATE": input_VIEWSTATE.get('value'),
                    "__VIEWSTATEGENERATOR": input_VIEWSTATEGENERATOR.get('value')
                })
                content = get_req(
                    url=f"http://qldt.ptit.edu.vn/Default.aspx?page=thoikhoabieu&id={self._masv.upper()}",
                    headers=HEADERS,
                    type='text'
                )
                soup = get_soup(content, 'html5lib')
            mobj = re.search(self._regex_data, content)
            if not mobj:
                return {
                    'messages': [
                        {'text': f"Mã sinh viên {self._masv} không tồn tại :P ."}
                    ]
                }
            _masv, _name, _class = mobj.groups()
            all_td = soup.findAll('td', attrs={'onmouseover': True})
            for td in all_td:
                if not td:
                    continue
                onmouseover = td.get('onmouseover')
                onmouseover = str(onmouseover).replace('ddrivetip(', '[').replace(')', ']').replace("'", '"')
                dd = json.loads(onmouseover)
                tm = extract_ddrivetip(*dd)
                if tm:
                    data.append(tm)
            textout = f"""- Mã Sinh Viên: {_masv}\n- Họ Tên: {_name}\n- Lớp: {_class}\n- Ngày {now.strftime("%d-%m-%Y")} {self.lst_day.get(now.strftime('%A').lower())} có {len(data)} kíp. :D\n"""
            for idx, da in enumerate(data):
                t = ''
                for k, v in da.items():
                    t += f'+ {k}  :  {v}\n'
                textout += f"""\n******* Kíp {idx + 1} *******\n\n{t}"""
            textout += '\n- FB : fb.com/100011734236090'
            return {
                "messages": [
                    {
                        "text": textout
                    },
                ],
            }
        return {
            "messages": [
                {"text": f"Không tìm thấy tkb {self._masv}"}
            ]
        }

    def get_img(self):
        if self._masv:
            if not re.match(self._regex_masv, self._masv):
                return {
                    'messages': [
                        {'text': ""}
                    ]
                }
            content = get_req(
                url=f"http://qldt.ptit.edu.vn/Default.aspx?page=thoikhoabieu&id={self._masv.upper()}",
                headers=HEADERS,
                type='text'
            )
            soup = get_soup(content, 'html5lib')
            span_captcha = soup.find('span', attrs={'id': 'ctl00_ContentPlaceHolder1_ctl00_lblCapcha'})
            if span_captcha:
                text_captcha = span_captcha.text
                input_VIEWSTATE = soup.find('input', attrs={'name': "__VIEWSTATE"})
                input_VIEWSTATEGENERATOR = soup.find('input', attrs={'name': "__VIEWSTATEGENERATOR"})
                url_post = f"http://qldt.ptit.edu.vn/Default.aspx?page=thoikhoabieu&id={self._masv.upper()}"
                post_req(url=url_post, headers=self._headers, type='text', data={
                    'ctl00$ContentPlaceHolder1$ctl00$txtCaptcha': text_captcha,
                    "ctl00$ContentPlaceHolder1$ctl00$btnXacNhan": "Vào website",
                    "__EVENTTARGET": "",
                    "__EVENTARGUMENT": "",
                    "__VIEWSTATE": input_VIEWSTATE.get('value'),
                    "__VIEWSTATEGENERATOR": input_VIEWSTATEGENERATOR.get('value')
                })
                content = get_req(
                    url=f"http://qldt.ptit.edu.vn/Default.aspx?page=thoikhoabieu&id={self._masv.upper()}",
                    headers=HEADERS,
                    type='text'
                )
                soup = get_soup(content, 'html5lib')
            mobj = re.search(self._regex_data, content)
            if not mobj:
                return {
                    'messages': [
                        {'text': f""}
                    ]
                }
            _masv, _name, _class = mobj.groups()
            div_info = soup.find('div', attrs={'style': 'width: 100%; text-align: center; '})
            div_tkb = soup.find('div', attrs={'id': 'ctl00_ContentPlaceHolder1_ctl00_pnlTuan'})
            html_string = self._default_html % (div_info, div_tkb)
            html_string = html_string.replace('\n', '').replace('width:90px', 'width:100%')
            # print('da chay den day')
            # with open('abcdef.html','w',encoding='utf-8') as f:
            #     f.write(html_string)
            return {
                "messages": [
                    {
                        "attachment": {
                            "type": "image",
                            "payload": {
                                "url": post_image(html_string)
                            }
                        }
                    }
                ],
            }
        return {
            "messages": [
                {"text": f""}
            ]
        }
