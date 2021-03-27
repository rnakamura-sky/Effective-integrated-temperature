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
import wx.lib.scrolledpanel
import db
from db import get_connection, db_init, insert_temperature, TemperatureModel, db_insert_default_values
import scraping


class TemperatureTableGrid(wx.grid.Grid):
    """
    有効積算温度を集計するグリッドです。
    """
    def __init__(self, parent, data:pd.DataFrame):
        wx.grid.Grid.__init__(self, parent, -1)

        self.data = data

        row, col = data.shape
        self.CreateGrid(row, col)
        self._output_table(data)

        self.SetRowLabelAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTER)
        self.SetRowLabelSize(0)
        self.AutoSize()

        self.freeze_info = None
    
    def _output_table(self, data:pd.DataFrame):
        for i, column in enumerate(data.columns):
            self.SetColLabelValue(i, str(column))
        
        for i, row in enumerate(data.iterrows()):
            
            base = row[1][1]
            accum = row[1][2]
            temp_sum = row[1][3]
            temp_sum_before_10days = sum(row[1][-10:])
            alert_temp = 10.0
            print(base, accum, temp_sum, temp_sum_before_10days)

            colour = (255, 255, 255, 255)
            if i == 0:
                colour = (200, 255, 255)
            elif accum > temp_sum and accum < temp_sum + alert_temp:
                colour = (255, 255, 100)
            elif accum <= temp_sum and accum > temp_sum - temp_sum_before_10days:
                colour = (255, 200, 200)
            elif accum <= temp_sum:
                colour = (100, 100, 100)

            self.SetRowLabelValue(i, str(row[0]))
            for j, cell in enumerate(row[1]):
                self.SetCellValue(i, j, str(cell))
                self.SetReadOnly(i, j, True)

                # 色付け
                self.SetCellBackgroundColour(i, j, colour)

    
    def freeze_table(self, row:int, col:int):
        self.freeze_info = (row, col)
        self.FreezeTo(row=row, col=col)
    
    def update_table(self, data:pd.DataFrame):
        current_row, current_col = self.data.shape
        self.data = data
        row, col = data.shape

        self.FreezeTo(0, 0)
        # self.ClearGrid()
        self.DeleteRows(pos=0, numRows=current_row)
        self.DeleteCols(pos=0, numCols=current_col)

        self.AppendRows(numRows=row)
        self.AppendCols(numCols=col)
        self._output_table(data)

        if self.freeze_info:
            freeze_col, freeze_row = self.freeze_info
            self.FreezeTo(row=freeze_col, col=freeze_row)
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

class Controller():
    def __init__(self, conn, current_day, criteria_day, proxies):
        self.conn = conn
        self.current_day = current_day
        self.criteria_day = criteria_day
        self.proxies = proxies
        self.scrape_temp = scraping.ScrapeTemp()

        self.targets = None
        self.target_types = None
        self.temperatures = None
        self.table_data = None
    
    def get_targets(self):
        if self.targets is None:
            self.targets = db.get_targets(self.conn)
        return self.targets
    
    def get_target_types(self):
        if self.target_types is None:
            self.target_tyes = db.get_target_types(self.conn)
        return  self.target_tyes
    
    def get_temperatures(self):
        if self.temperatures is None:
            self.temperatures = db.get_temperature_info(self.conn, self.criteria_day)
        return self.temperatures
    
    def get_table_data(self):
        if self.table_data is None:
            targets = self.get_targets()
            temperatures = self.get_temperatures()
            self.table_data = calc_table_data(targets, temperatures)
        return self.table_data
    
    def has_all_day(self):
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
        days = self.get_empty_days()

        scrape_temp = self.scrape_temp
        proxies = self.proxies
        conn = self.conn

        for day in days:
            temp = scrape_temp.get_temperature(day, proxies=proxies)
            temp_model = TemperatureModel(date=day, temp=temp)
            insert_temperature(conn, temp_model)
        conn.commit()

        self.temperatures = None
        self.table_data = None
    
    def update_current_day(self, day):
        self.current_day = day
        self.temperatures = None
        self.table_data = None
    
    def get_current_day(self):
        return self.current_day
    
    def registor_target(self, data:dict):
        conn = self.conn
        target = db.TargetModel(**data)
        db.insert_target(conn, target)
        
        self.targets = None
        self.table_data = None


