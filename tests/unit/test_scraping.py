# coding: utf-8
"""
気温取得用スクレイピング機能のテスト
"""
import os
import datetime
import pytest
import scraping
import time

temperature_datas = [
    (datetime.date(year=2021, month=3, day=14), 11.8),
    (datetime.date(year=2021, month=3, day=5), 9.5),
    (datetime.date(year=2021, month=1, day=20), 0.3),
    (datetime.date(year=2020, month=10, day=29), 15.1),
    (datetime.date(year=2019, month=12, day=20), 9.5),
    (datetime.date(year=2020, month=10, day=27), 14.4),
    (datetime.date(year=2021, month=1, day=9), -1.6),
    (datetime.date(year=2021, month=1, day=10), -0.8),
    (datetime.date(year=2021, month=1, day=11), -1.0),
    (datetime.date(year=2021, month=1, day=12), -0.1),
]

reg_datas = [
    ('11.8', 11.8),
    ('2.0', 2.0),
    ('-17.7', -17.7),
    ('11.8 )', 11.8),
    ('-11.8 )', -11.8),
    ('11.8 ]', 11.8),
    ('-11.8 ]', -11.8),
]

@pytest.mark.parametrize('day, answer', temperature_datas)
def test_get_temperature(day, answer):
    """
    スクレイピイングによる平均気温情報取得機能テスト
    """
    time.sleep(2.0) 
    
    proxies = {
        'http': os.environ['http_proxy'],
        'https': os.environ['https_proxy'],
    }
    scrape_temp = scraping.ScrapeTemp()
    result = scrape_temp.get_temperature(day, proxies=proxies)

    assert isinstance(result, float)
    assert result == answer

def test_get_temperature_cache():
    """
    キャッシュ機能が正常に動作するかテスト
    """
    proxies = {
        'http': os.environ['http_proxy'],
        'https': os.environ['https_proxy'],
    }
    scrape_temp = scraping.ScrapeTemp()
    for date, answer in temperature_datas:
        result = scrape_temp.get_temperature(date, proxies=proxies)
        assert isinstance(result, float)
        assert result == answer

@pytest.mark.parametrize('value, answer', reg_datas)
def test_get_float_value(value, answer):
    """
    スクレイピングで取得した値をfloatに変換する機能テスト
    """
    scrape_temp = scraping.ScrapeTemp()
    result = scrape_temp._get_float_value(value)
    assert isinstance(result, float)
    assert result == answer
