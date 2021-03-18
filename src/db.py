# coding: utf-8
"""
データベースを操作するための定義をするモジュール
"""
import sqlite3
from datetime import date


class TemperatureModel():
    """
    気温情報を管理するためのモデル
    """
    def __init__(self, id:int=None, date:date=None, temp:float=0.0) -> None:
        self.id = id
        self.date = date
        self.temp = temp


class TargetTypeModel():
    """
    ターゲットのタイプを管理するためのモデル
    """
    def __init__(self, id:int=None, name:str='', comment:str=''):
        self.id = id
        self.name = name
        self.comment = comment


class TargetModel():
    """
    ターゲットを管理するためのモデル
    """
    def __init__(self, id:int=None, name:str='', type:TargetTypeModel=None, base:float=0.0, accum:float=0.0, comment:str=''):
        self.id = id
        self.name = name
        self.type = type
        self.base = base
        self.accum = accum
        self.comment = comment


def get_connection(db_name):
    """
    データベースの接続インスタンスを取得します。
    """
    # データベースの接続
    # detect_typesを指定し、カラム型を読み取る
    conn = sqlite3.connect(db_name, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


def db_init(conn, schema_filename):
    """
    データベースを初期化するためのメソッド
    """
    with open(schema_filename, 'rt') as file:
        schema = file.read()

    conn.executescript(schema)


def db_insert_default_values(conn):
    """
    データベースの初期化後にデフォルト値として設定しておく値を設定します。
    """
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO TargetType(Name, Comment) VALUES (?, ?);',
        ('植物', '植物につけるタイプ')
    )

    cursor.execute(
        'INSERT INTO TargetType(Name, Comment) VALUES (?, ?);',
        ('虫', '虫につけるタイプ')
    )

    conn.commit()

    cursor.close()


def insert_temperature(conn, data:TemperatureModel):
    """
    気温情報を登録します。
    登録されたらdata内のid が振られます。
    """
    _id = -1
    _date = data.date
    _temp = data.temp

    cursor = conn.cursor()

    cursor.execute(
        'INSERT INTO Temperature(Date, Temperature) '
        'VALUES (?, ?);',
        (_date, _temp)
    )
    _id = cursor.lastrowid

    conn.commit()
    cursor.close()

    data.id = _id
    return data


def get_target_types(conn):
    """
    ターゲットタイプの一覧を取得します。
    """
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM TargetType;')
    results = []
    for row in cursor.fetchall():
        data = dict(row)
        target_type = TargetTypeModel(data['Id'], data['Name'], data['Comment'])
        results.append(target_type)
    
    cursor.close()

    return results


def insert_target(conn, target):
    """
    ターゲットを登録します。
    """
    _id = -1
    _name = target.name
    _type = target.type.id
    _base = target.base
    _accum = target.accum
    _comment = target.comment

    cursor = conn.cursor()

    cursor.execute(
        'INSERT INTO Target(Name, Type, Base, Accumulation, Comment) '
        'VALUES (?, ?, ?, ?, ?);',
        (_name, _type, _base, _accum, _comment)
    )
    _id = cursor.lastrowid

    conn.commit()
    cursor.close()

    target.id = _id
    return target
