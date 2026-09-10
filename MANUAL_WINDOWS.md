# Chemical Scanner 利用マニュアル（Windows版）

試薬瓶のラベルをWebcamで撮影し、OCRでCAS番号・化合物名を自動抽出、PubChemで化合物情報を取得、労働安全衛生法のリスク対象化合物かどうかを自動判定するWebアプリケーションです。

このマニュアルは **Windows PC + 外付けUSB Webcam** での利用を前提としたセットアップ手順と使い方をまとめたものです（Mac版の手順は `MANUAL.md` を参照してください）。

---

## 1. 動作環境

- **Windows 10 / 11**
- **USB Webcam**（内蔵カメラがあればそれでも代用可能ですが、試薬瓶を撮影しやすい外付けWebcam推奨）
- **インターネット接続**（初回のOCRモデルダウンロード、PubChem検索に必要）
- 管理者権限（インストール作業のため。通常利用時は不要）

---

## 2. セットアップ手順

### 2-1. Git for Windows のインストール

リポジトリ（アプリのソースコード）を取得するために必要です。すでにインストール済みの場合はスキップしてください。

1. https://git-scm.com/download/win からインストーラーをダウンロード
2. インストーラーを実行し、基本的にすべて「Next（デフォルト設定のまま）」で進めてOKです

インストール後、確認のため「スタートメニュー」から **Git Bash** を開き、以下を実行します。

```bash
git --version
```

バージョンが表示されれば成功です。

### 2-2. Miniconda（Python環境管理ツール）のインストール

1. https://docs.conda.io/en/latest/miniconda.html を開く
2. 「Miniconda3 Windows 64-bit」をダウンロードしてインストーラーを実行
3. インストール中の設定はデフォルトのままでOKです（「Add Miniconda3 to my PATH environment variable」はチェックしなくても構いません。次の手順で使う「Anaconda Prompt」はPATH設定に依存しません）

インストールが終わると、スタートメニューに **「Anaconda Prompt (miniconda3)」** が追加されます。以降の操作はこのAnaconda Promptで行います（PowerShellやコマンドプロンプトではなく、こちらを使うのが最も簡単です）。

### 2-3. リポジトリの取得

**スタートメニューから「Anaconda Prompt (miniconda3)」を開いて**、以下を実行します。

```bat
cd Desktop
git clone https://github.com/sakamoto93/chemical-scanner.git
cd chemical-scanner
```

（`cd Desktop` の部分は、アプリを置きたい場所に読み替えてください）

### 2-4. Python仮想環境の作成

```bat
conda create -n chemical-scanner python=3.9
conda activate chemical-scanner
```

「Proceed ([y]/n)?」と聞かれたら `y` を入力してEnterを押してください。

以降、このアプリを使うたびに、Anaconda Promptを開いて `conda activate chemical-scanner` を実行する必要があります。

### 2-5. 依存パッケージのインストール

```bat
pip install -r requirements.txt
```

数分かかります。

> **エラーが出た場合（PaddleOCR関連）**
> `Microsoft Visual C++ 14.0 or greater is required` のようなエラーが出た場合は、以下から「Microsoft Visual C++ Redistributable」をインストールしてから、もう一度 `pip install -r requirements.txt` を実行してください。
> https://learn.microsoft.com/ja-jp/cpp/windows/latest-supported-vc-redist

### 2-6. Webcamの接続とカメラの確認

USB WebcamをPCに接続してください（ドライバのインストールは通常不要です）。

内蔵カメラと外付けWebcamの両方が認識される場合、アプリがどちらを使うかを確認する必要があります。

```bat
python scripts\find_camera.py
```

実行すると `scripts\camera_test_output\` フォルダに `camera_0.jpg`、`camera_1.jpg` などの画像が保存されます。エクスプローラーでこのフォルダを開き、**どの画像がWebcamで撮影したものか**を確認してください。

- Webcamが `camera_0.jpg` だった場合 → 追加設定は不要です
- Webcamが `camera_1.jpg` など、0以外だった場合 → サーバー起動時に `CAMERA_INDEX` を指定します（後述）

初回実行時、Windowsから「カメラへのアクセスを許可しますか」という許可ダイアログが表示される場合があります。**許可してください**。

ダイアログが出ずに映像が取得できない場合は、以下を確認してください。

```
Windowsの設定 → プライバシーとセキュリティ → カメラ
→「カメラへのアクセス」がオンになっているか
→「アプリがカメラにアクセスできるようにする」がオンになっているか
→「デスクトップアプリがカメラにアクセスできるようにする」がオンになっているか
```

### 2-7. サーバーの起動

Webcamが index 0 の場合：

```bat
python app.py
```

Webcamが index 0 以外（例: 1）の場合：

```bat
set CAMERA_INDEX=1
python app.py
```

（Anaconda Promptはコマンドプロンプト方式なので `set 変数名=値` の後に改行してから実行してください。PowerShellを使っている場合は `$env:CAMERA_INDEX="1"` という書き方になります。）

初回起動時は、以下の理由で数分かかることがあります。

1. **PaddleOCRのモデルダウンロード**（初回のみ、3〜5分程度）
2. リスク対象化合物データベースの読み込み（数秒）

以下のようなログが表示されればサーバー起動成功です。

```
✅ Risk assessment system ready: 2597 compounds loaded
📷 Using camera index: 0 (環境変数 CAMERA_INDEX で変更可能)
🚀 Starting with HTTP (port 8000)
   Access from MacBook: http://localhost:8000
