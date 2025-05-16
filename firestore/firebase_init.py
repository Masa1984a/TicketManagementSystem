"""
Firebase初期化スクリプト
このスクリプトは、Firestoreにサンプルデータを追加します。
"""

import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import os
import json # 元のスクリプトに含まれていましたが、このコードでは直接は使用されていません
import argparse

def init_firebase():
    """Firebaseを初期化し、指定されたFirestoreクライアントを返す"""
    # 接続したいデータベースのIDをここで指定します
    target_database_id = "mcp-status-test"

    try:
        # 既に初期化されているか確認
        firebase_admin.get_app()
    except ValueError:
        # 初期化されていない場合
        cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'firebase-credentials.json')
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print(f"認証情報ファイル '{cred_path}' を使用してFirebaseアプリを初期化しました。")
        else:
            # デフォルト認証情報を使用
            print(f"警告: 認証情報ファイル '{cred_path}' が見つかりませんでした。")
            print("アプリケーションのデフォルト認証情報を使用してFirebaseアプリの初期化を試みます。")
            print("これがローカル環境での意図しない動作である場合、認証設定を確認してください。")
            firebase_admin.initialize_app()
            print("アプリケーションのデフォルト認証情報を使用してFirebaseアプリを初期化しました。")
    
    # ここで database_id を指定してFirestoreクライアントを取得します
    print(f"FirestoreクライアントをデータベースID '{target_database_id}' で取得します。")
    return firestore.client(database_id=target_database_id)

def create_master_data(db):
    """マスターデータを作成"""
    # ユーザー
    users = [
        {"userId": "user1", "name": "山田 太郎", "email": "taro.yamada@example.com", "role": "担当者", "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)},
        {"userId": "user2", "name": "鈴木 花子", "email": "hanako.suzuki@example.com", "role": "担当者", "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)},
        {"userId": "user3", "name": "佐藤 次郎", "email": "jiro.sato@example.com", "role": "リクエスタ", "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)},
        {"userId": "user4", "name": "高橋 三郎", "email": "saburo.takahashi@example.com", "role": "リクエスタ", "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)}
    ]
    
    for user_data in users: # 変数名を user から user_data に変更 (datetime.user との潜在的衝突を避けるため)
        db.collection('users').document(user_data["userId"]).set(user_data)
    print(f"{len(users)}件のユーザーデータを作成しました。")
    
    # アカウント
    accounts = [
        {"accountId": "acc1", "name": "株式会社ABC", "orderNo": 1, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)},
        {"accountId": "acc2", "name": "XYZ株式会社", "orderNo": 2, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)},
        {"accountId": "acc3", "name": "123株式会社", "orderNo": 3, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)}
    ]
    
    for account in accounts:
        db.collection('accounts').document(account["accountId"]).set(account)
    print(f"{len(accounts)}件のアカウントデータを作成しました。")
    
    # カテゴリ
    categories_data = [ # 変数名を categories から categories_data に変更
        {"categoryId": "cat1", "name": "問合せ", "orderNo": 1, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)},
        {"categoryId": "cat2", "name": "データ修正依頼", "orderNo": 2, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)},
        {"categoryId": "cat3", "name": "障害報告", "orderNo": 3, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)}
    ]
    
    for category in categories_data:
        db.collection('categories').document(category["categoryId"]).set(category)
    print(f"{len(categories_data)}件のカテゴリデータを作成しました。")
    
    # カテゴリ詳細
    category_details = [
        {"categoryDetailId": "catd1", "name": "ポータル・記事・検索機能に関する問合せ", "categoryId": "cat1", "categoryName": "問合せ", "orderNo": 1, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)},
        {"categoryDetailId": "catd2", "name": "サポート管理に関する問合せ", "categoryId": "cat1", "categoryName": "問合せ", "orderNo": 2, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)},
        {"categoryDetailId": "catd3", "name": "マスターデータ修正依頼", "categoryId": "cat2", "categoryName": "データ修正依頼", "orderNo": 1, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)},
        {"categoryDetailId": "catd4", "name": "システム障害", "categoryId": "cat3", "categoryName": "障害報告", "orderNo": 1, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)}
    ]
    
    for detail in category_details:
        db.collection('categoryDetails').document(detail["categoryDetailId"]).set(detail)
    print(f"{len(category_details)}件のカテゴリ詳細データを作成しました。")
    
    # ステータス
    statuses = [
        {"statusId": "stat1", "name": "受付済", "orderNo": 1, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)},
        {"statusId": "stat2", "name": "対応中", "orderNo": 2, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)},
        {"statusId": "stat3", "name": "確認中", "orderNo": 3, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)},
        {"statusId": "stat4", "name": "完了", "orderNo": 4, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)}
    ]
    
    for status in statuses:
        db.collection('statuses').document(status["statusId"]).set(status)
    print(f"{len(statuses)}件のステータスデータを作成しました。")
    
    # 受付チャネル
    request_channels = [
        {"requestChannelId": "ch1", "name": "Email", "orderNo": 1, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)},
        {"requestChannelId": "ch2", "name": "電話", "orderNo": 2, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)},
        {"requestChannelId": "ch3", "name": "Teams", "orderNo": 3, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)}
    ]
    
    for channel in request_channels:
        db.collection('requestChannels').document(channel["requestChannelId"]).set(channel)
    print(f"{len(request_channels)}件の受付チャネルデータを作成しました。")
    
    # 対応分類
    response_categories_data = [ # 変数名を response_categories から response_categories_data に変更
        {"responseCategoryId": "resp1", "name": "Japanから回答可", "parentCategory": "問合せ", "orderNo": 1, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)},
        {"responseCategoryId": "resp2", "name": "無償対応", "parentCategory": "データ修正依頼", "orderNo": 1, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)},
        {"responseCategoryId": "resp3", "name": "開発修正対応", "parentCategory": "障害報告", "orderNo": 1, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)}
    ]
    
    for category in response_categories_data:
        db.collection('responseCategories').document(category["responseCategoryId"]).set(category)
    print(f"{len(response_categories_data)}件の対応分類データを作成しました。")
    
    # チケット採番用カウンター
    db.collection('counters').document('tickets').set({'count': 0})
    print("チケット採番用カウンターを作成しました。")
    
    print("マスターデータの作成が完了しました。")

