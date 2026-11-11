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
python -m unittest discover -s tests -p "test_generation_logger.py" -v
python -m unittest discover -s tests -p "test_index_service.py" -v
python -m unittest discover -s tests -p "test_html.py" -v
python -m unittest discover -s tests -p "test_session.py" -v
```

## 各テストの概要

### `tests/test_config.py`

設定ファイルの読み込み、モデル選択、旧設定からの移行を検証します。

- バージョン3.0の設定を読み込み、Foundryのデプロイ名、画像サイズ、品質を正しく取得できること
- OpenAIを選択した場合に、選択中のFlareまたはSunburstに対応するモデル名を取得できること
- バージョン2.0のAzureおよびGPT Image 1設定を、バージョン3.0のFoundryおよびGPT Image 2.5設定へ移行できること
- 移行後の設定から古い`azure`および`gptimage1`項目が削除されること
- 古いウェルカムメッセージが現在の既定値へ更新されること

テスト用の設定ファイルは一時ディレクトリへ作成され、通常の`config.json`は変更しません。

### `tests/test_dalle.py`

GPT ImageクライアントとAPIへ渡すパラメーターを検証します。

- `flare`と`sunburst`から、それぞれ正しいOpenAIモデル名を取得できること
- Azure OpenAIおよびMicrosoft Foundryのエンドポイントを`/openai/v1/`形式へ正規化できること
- 指定したデプロイ名、プロンプト、画像サイズ、品質、PNG形式が画像生成APIへ正しく渡されること
- 最大2枚の入力画像が順序を保って画像編集APIへ渡され、API呼び出し中にファイルが開かれること
- 編集範囲のマスクが画像編集APIへ渡され、API呼び出し中にファイルが開かれること
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
- 解像度と品質のクイック設定を保存し、不正な設定値を拒否すること
- クリップボードまたはドラッグ＆ドロップから入力画像を登録・解除できること
- 画像以外のデータと20MB以上の入力画像を拒否すること
- 長辺が2048pxを超える画像を縦横比を維持して縮小すること
- PNG画像を縮小しても透明度が維持されること
- 登録した最大2枚の入力画像を順序を保って画像生成処理へ渡すこと
- 編集範囲マスクの形式と画像サイズを検証し、画像生成処理へ渡すこと
- 入力画像、サムネイル、編集範囲マスクを`logs/input-images`へ保存すること
- 再作成時に元の編集範囲マスクを復元すること
- エントリー削除時に生成画像と入力画像を削除すること
- エントリー削除後も発生済みのトークン使用量と概算料金を保持すること
- セッション内の全画像またはお気に入り画像だけを一括保存できること
- 一括保存先の同名ファイルを上書きせず、欠損画像をスキップすること

画像生成クライアントはモックへ置き換え、APIキーとエンドポイントにはテスト専用の値を使用します。そのため、外部APIへの接続は行いません。

### `tests/test_html.py`

設定画面のHTMLとJavaScriptの対応関係を検証します。

- `src/html/config.html`内の要素IDを収集すること
- JavaScriptの`getElementById()`が参照するIDが、すべてHTML内に存在すること
- 解像度・品質のクイック設定と入力画像プレビューの要素が存在すること
- 品質の選択肢が英語表記であること
- 現在使用中のAPI種別を表示する処理が存在すること
- クリップボード貼り付けとドラッグ＆ドロップの処理が存在すること
- 入力画像の20MB制限と縮小通知の処理が存在すること
- セッション画像の一括保存UIとAPI呼び出しが存在すること
- ブラシサイズ、右ドラッグでの消去、ズーム、移動、一括クリアを備えた編集範囲指定UIが存在すること

設定画面の要素を削除または改名した際に、JavaScript側の参照だけが古いまま残る問題を検出できます。

### `tests/test_session.py`

セッションエントリーの入力画像メタデータに関する互換性と保存形式を検証します。

- 入力画像情報を持たない古いセッションデータを読み込めること
- 入力画像のファイル名、解像度、容量、縮小有無を保存・復元できること
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
