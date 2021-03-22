# coding: utf-8
"""
スクレイピングして気温を取得する機能
"""
import time
import datetime
import re
import requests
from bs4 import BeautifulSoup


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

        self.template_url = 'https://www.data.jma.go.jp/obd/stats/etrn/view/daily_s1.php?' \
                            'prec_no={prefecture}&block_no={location}&year={year}&month={month}&day={day}&view='

        # スクレイピング用の設定
        self.data_start_row = 3
        self.average_idx = 5

        # スクレイピングした文字を整形するための設定
        self.pattern = r'^(-{0,1}[\d.]+)[^.\d]*$'
        self.matcher = re.compile(self.pattern)


        # 同じページを取得する場合にはキャッシュを使用するように設定
        self.load_interval = 2.0
        self.load_time = None
        self.cache = None

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
            
            rows_data = self._fetch_month_data(date=date, proxies=proxies)
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

        average = row.select('td.data_0_0')[self.average_idx].string

        average = self._get_float_value(average)

        return float(average)

    def _fetch_month_data(self, date:datetime.date, proxies):
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
        load_url = self.template_url.format(**url_data)
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

