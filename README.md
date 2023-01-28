# OBC debug console

## 主要機能

- デバッグレベルによる出力文字色の変更
- 表示デバッグレベルの設定
- ログの保存
- プログラム起動時に接続されている COM ポート一覧の表示と選択
- ボーレートの選択
- オートスクロールの有効・無効
- CPU ごとのテーマ変更

## 動作環境

必ずしも同じである必要はないと思います．

- Python3.9.12
- pyserial==3.5
- pysimplegui==4.60.4

## 使い方

### 基本

1. obc-debug-console.exe を起動する
2. CPU を選択する
3. COM ポート，ボーレートを選択する
4. ログの保存先を指定する
5. Open ボタンを押しシリアルポートを開くとログが表示され，保存される
6. Close ボタンを押しシリアルポートを閉じるとログの保存が終了する

※シリアルポートを開いている間は CPU，COM ポート，ボーレート，ログの保存先の変更はできない．

### 出力レベル

| レベル |      色      |      説明      |
| :----: | :----------: | :------------: |
|  NONE  |              | 何も表示しない |
| FATAL  | 赤（背景白） | 致命的なエラー |
| ERROR  |      赤      |     エラー     |
|  WARN  |     黄色     |      警告      |
|  INFO  |      緑      |      情報      |
| DEBUG  |      白      |    デバッグ    |

### ショートカットキー

|     キー     |                   機能                   |
| :----------: | :--------------------------------------: |
|  Shift + O   |           シリアルポートを開く           |
|  Shift + C   |          シリアルポートを閉じる          |
|  Shift + R   |     シリアルポート一覧の再度読み込み     |
|  Shift + E   |                  閉じる                  |
|  Shift + A   | オートスクロールの有効・無効を切り替える |
|  Shift + Up  |            表示レベルを上げる            |
| Shift + Down |            表示レベルを下げる            |
| Control + m  |          Main CPU に切り替える           |
| Control + t  |        Transmit CPU に切り替える         |
| Control + r  |         Receive CPU に切り替える         |

##

## サンプル

- プログラム例  
  ![プログラム例](https://github.com/e-kagaku-satellite-project/obc-debug-console/blob/main/sample/program.png)
- コンソール出力  
  ![コンソール出力](https://github.com/e-kagaku-satellite-project/obc-debug-console/blob/main/sample/console.png)
- [ログ](https://github.com/e-kagaku-satellite-project/obc-debug-console/blob/main/sample/log_sample.csv)

## PIC 側での書き方

通常出力の前に出力レベル指示詞（`FATAL,`，`ERROR,`，`WARN,`，`INFO,`，`DEBUG,`）を，一番最後に改行文字を加えないとコンソールには出力されないようになっています．  
`PRINT_INFO`，`PRINT_DEBUG`等の出力関数を使えば自動的に追加されるようになっています．  
(それらの関数の定義は Main CPU の debug.h を確認してください．)  
またコンソール側では改行文字を文の区切りとしているため，途中に改行文字を入れるとそれ以降が表示されなくなります．

コンソール側ではカンマはすべてタブに置換されて出力されるようにしています．  
これはコンソール表示前の文字は CSV 形式で閲覧しやすいようにする，コンソールでは余白を設けて見やすいようにするためです．

## テーマ

CPU のテーマは各サブシステムで統一してもらえれば，自由に設定して構いません．  
テーマの一覧は下記 URL を参照のこと．  
[Themes in PySimpleGUI](https://www.geeksforgeeks.org/themes-in-pysimplegui/)

## 追加予定の機能

- ログの保存先の指定(ファイル検索できるようにする)
- ログの保存形式の指定（Raw, CSV etc...)
- コンソール内の文字を選択した際にハイライトする
- コンソール内検索
- 保存フォルダがシリアルオープン時に見えにくい現象の修正
- 環境によってタブ幅が変わる現象の修正
