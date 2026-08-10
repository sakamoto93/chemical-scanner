# Chemical Scanner - Claude開発進捗ログ

## プロジェクト概要

試薬瓶のラベルからOCRで化合物情報を自動抽出し、CAS番号・化合物名・法令情報などを一元管理するWebアプリケーション。

研究室の試薬管理台帳と統合し、効率化を目指す。

---

## 今日の進捗（2026-08-10）

### ✅ 完了したマイルストーン

#### Step1-1: カメラ表示機能（8月8日完成）
- FastAPI + OpenCV でWebカメラのライブストリーミング実装
- ブラウザでリアルタイム映像表示

#### Step1-2: OCR機能実装（本日完成）
- **PaddleOCR** 統合
- カメラからのフレームキャプチャ (`/capture` エンドポイント)
- テキスト抽出 (`/ocr` エンドポイント)
- 信頼度付きテキスト表示

**実装内容：**
```
app.py:
- GET /capture: 静止画キャプチャ（ストリーミングハング問題を解決）
- POST /ocr: PaddleOCR処理（辞書形式の新しい結果構造に対応）

templates/index.html:
- 「キャプチャ&OCR実行」ボタン
- OCR結果表示エリア（テキスト + 信頼度）

static/style.css:
- UIレイアウト・スタイリング
```

### 📊 テスト結果

**テスト試薬：** Wako Thymol (CAS: 不明な試薬)
- 検出テキスト例：
  - `Thymol` (100.0%)
  - `3-Methyladenine` (100.0%)
  - `CAS RN 5142-23-4` (99.9%)
  - `TOKYO CHEMICAL INDUSTRY CO` (93.9%)

**OCR精度：** 信頼度95%以上のテキストは高い精度で認識

---

## 発見・課題

### 重要な発見

1. **CAS番号がない試薬も多い**
   - 直接CAS番号が記載されていない試薬瓶が存在
   - 化合物名や化学式からの逆引きが必須

2. **複数言語対応の必要性**
   - 英語・日本語・中国語が混在するラベル
   - 現在は英語優先（`lang='en'`）

3. **ストリーミングハング問題を解決**
   - `/video_feed` (ストリーミング) から直接 `.blob()` で読み込むとハング
   - → `/capture` エンドポイントで静止画を返すことで解決

### 技術的課題

- PaddleOCR バージョンアップによる結果フォーマット変更
  - 旧形式：タプルのリスト
  - 新形式：辞書形式 (`rec_texts`, `rec_scores`)

---

## Step1-3 実装計画

### 目標
CAS番号がない試薬に対応し、化合物名/化学式からCAS番号を取得する

### 実装戦略

```
OCR結果（テキスト抽出完了）
    ↓
CAS番号の抽出（正規表現 + チェックディジット検証）
    ↓ (CAS番号がある場合)
PubChem APIで化合物情報取得

OR

化合物名/化学式の抽出（テキスト分析）
    ↓ (CAS番号がない場合)
PubChem APIで逆引き検索
    ↓
CAS番号を取得
    ↓
一覧に統合
```

### PubChem API検索優先順位

1. **CAS番号** - 最も正確（直接検索）
2. **IUPAC名** - 国際命名法（精度高）
3. **化学式** - 分子式マッチング
4. **商品名** - 曖昧性が高い（最後）

### 必要な実装

- `requirements.txt` に `pubchempy` または `requests` 追加
- `app.py` に以下の関数を追加：
  - `extract_cas_number()` - 正規表現でCAS番号抽出
  - `validate_cas_checkdigit()` - チェックディジット検証
  - `search_pubchem()` - PubChem APIでの検索
  - `parse_compound_info()` - テキストから化合物情報を抽出

---

## 開発環境セットアップ

### Macでのセットアップ

```bash
# 仮想環境作成（既に存在）
conda activate chemical-scanner

# 依存パッケージインストール
pip install -r requirements.txt

# サーバー起動
cd /Volumes/mac移動用/化学物質管理
python app.py

# ブラウザアクセス
open http://localhost:8000
```

### 注意点

- PaddleOCR初回実行時はモデルダウンロード（3-5分）
- カメラアクセス許可が必要
- 十分な照明環境でテスト推奨

---

## Git運用状況

### ブランチ構成

```
main (リモート)
└── claude/chemical-scanner-files-f1gxcu (開発ブランチ)
    ├── Step1-1: Camera display (完成)
    ├── Step1-2: OCR implementation (完成)
    └── Step1-3: CAS lookup (計画中)
```

### 最新コミット

```
4849316 docs: Update Step1-3 implementation plan with CAS number reverse lookup strategy
73c661b Fix: PaddleOCR result parsing for new API format
793620c Fix: Update PaddleOCR parameters (use_textline_orientation, lang='en')
0a03d26 Step1-2: Implement PaddleOCR text extraction from camera
9edeb6b Update: iPhone Claude GitHub integration support
e313b62 Step1-1: Camera display with FastAPI and OpenCV
```

### iPhone Claude対応

- ✅ iPhone Claudでのコミット・プッシュ可能
- ✅ GitHubとの連携完了
- ⚠️ 実行環境はMacで必須（モバイルデバイスでは実行不可）

---

## 技術スタック

| レイヤー | 技術 | バージョン |
|---------|------|-----------|
| **Backend** | FastAPI | 0.104.1 |
| **Server** | Uvicorn | 0.24.0 |
| **OCR** | PaddleOCR | ≥2.7.0.3 |
| **Image Processing** | OpenCV | 4.8.1.78 |
| **NumPy** | NumPy | <2 |
| **Chemistry API** | PubChem API | (計画) |

---

## 次回作業予定

1. **Step1-3実装** - CAS番号逆引き機能
   - PubChem API統合
   - テキスト解析・化合物情報抽出
   - 正規表現によるCAS番号検証

2. **テスト拡張** - より多くの試薬でテスト
   - 英語ラベル
   - 日本語ラベル
   - 中国語ラベル

3. **UI改善**
   - 検出されたCAS番号のハイライト
   - 複数試薬の連続スキャン機能
   - 結果の一覧表示

---

## 参考リンク

- **GitHub Repository**: https://github.com/sakamoto93/chemical-scanner
- **PaddleOCR**: https://github.com/PaddlePaddle/PaddleOCR
- **PubChem API**: https://pubchem.ncbi.nlm.nih.gov/docs/PubChem-REST-API
- **FastAPI**: https://fastapi.tiangolo.com/

---

**最終更新:** 2026-08-10
**担当**: Claude + iPhone Claude
**ステータス**: Step1-2完成 → Step1-3準備中