INFO:     Uvicorn running on http://0.0.0.0:8000
```

> **Windowsファイアウォールの確認画面が出た場合**
> 「Pythonのネットワークアクセスを許可しますか」という趣旨のダイアログが出ることがあります。**「アクセスを許可する」**を選んでください（同一PC内のブラウザからアクセスするだけなので、プライベートネットワークの許可で十分です）。

### 2-8. ブラウザでアクセス

ブラウザ（Edge / Chrome）で以下のURLを開いてください。

```
http://localhost:8000
```

Webcamのライブ映像が表示されれば、セットアップは完了です。

---

## 3. 使い方

### 3-1. 試薬の自動スキャン

1. 試薬瓶のラベルがWebcamにはっきり映るように配置します
2. 「自動スキャン: 開始」ボタンをクリックします
3. 数秒のカウントダウンの後、自動でスキャンが始まります（位置調整の時間として使ってください）
4. OCRでテキストが検出されると、画面下部に結果が表示されます
   - CAS番号（記載があれば）
   - 化合物名・通称名
   - 分子式・分子量
   - **リスク対象化合物の場合は赤い警告バナー**が表示されます（労働安全衛生法のラベル表示・SDS交付義務対象）
5. 内容を確認し、「リストに追加」をクリックすると下部の一覧に追加されます
6. 「自動スキャン: 停止」で読み取りを止められます

**スキャン設定**（画面上部）で以下を調整できます。

- **スタートアップ遅延**：ボタンを押してから実際にスキャンが始まるまでの秒数（試薬瓶を配置する時間）
- **スキャン間隔**：何秒おきに読み取りを行うか（サーバーの処理速度に応じて調整してください。目安は5〜8秒）

### 3-2. 試薬名を手入力して検索

OCRでラベルは読めているのにCAS番号が記載されていない試薬や、PubChem検索がヒットしない試薬については、手入力検索が使えます。

1. 「試薬名を手入力して検索」欄に試薬名を入力
2. 「検索」ボタン（またはEnterキー）をクリック

> **重要**：PubChemは英語名での検索に強いです。「チモール」ではヒットしないことが多いので、**英語名（例: Thymol）で入力**してください。

3. 検索結果（化合物情報・リスク対象かどうか）が表示されます
4. 「リストに追加」で一覧に追加します

### 3-3. 検出済み試薬一覧

読み取った・検索した試薬は下部の一覧テーブルに表示されます。

- **リスク列**：「⚠️ 対象」と表示されている試薬は、労働安全衛生法のラベル表示・SDS交付義務対象です
- **削除**：各行の削除ボタンでリストから除外できます（誤って追加した場合など）

### 3-4. リストのエクスポート

一覧に試薬が1件以上ある場合、下部に以下のボタンが表示されます。

- **Excelダウンロード**：`.xlsx` 形式でダウンロード
- **CSVダウンロード**：`.csv` 形式でダウンロード（日本語も文字化けしません）

ファイル名には日時が自動で付与されます（例: `chemical_list_20260901_103000.xlsx`）。ダウンロード先はブラウザの既定のダウンロードフォルダ（通常 `ダウンロード` フォルダ）です。

---

## 4. よくあるトラブルと対処法（Windows特有）

| 症状 | 原因・対処法 |
|------|------|
| `pip install` 中に `Microsoft Visual C++ 14.0 is required` エラー | 「Microsoft Visual C++ Redistributable」をインストールしてから再実行 |
| サーバー起動に時間がかかる | 初回のみPaddleOCRがモデルをダウンロードします（3〜5分）。ネット接続を確認して待ってください。 |
| カメラ映像が真っ黒／表示されない | Windowsの設定 → プライバシーとセキュリティ → カメラ、で「デスクトップアプリのカメラアクセス」がオンになっているか確認 |
| 内蔵カメラの映像が出てWebcamが映らない | `python scripts\find_camera.py` で正しいインデックスを確認し、`set CAMERA_INDEX=<番号>` を指定して起動し直してください |
| 「Windowsセキュリティの重要な警告」（ファイアウォール）が出る | 「アクセスを許可する」を選択してください（プライベートネットワークのみで十分です） |
| `conda` コマンドが見つからない（Command Not Found） | 「Anaconda Prompt (miniconda3)」から実行しているか確認してください。通常のコマンドプロンプトやPowerShellでは追加設定が必要です |
| OCRでCAS番号は読めるのに化合物情報が出ない | ラベルの文字がかすれている、あるいはPubChemに該当データがない可能性があります。「試薬名を手入力して検索」で英語名を試してください |
| 手入力検索でヒットしない | 日本語名では検索がヒットしにくいです。英語名（IUPAC名や商品名の英語表記）で試してください |
| `ModuleNotFoundError` が出る | `conda activate chemical-scanner` を実行し忘れている可能性があります。仮想環境を有効化してから `pip install -r requirements.txt` をやり直してください |
| 日本語のファイルパスで文字化け・エラーが出る | フォルダ名を一時的に英数字のみのパス（例: `C:\chemical-scanner`）に変更して試してください |

---

## 5. サーバーの停止・再起動

Anaconda Promptで `Ctrl + C` を押すとサーバーが停止します。

次回起動する際は、Anaconda Promptを開いて以下を実行してください（Webcamのインデックスが前回と同じであれば同じコマンドでOKです）。

```bat
cd Desktop\chemical-scanner
conda activate chemical-scanner
python app.py
```

---

## 6. フィードバックについて

使ってみて気づいた点（動作しない・分かりにくい・こうしてほしい等）があれば、開発担当まで共有してください。特に以下の情報があると調査がスムーズです。

- 何をしようとしたか
- 実際に何が起きたか（画面のスクリーンショットがあると尚良い）
- Anaconda Promptに表示されているエラーメッセージ（あれば）
- Windowsのバージョン（10 / 11）
