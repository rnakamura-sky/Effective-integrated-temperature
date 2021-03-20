# coding: utf-8
"""
スクレイピングして気温を取得する機能
"""
import datetime
import re
import requests
from bs4 import BeautifulSoup

def fetch_temperature(day:datetime.date=None) -> float:
    """
    指定した日付の情報を取得します。
    """

    # load_url_template = 'https://www.data.jma.go.jp/obd/stats/etrn/view/daily_s1.php?prec_no=49&block_no=47638&year=2021&month=3&day=14&view='
    load_url_template = 'https://www.data.jma.go.jp/obd/stats/etrn/view/daily_s1.php?prec_no=49&block_no=47638&year={}&month={}&day={}&view='
    proxies = {
        'http': '',
        'https': ''
    }

    if day is None:
        oneday = datetime.timedelta(days=1)
        day = datetime.date.today() - oneday

    year = day.year
    month = day.month
    day = day.day

    load_url = load_url_template.format(year, month, day)
    data_start_row = 4
    average_idx = 5

    row_idx = data_start_row + day - 1


    html = requests.get(load_url, proxies=proxies)
    soup = BeautifulSoup(html.content, 'html.parser')

    table = soup.find('table', class_='data2_s', id='tablefix1')
    rows = table.find_all('tr')
    row = rows[row_idx]

    average = row.select('td.data_0_0')[average_idx].string

    pattern = '^-{0,1}(\d+)\D.*$'
    matcher = re.compile(pattern)
    match = matcher.match(average)

    average = match.group(1)


    return float(average)
    
