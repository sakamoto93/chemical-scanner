# Claude Code 開発ガイドライン

このプロジェクトでの Claude による操作ルール

---

## Git ブランチ管理

### ✅ 必ず守ること

1. **main ブランチには直接プッシュしない**
   - main は常に動作する状態を維持する必要があります
   - 新しい機能・変更は feature ブランチで開発

2. **ブランチ命名規則**
   ```
   feature/<機能名>    # 新機能
   bugfix/<バグ名>     # バグ修正
   docs/<ドキュメント> # ドキュメント更新
   ```

3. **コミット前に確認を取る**
   - 大きな変更の場合は、必ずプッシュ前に内容を表示して確認する

4. **プッシュ前に実行テスト**
   - コード変更の場合は `python app.py` で動作確認
   - エラーがないことを確認してからコミット

---

## iPhone/iPad での操作

### 推奨される作業
- ✅ コード確認・参照
- ✅ ドキュメント閲覧
- ✅ ファイル内容の確認
- ✅ 設計・要件の記録

### 避けるべき作業
- ❌ コード直接編集（同期の問題）
- ❌ main ブランチへの直接プッシュ
- ❌ 複雑な Git 操作

### iPhone で編集する場合
```
feature/iphone-<機能名>
```
というブランチを作成してください

---

## コミットメッセージの形式

```
<Type>: <説明>

<詳細（必要に応じて）>
```

**Type の種類：**
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント更新
- `refactor`: コード整理
- `test`: テスト追加

**例：**
```
feat: PaddleOCR を使用した OCR 機能を実装
docs: Step1-1 の進捗を PROGRESS.md に記録
```

---

## 開発フロー（必須）

1. **feature ブランチを作成**
   ```bash
   git checkout -b feature/<機能名>
   ```

2. **実装・テスト**
   - コード変更
   - 動作確認

3. **コミット**
   ```bash
   git commit -m "feat: 機能説明"
   ```

4. **プッシュ前に確認**
   - `git diff origin/main` で変更内容を確認
   - 不要な変更がないか確認

5. **プッシュ**
   ```bash
   git push origin feature/<機能名>
   ```

6. **main にマージ**
   - MacBook で確認後、main にマージして push

---

## プロジェクト構成

```
chemical-scanner/
├── app.py                 # FastAPI メインアプリ
├── requirements.txt       # Python 依存パッケージ
├── Readme.md             # プロジェクト概要
├── PROGRESS.md           # 進捗状況
├── CLAUDE.md             # このファイル（開発ガイド）
├── templates/
│   └── index.html        # HTML テンプレート
├── static/
│   └── style.css         # CSS スタイル
└── scanner/              # (将来用) OCR 処理モジュール
```

---

## 重要な環境設定

### 仮想環境
```bash
conda activate chemical-scanner
```

### サーバー起動
```bash
python app.py
```

### Git 設定（初回のみ）
```bash
git config user.name "sakamoto93"
git config user.email "kyuchan.q@gmail.com"
```

---

## トラブルシューティング

### NumPy バージョンエラーが出た場合
```bash
python -m pip install --upgrade numpy<2
```

### pip が見つからない場合
```bash
python -m ensurepip --upgrade
```

### サーバーが起動しない場合
1. 仮想環境が有効化されているか確認
2. `python app.py` を実行
3. エラーメッセージをコピーして確認

---

## 質問・迷った場合

- このガイドを参照してください
- 特に **Git ブランチ管理** と **開発フロー** は必ず守ってください
- 不確実な場合は、MacBook での操作を推奨します
