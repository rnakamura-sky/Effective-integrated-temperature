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
    def __init__(self, id:int=-1, name:str='', type:TargetTypeModel=None, datas:list=None, comment:str=''):
        self.id = id
        self.name = name
        self.type = type
        self.datas = datas
        self.comment = comment
    
    def __str__(self):
        return f'Id:{self.id} Name:{self.name} Comment:{self.comment}'

class TargetDataModel():
    """
    ターゲット内でのデータを管理するためのモデル
    """
    def __init__(self, id:int=-1, target:TargetModel=None, refer=None, state:str='', base:float=0.0, accum:float=0.0, comment:str=''):
        self.id = id
        self.target = target
        self.refer = refer
        self.state = state
        self.base = base
        self.accum = accum
        self.comment = comment

    def __str__(self):
        return f'Id:{self.id} State:{self.state} Base:{self.base} Accum:{self.accum} Comment:{self.comment}'


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
    # _base = target.base
    # _accum = target.accum
    _comment = target.comment

    target_datas = target.datas

    cursor = conn.cursor()

    cursor.execute(
        'INSERT INTO Target(Name, Type, Comment) '
        'VALUES (?, ?, ?);',
        (_name, _type, _comment)
    )
    _id = cursor.lastrowid
    target.id = _id
    for data in target_datas:
        _id_data = -1
        _state = data.state
        _refer = data.refer.id if data.refer is not None else None
        _base = data.base
        _accum = data.accum
        _comment = data.comment
        cursor.execute(
            'INSERT INTO TargetData(Target, State, Reference, Base, Accumulation, Comment) '
            'VALUES (?, ?, ?, ?, ?, ?);',
            (_id, _state, _refer, _base, _accum, _comment)
        )
        _id_data = cursor.lastrowid
        data.id = _id_data
        data.target = target
    conn.commit()
    cursor.close()

    return target

def delete_target(conn, target_id):
    """
    指定されたターゲットを削除します。
    """
    cursor = conn.cursor()
    cursor.execute(
        'DELETE FROM Target WHERE Id = ?', (target_id,)
    )
    cursor.execute(
        'DELETE FROM TargetData WHERE Target = ?', (target_id,)
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
    _comment = target.comment

    cursor = conn.cursor()

    cursor.execute(
        'UPDATE Target '
        'SET Name = ?, Type = ?, Comment = ? '
        'WHERE Id = ?;',
        (_name, _type, _comment, _id)
    )
    for data in target.datas:
        _data_id = data.id
        _state = data.state
        _refer = None if data.refer is None else data.refer.id
        _base = data.base
        _accum = data.accum
        _comment = data.comment
        cursor.execute(
            'UPDATE TargetData '
            'SET State = ?, Reference = ?, Base = ?, Accumulation = ?, Comment = ? '
            'WHERE Id = ?;',
            (_state, _refer, _base, _accum, _comment, _data_id)
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
    cursor.execute(
        'SELECT * '
        'FROM TargetData '
        'WHERE Target = ?;',
        (id, )
    )
    result_datas = cursor.fetchall()

    target_type = get_target_type(conn, result['Type'])

    target = TargetModel(
        id=result['Id'],
        name=result['Name'],
        type=target_type,
        comment=result['Comment']
    )
    target_data_dict = dict()
    for result_data in result_datas:
        target_data = TargetDataModel(
            id=result_data['Id'],
            target=target,
            state=result_data['State'],
            refer=result_data['Reference'],
            base=result_data['Base'],
            accum=result_data['Accumulation'],
            comment=result_data['Comment']
        )
        target_data_dict[target_data.id] = target_data
    target_datas = []
    for tmp in target_data_dict.values():
        print(tmp.refer)
        if tmp.refer is not None:
            tmp.refer = target_data_dict[tmp.refer]
        target_datas.append(tmp)
    target.datas = target_datas

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
    result_dict = dict()
    for row in cursor.fetchall():
        data = dict(row)
        target_type = target_type_dict[data['Type']]
        target = TargetModel(
            id=data['Id'],
            name=data['Name'],
            type=target_type,
            datas=[],
            comment=data['Comment'],
        )
        result_dict[target.id] = target

    target_datas = []
    cursor.execute('SELECT * FROM TargetData;')
    result_data_dict = dict()
    for row in cursor.fetchall():
        data = dict(row)
        target_data = TargetDataModel(
            id=data['Id'],
            target=data['Target'],
            state=data['State'],
            refer=data['Reference'],
            base=data['Base'],
            accum=data['Accumulation'],
            comment=data['Comment']
        )
        result_data_dict[target_data.id] = target_data    

    for data in result_data_dict.values():
        if data.refer is not None:
            data.refer = result_data_dict[data.refer]
        target = result_dict[data.target]
        data.target = target
        target.datas.append(data)
    
    results = list(result_dict.values())
    cursor.close()

    return results


