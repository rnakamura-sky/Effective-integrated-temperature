# coding: utf-8
"""
    有効積算温度を確認できるツール
"""
# import sqlite3
import datetime
import os
import pandas as pd
import wx
import wx.grid
import db
from db import get_connection, db_init, insert_temperature, TemperatureModel, db_insert_default_values
import scraping


class MainFrame(wx.Frame):
    def __init__(self, *args):
        wx.Frame.__init__(self, *args)

class TemperatureTableGrid(wx.grid.Grid):
    """
    有効積算温度を集計するグリッドです。
    """
    def __init__(self, parent, data:pd.DataFrame):
        wx.grid.Grid.__init__(self, parent, -1)

        self.data = data
        row, col = data.shape
        self.CreateGrid(row, col)

        # self.SetColLabelValue(0, data.index.name)
        for i, column in enumerate(data.columns):
            self.SetColLabelValue(i, str(column))
        
        for i, row in enumerate(data.iterrows()):
            self.SetRowLabelValue(i, str(row[0]))
            for j, cell in enumerate(row[1]):
                self.SetCellValue(i, j, str(cell))
        self.SetRowLabelAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTER)

        # self.SetRowLabelSize(0)
        self.AutoSize()


def init_temperature(conn, proxies=None):
    """
    気温情報を初期登録します。
    """
    today = datetime.date.today()
    criteria_date = datetime.date(year=today.year, month=1, day=1)
    oneday = datetime.timedelta(days=1)

    scrape_temp = scraping.ScrapeTemp()
    day = criteria_date

    while day != today:
        temp = scrape_temp.get_temperature(day, proxies=proxies)
        temp_model = TemperatureModel(date=day, temp=temp)
        insert_temperature(conn, temp_model)
        day = day + oneday
    
    conn.commit()

def calc_table_data(targets, temperatures) -> pd.DataFrame:
    """
    積算有効温度情報を表示するための表を作成します。
    """
    temperature_dict = {temp.date: temp for temp in temperatures}
    date_list = list(temperature_dict.keys())
    temp_list = [t.temp for t in temperature_dict.values()]

    index_column = 'Id'
    column_list = ['Id', '名前', 'ゼロ点', '積算有効温度', '積算温度'] + [d.strftime('%m/%d') for d in date_list]

    df = pd.DataFrame(columns=column_list)
    df = df.set_index(index_column)

    # 1行目には気温情報を入れておきます。
    row_temp = ['気温', 0.0, 0.0, round(sum(temp_list), 1)] + temp_list
    df.loc[0] = row_temp

    for target in targets:
        target_temp_list = [round(t - target.base, 1) if t > target.base else 0.0 for t in temp_list]
        row_target = [target.name, target.base, target.accum, round(sum(target_temp_list), 1)] + target_temp_list
        df.loc[target.id] = row_target
    return df

if __name__ == '__main__':
    print('Hello World')

    proxies = {
        'http': os.environ['http_proxy'],
        'https': os.environ['https_proxy'],
    }

    # 基準となる日付を取得
    today = datetime.date.today()
    criteria_day = datetime.date(year=today.year, month=1, day=1)

    # 設定ファイル等を格納するためのフォルダ指定
    instance_path = './instance'
    if not os.path.exists(instance_path):
        os.mkdir(instance_path)

    db_name = 'example.db'
    schema_filename = 'schema.sql'

    # パスを変換
    db_name = os.path.join(instance_path, db_name)

    conn = None
    if not os.path.exists(db_name):
        # データベースと接続
        conn = get_connection(db_name)
        
        # データベースの初期化
        db_init(conn, schema_filename)

        # 初期データ投入
        db_insert_default_values(conn)
        
        # 気温初期データ取得
        init_temperature(conn, proxies)
    else:
        # データベースと接続
        conn = get_connection(db_name)

    # テーブルデータを取得
    targets = db.get_targets(conn)
    target_types = db.get_target_types(conn)
    temperatures = db.get_temperature_info(conn, criteria_day)

    conn.close()

    table_data = calc_table_data(targets, temperatures)
    # print(table_data.head())

    # アプリケーション起動
    app = wx.App()
    frame = MainFrame(None, -1, 'Sample')
    table = TemperatureTableGrid(frame, table_data)
    table.FreezeTo(row=1, col=4)
    frame.Show()
    app.MainLoop()
