# coding:utf-8
"""
db.pyのテスト
"""
import os
import db

def test_sample():
    """
    テストのサンプル
    """
    assert 1 == 1


def test_get_connection(get_db_name):
    """
    DBのコネクションが正常に取得できることをテスト
    """
    is_exists = os.path.exists(get_db_name)
    assert not is_exists
    conn = db.get_connection(get_db_name)

    is_exists = os.path.exists(get_db_name)
    assert is_exists
    assert conn is not None

    if conn is not None:
        conn.close()

def test_db_init(get_db_name, get_schema_filename):
    """
    DB初期化のテスト
    テーブルが作成できていることを確認します。
    """
    conn = db.get_connection(get_db_name)
    db.db_init(conn, get_schema_filename)

    # Tableが作成できていることをSELECT文で確認
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Target;')
    cursor.execute('SELECT * FROM TargetType;')
    cursor.execute('SELECT * FROM Tempreture;')

    if cursor is not None:
        cursor.close()

    if conn is not None:
        conn.close()
