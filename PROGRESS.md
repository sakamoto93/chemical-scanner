# 進捗状況

**最終更新日**: 2026-08-08

---

## 完了（✅）

### Step1-1: カメラ表示機能
- **実装内容**
  - FastAPI でバックエンド Webサーバーを構築
  - OpenCV でカメラからのビデオストリーミング実装（MJPEG形式）
  - HTML/CSS でフロントエンド構築
  - 仮想環境（conda）の導入と環境構築

- **動作確認**
  - Chrome でブラウザにライブ映像がリアルタイムで表示される
  - http://localhost:8000 でアクセス可能

- **コミット**
  - Commit: e313b62 "Step1-1: Camera display with FastAPI and OpenCV"

---

## 進行中（🔄）

なし

---

## 次の予定（📋）

### Step1-2: PaddleOCR 導入（予定日: 2026-08-10）
- 画面内の文字列を OCR で読み取り
- 実際の試薬瓶のラベルを使用してテスト
- 完成条件：画面内の文字列が取得できること

### Step1-3 以降
- CAS番号抽出（正規表現 + チェックディジット検証）
- PubChem 検索（CAS番号 → 化合物名取得）
- 一覧表示機能
- Excel 出力機能

---

## 既知の問題

### Safari との互換性
- Safari では MJPEG ストリーミング（img タグ経由）が動作しない
- Chrome では正常に動作
- **対応方法**: 後の段階で WebSocket または Canvas を使った代替実装を検討

### NumPy バージョン競合（解決済み）
- OpenCV 4.8.1.78 が NumPy 1.x 用にコンパイルされていた
- **解決方法**: requirements.txt に `numpy<2` を指定、仮想環境を導入

---

## 環境構成

### ローカル開発環境
- **OS**: macOS
- **Python**: 3.11.15（仮想環境: chemical-scanner）
- **仮想環境管理**: conda

### 主要ライブラリ
- FastAPI 0.104.1
- Uvicorn 0.24.0
- OpenCV (opencv-python) 4.8.1.78
- Python-multipart 0.0.6
- NumPy < 2

### リポジトリ
- **GitHub**: https://github.com/sakamoto93/chemical-scanner
- **ブランチ**: main（常に動作する状態を維持）

---

## 開発者メモ

### 仮想環境の使用方法
```bash
# 仮想環境を有効化
conda activate chemical-scanner

# サーバーを起動
python app.py

# 完了後
conda deactivate
```

### Git ワークフロー
```bash
# 編集・実装
git add .
git commit -m "機能説明"
git push origin main
```

### アクセス可能な環境
- MacBook: CLI、デスクトップアプリ
- iPhone/iPad: Claude Code Web版（claude.ai/code）

---

## バージョン管理
- **v0.1.0**: FastAPI 基本実装
- **v0.2.0**: Camera（Step1-1 完了）
- v0.3.0（予定）: OCR（Step1-2）
- v0.4.0（予定）: CAS Validation（Step1-3）
- v0.5.0（予定）: PubChem（Step1-4）
- v0.6.0（予定）: Compound List（Step1-5）
- v0.7.0（予定）: Excel Export（Step1-6）
- v1.0.0（予定）: Step1 完成
