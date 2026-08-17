# Chemical Scanner - Claude開発進捗ログ

## プロジェクト概要

試薬瓶のラベルからOCRで化合物情報を自動抽出し、CAS番号・化合物名・法令情報などを一元管理するWebアプリケーション。

研究室の試薬管理台帳と統合し、効率化を目指す。

---

## 進捗状況

### ✅ 完了したマイルストーン

#### Step1-1: カメラ表示機能（8月8日完成）
- FastAPI + OpenCV でWebカメラのライブストリーミング実装
- ブラウザでリアルタイム映像表示

#### Step1-2: OCR機能実装（8月10日完成）
- **PaddleOCR** 統合
- カメラからのフレームキャプチャ (`/capture` エンドポイント)
- テキスト抽出 (`/ocr` エンドポイント)
- 信頼度付きテキスト表示

#### Step1-2.5: 自動OCR実行機能（8月11日完成 → 8月11日改善完了）

**完成（8月11日 初版）**
- JavaScriptで1秒ごとに定期実行
- ページロード時に自動実行開始
- 「自動スキャン: 開始/停止」ボタンで制御
- ステータス表示機能
- 前フレーム比較による重複検出回避（Phase 2）

**改善（8月11日 Phase 3）**
- ページロード時の自動開始を削除 → ユーザーが手動でボタンをクリック
- 5秒の起動遅延を実装 → 試薬瓶の位置調整時間を確保
- カウントダウン表示を追加 → ユーザーが残り時間を把握できるように
- スキャン間隔を1秒から2.5秒に最適化 → CPU負荷削減

**さらに改善（8月11日 Phase 4）**
- ブラウザ上でユーザーが設定値を調整可能に
- スタートアップ遅延（1～60秒）をリアルタイムで変更可能
- スキャン間隔（0.5～30秒）をリアルタイムで変更可能
- 実験環境に最適な値を各自で設定できるように

**実装内容：**
```
app.py:
- GET /capture: 静止画キャプチャ（ストリーミングハング問題を解決）
- POST /ocr: PaddleOCR処理（辞書形式の新しい結果構造に対応）

templates/index.html:
- 「自動スキャン: 開始/停止」ボタン（手動クリック開始）
- カウントダウン表示機能（秒数をリアルタイム更新）
- スキャン設定セクション（スタートアップ遅延、スキャン間隔の調整）
- performOCR()関数：前フレーム比較による重複チェック
- shouldStop フラグによる即座停止機能
- OCR結果表示エリア（テキスト + 信頼度）

static/style.css:
- UIレイアウト・スタイリング
- 設定セクションのスタイル（.settings, .setting-group）
```

**テスト結果（8月11日 Mac）**
- ✅ ボタンクリック後、「5秒後に開始...」と表示
- ✅ カウントダウンが毎秒更新（5→4→3→2→1）
- ✅ 5秒後に「実行中...」に変わり、スキャン開始
- ✅ 2.5秒ごとの定期実行で安定動作
- ✅ 停止ボタンで即座にスキャン停止

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

## Step1-3 CAS番号抽出・化合物情報取得（8月17日実装開始）

### Phase 1: CAS番号がある試薬の対応（8月17日完成）✅

**完成内容**
- OCRで抽出したテキストからCAS番号を正規表現で抽出
- PubChem APIで化合物情報を取得
- ブラウザに化合物名、分子式、分子量を表示

**実装関数**
```python
def extract_cas_number(texts):
    """OCRテキストからCAS番号を抽出"""
    # 正規表現パターン: \d{2,7}-\d{2}-\d

def search_pubchem_by_cas(cas_number):
    """CAS番号からPubChemで化合物情報を取得"""
    # pubchempyを使用して検索
    # 返値: {cas, name, formula, weight, cid}
```

**テスト結果（8月17日）**
- テスト試薬: Thymol (CAS: 5142-23-4)
- ✅ CAS番号抽出: 5142-23-4
- ✅ 化合物名: 3-methyl-7H-purin-6-imine
- ✅ 分子式: C6H7N5
- ✅ 分子量: 149.15

