# coding:utf-8
"""
db.pyのテスト
"""
import os
import datetime
import random
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

def test_db_init(get_db_no_schema, get_schema_filename):
    """
    DB初期化のテスト
    テーブルが作成できていることを確認します。
    """
    conn = get_db_no_schema
    db.db_init(conn, get_schema_filename)

    # Tableが作成できていることをSELECT文で確認
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Target;')
    cursor.execute('SELECT * FROM TargetData')
    cursor.execute('SELECT * FROM TargetType;')
    cursor.execute('SELECT * FROM Temperature;')

    if cursor is not None:
        cursor.close()

def test_db_insert_default_values(get_db_no_init_data):
    """
    DBを初期化して初期値としてデータ登録するテスト
    """
    conn = get_db_no_init_data
    db.db_insert_default_values(conn)

    cursor = conn.cursor()

    cursor.execute('SELECT * FROM TargetType;')

    target_types = []
    for row in cursor.fetchall():
        target_types.append(dict(row))


    assert len(target_types) == 2
    for target_type in target_types:
        assert target_type['Id'] in [1, 2]
        assert target_type['Name'] in ['植物', '虫']
        assert target_type['Comment'] in ['植物につけるタイプ', '虫につけるタイプ']

    if cursor is not None:
        cursor.close()


def test_insert_temperature(get_db):
    """
    気温情報登録テスト
    """

    date = datetime.date(2021, 3, 18)
    temp = 26.5
    test_data = db.TemperatureModel(date=date, temp=temp)
    conn = get_db
    db.insert_temperature(conn, test_data)

    temp_id = test_data.id

    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Temperature WHERE Id = ?', (temp_id,))
    result = cursor.fetchone()

    data = dict(result)

    assert temp_id is not None
    assert data['Date'] == date
    assert data['Temperature'] == temp

    if cursor is not None:
        cursor.close()

def test_get_target_type(get_db):
    """
    ターゲットタイプ取得機能テスト
    """
    _id = -1
    name = 'TEST TYPE'
    comment = 'TEST TYPE COMMENT'

    conn = get_db
    cursor = conn.cursor()

    cursor.execute(
        'INSERT INTO TargetType(Name, Comment) VALUES (?, ?);',
        (name, comment))
    _id = cursor.lastrowid
    conn.commit()
    cursor.close()

    result = db.get_target_type(conn, _id)
    assert isinstance(result, db.TargetTypeModel)
    assert result.id == _id
    assert result.name == name
    assert result.comment == comment

def test_get_target_types(get_db):
    """
    ターゲットタイプ一覧取得機能テスト
    """
    conn = get_db
    target_type_list = db.get_target_types(conn)

    assert len(target_type_list) == 2
    for target_type in target_type_list:
        assert isinstance(target_type, db.TargetTypeModel)
        assert target_type.id in [1, 2]
        assert target_type.name in ['植物', '虫']
        assert target_type.comment in ['植物につけるタイプ', '虫につけるタイプ']
    

def test_insert_target(get_db):
    """
    ターゲット登録機能のテスト
    """
    target_id = -1
    target_name = '桜'
    target_type = None
    target_comment = '桜'

    target_data_state = 'TEST'
    target_data_base = 10.0
    target_data_accum = 400.0
    target_data_comment = 'TEST DATA'

    conn = get_db
    cursor = conn.cursor()

    # ターゲットタイプが必要なのでターゲットタイプを取得
    target_type_list = db.get_target_types(conn)

    for _target_type in target_type_list:
        if _target_type.name == '植物':
            target_type = _target_type
            break
    assert target_type is not None

    target_data = db.TargetDataModel(
        state=target_data_state,
        refer=None,
        base=target_data_base,
        accum=target_data_accum,
        comment=target_data_comment,
    )

    target = db.TargetModel(
        name=target_name,
        type=target_type,
        datas=[target_data],
        comment=target_comment)

    db.insert_target(conn, target)

    cursor.execute('SELECT * FROM Target WHERE Id = ?;', (target.id,))
    result_target = dict(cursor.fetchone())
    cursor.execute('SELECT * FROM TargetData WHERE Id = ?;', (target.datas[0].id, ))
    result_target_data = dict(cursor.fetchone())

    assert result_target['Id'] == target.id
    assert result_target['Name'] == target.name
    assert result_target['Type'] == target.type.id
    assert result_target['Comment'] == target.comment
    
    assert result_target_data['Id'] == target_data.id
    assert result_target_data['Target'] == target_data.target.id
    assert result_target_data['Reference'] is None
    assert result_target_data['State'] == target_data.state
    assert result_target_data['Base'] == target_data.base
    assert result_target_data['Accumulation'] == target_data.accum
    assert result_target_data['Comment'] == target_data.comment
    cursor.close()


