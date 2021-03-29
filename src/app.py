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


def create_default_target(conn):
    """
    初期値として、ターゲットを追加します。
    植物を育てる時に害虫となる虫を追加しています。
    """

    # target_type取得
    target_types = db.get_target_types(conn)
    target_type_dict = {tt.name: tt for tt in target_types}
    target_list = [
        db.TargetModel(name='ブドウトラカミキリ　卵～',                    type=target_type_dict['虫'], base=9.7, accum=114.1, comment='ブドウトラカミキリ　卵～'),
        db.TargetModel(name='ブドウトラカミキリ　卵～成虫羽化',             type=target_type_dict['虫'], base=8.0, accum=408.4, comment='ブドウトラカミキリ　卵～成虫羽化'),
        db.TargetModel(name='クワコナカイガラムシ　卵～',                  type=target_type_dict['虫'], base=12.3, accum=127.0, comment='クワコナカイガラムシ　卵～'),
        db.TargetModel(name='クワコナカイガラムシ　雌幼虫～成虫羽化',       type=target_type_dict['虫'], base=10.8, accum=346.0, comment='クワコナカイガラムシ　雌幼虫～成虫羽化'),
        db.TargetModel(name='クワコナカイガラムシ　幼虫～産卵前期',         type=target_type_dict['虫'], base=9.7, accum=549.0, comment='クワコナカイガラムシ　幼虫～産卵前期'),
        db.TargetModel(name='ミカンキイロアザミウマ　卵～',                 type=target_type_dict['虫'], base=9.2, accum=50.0, comment='ミカンキイロアザミウマ　卵～'),
        db.TargetModel(name='ミカンキイロアザミウマ　幼虫～蛹',             type=target_type_dict['虫'], base=9.0, accum=90.3, comment='ミカンキイロアザミウマ　幼虫～蛹'),
        db.TargetModel(name='ミカンキイロアザミウマ　蛹～羽化',              type=target_type_dict['虫'], base=9.8, accum=66.7, comment='ミカンキイロアザミウマ　蛹～羽化'),
        db.TargetModel(name='ミカンキイロアザミウマ　幼虫～成虫羽化',        type=target_type_dict['虫'], base=9.5, accum=194.0, comment='ミカンキイロアザミウマ　幼虫～成虫羽化'),
        db.TargetModel(name='チャノキイロアザミウマ（大阪）　卵～',          type=target_type_dict['虫'], base=9.5, accum=119.0, comment='チャノキイロアザミウマ（大阪）　卵～'),
        db.TargetModel(name='チャノキイロアザミウマ（大阪）　幼虫～成虫羽化', type=target_type_dict['虫'], base=7.7, accum=181.8, comment='チャノキイロアザミウマ（大阪）　幼虫～成虫羽化'),
        db.TargetModel(name='チャノキイロアザミウマ（静岡）　卵～成虫羽化',   type=target_type_dict['虫'], base=9.7, accum=265.0, comment='チャノキイロアザミウマ（静岡）　卵～成虫羽化'),
        db.TargetModel(name='フタテンヒメヨコバイ　卵～',                   type=target_type_dict['虫'], base=10.8, accum=125.0, comment='フタテンヒメヨコバイ　卵～'),
        db.TargetModel(name='フタテンヒメヨコバイ　幼虫～成虫羽化',          type=target_type_dict['虫'], base=13.0, accum=200.0, comment='フタテンヒメヨコバイ　幼虫～成虫羽化'),
        db.TargetModel(name='フタテンヒメヨコバイ　卵～成虫羽化',            type=target_type_dict['虫'], base=11.0, accum=333.0, comment='フタテンヒメヨコバイ　卵～成虫羽化'),
        db.TargetModel(name='コウモリガ　卵～',                            type=target_type_dict['虫'], base=6.7, accum=200.0, comment='コウモリガ　卵～'),
        db.TargetModel(name='コウモリガ　卵～4齢幼虫',                      type=target_type_dict['虫'], base=7.2, accum=390.0, comment='コウモリガ　卵～4齢幼虫'),
        db.TargetModel(name='ハスモンヨトウ　卵～',                         type=target_type_dict['虫'], base=10.1, accum=63.7, comment='ハスモンヨトウ　卵～'),
        db.TargetModel(name='ハスモンヨトウ　卵～成虫羽化',                  type=target_type_dict['虫'], base=10.3, accum=526.3, comment='ハスモンヨトウ　卵～成虫羽化'),
        db.TargetModel(name='ハスモンヨトウ　卵～卵',                       type=target_type_dict['虫'], base=10.3, accum=628.7, comment='ハスモンヨトウ　卵～'),
    ]

    for target in target_list:
        db.insert_target(conn, target)


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
    
    def get_target(self, target_id):
        return db.get_target(self.conn, target_id)
    
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
    
    def update_target(self, data:dict):
        conn = self.conn
        target = db.TargetModel(**data)
        db.update_target(conn, target)

        self.targets = None
        self.table_data = None
    
    def delete_target(self, target_id):
        conn = self.conn
        db.delete_target(conn, target_id)

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

