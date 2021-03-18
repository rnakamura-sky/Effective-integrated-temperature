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
    target_base = 10.0
    target_accum = 400.0
    target_comment = '桜'

    conn = get_db
    cursor = conn.cursor()

    # ターゲットタイプが必要なのでターゲットタイプを取得
    target_type_list = db.get_target_types(conn)

    for _target_type in target_type_list:
        if _target_type.name == '植物':
            target_type = _target_type
            break
    assert target_type is not None

    target = db.TargetModel(
        name=target_name,
        type=target_type,
        base=target_base,
        accum=target_accum,
        comment=target_comment)

    db.insert_target(conn, target)

    cursor.execute('SELECT * FROM Target Where Id = ?;', (target.id,))

    result = dict(cursor.fetchone())

    assert result['Id'] == target.id
    assert result['Name'] == target.name
    assert result['Type'] == target.type.id
    assert result['Base'] == target.base
    assert result['Accumulation'] == target.accum
    assert result['Comment'] == target.comment


    cursor.close()


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
    

    