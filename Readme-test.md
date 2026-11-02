# テストガイド

このプロジェクトのテストは、Python標準ライブラリの`unittest`を使用しています。`pytest`やビルド用ライブラリは必要ありません。

## 実行環境の準備

PowerShellでリポジトリのルートディレクトリを開き、仮想環境を作成して依存ライブラリをインストールします。

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

使用するPythonのバージョンは`.python-version`に記載されています。

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
python -m unittest discover -s tests -p "test_index_service.py" -v
python -m unittest discover -s tests -p "test_html.py" -v
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
- APIレスポンスからBase64画像と修正済みプロンプトを取得できること

OpenAIクライアントはモックへ置き換えているため、実際のAPI通信や課金は発生しません。

### `tests/test_index_service.py`

画面側のサービスが設定内容と環境変数から画像生成クライアントを正しく構築することを検証します。

- 選択中のモデルに対応するFoundryデプロイ名を使用すること
- 設定された名前の環境変数からAPIキーとエンドポイントを取得すること
- APIキー、正規化済みエンドポイント、デプロイ名を`GPTImageClient`へ渡すこと

画像生成クライアントはモックへ置き換え、APIキーとエンドポイントにはテスト専用の値を使用します。そのため、外部APIへの接続は行いません。

### `tests/test_html.py`

設定画面のHTMLとJavaScriptの対応関係を検証します。

- `src/html/config.html`内の要素IDを収集すること
- JavaScriptの`getElementById()`が参照するIDが、すべてHTML内に存在すること

設定画面の要素を削除または改名した際に、JavaScript側の参照だけが古いまま残る問題を検出できます。

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
