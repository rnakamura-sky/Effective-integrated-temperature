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
    def __init__(self, id:int=-1, date:date=None, temp:float=0.0) -> None:
        self.id = id
        self.date = date
        self.temp = temp
    
    def __str__(self):
        return f'Id:{self.id} Date:{self.date} Temp:{self.temp}'


class TargetTypeModel():
    """
    ターゲットのタイプを管理するためのモデル
    """
    def __init__(self, id:int=-1, name:str='', comment:str=''):
        self.id = id
        self.name = name
        self.comment = comment
    
    def __str__(self):
        return f'Id:{self.id} Name:{self.name} Comment:{self.comment}'


class TargetModel():
    """
    ターゲットを管理するためのモデル
    """
    def __init__(self, id:int=-1, name:str='', type:TargetTypeModel=None, base:float=0.0, accum:float=0.0, comment:str=''):
        self.id = id
        self.name = name
        self.type = type
        self.base = base
        self.accum = accum
        self.comment = comment
    
    def __str__(self):
        return f'Id:{self.id} Name:{self.name} Type:{self.type.name} Base:{self.base} Accum:{self.accum} Comment:{self.comment}'


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

def get_target_type(conn, id):
    """
    ターゲットタイプを取得します。
    """
    cursor = conn.cursor()

    cursor.execute(
        'SELECT * '
        'FROM TargetType '
        'WHERE Id = ?;',
        (id,))
    result = cursor.fetchone()
    target_type = TargetTypeModel(
        id=result['Id'],
        name=result['Name'],
        comment=result['Comment']
    )
    cursor.close()
    return target_type

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

def delete_target(conn, target_id):
    """
    指定されたターゲットを削除します。
    """
    cursor = conn.cursor()
    cursor.execute(
        'DELETE FROM Target WHERE Id = ?', (target_id,)
    )
    conn.commit()
    cursor.close()

    return True

def update_target(conn, target):
    """
    ターゲットを更新します。
    """
    _id = target.id
    _name = target.name
    _type = target.type.id
    _base = target.base
    _accum = target.accum
    _comment = target.comment

    cursor = conn.cursor()

    cursor.execute(
        'UPDATE Target '
        'SET Name = ?, Type = ?, Base = ?, Accumulation = ?, Comment = ? '
        'WHERE Id = ?;',
        (_name, _type, _base, _accum, _comment, _id)
    )
    conn.commit()
    cursor.close()

    return target

def get_target(conn, id):
    """
    ターゲットを取得する
    """
    cursor = conn.cursor()

    cursor.execute(
        'SELECT * '
        'FROM Target '
        'WHERE Id = ?;',
        (id,)
    )
    result = cursor.fetchone()

    target_type = get_target_type(conn, result['Type'])

    target = TargetModel(
        id=result['Id'],
        name=result['Name'],
        type=target_type,
        base=result['Base'],
        accum=result['Accumulation'],
        comment=result['Comment']
    )

    cursor.close()
    return target

def get_temperature_info(conn, base_day:date):
    """
    気温情報の一覧を取得します。
    """
    cursor = conn.cursor()

    cursor.execute(
        'SELECT * '
        'FROM Temperature '
        'WHERE Date >= ? '
        'ORDER BY Date ASC;',
        (base_day,)
    )
    results = cursor.fetchall()

    temps = []
    for row in results:
        _r = dict(row)
        temp = TemperatureModel(_r['Id'], _r['Date'], _r['Temperature'])
        temps.append(temp)

    cursor.close()
    
    return temps

def get_targets(conn):
    """
    ターゲットの一覧を取得します。
    """

    # 先にターゲットタイプを取得しておきます。
    target_types = get_target_types(conn)
    # 扱いやすいようdictに変換
    target_type_dict = {t.id: t for t in target_types}

    cursor = conn.cursor()

    cursor.execute('SELECT * FROM Target;')
    results = []
    for row in cursor.fetchall():
        data = dict(row)
        target_type = target_type_dict[data['Type']]
        target = TargetModel(
            id=data['Id'],
            name=data['Name'],
            type=target_type,
            base=data['Base'],
            accum=data['Accumulation'],
            comment=data['Comment'],
        )
        results.append(target)
    
    cursor.close()

    return results


