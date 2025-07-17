[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/masa1984a-ticketmanagementsystem-badge.png)](https://mseep.ai/app/masa1984a-ticketmanagementsystem)

# チケット管理システム - MCP/Firebase 連携

このプロジェクトは、Claude for Desktop (MCPクライアント) とFirebase Firestoreを連携させ、チケット管理システムを実現するMCPサーバーを提供します。

## 機能概要

- チケットの作成、更新、履歴追加
- チケット一覧の取得 (フィルタリング、並べ替え機能付き)
- チケット詳細の閲覧
- マスターデータ (ユーザー、アカウント、カテゴリなど) の取得

## システム構成

- **フロントエンド**: Claude for Desktop (MCPクライアント)
- **バックエンド**: Python MCP Server (Model Context Protocol)
- **データベース**: Google Cloud Firestore

## 前提条件

- Python 3.10以上
- firebase-admin
- mcp[cli] 1.8.0以上
- Google Cloud Firestoreへのアクセス権限
- Claude for Desktop
- uv コマンドラインツール (Claude for Desktopの設定で使用)

## 環境構築手順

### 1. GCPプロジェクトの設定

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいGCPプロジェクトを作成するか、既存のプロジェクトを選択
3. 「お支払い」セクションで課金が有効になっているか確認し、必要に応じて有効化

### 2. Firestoreの設定

1. Cloud Firestore APIを有効化する
   ```
   Google Cloud Console > APIとサービス > ライブラリ > Cloud Firestore API
   ```

2. Firestoreデータベースの作成
   - モード: **Nativeモード**を選択
   - ロケーション: データベースのリージョンを選択 (例: `asia-northeast1` (東京))
   - データベースID: `mcp-status-test` (このプロジェクトでは利用)

3. セキュリティルールの設定
   - Firestoreの「ルール」タブに移動
   - 開発用ルールの例 (**本番環境では使用しないでください**):
     ```
     rules_version = '2';
     service cloud.firestore {
       match /databases/{database}/documents {
         match /{document=**} {
           allow read, write: if true; // 開発用: 誰でも読み書き可能
         }
       }
     }
     ```

### 3. サービスアカウントと秘密鍵の取得

1. サービスアカウントの作成
   ```
   Google Cloud Console > IAMと管理 > サービスアカウント > サービスアカウントを作成
   ```

2. ロールの付与
   - 「Cloud Datastore ユーザー」ロールを選択
   - または「Firestore データ閲覧者」と「Firestore データ編集者」ロールを付与

3. 秘密鍵 (JSON) のダウンロード
   - サービスアカウントの「キー」タブで「新しい鍵を作成」
   - JSONキーをダウンロードし、`firebase-credentials.json`という名前に変更

   **注意: 秘密鍵ファイルはGitリポジトリに含めないでください。**

### 4. ローカル開発環境のセットアップ

1. リポジトリをクローン
   ```bash
   git clone https://github.com/Masa1984a/ticket-management-mcp.git
   cd ticket-management-mcp
   ```

2. Python仮想環境の作成とアクティベーション
   ```bash
   # プロジェクトディレクトリに移動
   cd プロジェクトディレクトリパス

   # Python仮想環境を作成
   python -m venv .venv

   # 仮想環境をアクティベート (Windows/PowerShell)
   .\.venv\Scripts\Activate.ps1
   # (コマンドプロンプトの場合)
   # .\.venv\Scripts\activate.bat
   # (Linux/Macの場合)
   # source .venv/bin/activate
   ```

3. 秘密鍵ファイルの配置
   - ダウンロードした秘密鍵JSONファイルを`firebase-credentials.json`という名前でプロジェクトルートに配置

4. 依存関係のインストール
   ```bash
   # pipを最新版にアップグレード
   python -m pip install --upgrade pip

   # 依存関係をインストール
   pip install -r requirements.txt
   ```

5. 環境変数の設定

秘密鍵ファイルをプロジェクトルートに置く代わりに、環境変数を設定することも可能です：

```bash
# Windows/PowerShell
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\your\firebase-credentials.json"

# Linux/Mac
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/firebase-credentials.json"
```

6. Claude for Desktopの設定

Claude for Desktopの設定ファイル`claude_desktop_config.json`を編集：

```json
{
  "mcpServers": {
    "TicketManagementSystem": {
      "command": "uv",
      "args": [
        "--directory", "プロジェクトディレクトリパス",
        "run",
        "main.py"
      ]
    }
  }
}
```

**注意**: `プロジェクトディレクトリパス`は実際のプロジェクトパスに置き換えてください。Windowsの場合はパスのバックスラッシュをエスケープする必要があります。例: `C:\\Users\\username\\projects\\ticket-system`

### 5. サンプルデータ準備
1. まず基本的なマスターデータを作成します:

```bash
python ./firestore/firebase_init.py
```

2. 次に、デモ用の追加データを作成します:

```bash
python ./firestore/demo_data_generator.py
```

このコマンドは以下のデータを作成します:
- 追加ユーザー（「上司 進」管理者ユーザー）
- 追加カテゴリ（UX改修依頼など）
- Chat/LLM受付チャネル
- 約40件のデモ用サンプルチケット（バランスの取れたカテゴリ×ステータスの組み合わせ）
- 検索機能に関連するサンプルチケット

3. 投入したデータのチェックをします:
```bash
python ./firestore/check_firestore_data.py --tickets --search
```

4. もしうまくデータが作成されない場合、下記スクリプトを実行して原因を切り分けをしてください。
- test_firebase.py: Firestoreへの接続確認
- test_firestore_write.py: Firestoreへのデータ作成確認

## 実行方法

### ローカルでのテスト実行

Python MCPサーバーを直接実行:

```bash
python main.py
```

または、MCP Inspectorを使用:

```bash
mcp dev main.py
```

- MCP Inspectorは、MCP Server開発者向けの対話型デバッグツールです。開発者がAIアプリ（Claude for desktop、Cursor、Roo Code等）と連携するカスタムツールやサーバーをテスト・検証するためのビジュアルインターフェースを提供します。

### Claude for Desktopへの登録

MCPサーバーをClaude for Desktopに登録:

./claude_desktop_configuration/claude_desktop_configuration.jsonを、Claude for desktopの適切なフォルダへコピーしてください。

上記対応後、Claude for desktopを起動します。

## 使用方法 (Claude for Desktop)

以下のような自然言語の指示でシステムを操作できます:

- 「新しいチケットを作成して」
- 「担当が山田さんのチケット一覧を表示して」
- 「チケットTCK-0001の詳細を表示して」
- 「チケットTCK-0001のステータスを"対応中"に更新して」
- 「チケットTCK-0001にコメントを追加して」

インデックスエラーが発生した場合、エラーに記載されているURLからインデックスのビルドをしてください。

## 開発者向け情報

### プロジェクト構造

- `main.py`: MCPサーバーの実装
- `requirements.txt`: 依存関係リスト
- `README.md`: プロジェクト説明

### Firestoreスキーマ

このシステムは次のコレクションを使用します:

- `users`: ユーザー情報 (担当者、リクエスタ)
- `accounts`: アカウント情報
- `categories`: カテゴリ情報
- `categoryDetails`: カテゴリ詳細情報
- `statuses`: ステータス情報
- `requestChannels`: 受付チャネル情報
- `responseCategories`: 対応分類情報
- `tickets`: チケット情報
- `counters`: 自動採番用カウンター

### MCPサーバーAPI

このMCPサーバーは次のツールとリソースを提供します:

**ツール:**
- `get_ticket_list`: チケット一覧取得
- `get_ticket_detail`: チケット詳細取得
- `create_ticket`: チケット作成
- `update_ticket`: チケット更新
- `add_ticket_history`: チケット履歴追加
- `get_users`: ユーザー一覧取得
- `get_accounts`: アカウント一覧取得
- `get_categories`: カテゴリ一覧取得
- `get_category_details`: カテゴリ詳細一覧取得
- `get_statuses`: ステータス一覧取得
- `get_request_channels`: 受付チャネル一覧取得

## ライセンス

MITライセンスの下で提供されています。詳細はLICENSEファイルを参照してください。