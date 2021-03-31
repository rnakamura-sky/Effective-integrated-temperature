# coding: utf-8
"""
    有効積算温度を確認できるツール
"""
# import sqlite3
import datetime
import os
from logging import getLogger, basicConfig, DEBUG
from collections import namedtuple
import pandas as pd
import wx
import wx.grid
import wx.lib.scrolledpanel
import db
import scraping
from controllers import Controller

log_format = '[%(asctime)s][%(levelname)s] %(message)s'
date_format = '%Y/%m/%d %H:%M:%S %p'
# basicConfig(filename='log.txt', fromat=log_format, datefmt=date_format, level=DEBUG)
basicConfig(filename='log.txt', datefmt=date_format, level=DEBUG)
logger = getLogger(__name__)

InputTarget = namedtuple('InputTarget',
    ['type', 'name', 'comment', 'datas'])
InputTargetData = namedtuple('InputTargetData',
    ['id', 'refer', 'state', 'base', 'accum', 'comment'])

def create_default_target(conn):
    """
    初期値として、ターゲットを追加します。
    植物を育てる時に害虫となる虫を追加しています。
    """

    # target_type取得
    target_types = db.get_target_types(conn)
    target_type_dict = {tt.name: tt for tt in target_types}
    # データについて
    # InputTarget(type='虫', name='ブドウトラカミキリ', comment='ブドウトラカミキリ',
    #  datas=[InputTargetData(id=1, refer=None, state='卵～幼虫', base=9.7, accum=114.1, comment=''),
    input_target_list = [
        InputTarget('虫', 'ブドウトラカミキリ','ブドウトラカミキリ',
            [InputTargetData(1, None, '卵～幼虫', 9.7, 114.1, ''),
             InputTargetData(2, None, '卵～成虫羽化', 8.0, 408.4, '')]),
        InputTarget('虫', 'クワコナカイガラムシ', 'クワコナカイガラムシ',
            [InputTargetData(1, None, '卵～幼虫', 12.3, 127.0, ''),
             InputTargetData(2, 1, '幼虫～産卵前期', 9.7, 549.0, ''),
             InputTargetData(3, 1, '雌幼虫～成虫羽化', 10.8, 346.0, '')]),
        InputTarget('虫', 'ミカンキイロアザミウマ', 'ミカンキイロアザミウマ',
            [InputTargetData(1, None, '卵～幼虫', base=9.2, accum=50.0, comment=''),
             InputTargetData(2, 1, '幼虫～蛹', 9.0, 90.3, ''),
             InputTargetData(3, 2, '蛹～羽化', 9.8, 66.7, ''),
             InputTargetData(4, 1, '幼虫～成虫羽化', 9.5, 194.0, '')]),
        InputTarget('虫', 'チャノキイロアザミウマ','チャノキイロアザミウマ',
            [InputTargetData(1, None, '（大阪）　卵～幼虫', 9.5, 119.0, ''),
             InputTargetData(2, 1, '（大阪）　幼虫～成虫羽化', 7.7, 181.8, ''),
             InputTargetData(3, None, '（静岡）　卵～成虫羽化', 9.7, 265.0, '')]),
        InputTarget('虫', 'フタテンヒメヨコバイ', 'フタテンヒメヨコバイ',
            [InputTargetData(1, None, '卵～幼虫', 10.8, 125.0, ''),
             InputTargetData(2, 1, '幼虫～成虫羽化', 13.0, 200.0, ''),
             InputTargetData(3, None, '卵～成虫羽化', 11.0, 333.0, '')]),
        InputTarget('虫', 'コウモリガ', 'コウモリガ',
            [InputTargetData(1, None, '卵～幼虫', 6.7, 200.0, ''),
             InputTargetData(2, None, '卵～4齢幼虫', 7.2, 390.0, '')]),
        InputTarget('虫', 'ハスモンヨトウ', 'ハスモンヨトウ',
            [InputTargetData(1, None, '卵～幼虫', 10.1, 63.7, ''),
             InputTargetData(2, None, '卵～成虫羽化', 10.3, 526.3, ''),
             InputTargetData(3, None, '卵～卵', 10.3, 628.7, '')]),
    ]

    for in_target in input_target_list:
        target_type = target_type_dict.get(in_target.type, None)
        if target_type is None:
            raise ValueError('指定したターゲットタイプが存在しません。')
        target = db.TargetModel(
            name=in_target.name,
            type=target_type,
            datas=[],
            comment=in_target.comment
        )

        db.insert_target(conn, target)

        target_data_dict = dict()
        for in_target_data in in_target.datas:
            refer = None
            if in_target_data.refer is not None:
                refer = target_data_dict[in_target_data.refer]
            target_data = db.TargetDataModel(
                target=target,
                refer=refer,
                state=in_target_data.state,
                base=in_target_data.base,
                accum=in_target_data.accum,
                comment=in_target_data.comment
            )
            db.insert_target_data(conn, target_data)
            target_data_dict[in_target_data.id] = target_data


