# coding: utf-8
"""
気温取得用スクレイピング機能のテスト
"""
import datetime
import pytest
import scraping
import time

temperature_datas = [
    (datetime.date(year=2021, month=3, day=14), 11.8),
    (datetime.date(year=2021, month=3, day=5), 9.5),
    (datetime.date(year=2021, month=1, day=20), 7.4),
    (datetime.date(year=2020, month=10, day=29), 15.1),
]


@pytest.mark.parametrize('day, answer', temperature_datas)
def test_fetch_temperature(day, answer):
    """
    スクレイピイングによる平均気温情報取得機能テスト
    """
    time.sleep(5.0) 
    result = scraping.fetch_temperature(day)

    assert isinstance(result, float)
    assert answer == answer