def create_sample_tickets(db):
    """サンプルチケットを作成"""
    # 今日の日付
    today = datetime.datetime.now(datetime.timezone.utc) # タイムゾーンをUTCに統一
    
    # サンプルチケット
    tickets = [
        {
            "ticketId": "TCK-0001",
            "receptionDateTime": today - datetime.timedelta(days=5),
            "requestorId": "user3",
            "requestorName": "佐藤 次郎",
            "accountId": "acc1",
            "accountName": "株式会社ABC",
            "categoryId": "cat1",
            "categoryName": "問合せ",
            "categoryDetailId": "catd1",
            "categoryDetailName": "ポータル・記事・検索機能に関する問合せ",
            "requestChannelId": "ch1",
            "requestChannelName": "Email",
            "summary": "検索機能が正常に動作しない",
            "description": "検索ボックスに特定のキーワードを入力しても結果が表示されません。\n再現手順：\n1. トップページの検索ボックスに「特殊文字」を含む検索語を入力\n2. 検索ボタンをクリック\n3. 「検索結果がありません」と表示される",
            "attachments": [
                {"fileName": "error_screenshot.png", "fileUrl": "https://example.com/storage/error_screenshot.png", "uploadedAt": today - datetime.timedelta(days=5)}
            ],
            "personInChargeId": "user1",
            "personInChargeName": "山田 太郎",
            "statusId": "stat2",
            "statusName": "対応中",
            "scheduledCompletionDate": today + datetime.timedelta(days=2),
            "completionDate": None,
            "actualEffortHours": None,
            "responseCategoryId": None,
            "responseCategoryName": None,
            "responseDetails": None,
            "hasDefect": False,
            "externalTicketId": "EXT-123",
            "remarks": "",
            "createdAt": today - datetime.timedelta(days=5),
            "updatedAt": today - datetime.timedelta(days=3),
            "history": [
                {
                    "timestamp": today - datetime.timedelta(days=5),
                    "userId": "user1",
                    "userName": "山田 太郎",
                    "changedFields": [],
                    "comment": "新規チケット作成"
                },
                {
                    "timestamp": today - datetime.timedelta(days=3),
                    "userId": "user1",
                    "userName": "山田 太郎",
                    "changedFields": [
                        {
                            "field": "status",
                            "oldValue": "受付済",
                            "newValue": "対応中"
                        }
                    ],
                    "comment": "調査を開始しました。特殊文字のエスケープ処理に問題がある可能性があります。"
                }
            ]
        },
        {
            "ticketId": "TCK-0002",
            "receptionDateTime": today - datetime.timedelta(days=10),
            "requestorId": "user4",
            "requestorName": "高橋 三郎",
            "accountId": "acc2",
            "accountName": "XYZ株式会社",
            "categoryId": "cat2",
            "categoryName": "データ修正依頼",
            "categoryDetailId": "catd3",
            "categoryDetailName": "マスターデータ修正依頼",
            "requestChannelId": "ch2",
            "requestChannelName": "電話",
            "summary": "ユーザーマスターの情報更新依頼",
            "description": "弊社の担当者が変更になりました。以下の通り更新をお願いします。\n\n旧担当：鈴木一郎\n新担当：田中五郎\nメールアドレス：goro.tanaka@xyz.co.jp\n電話番号：03-1234-5678",
            "attachments": [],
            "personInChargeId": "user2",
            "personInChargeName": "鈴木 花子",
            "statusId": "stat4",
            "statusName": "完了",
            "scheduledCompletionDate": today - datetime.timedelta(days=8),
            "completionDate": today - datetime.timedelta(days=9),
            "actualEffortHours": 1.5,
            "responseCategoryId": "resp2",
            "responseCategoryName": "無償対応",
            "responseDetails": "マスターデータの更新が完了しました。\n変更内容の確認をお願いします。",
            "hasDefect": False,
            "externalTicketId": "",
            "remarks": "",
            "createdAt": today - datetime.timedelta(days=10),
            "updatedAt": today - datetime.timedelta(days=9),
            "history": [
                {
                    "timestamp": today - datetime.timedelta(days=10),
                    "userId": "user2",
                    "userName": "鈴木 花子",
                    "changedFields": [],
                    "comment": "新規チケット作成"
                },
                {
                    "timestamp": today - datetime.timedelta(days=9),
                    "userId": "user2",
                    "userName": "鈴木 花子",
                    "changedFields": [
                        {
                            "field": "status",
                            "oldValue": "受付済",
                            "newValue": "完了"
                        }
                    ],
                    "comment": "マスターデータの更新が完了しました。お客様に確認依頼のメールを送信しました。"
                }
            ]
        },
        {
            "ticketId": "TCK-0003",
            "receptionDateTime": today - datetime.timedelta(days=1),
            "requestorId": "user3",
            "requestorName": "佐藤 次郎",
            "accountId": "acc1",
            "accountName": "株式会社ABC",
            "categoryId": "cat3",
            "categoryName": "障害報告",
            "categoryDetailId": "catd4",
            "categoryDetailName": "システム障害",
            "requestChannelId": "ch3",
            "requestChannelName": "Teams",
            "summary": "ダッシュボードが表示されない",
            "description": "今朝からダッシュボードにアクセスするとエラーが表示されます。\nエラーメッセージ：「データの読み込みに失敗しました」\n\n複数のユーザーで同様の事象が発生しています。",
            "attachments": [],
            "personInChargeId": "user1",
            "personInChargeName": "山田 太郎",
            "statusId": "stat1",
            "statusName": "受付済",
            "scheduledCompletionDate": today + datetime.timedelta(days=1),
            "completionDate": None,
            "actualEffortHours": None,
            "responseCategoryId": None,
            "responseCategoryName": None,
            "responseDetails": None,
            "hasDefect": True,
            "externalTicketId": "INC-456",
            "remarks": "緊急対応が必要です。",
            "createdAt": today - datetime.timedelta(days=1),
            "updatedAt": today - datetime.timedelta(days=1),
            "history": [
                {
                    "timestamp": today - datetime.timedelta(days=1),
                    "userId": "user1",
                    "userName": "山田 太郎",
                    "changedFields": [],
                    "comment": "新規チケット作成"
                }
            ]
        }
    ]
    
    # チケット登録
    for ticket in tickets: # 変数 i は未使用だったので削除
        db.collection('tickets').document(ticket["ticketId"]).set(ticket)
    
    # カウンターを更新
    db.collection('counters').document('tickets').set({'count': len(tickets)})
    
    print(f"{len(tickets)}件のサンプルチケットを作成しました。")

def main():
    parser = argparse.ArgumentParser(description='Firestore初期化スクリプト')
    parser.add_argument('--master-only', action='store_true', help='マスターデータのみを作成')
    parser.add_argument('--tickets-only', action='store_true', help='サンプルチケットのみを作成')
    args = parser.parse_args()
    
    # Firestore初期化
    print("Firestoreの初期化を開始します...")
    db = init_firebase()
    print("Firestoreの初期化が完了しました。データベースクライアントを取得しました。")
    
    if args.tickets_only:
        print("サンプルチケットのみを作成します...")
        create_sample_tickets(db)
    elif args.master_only:
        print("マスターデータのみを作成します...")
        create_master_data(db)
    else:
        print("マスターデータとサンプルチケットを作成します...")
        create_master_data(db)
        create_sample_tickets(db)
    
    print("すべての処理が完了しました。")

if __name__ == "__main__":
    main()