class TargetAddDialog(wx.Dialog):
    def __init__(self, controller):
        wx.Dialog.__init__(self, None, -1, '生物追加', size=(400, 300))

        targets = controller.get_target_types()

        self.text_name = wx.TextCtrl(self)
        self.combo_type = wx.ComboBox(self, wx.ID_ANY, '', style=wx.CB_READONLY)
        for target in targets:
            self.combo_type.Append(target.name ,target)
        self.spind_base = wx.SpinCtrlDouble(self, wx.ID_ANY, '0.0', inc=0.1, min=-30.0, max=40.0)
        self.spind_accum = wx.SpinCtrlDouble(self, wx.ID_ANY, '0.0', inc=0.1, min=0.0, max=10000.0)
        self.text_comment = wx.TextCtrl(self)

        button_ok = wx.Button(self, wx.ID_OK)
        button_ok.SetDefault()
        button_cancel = wx.Button(self, wx.ID_CANCEL)

        button_sizer = wx.StdDialogButtonSizer()
        button_sizer.AddButton(button_ok)
        button_sizer.AddButton(button_cancel)
        button_sizer.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text_name, 0, wx.EXPAND)
        sizer.Add(self.combo_type, 0, wx.EXPAND)
        sizer.Add(self.spind_base, 0, wx.EXPAND)
        sizer.Add(self.spind_accum, 0, wx.EXPAND)
        sizer.Add(self.text_comment, 0, wx.EXPAND)

        sizer.Add(button_sizer, 0, wx.EXPAND)
        self.SetSizer(sizer)

    def get_data(self):
        print(self.combo_type.GetSelection())
        if self.combo_type.GetSelection() > -1:
            _type = self.combo_type.GetClientData(self.combo_type.GetSelection())
        else:
            _type = None
        result_data = {
            'name': self.text_name.GetValue(),
            'type': _type,
            'base': self.spind_base.GetValue(),
            'accum': self.spind_accum.GetValue(),
            'comment': self.text_comment.GetValue(),
        }
        return result_data