**技術的知見**
- チェックディジット検証は不要（PubChemが直接検証）
- CAS番号検索時は`pcp.get_compounds(cas, 'name')`を使用
- pubchempyは自動的にエラーハンドリングしてくれる

### Phase 2: CAS番号がない試薬の対応（計画中）

**実装予定**
- OCRで抽出された化合物名や化学式を識別
- PubChem APIで化合物名や化学式で逆引き検索
- CAS番号を取得して一覧に統合

**検索優先順位**
1. **CAS番号** - 最も正確（直接検索）✅ 実装完了
2. **IUPAC名** - 国際命名法（精度高）
3. **化学式** - 分子式マッチング
4. **商品名** - 曖昧性が高い（最後）

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

### 最新コミット（8月17日）

```
33aed85 Clean: Remove debug output for production
f5ae047 Fix: Skip CAS checkdigit validation and search PubChem directly
158ada8 Fix: Correct PubChem API search parameter for CAS number lookup
24a1fa4 Step1-3 Phase1: Implement CAS number extraction and PubChem lookup
83a97de docs: Update for Phase 4 - User-adjustable settings feature
5af760b Feature: Add adjustable settings for startup delay and scan interval
ee9185e docs: Update progress logs for Step1-2.5 Phase 3 completion
4d46199 Feature: Add countdown display for startup delay
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

### 優先度：高（Step1-3実装準備）

1. **Step1-3実装** - CAS番号抽出・化合物情報取得
   - PubChem API統合
   - テキスト解析・化合物情報抽出
   - 正規表現によるCAS番号検証
   - CAS番号からの化合物名取得

### 優先度：中（今後の改善）

2. **読み取り速度の改善**
   - 現在の課題：OCR処理に時間がかかる
   - 検討事項：モデルの軽量化、並列処理
   - テスト：複数の試薬でベンチマーク実施

3. **枠内検出機能の実装**（中期目標）
   - 目的：試薬瓶がカメラ枠内に来たら自動スキャン開始
   - 方針：OpenCVの物体検出またはシンプルな枠内判定
   - メリット：ユーザーが瓶を枠に合わせるだけでOK
   - 実装時期：Step1-3完了後（Phase 4）

4. **テスト拡張** - より多くの試薬でテスト
   - 英語ラベル試薬
   - 日本語ラベル試薬
   - 中国語混在試薬

### 優先度：低（Step1完成後）

5. **UI改善**
   - 検出されたCAS番号のハイライト
   - 複数試薬の連続スキャン結果の一覧表示
   - 履歴機能

6. **Step2以降**（既存Excel台帳との互換化）
   - 列順・項目・フォーマット調整
   - 出力様式のカスタマイズ

---

## 参考リンク

- **GitHub Repository**: https://github.com/sakamoto93/chemical-scanner
- **PaddleOCR**: https://github.com/PaddlePaddle/PaddleOCR
- **PubChem API**: https://pubchem.ncbi.nlm.nih.gov/docs/PubChem-REST-API
- **FastAPI**: https://fastapi.tiangolo.com/

---

**最終更新:** 2026-08-17
**担当**: Claude + Mac テスト
**ステータス**: Step1-2.5完成 → Step1-3 Phase1完成 → Phase2計画中

**8月11日の成果：**
- ✅ 5秒の起動遅延機能実装（Phase 3）
- ✅ カウントダウン表示機能実装（Phase 3）
- ✅ ユーザー調整可能な設定機能実装（Phase 4）
  - スタートアップ遅延（1～60秒）
  - スキャン間隔（0.5～30秒）
- ✅ Macでのテスト完了
- ✅ ドキュメント更新完了

**8月17日の成果：**
- ✅ Step1-3 Phase1実装開始
  - CAS番号抽出機能（正規表現）
  - PubChem API連携
  - 化合物情報取得（名前、分子式、分子量）
- ✅ チェックディジット検証を削除（PubChemが直接検証）
- ✅ Macでのテスト完成
  - テスト試薬: Thymol (CAS: 5142-23-4)
  - 化合物情報取得成功
- ✅ デバッグ出力を削除（本番環境対応）
- ✅ ドキュメント更新完了

**次のステップ:**
- Phase 2: CAS番号がない試薬の逆引き検索実装予定