class TemperatureTableGrid(wx.grid.Grid):
    """
    有効積算温度を集計するグリッドです。
    """
    def __init__(self, parent, data:pd.DataFrame):
        wx.grid.Grid.__init__(self, parent, -1)

        self.data = data

        row, col = data.shape
        self.CreateGrid(row, col)
        self.SetDefaultCellAlignment(horiz=wx.ALIGN_RIGHT, vert=wx.ALIGN_CENTRE)

        self._output_table(data)

        self.SetRowLabelAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTER)
        self.SetRowLabelSize(0)
        self.AutoSize()

        self.freeze_info = None

    def _output_table(self, data:pd.DataFrame):
        for i, column in enumerate(data.columns):
            self.SetColLabelValue(i, str(column))

        target_count = 0
        for i, row in enumerate(data.iterrows()):

            target_name = row[1][0]
            accum = row[1][3]
            temp_sum = row[1][4]
            temp_sum_before_10days = row[1][-10]
            alert_temp = 10.0

            if len(target_name) != 0:
                target_count += 1

            colour = (255, 255, 255, 255)
            target_colour = (255, 255, 255, 255)
            if target_count % 2 == 1:
                colour = (225, 255, 255)
                target_colour = (225, 255, 255)

            if i == 0:
                colour = (200, 255, 255)
            elif accum > temp_sum and accum < temp_sum + alert_temp:
                colour = (255, 255, 100)
            elif accum <= temp_sum and accum > temp_sum_before_10days:
                colour = (255, 200, 200)
            elif accum <= temp_sum:
                colour = (100, 100, 100)


            self.SetRowLabelValue(i, str(row[0]))
            is_over_accum = False
            for j, cell in enumerate(row[1]):
                self.SetCellValue(i, j, str(cell))
                self.SetReadOnly(i, j, True)

                # Alignment
                if j < 2:
                    self.SetCellAlignment(row=i, col=j, horiz=wx.ALIGN_LEFT, vert=wx.ALIGN_CENTER)

                # 色付け
                if i > 1 and j < 1:
                    self.SetCellBackgroundColour(i, j, target_colour)
                elif not is_over_accum and i > 1 and j > 4 and float(cell) >= float(accum):
                    self.SetCellBackgroundColour(i, j, wx.Colour("ORANGE"))
                    is_over_accum = True
                else:
                    self.SetCellBackgroundColour(i, j, colour)


    def freeze_table(self, row:int, col:int):
        """
        テーブルデータの固定領域の設定を行います。
        """
        self.freeze_info = (row, col)
        self.FreezeTo(row=row, col=col)

    def update_table(self, data:pd.DataFrame):
        """
        テーブルデータを更新します。
        """
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
        temp_model = db.TemperatureModel(date=day, temp=temp)
        db.insert_temperature(conn, temp_model)
        day = day + oneday

    conn.commit()


