# coding: utf-8
"""
気温取得用スクレイピング機能のテスト
"""
import datetime
import scraping

def test_fetch_temperature():
    """
    スクレイピイングによる平均気温情報取得機能テスト
    """
    day = datetime.date(year=2021, month=3, day=14)
    result = scraping.fetch_temperature(day)

    assert isinstance(result, float)
    assert result == 11.8
