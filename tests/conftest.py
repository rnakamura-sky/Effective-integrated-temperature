# coding: utf-8
"""
テスト用の設定
"""
import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/../src/'))

import pytest

import db


@pytest.fixture(scope='function')
def get_db_name(tmpdir):
    """
    データーベース名を取得するためのフィクスチャ
    """
    db_name = 'example.db'
    p = tmpdir.mkdir('tmp').join(db_name)
    return str(p)

@pytest.fixture(scope='function')
def get_schema_filename():
    """
    DBのスキーマファイルパスを取得するためのfixture
    """
    schema_filename = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/../schema.sql')
    return schema_filename

@pytest.fixture(scope='function')
def get_db_no_schema(get_db_name):
    conn = db.get_connection(get_db_name)
    yield conn

    if conn is not None:
        conn.close()

@pytest.fixture(scope='function')
def get_db_no_init_data(get_db_no_schema, get_schema_filename):
    conn = get_db_no_schema
    db.db_init(conn, get_schema_filename)
    conn.commit()
    return conn

@pytest.fixture(scope='function')
def get_db(get_db_no_init_data):
    conn = get_db_no_init_data
    db.db_insert_default_values(conn)
    return conn