class MainFrame(wx.Frame):
    def __init__(self, parent, id, title, size, controller, debug=False):
        wx.Frame.__init__(self, parent, id, title, size=size)

        self.controller = controller
        table_data = controller.get_table_data()
        message = self.get_message()

        # ステータスバーの作成
        self.CreateStatusBar()
        self.SetStatusText('Effective integrated temperature')
        self.GetStatusBar().SetBackgroundColour(None)

        # メニューバーの作成
        menubar = wx.MenuBar()
        menu_file = wx.Menu()
        menu_file.Append(1, 'Finish')
        menubar.Append(menu_file, 'File')

        menu_edit = wx.Menu()
        menu_add_target = menu_edit.Append(-1, '生物追加')
        self.Bind(wx.EVT_MENU, self.add_target, menu_add_target)
        menubar.Append(menu_edit, 'Edit')
        self.SetMenuBar(menubar)

        # panel_headerの作成
        panel_header = wx.Panel(self, wx.ID_ANY)

        panel_h_message = wx.Panel(panel_header, wx.ID_ANY)
        
        self.static_text_message = wx.StaticText(panel_h_message, wx.ID_ANY, message, style=wx.TE_MULTILINE)
    
        panel_h_update = wx.Panel(panel_header, wx.ID_ANY)
        self.button_temperature = wx.Button(panel_h_update, wx.ID_ANY, 'update')
        self.button_temperature.Bind(wx.EVT_BUTTON, self.click_button_temperature)

        # panel_tableの作成
        self.panel_table = wx.Panel(self, wx.ID_ANY, style=wx.SIMPLE_BORDER)

        self.table = TemperatureTableGrid(self.panel_table, table_data)
        self.table.freeze_table(row=1, col=4)

        # layout設定 ############################################
        # panel_h_messageのレイアウト設定
        # layout_h_message = wx.BoxSizer(wx.VERTICAL)
        box_h_message = wx.StaticBox(panel_h_message, wx.ID_ANY, 'message')
        layout_h_message = wx.StaticBoxSizer(box_h_message, wx.VERTICAL)
        layout_h_message.Add(self.static_text_message)
        panel_h_message.SetSizer(layout_h_message)

        # panel_h_updateのレイアウト設定
        # layout_h_update = wx.BoxSizer(wx.VERTICAL)
        box_h_update = wx.StaticBox(panel_h_update, wx.ID_ANY, 'update')
        layout_h_update = wx.StaticBoxSizer(box_h_update, wx.VERTICAL)
        layout_h_update.Add(self.button_temperature)
        panel_h_update.SetSizer(layout_h_update)

        # panel_headerのレイアウト設定
        layout_header = wx.BoxSizer(wx.HORIZONTAL)
        layout_header.Add(panel_h_message, proportion=1, flag=wx.EXPAND)
        layout_header.Add(panel_h_update)
        panel_header.SetSizer(layout_header)

        # panel_tableのレイアウト設定
        self.layout_table = wx.BoxSizer(wx.VERTICAL)
        self.layout_table.Add(self.table, proportion=1, flag=wx.EXPAND)
        self.panel_table.SetSizer(self.layout_table)

        # frameのレイアウト設定
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(panel_header, flag=wx.EXPAND)
        layout.Add(self.panel_table, proportion=1, flag=wx.EXPAND)
        self.SetSizer(layout)

        # デバッグモードの時には、Frame Panelに色をつける
        if debug:
            self.SetBackgroundColour('#000000')
            panel_header.SetBackgroundColour((255, 255, 200))
            self.panel_table.SetBackgroundColour((200, 255, 200))

            panel_h_message.SetBackgroundColour('#ABCDEF')
            panel_h_update.SetBackgroundColour('#098765')
    
    def get_message(self):
        if not self.controller.has_all_day():
            is_latest = False
            message = '昨日までのデータで取得できていない日が存在します。更新してください。'
        else:
            is_latest = True
            current_day = self.controller.get_current_day()
            message = f'{current_day.strftime("%Y年%m月%d日")}時点のデータです。情報を更新する場合はupdateボタンを押してください。'
        return message


    def click_button_temperature(self, event):
        today = datetime.date.today()
        self.controller.update_current_day(today)
        self.controller.update_temperatures()
        self.update_show_data()
    
    def add_target(self, event):
        dialog = TargetAddDialog(self.controller)
        result = dialog.ShowModal()
        while result == wx.ID_OK:
            data = dialog.get_data()
            if target_data_check(data):
                self.controller.registor_target(data)
                self.update_show_data()
                break
            wx.MessageBox('入力エラーがあります', '入力エラー')
            result = dialog.ShowModal()
        dialog.Destroy()
    
    def update_show_data(self):
        table_data = self.controller.get_table_data()
        self.table.update_table(table_data)
        message = self.get_message()
        self.static_text_message.SetLabelText(message)
        self.panel_table.SendSizeEvent()


def target_data_check(data):
    if data['name'] is None or len(data['name']) == 0:
        print('error name')
        return False
    if data['type'] is None or not isinstance(data['type'], db.TargetTypeModel):
        print('error type')
        return False
    if data['base'] is None or not isinstance(data['base'], float):
        print('error base', type(data['base']))
        return False
    if data['accum'] is None or not isinstance(data['accum'], float):
        print('error accum')
        return False
    return True

if __name__ == '__main__':
    debug = True

    proxies = {
        'http': os.environ.get('http_proxy'),
        'https': os.environ.get('https_proxy'),
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


    # アプリケーション起動
    application = wx.App()
    controller = Controller(conn, today, criteria_day, proxies)
    frame = MainFrame(None, wx.ID_ANY, 'Effective integrated temperature', size=(800, 600), controller=controller, debug=debug)
    frame.Show()
    application.MainLoop()

    conn.close()