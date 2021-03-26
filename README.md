## About
有効積算温度をチェックするためのツールを作成します。
使用する環境はWindows OSを想定し、exeとして提供できるようにします。

## 開発環境を整える
~~~
pip install -r requirements.txt
~~~

## リリース用にexeファイルにまとめる
~~~
pyinstaller src\app.py --onefile --noconsole
~~~
成功すると下記のようなログが出力されます。
~~~
149460 INFO: Building EXE from EXE-00.toc completed successfully
~~~
./dist/app.exeがWindowsで実行できるファイルになります。

初回に実行する場合はexeと同じフォルダ内にschema.sqlが必要となります。
