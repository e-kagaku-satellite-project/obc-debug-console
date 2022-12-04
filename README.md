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
