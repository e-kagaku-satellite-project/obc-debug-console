# OBC debug console

## 主要機能
- デバッグレベルによる出力文字色の変更
- 表示デバッグレベルの設定
- ログの保存
- プログラム起動時に接続されているCOMポート一覧の表示と選択
- ボーレートの選択
- オートスクロールの有効・無効
- CPUごとのテーマ変更

## 動作環境
必ずしも同じである必要はないと思います．
- Python3.9.12
- pyserial==3.5
- pysimplegui==4.60.4

## サンプル
- プログラム例  
![プログラム例](https://github.com/e-kagaku-satellite-project/obc-debug-console/blob/main/sample/program.png)
- コンソール出力  
![コンソール出力](https://github.com/e-kagaku-satellite-project/obc-debug-console/blob/main/sample/console.png)
- [ログ](https://github.com/e-kagaku-satellite-project/obc-debug-console/blob/main/sample/log_sample.csv)

## PIC側での書き方
通常出力の前に出力レベル指示詞（`FATAL,`，`ERROR,`，`WARN,`，`INFO,`，`DEBUG,`）を，一番最後に改行文字を加えないとコンソールには出力されないようになっています．  
`PRINT_INFO`，`PRINT_DEBUG`等の出力関数を使えば自動的に追加されるようになっています．  
(それらの関数の定義はMain CPUのdebug.hを確認してください．)  
またコンソール側では改行文字を文の区切りとしているため，途中に改行文字を入れるとそれ以降が表示されなくなります．  

コンソール側ではカンマはすべてタブに置換されて出力されるようにしています．  
これはコンソール表示前の文字はCSV形式で閲覧しやすいようにする，コンソールでは余白を設けて見やすいようにするためです．


## テーマ
CPUのテーマは各サブシステムで統一してもらえれば，自由に設定して構いません．  
テーマの一覧は下記URLを参照のこと．  
[Themes in PySimpleGUI](https://www.geeksforgeeks.org/themes-in-pysimplegui/)
## 追加予定の機能
- ログの保存先の指定(ファイル検索できるようにする)
- ログの保存形式の指定（Raw, CSV etc...)
- コンソール内の文字を選択した際にハイライトする
- コンソール内検索
- 保存フォルダがシリアルオープン時に見えにくい現象の修正
- 環境によってタブ幅が変わる現象の修正
