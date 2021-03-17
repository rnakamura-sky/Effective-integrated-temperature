# coding: utf-8
"""
データベースを操作するための定義をするモジュール
"""
import sqlite3

def get_connection(db_name):
    """
    データベースの接続インスタンスを取得します。
    """
    # データベースの接続
    # detect_typesを指定し、カラム型を読み取る
    conn = sqlite3.connect(db_name, detect_types=sqlite3.PARSE_DECLTYPES)
    return conn


def db_init(conn, schema_filename):
    """
    データベースを初期化するためのメソッド
    """
    with open(schema_filename, 'rt') as f:
        schema = f.read()

    conn.executescript(schema)

def db_insert_default_values(conn):
    """
    データベースの初期化後にデフォルト値として設定しておく値を設定します。
    """
    pass
