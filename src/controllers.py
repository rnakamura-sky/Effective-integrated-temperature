# coding: utf-8
"""
GUIとビジネスロジックをつなぎ合わせるコントローラー
"""
import datetime
import pandas as pd
import db
import scraping

class CalcTargetData:
    """
    ターゲットデータの有効積算温度を計算するときに
    参照するターゲットデータを考慮した計算を行うためのクラス
    """
    def __init__(self, target_data, myself=False):
        self.target_data = target_data
        self.myself = myself
        self.finish = False
        self.current_accum = 0.0
        self.before = None
        if target_data.refer is not None:
            self.before = CalcTargetData(target_data.refer)

    def calc_accum(self, temp:float) -> float:
        """
        有効積算温度を計算します。
        """
        if not self.myself and self.finish:
            return self.current_accum

        if self.before is not None:
            if self.before.finish:
                diff = temp - self.target_data.base if temp > self.target_data.base else 0.0
                self.current_accum = self.current_accum + diff
            else:
                self.before.calc_accum(temp)
        else:
            diff = temp - self.target_data.base if temp > self.target_data.base else 0.0
            self.current_accum = self.current_accum + diff
        if self.current_accum >= self.target_data.accum:
            self.finish = True

        return self.current_accum


def calc_table_data(targets, temperatures) -> pd.DataFrame:
    """
    積算有効温度情報を表示するための表を作成します。
    """
    temperature_dict = {temp.date: temp for temp in temperatures}
    date_list = list(temperature_dict.keys())
    temp_list = [t.temp for t in temperature_dict.values()]

    index_column = 'Id'
    column_list = ['Id', '名前', '状態', 'ゼロ点', '積算有効温度', '積算温度'] \
                + [d.strftime('%m/%d') for d in date_list]

    data = pd.DataFrame(columns=column_list)
    data = data.set_index(index_column)

    # 1行目には気温情報を入れておきます。
    row_temp = ['気温', '-', 0.0, 0.0, round(sum(temp_list), 1)] + temp_list
    data.loc[0] = row_temp

    for target in targets:
        is_first = True
        for target_data in target.datas:
            calc_module = CalcTargetData(target_data, myself=True)
            target_temp_list = [0.0 for i in range(len(temp_list))]
            sum_value = 0.0
            for i, temp in enumerate(temp_list):
                sum_value = calc_module.calc_accum(temp)
                target_temp_list[i] = round(sum_value, 1)

            if is_first:
                row_target = [target.name, target_data.state, target_data.base, \
                                target_data.accum, round(target_temp_list[-1], 1)]  \
                            + target_temp_list
                is_first = False
            else:
                row_target = ['', target_data.state, target_data.base, \
                                target_data.accum, round(target_temp_list[-1], 1)] \
                            + target_temp_list

            data.loc[target_data.id] = row_target
    return data