class TargetAddDialog(wx.Dialog):
    """
    ターゲットを登録するダイアログ
    """
    def __init__(self, controller):
        wx.Dialog.__init__(self, None, -1, '虫・植物情報追加', size=(400, 300))

        target_types = controller.get_target_types()
        label_name = wx.StaticText(self, wx.ID_ANY, '虫・植物名')
        self.text_name = wx.TextCtrl(self)
        label_type = wx.StaticText(self, wx.ID_ANY, 'タイプ')
        self.combo_type = wx.ComboBox(self, wx.ID_ANY, '', style=wx.CB_READONLY)
        for target_type in target_types:
            self.combo_type.Append(target_type.name ,target_type)
        label_state = wx.StaticText(self, wx.ID_ANY, '状態')
        self.text_state = wx.TextCtrl(self, wx.ID_ANY, '標準')
        label_base = wx.StaticText(self, wx.ID_ANY, 'ゼロ点')
        self.spind_base = wx.SpinCtrlDouble(self, wx.ID_ANY, '0.0', inc=0.1, min=-30.0, max=40.0)
        label_accum = wx.StaticText(self, wx.ID_ANY, '有効積算温度')
        self.spind_accum = wx.SpinCtrlDouble(self, wx.ID_ANY, '0.0', inc=0.1, min=0.0, max=10000.0)
        label_comment = wx.StaticText(self, wx.ID_ANY, 'コメント')
        self.text_comment = wx.TextCtrl(self)

        button_ok = wx.Button(self, wx.ID_OK)
        button_ok.SetDefault()
        button_cancel = wx.Button(self, wx.ID_CANCEL)

        button_sizer = wx.StdDialogButtonSizer()
        button_sizer.AddButton(button_ok)
        button_sizer.AddButton(button_cancel)
        button_sizer.Realize()

        sizer_name = wx.BoxSizer(wx.VERTICAL)
        sizer_name.Add(label_name, 0, wx.EXPAND)
        sizer_name.Add(self.text_name, 0, wx.EXPAND)

        sizer_type = wx.BoxSizer(wx.HORIZONTAL)
        sizer_type.Add(label_type, 0, wx.EXPAND)
        sizer_type.Add(self.combo_type, 0, wx.EXPAND)

        sizer = wx.BoxSizer(wx.VERTICAL)
        # sizer.Add(label_name, 0, wx.EXPAND)
        # sizer.Add(self.text_name, 0, wx.EXPAND)
        sizer.Add(sizer_name, 0, wx.EXPAND)
        # sizer.Add(label_type, 0, wx.EXPAND)
        # sizer.Add(self.combo_type, 0, wx.EXPAND)
        sizer.Add(sizer_type, 0, wx.EXPAND)
        sizer.Add(label_state, 0, wx.EXPAND)
        sizer.Add(self.text_state, 0, wx.EXPAND)
        sizer.Add(label_base, 0, wx.EXPAND)
        sizer.Add(self.spind_base, 0, wx.EXPAND)
        sizer.Add(label_accum, 0, wx.EXPAND)
        sizer.Add(self.spind_accum, 0, wx.EXPAND)
        sizer.Add(label_comment, 0, wx.EXPAND)
        sizer.Add(self.text_comment, 0, wx.EXPAND)

        sizer.Add(button_sizer, 0, wx.EXPAND)
        self.SetSizer(sizer)

    def get_data(self):
        """
        ダイアログで設定された情報を取得します。
        """
        if self.combo_type.GetSelection() > -1:
            _type = self.combo_type.GetClientData(self.combo_type.GetSelection())
        else:
            _type = None
        result_data = {
            'name': self.text_name.GetValue(),
            'type': _type,
            'state': self.text_state.GetValue(),
            'base': self.spind_base.GetValue(),
            'accum': self.spind_accum.GetValue(),
            'comment': self.text_comment.GetValue(),
        }
        return result_data


