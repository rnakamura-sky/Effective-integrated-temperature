# coding: utf-8
"""
スクレイピングして気温を取得する機能
"""
from collections import namedtuple
import datetime
import re
import time
import requests
from bs4 import BeautifulSoup

Prefecture = namedtuple('Prefecture', ['code', 'name'])
Block = namedtuple('Block', ['pref_code', 'code', 'name'])

class ScrapeTemp():
    """
    気象庁から気温データを取得するための機能
    """
    def __init__(self, prefecture:int=49, location:int=47638):
        """
        初期化
        取得する気温の場所はデフォルトとして山梨県の甲府としています。
        """
        self.prefecture = prefecture
        self.location = location

        self.template_url = \
            'https://www.data.jma.go.jp/obd/stats/etrn/view/daily_s1.php?' \
            'prec_no={prefecture}&block_no={location}&year={year}&month={month}&day={day}&view='
        self.template_average_url = \
            'https://www.data.jma.go.jp/obd/stats/etrn/view/nml_sfc_d.php?' \
            'prec_no={prefecture}&block_no={location}&year={year}&month={month}&day={day}&view=p1'
        self.prefecture_url = \
            'https://www.data.jma.go.jp/obd/stats/etrn/select/prefecture00.php?' \
            'prec_no=&block_no=&year=&month=&day=&view=p1'

        self.template_block_url = \
            'https://www.data.jma.go.jp/obd/stats/etrn/select/prefecture.php?' \
            'prec_no={prefecture}&block_no=&year=&month=&day=&view=p1'
        # スクレイピング用の設定
        self.data_start_row = 3
        self.temp_idx = 5
        self.average_data_start_row = 2
        self.average_temp_idx = 1

        # スクレイピングした文字を整形するための設定
        self.pattern = r'^(-{0,1}[\d.]+)[^.\d]*$'
        self.matcher = re.compile(self.pattern)


        # 同じページを取得する場合にはキャッシュを使用するように設定
        self.load_interval = 2.0
        self.load_time = None
        self.cache = None
        self.average_cache = None

    def get_average_temperature(self, date:datetime.date=None, proxies:dict=None) -> float:
        """
        指定した日付に対応した平均情報を取得します。
        """
        if date is None:
            raise ValueError('日の情報が設定されていません。')
        month = date.month
        day = date.day

        if self.average_cache is None \
            or not self.average_cache['month'] == month:
            if proxies is None:
                proxies = {
                    'http': '',
                    'https': '',
                }

            # お作法としてアクセス間隔を空けます。
            if self.load_time is not None:
                current_time = time.perf_counter()
                interval = self.load_interval - (current_time - self.load_time)
                if  interval > 0:
                    time.sleep(interval)

            rows_data = self._fetch_month_data(self.template_average_url,
                                               date=date, proxies=proxies)
            # キャッシュにデータを格納します。
            self.average_cache = {
                'month': month,
                'rows': rows_data
            }
            self.load_time = time.perf_counter()

        index_row = self.average_data_start_row + day
        rows_data = self.average_cache['rows']
        row = rows_data[index_row]

        average = row.select('td')[self.average_temp_idx].string

        average = self._get_float_value(average)

        return float(average)


    def get_temperature(self, date:datetime.date=None, proxies:dict=None) -> float:
        """
        指定した日付の情報を取得します。
        """
        if date is None:
            oneday = datetime.timedelta(days=1)
            date = datetime.date.today() - oneday
        year = date.year
        month = date.month
        day = date.day

        if self.cache is None \
            or not (self.cache['year'] == year and self.cache['month'] == month):
            # キャッシュに情報がない場合はサイトから取得します。
            if proxies is None:
                proxies = {
                    'http': '',
                    'https': '',
                }

            # お作法としてアクセス間隔を空けます。
            if self.load_time is not None:
                current_time = time.perf_counter()
                interval = self.load_interval - (current_time - self.load_time)
                if  interval > 0:
                    time.sleep(interval)

            rows_data = self._fetch_month_data(self.template_url, date=date, proxies=proxies)
            # キャッシュにデータを格納します。
            self.cache = {
                'year': year,
                'month': month,
                'rows': rows_data
            }
            self.load_time = time.perf_counter()

        index_row = self.data_start_row + day
        rows_data = self.cache['rows']
        row = rows_data[index_row]

        average = row.select('td.data_0_0')[self.temp_idx].string

        average = self._get_float_value(average)

        return float(average)

    def _fetch_month_data(self, template_url, date:datetime.date, proxies):
        """
        サイトからデータを取得してきます。
        """
        year = date.year
        month = date.month
        day = date.day

        url_data = {
            'prefecture': self.prefecture,
            'location': self.location,
            'year': year,
            'month': month,
            'day': day,
        }
        load_url = template_url.format(**url_data)
        html = requests.get(load_url, proxies=proxies)
        soup = BeautifulSoup(html.content, 'html.parser')
        table = soup.find('table', class_='data2_s', id='tablefix1')
        rows = table.find_all('tr')

        return rows

    def _get_float_value(self, value:str):
        """
        スクレイピングで取得した文字から数値データを取得します。
        """
        match = self.matcher.match(value)
        re_value = match.group(1)

        return float(re_value)

    def get_prefecture_list(self, proxies):
        """
        都府県・地方の一覧を取得します。
        """
        if proxies is None:
            proxies = {
                'http': '',
                'https': '',
            }
        # お作法としてアクセス間隔を空けます。
        if self.load_time is not None:
            current_time = time.perf_counter()
            interval = self.load_interval - (current_time - self.load_time)
            if  interval > 0:
                time.sleep(interval)

        load_url = self.prefecture_url
        html = requests.get(load_url, proxies=proxies)
        self.load_time = time.perf_counter()

        pattern = r'^.*prec_no=(\d+).*$'
        matcher = re.compile(pattern)

        soup = BeautifulSoup(html.content, 'html.parser')
        map_japan = soup.find('map')
        area_datas = map_japan.find_all('area')
        result_list = []

        for area_data in area_datas:
            name = area_data.attrs['alt']
            url = area_data.attrs['href']
            match = matcher.match(url)
            if match:
                code = match.group(1)
            else:
                code = None

            pref = Prefecture(code=code, name=name)
            result_list.append(pref)

        return result_list


    def get_block_list(self, pref_code, proxies):
        """
        地点の一覧を取得します。
        """
        if proxies is None:
            proxies = {
                'http': '',
                'https': '',
            }
        # お作法としてアクセス間隔を空けます。
        if self.load_time is not None:
            current_time = time.perf_counter()
            interval = self.load_interval - (current_time - self.load_time)
            if  interval > 0:
                time.sleep(interval)

        url_data = {
            'prefecture': pref_code
        }
        load_url = self.template_block_url.format(**url_data)
        html = requests.get(load_url, proxies=proxies)
        self.load_time = time.perf_counter()

        pref_pattern = r'^.*prec_no=(\d+).*$'
        block_pattern = r'^.*block_no=(\d+).*$'
        pref_matcher = re.compile(pref_pattern)
        block_matcher = re.compile(block_pattern)

        soup = BeautifulSoup(html.content, 'html.parser')
        map_japan = soup.find('map')
        area_datas = map_japan.find_all('area')
        result_list = []

        for area_data in area_datas:
            name = area_data.attrs['alt']
            url = area_data.attrs['href']
            match = pref_matcher.match(url)
            if match:
                _pref_code = match.group(1)
            else:
                continue

            match = block_matcher.match(url)
            if match:
                code = match.group(1)
            else:
                continue

            # codeが'00'の時は～全域という名前なので取得しない。
            if code == '00':
                continue

            block = Block(pref_code=_pref_code, code=code, name=name)
            if block not in result_list:
                result_list.append(block)

        return result_list