class Controller():
    """
    GUIからのリクエストをビジネスロジックをつなぐコントローラー
    """
    def __init__(self, conn, current_day, criteria_day, config, proxies):
        self.conn = conn
        self.current_day = current_day
        self.criteria_day = criteria_day
        self.config = config
        self.proxies = proxies

        location = config.get_location()
        self.scrape_temp = scraping.ScrapeTemp(location['prefecture'], location['block'])

        self.targets = None
        self.target_types = None
        self.temperatures = None
        self.table_data = None

    def get_targets(self):
        """
        ターゲット一覧を取得します。
        """
        if self.targets is None:
            self.targets = db.get_targets(self.conn)
        return self.targets

    def get_target(self, target_id):
        """
        idで指定されたターゲットを取得します。
        """
        return db.get_target(self.conn, target_id)

    def get_target_data(self, target_data_id):
        """
        idで指定されたターゲットデータを取得します。
        """
        return db.get_target_data(self.conn, target_data_id)

    def get_target_types(self):
        """
        ターゲットタイプ一覧を取得します。
        """
        if self.target_types is None:
            self.target_types = db.get_target_types(self.conn)
        return  self.target_types

    def get_temperatures(self):
        """
        気温情報を取得します。
        """
        if self.temperatures is None:
            self.temperatures = db.get_temperature_info(self.conn, self.criteria_day)
        return self.temperatures

    def get_table_data(self):
        """
        GUIで表示するためのテーブルデータを取得します。
        """
        if self.table_data is None:
            targets = self.get_targets()
            temperatures = self.get_temperatures()
            self.table_data = calc_table_data(targets, temperatures)
        return self.table_data

    def has_all_day(self):
        """
        基準となる日から現在の日付で存在しない日付があるか返します。
        """
        criteria_day = self.criteria_day
        current_day = self.current_day
        oneday = datetime.timedelta(days=1)

        temperatures = self.get_temperatures()
        days = sorted([temp.date for temp in temperatures])
        search_day = criteria_day
        for day in days:
            if search_day == day:
                pass
            else:
                return False
            search_day += oneday

        if search_day != current_day:
            return False
        return True

    def get_empty_days(self):
        """
        データがない日付一覧を取得します。
        """
        empty_days = []
        criteria_day = self.criteria_day
        current_day = self.current_day
        oneday = datetime.timedelta(days=1)

        temperatures = self.get_temperatures()
        days = sorted([temp.date for temp in temperatures])
        search_day = criteria_day

        while search_day < current_day:
            if search_day not in days:
                empty_days.append(search_day)
            search_day += oneday

        return empty_days

    def update_temperatures(self):
        """
        登録されていない日付データを更新します。
        """
        days = self.get_empty_days()

        scrape_temp = self.scrape_temp
        proxies = self.proxies
        conn = self.conn

        for day in days:
            temp = scrape_temp.get_temperature(day, proxies=proxies)
            temp_model = db.TemperatureModel(date=day, temp=temp)
            db.insert_temperature(conn, temp_model)
        conn.commit()

        self.temperatures = None
        self.table_data = None

    def update_current_day(self, day):
        """
        現在の日付とする日付を更新します。
        """
        self.current_day = day
        self.temperatures = None
        self.table_data = None

    def get_current_day(self):
        """
        設定されている現在の日付を取得します。
        """
        return self.current_day

    def registor_target(self, data:dict):
        """
        ターゲットを登録します。
        """
        conn = self.conn
        target_data = db.TargetDataModel(
            refer=None,
            state=data['state'],
            base=data['base'],
            accum=data['accum'],
            comment=data['comment']
        )
        target = db.TargetModel(
            name=data['name'],
            type=data['type'],
            datas=[target_data],
            comment='',
        )
        target_data.target = target
        db.insert_target(conn, target)

        self.targets = None
        self.table_data = None

    def update_target(self, data:dict):
        """
        ターゲットを更新します。
        """
        conn = self.conn
        target = db.TargetModel(
            id=data['id'],
            name=data['name'],
            type=data['type'],
            datas=[],
            comment=''
        )
        db.update_target(conn, target)

        self.targets = None
        self.table_data = None

    def registor_target_data(self, data:dict):
        """
        ターゲットデータを登録します。
        """
        conn = self.conn
        target_data = db.TargetDataModel(
            target=data['target'],
            refer=data['refer'],
            state=data['state'],
            base=data['base'],
            accum=data['accum'],
            comment=data['comment']
        )
        db.insert_target_data(conn, target_data)

        self.targets = None
        self.table_data = None

    def update_target_data(self, data:dict):
        """
        ターゲットデータを更新します。
        """
        conn = self.conn
        target_data = db.TargetDataModel(
            id=data['data_id'],
            target=data['target'],
            refer=data['refer'],
            state=data['state'],
            base=data['base'],
            accum=data['accum'],
            comment=data['comment']
        )

        db.update_target_data(conn, target_data)

        self.targets = None
        self.table_data = None

    def delete_target(self, target_id):
        """
        指定されたターゲットを削除します。
        """
        conn = self.conn
        db.delete_target(conn, target_id)

        self.targets = None
        self.table_data = None