class TargetUpdateDialog(wx.Dialog):
    """
    ターゲットを更新するダイアログ
    """
    def __init__(self, controller):
        wx.Dialog.__init__(self, None, -1, '虫・植物情報更新', size=(400, 300))

        targets = controller.get_targets()
        target_types = controller.get_target_types()

        self.combo_target = wx.ComboBox(self, wx.ID_ANY, '', style=wx.CB_READONLY)
        for target in targets:
            self.combo_target.Append(target.name, target)
        self.combo_target.Bind(wx.EVT_COMBOBOX, self.change_combo_target)

        self.text_name = wx.TextCtrl(self, -1, '')
        self.text_name.Disable()

        self.combo_type = wx.ComboBox(self, wx.ID_ANY, '', style=wx.CB_READONLY)
        for target_type in target_types:
            self.combo_type.Append(target_type.name ,target_type)
        self.combo_type.Disable()

        self.text_comment = wx.TextCtrl(self, -1, '')
        self.text_comment.Disable()

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
        sizer.Add(self.combo_target, 0, wx.EXPAND)
        sizer.Add(self.text_name, 0, wx.EXPAND)
        sizer.Add(self.combo_type, 0, wx.EXPAND)
        sizer.Add(self.text_comment, 0, wx.EXPAND)

        sizer.Add(button_sizer, 0, wx.EXPAND)
        self.SetSizer(sizer)

    def change_combo_target(self, event):
        """
        ターゲットが選択された時のダイアログ表示パラメータ設定
        """
        obj = event.GetEventObject()
        selection_id = obj.GetSelection()
        if selection_id > -1:
            target = self.combo_target.GetClientData(selection_id)
            self.text_name.SetLabelText(target.name)
            self.combo_type.SetStringSelection(target.type.name)
            self.text_comment.SetLabelText(target.comment)

            self.editable(True)
        else:
            self.editable(False)


    def editable(self, flag=False):
        """
        編集設定
        """
        if flag:
            self.text_name.Enable()
            self.combo_type.Enable()
            self.text_comment.Enable()
        else:
            self.text_name.Disable()
            self.combo_type.Disable()
            self.text_comment.Disable()

    def close_dialog(self, event):
        """
        ダイアログを閉じるイベント処理
        """
        self.SetReturnCode(wx.ID_DELETE)
        self.EndModal(wx.ID_DELETE)

    def get_data(self):
        """
        ダイアログで設定された情報を取得します。
        """
        _target_id = -1
        _target_selection = self.combo_target.GetSelection()
        if _target_selection > -1:
            _target_id = self.combo_target.GetClientData(_target_selection).id

        _type = None
        _type_selection = self.combo_type.GetSelection()
        if _type_selection > -1:
            _type = self.combo_type.GetClientData(_type_selection)

        result_data = {
            'id': _target_id,
            'name': self.text_name.GetValue(),
            'type': _type,
            'comment': self.text_comment.GetValue(),
        }
        return result_data

class TargetDataAddDialog(wx.Dialog):
    """
    ターゲットデータ登録ダイアログ
    """
    def __init__(self, controller):
        wx.Dialog.__init__(self, None, -1, '基準追加', size=(400, 300))

        targets = controller.get_targets()

        self.combo_target = wx.ComboBox(self, wx.ID_ANY, '', style=wx.CB_READONLY)
        for target in targets:
            self.combo_target.Append(str(target.name), target)
        self.combo_target.Bind(wx.EVT_COMBOBOX, self.change_combo_target)

        self.text_state = wx.TextCtrl(self)
        self.combo_refer = wx.ComboBox(self, wx.ID_ANY, '', style=wx.CB_READONLY)
        self.combo_refer.Append('', None)

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
        sizer.Add(self.combo_target, 0, wx.EXPAND)
        sizer.Add(self.text_state, 0, wx.EXPAND)
        sizer.Add(self.combo_refer, 0, wx.EXPAND)
        sizer.Add(self.spind_base, 0, wx.EXPAND)
        sizer.Add(self.spind_accum, 0, wx.EXPAND)
        sizer.Add(self.text_comment, 0, wx.EXPAND)

        sizer.Add(button_sizer, 0, wx.EXPAND)
        self.SetSizer(sizer)
        self.editable(flag=False)

    def editable(self, flag=False):
        """
        編集設定
        """
        if flag:
            self.text_state.Enable()
            self.combo_refer.Enable()
            self.spind_base.Enable()
            self.spind_accum.Enable()
            self.text_comment.Enable()

        else:
            self.text_state.Disable()
            self.combo_refer.Disable()
            self.spind_base.Disable()
            self.spind_accum.Disable()
            self.text_comment.Disable()

    def change_combo_target(self, event):
        """
        ターゲットが選択された時のダイアログ表示パラメータ設定
        """
        obj = event.GetEventObject()
        selection_id = obj.GetSelection()
        if selection_id > -1:
            target = self.combo_target.GetClientData(selection_id)
            self.combo_refer.Clear()
            self.combo_refer.Append('', None)
            for target_data in target.datas:
                self.combo_refer.Append(target_data.state, target_data)
            self.combo_refer.SetStringSelection('')

            self.editable(True)
        else:
            self.editable(False)

    def get_data(self):
        """
        ダイアログで設定された情報を取得します。
        """
        selection_target = self.combo_target.GetSelection()
        if selection_target > -1:
            target = self.combo_target.GetClientData(selection_target)
        else:
            target = None
        selection_refer = self.combo_refer.GetSelection()
        if selection_refer > -1:
            refer = self.combo_refer.GetClientData(selection_refer)
        else:
            refer = None
        result_data = {
            'target': target,
            'refer': refer,
            'state': self.text_state.GetValue(),
            'base': self.spind_base.GetValue(),
            'accum': self.spind_accum.GetValue(),
            'comment': self.text_comment.GetValue(),
        }
        return result_data

