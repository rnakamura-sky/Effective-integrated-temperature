# coding: utf-8
"""
設定ファイルを制御するためのモジュール
"""
import os
import configparser


class Config:
    """
    設定ファイルを制御するためのクラス
    """

    section_eit = 'eit'
    section_scraping = 'scraping'

    default_sections = [
        'eit',
        'scraping',
    ]

    default_values = {
        'DEBUG': ('eit', 'DEBUG', 'FALSE'),
        'prefecture': ('scraping', 'prefecture', '49'),
        'block': ('scraping', 'block', '47638'),
    }

    def __init__(self, config_file:str='config.ini'):
        self.config_file = config_file

        self.config = None

    def initComponent(self):
        """
        設定ファイルの初期値を設定します。
        """
        self.config = configparser.RawConfigParser()
        self.config.add_section(self.section_eit)
        self.config.set(self.section_eit, 'DEBUG', 'True')

        self.config.add_section(self.section_scraping)
        self.config.set(self.section_scraping, 'prefecture', '49')
        self.config.set(self.section_scraping, 'block', '47638')

    def collect(self):
        """
        設定ファイルで設定されていない項目について補正します。
        """
        config = self.config

        for section in self.default_sections:
            if not config.has_section(section):
                config.add_section(section)

        for k, v in self.default_values.items():
            if not config.has_option(v[0], v[1]):
                config.set(v[0], v[1], v[2])



    def load(self):
        """
        ファイルを読んで設定を読み込みます。
        なければ初期設定を作成して作成します。
        """
        if os.path.exists(self.config_file):
            self.config = configparser.ConfigParser()
            self.config.read(self.config_file)
            self.collect()
        else:
            self.initComponent()
            self.save()

    def save(self):
        """
        設定を保存します。
        """
        with open(self.config_file, 'w') as file:
            self.config.write(file)

    def get_location(self):
        """
        温度を取得する地域設定を取得する
        """
        result = {
            'prefecture': self.config.get(self.section_scraping, 'prefecture'),
            'block': self.config.get(self.section_scraping, 'block'),
        }
        return result

    def set_location(self, prefecture, block):
        """
        温度を取得する地域設定を設定する
        """
        self.config.set(self.section_scraping, 'prefecture', prefecture)
        self.config.set(self.section_scraping, 'block', block)

    def debug(self):
        """
        デバッグ設定かどうかを確認
        """
        return self.config.get('eit', 'DEBUG')