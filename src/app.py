# coding: utf-8
"""
    有効積算温度を確認できるツール
"""
# import sqlite3
import datetime
import os
from db import get_connection, db_init, insert_temperature, TemperatureModel, db_insert_default_values
import scraping


def init_temperature(conn, proxies=None):
    """
    気温情報を初期登録します。
    """
    today = datetime.date.today()
    criteria_date = datetime.date(year=today.year, month=1, day=1)
    oneday = datetime.timedelta(days=1)

    scrape_temp = scraping.ScrapeTemp()
    day = criteria_date

    while day != today:
        temp = scrape_temp.get_temperature(day, proxies=proxies)
        temp_model = TemperatureModel(date=day, temp=temp)
        insert_temperature(conn, temp_model)
        day = day + oneday
    
    conn.commit()



if __name__ == '__main__':
    print('Hello World')

    proxies = {
        'http': os.environ['http_proxy'],
        'https': os.environ['https_proxy'],
    }

    # 設定ファイル等を格納するためのフォルダ指定
    instance_path = './instance'
    if not os.path.exists(instance_path):
        os.mkdir(instance_path)

    db_name = 'example.db'
    schema_filename = 'schema.sql'

    # パスを変換
    db_name = os.path.join(instance_path, db_name)

    conn = None
    if not os.path.exists(db_name):
        # データベースと接続
        conn = get_connection(db_name)
        
        # データベースの初期化
        db_init(conn, schema_filename)

        # 初期データ投入
        db_insert_default_values(conn)
        
        # 気温初期データ取得
        init_temperature(conn, proxies)
    else:
        # データベースと接続
        conn = get_connection(db_name)


    conn.close()