class TargetDataUpdateDialog(wx.Dialog):
    """
    ターゲットデータ更新用ダイアログ
    """
    def __init__(self, controller, target_data):
        wx.Dialog.__init__(self, None, -1, '基準更新', size=(400, 300))
        target_types = controller.get_target_types()

        self.target = target_data.target
        self.target_id = self.target.id
        self.target_data_id = target_data.id

        self.text_name = wx.StaticText(self, wx.ID_ANY, str(self.target.name))
        self.combo_type = wx.ComboBox(self, wx.ID_ANY, '', style=wx.CB_READONLY)
        for target_type in target_types:
            self.combo_type.Append(target_type.name ,target_type)
        self.combo_type.SetStringSelection(self.target.type.name)
        self.combo_type.Disable()

        self.text_state = wx.TextCtrl(self, wx.ID_ANY, target_data.state)
        self.combo_refer = wx.ComboBox(self, wx.ID_ANY, '', style=wx.CB_READONLY)
        self.combo_refer.Append('', None)
        for _target_data in self.target.datas:
            if _target_data.id == target_data.id:
                continue
            self.combo_refer.Append(_target_data.state, _target_data)
        refer_default_state = '' if target_data.refer is None else target_data.refer.state
        self.combo_refer.SetStringSelection(refer_default_state)

        self.spind_base = wx.SpinCtrlDouble(self, wx.ID_ANY, inc=0.1, min=-30.0, max=40.0, \
                                                value=str(target_data.base))
        self.spind_accum = wx.SpinCtrlDouble(self, wx.ID_ANY, inc=0.1, min=0.0, max=10000.0, \
                                                value=str(target_data.accum))
        self.text_comment = wx.TextCtrl(self, -1, target_data.comment)

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
        sizer.Add(self.text_state, 0, wx.EXPAND)
        sizer.Add(self.combo_refer, 0, wx.EXPAND)
        sizer.Add(self.spind_base, 0, wx.EXPAND)
        sizer.Add(self.spind_accum, 0, wx.EXPAND)
        sizer.Add(self.text_comment, 0, wx.EXPAND)

        sizer.Add(button_sizer, 0, wx.EXPAND)
        self.SetSizer(sizer)

    def close_dialog(self, event):
        """
        ダイアログを閉じるイベント処理
        """
        self.SetReturnCode(wx.ID_DELETE)
        self.EndModal(wx.ID_DELETE)
        # self.Close(True)

    def get_data(self):
        """
        ダイアログで設定された情報を取得します。
        """
        selection_refer = self.combo_refer.GetSelection()
        if selection_refer > -1:
            _refer = self.combo_refer.GetClientData(selection_refer)
        else:
            _refer = None
        result_data = {
            'target': self.target,
            'data_id': self.target_data_id,
            'refer': _refer,
            'state': self.text_state.GetValue(),
            'base': self.spind_base.GetValue(),
            'accum': self.spind_accum.GetValue(),
            'comment': self.text_comment.GetValue(),
        }
        return result_data

