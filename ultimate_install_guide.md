# 🌟 決定版！初心者でも楽々インストール
## 日本株分析アプリ（J_Stock_StreamlitV2）

### 📖 このガイドについて
- **対象**: プログラミング完全初心者
- **所要時間**: 約15-20分
- **OS**: Windows・Mac両対応
- **前提知識**: 一切不要！

---

## 🎯 どちらのOSを使っていますか？

### 🪟 Windowsの方 → [Windows版へジャンプ](#windows版)
### 🍎 Macの方 → [Mac版へジャンプ](#mac版)

---

## 🪟 Windows版

### 📋 準備するもの
- Windowsパソコン
- インターネット接続
- 約500MB の空き容量

### ステップ 1: Python のインストール

1. **[Python公式サイト](https://www.python.org/downloads/)** にアクセス
2. 黄色い **「Download Python 3.xx.x」** ボタンをクリック
3. ダウンロードした `.exe` ファイルをダブルクリック
4. **🚨 重要**: インストール画面で **「Add Python to PATH」に必ずチェック** ✅
5. 「Install Now」をクリック

### ステップ 2: プロジェクトファイルのダウンロード

1. **[プロジェクトのGitHubページ](https://github.com/inata169/J_Stock_StreamlitV2)** にアクセス
2. 緑色の **「Code」** ボタンをクリック
3. **「Download ZIP」** を選択
4. デスクトップに `J_Stock_StreamlitV2-main.zip` を保存
5. ZIPファイルを **右クリック** → **「すべて展開」**

### ステップ 3: コマンドプロンプトを開く

1. **`Windows + R`** キーを同時押し
2. 「**cmd**」と入力して **Enter**
3. 黒い画面（コマンドプロンプト）が開きます

### ステップ 4: プロジェクトフォルダに移動

```cmd
cd Desktop\J_Stock_StreamlitV2-main
```

### ステップ 5: 仮想環境を作成

```cmd
python -m venv .venv
```

### ステップ 6: 仮想環境を有効化

```cmd
.venv\Scripts\activate
```

**✅ 成功すると**: プロンプトの前に `(.venv)` が表示されます

### ステップ 7: 必要なライブラリをインストール

```cmd
pip install -r requirements.txt
```

### ステップ 8: 環境設定（あれば）

```cmd
copy .env.example .env
```

### ステップ 9: アプリケーション起動！

```cmd
streamlit run app.py
```

**🎉 成功！**: ブラウザが自動で開いて株分析アプリが表示されます

---

## 🍎 Mac版

### 📋 準備するもの
- Macパソコン
- インターネット接続
- 約500MB の空き容量

### ステップ 1: Python のインストール

1. **[Python公式サイト](https://www.python.org/downloads/)** にアクセス
2. 黄色い **「Download Python 3.xx.x」** ボタンをクリック
3. ダウンロードした `.pkg` ファイルをダブルクリック
4. インストーラーの指示に従ってインストール
5. **「Install Certificates」** も忘れずにクリック

### ステップ 2: プロジェクトファイルのダウンロード

1. **[プロジェクトのGitHubページ](https://github.com/inata169/J_Stock_StreamlitV2)** にアクセス
2. 緑色の **「Code」** ボタンをクリック
3. **「Download ZIP」** を選択
4. ダウンロードした `J_Stock_StreamlitV2-main.zip` をデスクトップに移動
5. ZIPファイルをダブルクリックして展開

### ステップ 3: ターミナルを開く

1. **`Command + スペース`** でSpotlight検索を開く
2. 「**ターミナル**」と入力して **Enter**
3. ターミナル（黒い画面）が開きます

### ステップ 4: プロジェクトフォルダに移動

```bash
cd ~/Desktop/J_Stock_StreamlitV2-main
```

**確認コマンド**: 正しい場所にいるかチェック
```bash
ls -la
```
→ `app.py` と `requirements.txt` が見えればOK！

### ステップ 5: 仮想環境を作成

```bash
python3 -m venv .venv
```

### ステップ 6: 仮想環境を有効化

```bash
source .venv/bin/activate
```

**✅ 成功すると**: プロンプトの前に `(.venv)` が表示されます

### ステップ 7: 必要なライブラリをインストール

```bash
pip install -r requirements.txt
```

### ステップ 8: 環境設定（あれば）

```bash
cp .env.example .env
```

### ステップ 9: アプリケーション起動！

```bash
streamlit run app.py
```

**🎉 成功！**: ブラウザが自動で開いて株分析アプリが表示されます

---

## 🚨 トラブルシューティング

### ❌ よくあるエラーと解決法

#### 1. 「python は認識されていません」（Windows）
**原因**: PythonがPATHに追加されていない
**解決**: Pythonを再インストール（「Add Python to PATH」にチェック）

#### 2. 「command not found: python3」（Mac）
**解決法**:
```bash
python --version  # python3の代わりにpythonを試す
```

#### 3. 「requirements.txt が見つかりません」
**原因**: 間違ったフォルダにいる
**解決法**:
```bash
# 現在の場所を確認
pwd

# 正しいフォルダに移動
# Windows: cd Desktop\J_Stock_StreamlitV2-main
# Mac: cd ~/Desktop/J_Stock_StreamlitV2-main
```

#### 4. インストール中にエラー
**解決法**:
```bash
# pipをアップグレード
pip install --upgrade pip
```

#### 5. ポートが使用中
**解決法**:
```bash
# 別のポートで起動
streamlit run app.py --server.port 8502
```

### 🔄 最初からやり直したい場合

**Windows**:
```cmd
# フォルダを削除して最初から
rmdir /s J_Stock_StreamlitV2-main
```

**Mac**:
```bash
# フォルダを削除して最初から
rm -rf J_Stock_StreamlitV2-main
```

その後、ステップ2から再開してください。

---

## 🎮 次回起動時の簡単手順

一度インストールが完了すれば、次回は3ステップで起動できます：

**Windows**:
```cmd
cd Desktop\J_Stock_StreamlitV2-main
.venv\Scripts\activate
streamlit run app.py
```

**Mac**:
```bash
cd ~/Desktop/J_Stock_StreamlitV2-main
source .venv/bin/activate
streamlit run app.py
```

---

## 🛑 アプリの終了方法

1. **アプリを終了**: ターミナル/コマンドプロンプトで **`Ctrl + C`**
2. **仮想環境を終了**: `deactivate` と入力

---

## 💡 初心者向け豆知識

### 🤖 仮想環境って何？
- アプリ専用の「お部屋」を作ること
- 他のプログラムに影響しない安全な環境
- 削除も簡単（フォルダごと削除でOK）

### 📁 ファイルの場所がわからない時
**Windows**: エクスプローラーで「Desktop」フォルダを確認
**Mac**: Finderで「デスクトップ」を確認

### 🔤 コマンドのコピペ方法
- **コピー**: Ctrl+C（Windows）/ Command+C（Mac）
- **ペースト**: Ctrl+V（Windows）/ Command+V（Mac）

### 💾 完全削除方法
仮想環境を使っているので、**フォルダごと削除するだけ**でアンインストール完了！

---

## 🆘 それでもうまくいかない時

以下の情報をメモして、詳しい人に相談してください：

```bash
# システム情報確認コマンド
# Windows: ver
# Mac: sw_vers

# Python確認
python --version
# または
python3 --version
```

---

## 🎉 完了！

お疲れさまでした！これで日本株分析アプリが使えるようになりました。

**アクセス先**: http://localhost:8501

楽しい株式投資分析をお楽しみください！ 📈