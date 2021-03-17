# coding: utf-8
"""
テスト用の設定
"""
import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/../src/'))

import pytest


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