class TargetUpdateDialog(wx.Dialog):
    def __init__(self, controller, target):
        wx.Dialog.__init__(self, None, -1, '更新', size=(400, 300))
        target_types = controller.get_target_types()

        self.target_id = target.id

        self.text_name = wx.TextCtrl(self, -1, target.name)
        self.combo_type = wx.ComboBox(self, wx.ID_ANY, '', style=wx.CB_READONLY)
        for target_type in target_types:
            self.combo_type.Append(target_type.name ,target_type)
        self.combo_type.SetStringSelection(target.type.name)

        self.spind_base = wx.SpinCtrlDouble(self, wx.ID_ANY, inc=0.1, min=-30.0, max=40.0, value=str(target.base))
        self.spind_accum = wx.SpinCtrlDouble(self, wx.ID_ANY, inc=0.1, min=0.0, max=10000.0, value=str(target.accum))
        self.text_comment = wx.TextCtrl(self, -1, target.comment)

        button_ok = wx.Button(self, wx.ID_OK)
        button_ok.SetDefault()
        button_cancel = wx.Button(self, wx.ID_CANCEL)
        button_delete = wx.Button(self, wx.ID_DELETE)
        button_delete.Bind(wx.EVT_BUTTON, self.close_dialog)

        # button_sizer = wx.StdDialogButtonSizer()
        # button_sizer.AddButton(button_ok)
        # button_sizer.AddButton(button_cancel)
        # button_sizer.AddButton(button_delete)
        # button_sizer.Realize()
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(button_ok)
        button_sizer.Add(button_cancel)
        button_sizer.Add(button_delete)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text_name, 0, wx.EXPAND)
        sizer.Add(self.combo_type, 0, wx.EXPAND)
        sizer.Add(self.spind_base, 0, wx.EXPAND)
        sizer.Add(self.spind_accum, 0, wx.EXPAND)
        sizer.Add(self.text_comment, 0, wx.EXPAND)

        sizer.Add(button_sizer, 0, wx.EXPAND)
        self.SetSizer(sizer)
    
    def close_dialog(self, event):
        self.SetReturnCode(wx.ID_DELETE)
        self.EndModal(wx.ID_DELETE)
        # self.Close(True)

    def get_data(self):
        if self.combo_type.GetSelection() > -1:
            _type = self.combo_type.GetClientData(self.combo_type.GetSelection())
        else:
            _type = None
        result_data = {
            'id': self.target_id,
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
        self.table.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.update_target)

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
    
    def update_target(self, event):
        row = event.GetRow()
        if row == 0:
            return
        
        target_id = int(self.table.GetRowLabelValue(row))
        target = self.controller.get_target(target_id)
        dialog = TargetUpdateDialog(self.controller, target)
        result = dialog.ShowModal()
        while result == wx.ID_OK:
            update_data = dialog.get_data()
            if target_data_check(update_data):
                self.controller.update_target(update_data)
                self.update_show_data()
                break
            wx.MessageBox('入力エラーがあります', '入力エラー')
            result = dialog.ShowModal()
        print(result)
        if result == wx.ID_DELETE:
            delete_data = dialog.get_data()
            delete_target_id = delete_data['id']
            self.controller.delete_target(delete_target_id)
            self.update_show_data()
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

        # 初期値のデータを投入
        create_default_target(conn)

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