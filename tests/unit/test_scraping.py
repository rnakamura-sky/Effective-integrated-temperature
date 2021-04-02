# coding: utf-8
"""
気温取得用スクレイピング機能のテスト
"""
import os
import datetime
import time
import pytest
import scraping

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

average_temperature_datas = [
    (datetime.date(year=2021, month=3, day=14), 7.7),
    (datetime.date(year=2021, month=3, day=5), 6.4),
    (datetime.date(year=2021, month=1, day=20), 2.6),
    (datetime.date(year=2019, month=1, day=20), 2.6),
    (datetime.date(year=2020, month=10, day=29), 13.8),
    (datetime.date(year=2019, month=12, day=20), 4.3),
    (datetime.date(year=2020, month=10, day=27), 14.2),
    (datetime.date(year=2021, month=1, day=9), 3.0),
    (datetime.date(year=2021, month=1, day=10), 2.9),
    (datetime.date(year=2021, month=1, day=11), 2.9),
    (datetime.date(year=2021, month=1, day=12), 2.9),
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

@pytest.fixture()
def proxies():
    """
    プロキシを環境変数から取得するフィクスチャです。
    """
    result = {
        'http': os.environ.get('http_proxy'),
        'https': os.environ.get('https_proxy'),
    }
    return result

@pytest.mark.parametrize('day, answer', temperature_datas)
def test_get_temperature(proxies, day, answer):
    """
    スクレイピイングによる日毎の平均気温情報取得機能テスト
    """
    time.sleep(2.0)

    scrape_temp = scraping.ScrapeTemp()
    result = scrape_temp.get_temperature(day, proxies=proxies)

    assert isinstance(result, float)
    assert result == answer

@pytest.mark.parametrize('day, answer', average_temperature_datas)
def test_get_average(proxies, day, answer):
    """
    スクレイピングによる平均気温情報取得
    """
    time.sleep(2.0)

    scrape_temp = scraping.ScrapeTemp()
    result = scrape_temp.get_average_temperature(day, proxies=proxies)

    assert isinstance(result, float)
    assert result == answer


def test_get_temperature_cache(proxies):
    """
    キャッシュ機能が正常に動作するかテスト
    """

    scrape_temp = scraping.ScrapeTemp()
    for date, answer in temperature_datas:
        result = scrape_temp.get_temperature(date, proxies=proxies)
        assert isinstance(result, float)
        assert result == answer

def test_get_average_temperature_cache(proxies):
    """
    キャッシュ機能が正常に動作するかテスト
    """

    scrape_temp = scraping.ScrapeTemp()
    for date, answer in average_temperature_datas:
        result = scrape_temp.get_average_temperature(date, proxies=proxies)
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

def test_get_prefecture_list(proxies):
    """
    都府県・地方のデータ取得テスト
    """
    time.sleep(2.0)

    check_prefecture = scraping.Prefecture(code='49', name='山梨県')
    scrape_temp = scraping.ScrapeTemp()

    result_list = scrape_temp.get_prefecture_list(proxies=proxies)

    assert isinstance(result_list, list)
    assert isinstance(result_list[0], scraping.Prefecture)
    assert check_prefecture in result_list

def test_get_block_list(proxies):
    """
    都府県・地方のデータ取得テスト
    """
    time.sleep(2.0)

    check_block = scraping.Block(pref_code='49', code='47638', name='甲府')

    scrape_temp = scraping.ScrapeTemp()

    result_list = scrape_temp.get_block_list(pref_code=check_block.pref_code, proxies=proxies)

    assert isinstance(result_list, list)
    assert isinstance(result_list[0], scraping.Block)
    assert check_block in result_list