def test_get_target(get_db):
    """
    ターゲット登録機能のテスト
    """
    _target_id = -1
    _name = '桜'
    _type_id = -1
    _target_comment = '桜'

    _target_data_id = -1
    _state = 'TTT'
    _base = 10.0
    _accum = 400.0
    _target_data_comment = 'TEST'

    conn = get_db
    cursor = conn.cursor()

    target_type = None

    # ターゲットタイプが必要なのでターゲットタイプを取得
    target_type_list = db.get_target_types(conn)

    for _target_type in target_type_list:
        if _target_type.name == '植物':
            target_type = _target_type
            break
    assert target_type is not None
    _type_id = target_type.id

    cursor.execute(
        'INSERT INTO Target(Name, Type, Comment) VALUES (?, ?, ?);',
        (_name, _type_id, _target_comment)
    )
    _target_id = cursor.lastrowid
    cursor.execute(
        'INSERT INTO TargetData(Target, State, Base, Accumulation, Comment) VALUES (?, ?, ?, ?, ?);',
        (_target_id, _state, _base, _accum, _target_data_comment)
    )
    _target_data_id = cursor.lastrowid

    conn.commit()

    result = db.get_target(conn, _target_id)

    assert isinstance(result, db.TargetModel)
    assert result.id == _target_id
    assert result.name == _name
    assert result.type.id == _type_id
    assert result.comment == _target_comment
    assert len(result.datas) == 1

    result_target_data = result.datas[0]
    assert isinstance(result_target_data, db.TargetDataModel)
    assert result_target_data.id == _target_data_id
    assert result_target_data.target.id == _target_id
    assert result_target_data.state == _state
    assert result_target_data.refer is None
    assert result_target_data.base == _base
    assert result_target_data.accum == _accum
    assert result_target_data.comment == _target_data_comment

    cursor.close()

