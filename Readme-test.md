# テストガイド

このプロジェクトのテストは、Python標準ライブラリの`unittest`を使用しています。`pytest`やビルド用ライブラリは必要ありません。

## 実行環境の準備

PowerShellでリポジトリのルートディレクトリを開き、仮想環境を作成して依存ライブラリをインストールします。

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

現在使用しているPythonのバージョンは3.14.10です。正確なバージョンは`.python-version`に記載されています。

`requirements-build.txt`はアプリケーションのビルド用であり、テストの実行には不要です。

## すべてのテストを実行する

リポジトリのルートディレクトリで、次のコマンドを実行します。

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

仮想環境を有効化せずに実行する場合は、仮想環境内のPythonを直接指定できます。

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

すべて成功すると、最後に`OK`と表示されます。

## 特定のテストファイルを実行する

`-p`にファイル名を指定します。例えば、画像生成クライアントのテストだけを実行する場合は次のとおりです。

```powershell
python -m unittest discover -s tests -p "test_dalle.py" -v
```

ほかのテストも同じ方法で実行できます。

```powershell
python -m unittest discover -s tests -p "test_config.py" -v
python -m unittest discover -s tests -p "test_config_service.py" -v
python -m unittest discover -s tests -p "test_dalle.py" -v
python -m unittest discover -s tests -p "test_generation_logger.py" -v
python -m unittest discover -s tests -p "test_html.py" -v
python -m unittest discover -s tests -p "test_image_clipboard.py" -v
python -m unittest discover -s tests -p "test_image_options.py" -v
python -m unittest discover -s tests -p "test_index_service.py" -v
python -m unittest discover -s tests -p "test_pricing.py" -v
python -m unittest discover -s tests -p "test_session.py" -v
```

## 各テストの概要

| テストファイル | テスト数 | 主な対象 |
| --- | ---: | --- |
| `tests/test_config.py` | 6 | 設定の読み込み、移行、画像サイズプリセット |
| `tests/test_config_service.py` | 4 | 設定保存、Foundry入力検証、プロンプトの一時保存 |
| `tests/test_dalle.py` | 7 | GPT ImageクライアントとAPIパラメーター |
| `tests/test_generation_logger.py` | 2 | 画像生成ログ |
| `tests/test_html.py` | 22 | HTML要素とJavaScriptのUI連携 |
| `tests/test_image_clipboard.py` | 1 | Windowsクリップボード用画像変換 |
| `tests/test_image_options.py` | 3 | 画像サイズの正規化と検証 |
| `tests/test_index_service.py` | 40 | 画像生成・編集、入力画像、セッション操作 |
| `tests/test_pricing.py` | 3 | API料金の概算 |
| `tests/test_session.py` | 9 | セッション保存形式と旧形式互換性 |
| **合計** | **97** | |

### `tests/test_config.py`

設定ファイルの読み込み、モデル選択、画像サイズプリセット、旧設定からの移行を検証します。

- バージョン4.0の設定を読み込み、Foundryのデプロイ名、画像サイズ、品質、計画量を正しく取得できること
- OpenAIを選択した場合に、選択中のGPT Image 2.5 / 2.6モデル名を取得できること
- バージョン3.0のモデルとFoundryデプロイ設定を、GPT Image 2.5を維持したままバージョン4.0へ移行できること
- バージョン2.0のAzureおよびGPT Image 1設定を、バージョン4.0のFoundryおよびGPT Image設定へ移行できること
- 移行後の設定から古い`azure`および`gptimage1`項目が削除されること
- 古いウェルカムメッセージが現在の既定値へ更新されること
- 新規設定でGPT Image 2.6 Flareが既定モデルになること
- 画像サイズプリセットを読み込み、無効値の除外、重複除去、選択中サイズの追加ができること

テスト用の設定ファイルは一時ディレクトリへ作成され、通常の`config.json`は変更しません。

### `tests/test_config_service.py`

設定画面から送信されたモデル、計画量、Foundryデプロイ名の保存と入力検証、入力途中のプロンプトの一時保存を確認します。

- 選択中モデルに対応するFoundryデプロイ名を保存できること
- 選択中のFoundryデプロイ名が空の場合に設定を拒否すること
- 入力エラー時に現在の設定を途中まで変更しないこと
- 設定画面を開く際にプロンプトを一時保存し、1回だけ復元できること
- 空のプロンプトも一時保存できること

### `tests/test_dalle.py`

GPT ImageクライアントとAPIへ渡すパラメーターを検証します。

- `flare`と`sunburst`から、それぞれ正しいOpenAIモデル名を取得できること
- Azure OpenAIおよびMicrosoft Foundryのエンドポイントを`/openai/v1/`形式へ正規化できること
- 指定したデプロイ名、プロンプト、画像サイズ、品質、計画量、PNG形式が画像生成APIへ正しく渡されること
- 最大2枚の入力画像が順序を保って画像編集APIへ渡され、API呼び出し中にファイルが開かれること
- 編集範囲のマスクが画像編集APIへ渡され、API呼び出し中にファイルが開かれること
- GPT Image 2.6の画像編集APIへ計画量が渡されること
- APIレスポンスからBase64画像と改訂版プロンプトを取得できること

OpenAIクライアントはモックへ置き換えているため、実際のAPI通信や課金は発生しません。

### `tests/test_generation_logger.py`

画像生成ログへ通常生成と参照画像付き生成の情報が正しく記録されることを検証します。

