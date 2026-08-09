# Chemical Scanner

試薬瓶のラベルから CAS 番号を OCR で読み取り、化合物情報を取得し、一覧化・Excel 出力を行う Web アプリケーション。

---

# プロジェクトの目的

研究室で使用している試薬管理を効率化することを目的とする。

最終目標は既存の試薬管理台帳と統合し、

- CAS番号
- 化合物名
- 法令情報
- SDS
- 在庫管理

などを一元管理できるシステムを構築する。

ただし、最初から全機能を作るのではなく、段階的に開発する。

---

# 開発方針

## 小さく作る

一度に完成形を目指さない。

毎回

「動くもの」

を作る。

---

## GitHubで履歴管理

GitHubをバックアップとしてではなく、

「開発履歴」

として利用する。

動作確認できた段階で必ずコミットする。

iPhone ClaudからもGitHubへの連携ができるようになり、モバイルデバイスからも開発進捗の管理が可能になった。

---

## 常に動く状態を維持

main ブランチは必ず動作する状態にする。

新しい機能は feature ブランチで開発する。

例

main

├── feature/camera

├── feature/ocr

├── feature/pubchem

---

## 一段階ごとに完成させる

各Stepで

- 動作確認
- Git Commit
- GitHubへPush

を行う。

---

# 使用技術

Backend

- FastAPI

Frontend

- HTML
- CSS
- JavaScript

OCR

- PaddleOCR

画像処理

- OpenCV

化学データ

- PubChem API

Excel

- openpyxl

データベース

- Step1では使用しない
- Step3でSQLite導入予定

---

# ディレクトリ構成

chemical_scanner/

```
app.py

requirements.txt

README.md

scanner/

templates/

static/

exports/
```

---

# 開発ロードマップ

## Step1

CAS番号読み取りアプリ

目的

試薬瓶をカメラに向けるだけで

CAS番号

↓

化合物名取得

↓

一覧追加

↓

Excel出力

までを実現する。

---

### Step1-1

FastAPI

HTML

カメラ表示

完成条件

ブラウザにライブ映像が表示されること。

---

### Step1-2

PaddleOCR

完成条件

画面内の文字列が取得できること。

---

### Step1-3

CAS番号抽出

正規表現

チェックディジット検証

完成条件

CAS番号だけ抽出できること。

---

### Step1-4

PubChem検索

完成条件

CAS番号から化合物名を取得できること。

---

### Step1-5

一覧表示

完成条件

複数の試薬を追加できること。

---

### Step1-6

Excel出力

完成条件

一覧をExcelへ保存できること。

---

## Step2

既存Excel台帳との互換化

追加予定

- 列順
- 項目
- フォーマット
- 出力様式

---

## Step3

SQLite導入

追加予定

- データ保存
- 編集
- 削除
- 重複チェック

---

## Step4

法令情報追加

追加予定

- SDSリンク
- GHS
- 毒劇物
- PRTR
- リスクアセスメント
- 発がん性

※ 表示のみ実装

---

## Step5

既存試薬台帳との統合

追加予定

- 保管場所
- メーカー
- ロット番号
- 在庫管理
- QRコード

---

# Git運用ルール

## 初期化

```bash
git init
```

---

## 状態確認

```bash
git status
```

---

## 追加

```bash
git add .
```

---

## コミット

```bash
git commit -m "Camera completed"
```

---

## Push

```bash
git push
```

---

# バージョン管理

v0.1.0

FastAPI

---

v0.2.0

Camera

---

v0.3.0

OCR

---

v0.4.0

CAS Validation

---

v0.5.0

PubChem

---

v0.6.0

Compound List

---

v0.7.0

Excel Export

---

v1.0.0

Step1完成

---

# 開発時のルール

毎回

1. 実装
2. 動作確認
3. Git Commit
4. GitHub Push

までを1セットとする。

---

# 将来実装予定

- SDS検索
- リスクアセスメント対象判定
- GHS表示
- 毒劇物判定
- 発がん性表示
- PRTR
- 消防法
- 在庫管理
- QRコード
- 試薬ラベル印刷

※ これらは Step4以降で実装する。

---

# 最終目標

研究室の試薬管理台帳と完全統合し、

OCRによる登録

↓

法令情報取得

↓

在庫管理

↓

Excel出力

↓

既存台帳との同期

までを一つのWebアプリで実現する。