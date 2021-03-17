# coding: utf-8
"""
    有効積算温度を確認できるツール
"""
# import sqlite3
import os
from db import get_connection, db_init


if __name__ == '__main__':
    print('Hello World')

    # 設定ファイル等を格納するためのフォルダ指定
    instance_path = './instance'

    db_name = 'example.db'
    schema_filename = 'schema.sql'

    # パスを変換
    db_name = os.path.join(instance_path, db_name)

    # データベースと接続
    conn = get_connection(db_name)

    # データベースの初期化
    db_init(conn, schema_filename)
    
    cursor = conn.cursor()

    conn.commit()

    cursor.close()
    conn.close()