def test_update_target(get_db):
    """
    ターゲット更新機能のテスト
    """
    target_id = -1
    target_name = '桜'
    target_type = None
    target_comment = '桜'

    target_data_id = -1
    target_state = 'TTT'
    target_base = 10.0
    target_accum = 400.0
    target_data_comment = 'DATA'


    update_target_name = 'さくら'
    update_target_type = None
    update_target_comment = 'さくら'
    update_target_state = 'EEE'
    update_target_base = 20.0
    update_target_accum = 600.0
    update_target_data_comment = 'ATAD'

    conn = get_db
    cursor = conn.cursor()

    # ターゲットタイプが必要なのでターゲットタイプを取得
    target_type_list = db.get_target_types(conn)

    for _target_type in target_type_list:
        if _target_type.name == '植物':
            target_type = _target_type
        if _target_type.name == '虫':
            update_target_type = _target_type
    assert target_type is not None
    assert update_target_type is not None

    target_data = db.TargetDataModel(
        id=-1,
        target=None,
        refer=None,
        state=target_state,
        base=target_base,
        accum=target_accum,
        comment=target_data_comment
    )

    target = db.TargetModel(
        name=target_name,
        type=target_type,
        datas=[target_data],
        comment=target_comment)
    db.insert_target(conn, target)

    ## ここからテスト
    update_target_data = db.TargetDataModel(
        id=target_data.id,
        target=target,
        refer=None,
        state=update_target_state,
        base=update_target_base,
        accum=update_target_accum,
        comment=update_target_data_comment
    )
    update_target = db.TargetModel(
        id=target.id,
        name=update_target_name,
        type=update_target_type,
        datas=[update_target_data],
        comment=update_target_comment,
    )

    db.update_target(conn, update_target)

    cursor.execute('SELECT * FROM Target WHERE Id = ?;', (target.id,))
    result = dict(cursor.fetchone())
    cursor.execute('SELECT * FROM TargetData WHERE Id = ?;', (target_data.id, ))
    result_data = dict(cursor.fetchone())

    assert result['Id'] == target.id
    assert result['Name'] == update_target.name
    assert result['Type'] == update_target.type.id
    assert result['Comment'] == update_target.comment
    assert len(update_target.datas) == 1

    assert result_data['Id'] == target_data.id
    assert result_data['Target'] == target.id
    assert result_data['Reference'] == None
    assert result_data['State'] == update_target_state
    assert result_data['Base'] == update_target_data.base
    assert result_data['Accumulation'] == update_target_data.accum
    assert result_data['Comment'] == update_target_data_comment

    cursor.close()

def test_delete_target(get_db):
    """
    ターゲット削除機能テスト
    """
    conn = get_db
    target_type = db.get_target_type(conn, id=1)
    target_data = db.TargetDataModel(
        id=-1,
        target=None,
        refer=None,
        state='TEST',
        base=0.0,
        accum=100.0,
        comment='TEST'
    )
    target = db.TargetModel(
        id=-1,
        name='TEST TARGET',
        type=target_type,
        datas=[target_data],
        comment='TEST'
    )
    target_data.target = target

    db.insert_target(conn, target)
    assert target.id > 0
    assert target_data.id > 0

    db.delete_target(conn, target.id)

    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Target WHERE Id = ?;', (target.id,))
    result = cursor.fetchone()
    assert result is None
    cursor.execute('SELECT * FROM TargetData WHERE Target = ?;', (target.id,))
    result = cursor.fetchone()
    assert result is None

    cursor.close()


def test_get_targets(get_db):
    """
    ターゲット一覧取得メソッドテスト
    """
    conn = get_db
    target_types = db.get_target_types(conn)
    count = 0
    target_datas = [
        db.TargetModel(name='TEST1', type=target_types[0], comment='TEST1',
                        datas=[db.TargetDataModel(state='STATE1', base=10.0, accum=300.0, comment='TEST DATA1')]),
        db.TargetModel(name='TEST2', type=target_types[0], comment='TEST2',
                        datas=[db.TargetDataModel(state='STATE2', base=10.0, accum=300.0, comment='TEST DATA2')]),
        db.TargetModel(name='TEST3', type=target_types[1], comment='TEST3',
                        datas=[db.TargetDataModel(state='STATE3', base=10.0, accum=300.0, comment='TEST DATA3')]),
        db.TargetModel(name='TEST4', type=target_types[1], comment='TEST4',
                        datas=[db.TargetDataModel(state='STATE4', base=10.0, accum=300.0, comment='TEST DATA4')]),
    ]
    for t in target_datas:
        db.insert_target(conn, t)
    target_dict = dict()
    for t in target_datas:
        target_dict[t.id] = t
    
    target_list = db.get_targets(conn)

    assert len(target_list) == len(target_dict)
    for target in target_list:
        _temp = target_dict.get(target.id)
        assert _temp is not None
        assert target.name == _temp.name
        assert target.type.id == _temp.type.id
        assert target.comment == _temp.comment

        assert len(target.datas) == len(_temp.datas)
        target_data = target.datas[0]
        _temp_data = _temp.datas[0]
        assert target_data.id == _temp_data.id
        assert target_data.target.id == _temp_data.target.id
        assert target_data.refer is None
        assert target_data.state == _temp_data.state
        assert target_data.base == _temp_data.base
        assert target_data.accum == _temp_data.accum
        assert target_data.comment == _temp_data.comment