- 入力画像がない場合に通常生成として記録されること
- 入力画像がある場合に参照画像付き生成として記録されること
- 各入力画像のファイル名、変換前後の解像度と容量、縮小有無が記録されること

### `tests/test_index_service.py`

画面側のサービスが画像生成クライアントを構築し、クイック設定と入力画像を正しく処理することを検証します。

- 選択中のモデルに対応するFoundryデプロイ名を使用すること
- 設定された名前の環境変数からAPIキーとエンドポイントを取得すること
- APIキー、正規化済みエンドポイント、デプロイ名を`GPTImageClient`へ渡すこと
- 解像度と品質のクイック設定を保存し、設定画面の計画量を生成時に使用すること
- クリップボードまたはドラッグ＆ドロップから入力画像を登録・解除できること
- 画像以外のデータと20MB以上の入力画像を拒否すること
- 長辺が2048pxを超える画像を縦横比を維持して縮小すること
- PNG画像を縮小しても透明度が維持されること
- 登録した最大2枚の入力画像を順序を保って画像生成処理へ渡すこと
- 編集範囲マスクの形式と画像サイズを検証し、画像生成処理へ渡すこと
- 生成画像を編集用の入力画像として準備できること
- 生成画像をWindowsクリップボードへコピーできること
- 入力画像、サムネイル、編集範囲マスクを`logs/input-images`へ保存すること
- 再作成時に元のプロンプト、入力画像、編集範囲マスクを復元すること
- エントリー削除時に生成画像と入力画像を削除すること
- エントリー削除後も発生済みのトークン使用量と概算料金を保持すること
- お気に入りの更新、保存失敗時のロールバック、存在しないエントリーの拒否ができること
- 画像名の設定、削除、重複回避、不正値の拒否、保存ダイアログへの反映ができること
- セッション内の全画像またはお気に入り画像だけを一括保存できること
- 一括保存先の同名ファイルを上書きせず、キャンセルと不正な保存対象を適切に処理すること

画像生成クライアントはモックへ置き換え、APIキーとエンドポイントにはテスト専用の値を使用します。そのため、外部APIへの接続は行いません。

### `tests/test_html.py`

設定画面のHTMLとJavaScriptの対応関係を検証します。

- `src/html/config.html`内の要素IDを収集すること
- JavaScriptの`getElementById()`が参照するIDが、すべてHTML内に存在すること
- 解像度・品質のクイック設定と入力画像プレビューの要素が存在すること
- 品質の選択肢が英語表記であること
- 現在使用中のAPI種別を表示する処理が存在すること
- 設定画面を開く際にプロンプトを保存し、戻った際に復元する処理が存在すること
- クリップボード貼り付けとドラッグ＆ドロップの処理が存在すること
- 入力画像の20MB制限と縮小通知の処理が存在すること
- 画像のコピー、ズーム、再作成、お気に入り、画像名設定のUIとAPI呼び出しが存在すること
- 生成画像を参照画像として編集を開始できること
- セッション画像の一括保存UIとAPI呼び出しが存在すること
- ブラシサイズ、右ドラッグでの消去、ズーム、移動、一括クリアを備えた編集範囲指定UIが存在すること
- トークン使用量、生成ごとの概算料金、セッション全体の概算料金を表示すること
- コンテキストメニューの順序と区切り、モーダルとお気に入りボタンの重なり順が正しいこと

設定画面の要素を削除または改名した際に、JavaScript側の参照だけが古いまま残る問題を検出できます。

### `tests/test_image_clipboard.py`

Windowsクリップボードへ生成画像をコピーする際の画像形式変換を検証します。

- BMP画像からファイルヘッダーを除去し、クリップボード用DIBを作成できること

### `tests/test_image_options.py`

GPT Image APIで使用する画像サイズの正規化と検証を確認します。

- 対応する正方形・横長・縦長サイズを正規化できること
- APIの許容範囲外のサイズや不正な形式を拒否すること
- 画像サイズプリセットを正規化し、重複と無効値を除外できること

### `tests/test_pricing.py`

画像生成APIのトークン使用量から概算料金を計算する処理を検証します。

- 入力トークンと出力トークンの個別料率から概算料金を計算できること
- Foundryの任意のデプロイ名にプロバイダーのワイルドカード料率を適用できること
- 料金設定のないモデルでは概算不可として扱うこと

### `tests/test_session.py`

セッションエントリーの保存形式、利用履歴、旧形式との互換性を検証します。

- 入力画像情報を持たない古いセッションデータを読み込めること
- 入力画像のファイル名、解像度、容量、縮小有無を保存・復元できること
- 計画量、お気に入り、画像名、トークン使用量、概算料金を保存・復元できること
- 画像名から保存用ファイル名を生成し、画像名がない場合は内部ファイル名を使用すること
- 画像削除後も利用履歴を保存・復元し、旧形式のセッションから利用履歴を補完できること

## APIキーについて

現在のテストはAPIクライアントや環境変数をモックしているため、OpenAIまたはMicrosoft FoundryのAPIキーを設定する必要はありません。テストを実行しても画像生成APIの利用料金は発生しません。

## トラブルシューティング

### モジュールが見つからない場合

仮想環境が有効になっていることを確認し、依存ライブラリを再度インストールします。

```powershell
python -m pip install -r requirements.txt
```

### PowerShellで仮想環境を有効化できない場合

仮想環境を有効化せず、Pythonを直接指定してテストを実行します。

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

### テストファイルが見つからない場合

コマンドをリポジトリのルートディレクトリで実行していることを確認してください。