class MainFrame(wx.Frame):
    """
    有効積算温度ツールのメイン画面
    """
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
        menu_file.Append(1, '修了(未実装)')
        menubar.Append(menu_file, 'ファイル')

        menu_edit = wx.Menu()
        menu_add_target = menu_edit.Append(-1, '虫・植物情報作成')
        menu_update_target = menu_edit.Append(-1, '虫・植物情報更新(数値以外)') # 後々必要なくなる可能性あり
        menu_add_target_data = menu_edit.Append(-1, '虫・植物に基準を追加')
        self.Bind(wx.EVT_MENU, self.add_target, menu_add_target)
        self.Bind(wx.EVT_MENU, self.update_target, menu_update_target)
        self.Bind(wx.EVT_MENU, self.add_target_data, menu_add_target_data)
        menubar.Append(menu_edit, '編集')
        self.SetMenuBar(menubar)

        # panel_headerの作成
        panel_header = wx.Panel(self, wx.ID_ANY)

        panel_h_message = wx.Panel(panel_header, wx.ID_ANY)

        self.static_text_message = wx.StaticText(panel_h_message, wx.ID_ANY,
                                                message, style=wx.TE_MULTILINE)

        panel_h_update = wx.Panel(panel_header, wx.ID_ANY)
        self.button_temperature = wx.Button(panel_h_update, wx.ID_ANY, 'update')
        self.button_temperature.Bind(wx.EVT_BUTTON, self.click_button_temperature)

        # panel_tableの作成
        self.panel_table = wx.Panel(self, wx.ID_ANY, style=wx.SIMPLE_BORDER)

        self.table = TemperatureTableGrid(self.panel_table, table_data)
        self.table.freeze_table(row=1, col=5)
        self.table.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.update_target_data)

        # layout設定 ############################################
        # panel_h_messageのレイアウト設定
        box_h_message = wx.StaticBox(panel_h_message, wx.ID_ANY, 'message')
        layout_h_message = wx.StaticBoxSizer(box_h_message, wx.VERTICAL)
        layout_h_message.Add(self.static_text_message)
        panel_h_message.SetSizer(layout_h_message)

        # panel_h_updateのレイアウト設定
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
        """
        表示メッセージ取得機能
        """
        if not self.controller.has_all_day():
            message = '昨日までのデータで取得できていない日が存在します。更新してください。'
        else:
            current_day = self.controller.get_current_day()
            message = f'{current_day.strftime("%Y年%m月%d日")}時点のデータです。情報を更新する場合はupdateボタンを押してください。'
        return message


    def click_button_temperature(self, event):
        """
        気温情報更新ボタン処理
        """
        today = datetime.date.today()
        self.controller.update_current_day(today)
        self.controller.update_temperatures()
        self.update_show_data()

    def add_target(self, event):
        """
        ターゲット登録処理
        """
        dialog = TargetAddDialog(self.controller)
        result = dialog.ShowModal()
        while result == wx.ID_OK:
            data = dialog.get_data()
            if target_add_check(data):
                self.controller.registor_target(data)
                self.update_show_data()
                break
            wx.MessageBox('入力エラーがあります', '入力エラー')
            result = dialog.ShowModal()
        dialog.Destroy()

    def update_target(self, event):
        """
        ターゲットを更新する機能
        """
        dialog = TargetUpdateDialog(self.controller)
        result = dialog.ShowModal()
        while result == wx.ID_OK:
            update_data = dialog.get_data()
            if target_check(update_data):
                self.controller.update_target(update_data)
                self.update_show_data()
                break
            wx.MessageBox('入力エラーがあります', '入力エラー')
            result = dialog.ShowModal()
        # print(result)
        if result == wx.ID_DELETE:
            delete_data = dialog.get_data()
            delete_target_id = delete_data['id']
            self.controller.delete_target(delete_target_id)
            self.update_show_data()
        dialog.Destroy()

    def add_target_data(self, event):
        """
        ターゲットデータ登録処理
        """
        dialog = TargetDataAddDialog(self.controller)
        result = dialog.ShowModal()
        while result == wx.ID_OK:
            data = dialog.get_data()
            if target_data_check(data):
                self.controller.registor_target_data(data)
                self.update_show_data()
                break
            wx.MessageBox('入力エラーがあります', '入力エラー')
            result = dialog.ShowModal()
        dialog.Destroy()

    def update_target_data(self, event):
        """
        ターゲットデータ更新処理
        """
        row = event.GetRow()
        if row == 0:
            return

        target_data_id = int(self.table.GetRowLabelValue(row))
        target_data = self.controller.get_target_data(target_data_id)
        dialog = TargetDataUpdateDialog(self.controller, target_data)
        result = dialog.ShowModal()
        while result == wx.ID_OK:
            update_data = dialog.get_data()
            if target_data_check(update_data):
                self.controller.update_target_data(update_data)
                self.update_show_data()
                break
            wx.MessageBox('入力エラーがあります', '入力エラー')
            result = dialog.ShowModal()
        if result == wx.ID_DELETE:
            delete_data = dialog.get_data()
            delete_target_id = delete_data['id']
            self.controller.delete_target(delete_target_id)
            self.update_show_data()
        dialog.Destroy()


    def update_show_data(self):
        """
        表示データの更新
        """
        table_data = self.controller.get_table_data()
        self.table.update_table(table_data)
        message = self.get_message()
        self.static_text_message.SetLabelText(message)
        self.panel_table.SendSizeEvent()