def test_insert_target_data(get_db):
    """
    ターゲットデータを作成する機能テスト
    """
    conn = get_db
    target_type = db.get_target_type(conn, id=1)
    target_data = db.TargetDataModel(
        id=-1,
        target=None,
        refer=None,
        state='TEST',
        base=0.0,
        accum=100.0,
        comment='TEST'
    )
    target = db.TargetModel(
        id=-1,
        name='TEST TARGET',
        type=target_type,
        datas=[target_data],
        comment='TEST'
    )
    target_data.target = target

    db.insert_target(conn, target)

    new_target_data = db.TargetDataModel(
        id=-1,
        target=target,
        refer=None,
        state='NEW TEST',
        base=6.0,
        accum=123.4,
        comment='NEW COMMENT'
    )

    db.insert_target_data(conn, new_target_data)

    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM TargetData WHERE Id = ?;',
        (new_target_data.id, )
    )
    result = cursor.fetchone()

    assert result is not None
    assert result['Id'] == new_target_data.id
    assert result['Target'] == new_target_data.target.id
    assert result['Reference'] is None
    assert result['State'] == new_target_data.state
    assert result['Base'] == new_target_data.base
    assert result['Accumulation'] == new_target_data.accum
    assert result['Comment'] == new_target_data.comment



def test_update_target_data(get_db):
    """
    ターゲットデータを更新する機能テスト
    """
    conn = get_db
    target_type = db.get_target_type(conn, id=1)
    target_data = db.TargetDataModel(
        id=-1,
        target=None,
        refer=None,
        state='TEST',
        base=0.0,
        accum=100.0,
        comment='TEST'
    )
    target = db.TargetModel(
        id=-1,
        name='TEST TARGET',
        type=target_type,
        datas=[target_data],
        comment='TEST'
    )
    target_data.target = target

    db.insert_target(conn, target)

    update_target_data = db.TargetDataModel(
        id=target_data.id,
        target=target_data.target,
        refer=None,
        state='NEW TEST',
        base=6.0,
        accum=123.4,
        comment='NEW COMMENT'
    )

    db.update_target_data(conn, update_target_data)

    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM TargetData WHERE Id = ?;',
        (update_target_data.id, )
    )
    result = cursor.fetchone()

    assert result is not None
    assert target_data.id == update_target_data.id
    assert result['Id'] == update_target_data.id
    assert result['Target'] == update_target_data.target.id
    assert result['Reference'] is None
    assert result['State'] == update_target_data.state
    assert result['Base'] == update_target_data.base
    assert result['Accumulation'] == update_target_data.accum
    assert result['Comment'] == update_target_data.comment




def test_get_temperature_info(get_db):
    """
    気温情報をＤＢから取得するメソッドテスト
    いろいろ考慮する必要がありそうですが、今はある日付以降
    のデータを取得するメソッドとします。
    """
    before_days = 60
    oneday = datetime.timedelta(days=1)
    current_day = datetime.date.today()
    base_day = current_day - oneday * before_days
    temps = []
    random.seed(0)
    for i in range(60):
        _d = current_day - oneday * i
        _temp = random.uniform(-3.0, 25.0)
        tm = db.TemperatureModel(date=_d, temp=_temp)
        temps.append(tm)

    temps = sorted(temps, key=lambda x:x.date)
    
    conn = get_db
    for temp in temps:
        db.insert_temperature(conn, temp)
    
    results = db.get_temperature_info(conn, base_day)

    assert len(results) == before_days
    for _t, _r in zip(temps, results):
        assert _t.id == _r.id
        assert _t.date == _r.date
        assert _t.temp == _r.temp
    

    