# 🚀 株最強分析くん - デプロイ手順書

## 📁 ステップ1: ファイル構成の確認

プロジェクトフォルダに以下のファイルがあることを確認してください：

```
stock-analyzer/
├── app.py                      # メインアプリケーション
├── requirements.txt            # 依存パッケージ
├── .gitignore                  # Git除外設定
├── README.md                   # プロジェクト説明
└── data/                       # 自動生成（初回起動時）
    ├── analysis_history.json
    └── monthly_ranking.json
```

## 🔧 ステップ2: ローカルでの動作確認

### 2-1. 仮想環境の作成（推奨）

```bash
# Windowsの場合
python -m venv venv
venv\Scripts\activate

# Mac/Linuxの場合
python3 -m venv venv
source venv/bin/activate
```

### 2-2. パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2-3. アプリの起動

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` が自動的に開きます。

### 2-4. 動作テスト

1. 銘柄コード（例: 7203）を入力
2. 「分析開始」ボタンをクリック
3. スコアとグラフが表示されることを確認

## 📦 ステップ3: GitHubリポジトリの作成

### 3-1. GitHubで新規リポジトリを作成

1. https://github.com にアクセス
2. 右上の「+」→「New repository」をクリック
3. リポジトリ名: `stock-analyzer`（任意の名前でOK）
4. Public/Privateを選択
5. 「Create repository」をクリック

### 3-2. ローカルからプッシュ

```bash
# Gitの初期化（まだの場合）
git init

# ファイルをステージング
git add .

# コミット
git commit -m "Initial commit: 株最強分析くん"

# リモートリポジトリを追加（URLは自分のリポジトリに変更）
git remote add origin https://github.com/yourusername/stock-analyzer.git

# プッシュ
git branch -M main
git push -u origin main
```

### 3-3. GitHubで確認

ブラウザでリポジトリを開き、ファイルがアップロードされていることを確認

## ☁️ ステップ4: Streamlit Cloudでデプロイ

### 4-1. Streamlit Cloudにアクセス

https://share.streamlit.io にアクセス

### 4-2. GitHubで認証

「Sign up with GitHub」または「Continue with GitHub」をクリック

### 4-3. アプリをデプロイ

1. 「New app」ボタンをクリック
2. 以下を設定：
   - **Repository**: `yourusername/stock-analyzer`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL**: 任意のURL（例: `stock-analyzer-pro`）

3. 「Deploy!」をクリック

### 4-4. デプロイの進行状況

- デプロイには3〜5分程度かかります
- 画面に進行状況が表示されます
- エラーが出た場合はログを確認

### 4-5. デプロイ完了

✅ デプロイ完了後、自動的にアプリが開きます

あなたのアプリのURL: `https://stock-analyzer-pro.streamlit.app`

## 🔄 ステップ5: 更新とメンテナンス

### コードを更新する場合

```bash
# ファイルを編集後
git add .
git commit -m "Update: 機能追加"
git push
```

→ Streamlit Cloudが自動的に再デプロイします！

### アプリを停止する場合

1. Streamlit Cloudのダッシュボードにアクセス
2. アプリの設定（⚙️）→「Delete app」

## 🎯 トラブルシューティング

### エラー1: ModuleNotFoundError

**原因**: requirements.txtにパッケージが記載されていない

**解決策**: requirements.txtに不足しているパッケージを追加

```bash
# ローカルで確認
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements"
git push
```

### エラー2: デプロイが進まない

**原因**: app.pyの構文エラーまたは無限ループ

**解決策**: 
1. ローカルで `streamlit run app.py` を実行してエラーを確認
2. エラーを修正してプッシュ

### エラー3: データが保存されない

**原因**: Streamlit Cloudは一時的なストレージを使用

**解決策**: 
- 永続的なデータ保存が必要な場合は、外部DB（Supabase、Firebase等）を使用
- または、GitHubにデータファイルをコミットする設定にする

## 📊 デプロイ後の確認事項

### ✅ チェックリスト

- [ ] アプリが正常に表示される
- [ ] 銘柄コード入力が機能する
- [ ] スコア計算が正しく動作する
- [ ] グラフが表示される
- [ ] 履歴が保存される
- [ ] ランキングが表示される

### 🎉 完了！

おめでとうございます！あなたの株分析アプリが世界中からアクセス可能になりました！

## 🌐 公開URLの共有

デプロイが完了したら、以下のURLを共有できます：

```
https://あなたのアプリ名.streamlit.app
```

## 📱 次のステップ

1. **独自ドメインの設定**（有料プラン）
2. **認証機能の追加**
3. **データベースの統合**
4. **パフォーマンス最適化**
5. **モバイル対応の強化**

---

質問や問題があれば、Streamlit Communityフォーラムで質問できます：
https://discuss.streamlit.io/