def target_add_check(data):
    """
    登録するターゲットの入力チェック
    """
    if data['name'] is None or len(data['name']) == 0:
        print('error name')
        return False
    if data['type'] is None or not isinstance(data['type'], db.TargetTypeModel):
        print('error type')
        return False
    if data['state'] is None or len(data['state']) == 0:
        print('error state')
        return False
    if data['base'] is None or not isinstance(data['base'], float):
        print('error base')
        return False
    if data['accum'] is None or not isinstance(data['accum'], float):
        print('error accum')
        return False
    return True

def target_check(data):
    """
    ターゲットの入力チェック
    """
    if data['name'] is None or len(data['name']) == 0:
        print('error name')
        return False
    if data['type'] is None or not isinstance(data['type'], db.TargetTypeModel):
        print('error type')
        return False
    return True

def target_data_check(data):
    """
    登録するターゲットデータの入力チェック
    """
    if data['target'] is None or not isinstance(data['target'], db.TargetModel):
        print('error target')
        return False
    if data['refer'] is not None and not isinstance(data['refer'], db.TargetDataModel):
        print('error refer')
        return False
    if data['state'] is None or len(data['state']) == 0:
        print('error state')
        return False
    if data['base'] is None or not isinstance(data['base'], float):
        print('error base')
        return False
    if data['accum'] is None or not isinstance(data['accum'], float):
        print('error accum')
        return False
    return True

def run(debug):
    """
    実行関数
    """

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
        conn = db.get_connection(db_name)

        # データベースの初期化
        db.db_init(conn, schema_filename)

        # 初期データ投入
        db.db_insert_default_values(conn)

        # 気温初期データ取得
        init_temperature(conn, proxies)

        # 初期値のデータを投入
        create_default_target(conn)

    else:
        # データベースと接続
        conn = db.get_connection(db_name)


    # アプリケーション起動
    application_name = '有効積算温度チェックツール'
    application = wx.App()
    controller = Controller(conn, today, criteria_day, proxies)
    frame = MainFrame(None, wx.ID_ANY, application_name, size=(800, 600), \
                    controller=controller, debug=debug)
    frame.Show()
    application.MainLoop()

    conn.close()


if __name__ == '__main__':
    run(debug=True)
