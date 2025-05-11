"""
デモ用追加サンプルデータ生成スクリプト

このスクリプトは、デモ用の追加サンプルデータをFirestoreに追加します。
firebase_init.pyのコードを参考に、デモで見せやすいユースケースに合うデータを作成します。
"""

import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import os
import json
import argparse
import random

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

def create_additional_master_data(db):
    """追加のマスターデータを作成"""
    # 管理者ユーザー
    users = [
        {"userId": "user5", "name": "上司 進", "email": "boss@example.com", "role": "管理者", "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)}
    ]
    
    for user_data in users:
        db.collection('users').document(user_data["userId"]).set(user_data)
    print(f"{len(users)}件の追加ユーザーデータを作成しました。")
    
    # 追加カテゴリ
    categories_data = [
        {"categoryId": "cat4", "name": "UX改修依頼", "orderNo": 4, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)}
    ]
    
    for category in categories_data:
        db.collection('categories').document(category["categoryId"]).set(category)
    print(f"{len(categories_data)}件の追加カテゴリデータを作成しました。")
    
    # 追加カテゴリ詳細
    category_details = [
        {"categoryDetailId": "catd5", "name": "UI/UX改善提案", "categoryId": "cat4", "categoryName": "UX改修依頼", "orderNo": 1, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)},
        {"categoryDetailId": "catd6", "name": "検索機能改善提案", "categoryId": "cat4", "categoryName": "UX改修依頼", "orderNo": 2, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)}
    ]
    
    for detail in category_details:
        db.collection('categoryDetails').document(detail["categoryDetailId"]).set(detail)
    print(f"{len(category_details)}件の追加カテゴリ詳細データを作成しました。")
    
    # 追加受付チャネル
    request_channels = [
        {"requestChannelId": "ch4", "name": "Chat/LLM", "orderNo": 4, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)}
    ]
    
    for channel in request_channels:
        db.collection('requestChannels').document(channel["requestChannelId"]).set(channel)
    print(f"{len(request_channels)}件の追加受付チャネルデータを作成しました。")
    
    # 追加対応分類
    response_categories_data = [
        {"responseCategoryId": "resp4", "name": "デザイン検討必要", "parentCategory": "UX改修依頼", "orderNo": 2, "createdAt": datetime.datetime.now(datetime.timezone.utc), "updatedAt": datetime.datetime.now(datetime.timezone.utc)}
    ]
    
    for category in response_categories_data:
        db.collection('responseCategories').document(category["responseCategoryId"]).set(category)
    print(f"{len(response_categories_data)}件の追加対応分類データを作成しました。")
    
    print("追加マスターデータの作成が完了しました。")

def get_next_ticket_id(db):
    """次のチケットIDを生成する"""
    counter_ref = db.collection('counters').document('tickets')
    counter_doc = counter_ref.get()
    
    if counter_doc.exists:
        current_count = counter_doc.to_dict().get('count', 0)
        next_count = current_count + 1
        # フォーマット: TCK-XXXX (4桁のゼロ埋め)
        return f"TCK-{next_count:04d}", next_count
    else:
        # カウンターが存在しない場合は新規作成
        next_count = 4  # 既存のサンプルが3つなので4から開始
        return f"TCK-{next_count:04d}", next_count

def update_ticket_counter(db, count):
    """チケット採番用カウンターを更新"""
    db.collection('counters').document('tickets').set({'count': count})

def generate_ticket(db, ticket_id, category_id, category_name, category_detail_id, category_detail_name, 
                  status_id, status_name, days_ago_created, days_to_deadline, 
                  summary, description, requestor_id="user3", person_in_charge_id="user1", 
                  request_channel_id="ch1", completed=False, has_defect=False):
    """チケットデータを生成する"""
    today = datetime.datetime.now(datetime.timezone.utc)
    reception_date = today - datetime.timedelta(days=days_ago_created)
    scheduled_completion_date = today + datetime.timedelta(days=days_to_deadline)
    
    # ユーザー情報マッピング
    user_info = {
        "user1": {"name": "山田 太郎"},
        "user2": {"name": "鈴木 花子"},
        "user3": {"name": "佐藤 次郎"},
        "user4": {"name": "高橋 三郎"},
        "user5": {"name": "上司 進"}
    }
    
    # アカウント情報マッピング
    account_info = {
        "acc1": {"name": "株式会社ABC"},
        "acc2": {"name": "XYZ株式会社"},
        "acc3": {"name": "123株式会社"}
    }
    
    # チャネル情報マッピング
    channel_info = {
        "ch1": {"name": "Email"},
        "ch2": {"name": "電話"},
        "ch3": {"name": "Teams"},
        "ch4": {"name": "Chat/LLM"}
    }
    
    # ランダムにアカウントを選択
    account_id = random.choice(list(account_info.keys()))
    
    ticket = {
        "ticketId": ticket_id,
        "receptionDateTime": reception_date,
        "requestorId": requestor_id,
        "requestorName": user_info[requestor_id]["name"],
        "accountId": account_id,
        "accountName": account_info[account_id]["name"],
        "categoryId": category_id,
        "categoryName": category_name,
        "categoryDetailId": category_detail_id,
        "categoryDetailName": category_detail_name,
        "requestChannelId": request_channel_id,
        "requestChannelName": channel_info[request_channel_id]["name"],
        "summary": summary,
        "description": description,
        "attachments": [],
        "personInChargeId": person_in_charge_id,
        "personInChargeName": user_info[person_in_charge_id]["name"],
        "statusId": status_id,
        "statusName": status_name,
        "scheduledCompletionDate": scheduled_completion_date,
        "completionDate": today - datetime.timedelta(days=1) if completed else None,
        "actualEffortHours": random.uniform(1.0, 8.0) if completed else None,
        "responseCategoryId": None,
        "responseCategoryName": None,
        "responseDetails": None,
        "hasDefect": has_defect,
        "externalTicketId": f"EXT-{random.randint(1000, 9999)}" if random.random() > 0.7 else "",
        "remarks": "",
        "createdAt": reception_date,
        "updatedAt": reception_date,
        "history": [
            {
                "timestamp": reception_date,
                "userId": person_in_charge_id,
                "userName": user_info[person_in_charge_id]["name"],
                "changedFields": [],
                "comment": "新規チケット作成"
            }
        ]
    }
    
    # 状態が「対応中」または「確認中」の場合、ステータス変更履歴を追加
    if status_id in ["stat2", "stat3"]:
        status_change_date = reception_date + datetime.timedelta(days=1)
        initial_status = "stat1"  # 初期状態は「受付済」
        initial_status_name = "受付済"
        
        ticket["history"].append({
            "timestamp": status_change_date,
            "userId": person_in_charge_id,
            "userName": user_info[person_in_charge_id]["name"],
            "changedFields": [
                {
                    "field": "status",
                    "oldValue": initial_status_name,
                    "newValue": status_name
                }
            ],
            "comment": "対応を開始しました。" if status_id == "stat2" else "確認作業を開始しました。"
        })
        ticket["updatedAt"] = status_change_date
    
    # 状態が「完了」の場合、完了履歴を追加
    if completed:
        completion_date = today - datetime.timedelta(days=1)
        previous_status = "stat3" if random.random() > 0.5 else "stat2"
        previous_status_name = "確認中" if previous_status == "stat3" else "対応中"
        
        ticket["history"].append({
            "timestamp": completion_date,
            "userId": person_in_charge_id,
            "userName": user_info[person_in_charge_id]["name"],
            "changedFields": [
                {
                    "field": "status",
                    "oldValue": previous_status_name,
                    "newValue": "完了"
                }
            ],
            "comment": "対応が完了しました。"
        })
        ticket["updatedAt"] = completion_date
        
        # ランダムに対応分類を設定
        response_categories = [
            {"id": "resp1", "name": "Japanから回答可"},
            {"id": "resp2", "name": "無償対応"},
            {"id": "resp3", "name": "開発修正対応"},
            {"id": "resp4", "name": "デザイン検討必要"}
        ]
        selected_response = random.choice(response_categories)
        ticket["responseCategoryId"] = selected_response["id"]
        ticket["responseCategoryName"] = selected_response["name"]
        ticket["responseDetails"] = "調査および対応の結果、問題を解決しました。" if not has_defect else "修正プログラムをリリースしました。"
    
    # 添付ファイルを追加するケース (20%の確率)
    if random.random() < 0.2:
        attachment_types = ["screenshot.png", "error_log.txt", "report.pdf", "manual.docx"]
        attachment_file = random.choice(attachment_types)
        ticket["attachments"].append({
            "fileName": f"{ticket_id}_{attachment_file}",
            "fileUrl": f"https://example.com/storage/{ticket_id}/{attachment_file}",
            "uploadedAt": reception_date
        })
    
    return ticket

def create_demo_tickets(db, count=30):
    """デモ用のサンプルチケットを作成"""
    print(f"デモ用の追加サンプルチケット {count}件 を作成します...")
    
    # カテゴリとステータスの組み合わせを満遍なく含むようにする
    categories = [
        {"id": "cat1", "name": "問合せ", "details": [
            {"id": "catd1", "name": "ポータル・記事・検索機能に関する問合せ"},
            {"id": "catd2", "name": "サポート管理に関する問合せ"}
        ]},
        {"id": "cat2", "name": "データ修正依頼", "details": [
            {"id": "catd3", "name": "マスターデータ修正依頼"}
        ]},
        {"id": "cat3", "name": "障害報告", "details": [
            {"id": "catd4", "name": "システム障害"}
        ]},
        {"id": "cat4", "name": "UX改修依頼", "details": [
            {"id": "catd5", "name": "UI/UX改善提案"},
            {"id": "catd6", "name": "検索機能改善提案"}
        ]}
    ]
    
    statuses = [
        {"id": "stat1", "name": "受付済"},
        {"id": "stat2", "name": "対応中"},
        {"id": "stat3", "name": "確認中"},
        {"id": "stat4", "name": "完了"}
    ]
    
    # デモで使うサンプルチケット (検索関連の特定のキーワードを含む)
    search_related_tickets = [
        {
            "summary": "全文検索が一部ヒットしない",
            "description": "全文検索機能を使用した際に、特定のキーワードが含まれているはずの記事がヒットしません。\n再現手順：\n1. 検索ボックスに「運用マニュアル」と入力\n2. 検索ボタンをクリック\n3. 「運用マニュアル」という単語を含む記事が検索結果に表示されない",
            "category_id": "cat1",
            "category_detail_id": "catd1",
            "days_ago": 2,
            "days_to_deadline": 5,
            "has_defect": True
        },
        {
            "summary": "検索結果の並び順をカスタマイズしたい",
            "description": "検索結果が現在は日付順に表示されていますが、関連度順やカテゴリ別などでの並べ替えができるようにしたいです。\nユーザーからのフィードバックとして「探しているものが見つけづらい」という声があります。",
            "category_id": "cat4",
            "category_detail_id": "catd6",
            "days_ago": 7,
            "days_to_deadline": 14,
            "has_defect": False
        },
        {
            "summary": "検索機能のパフォーマンスが低下",
            "description": "先週のアップデート以降、検索機能の応答速度が著しく低下しています。\n特に大量の検索結果が返される場合に10秒以上かかることがあります。\nAPMツールのログも添付します。",
            "category_id": "cat3",
            "category_detail_id": "catd4",
            "days_ago": 3,
            "days_to_deadline": 1,
            "has_defect": True
        },
        {
            "summary": "検索機能に関するユーザー調査の依頼",
            "description": "現在の検索機能について、ユーザーの利用状況や改善要望を把握するためのアンケート調査を実施したいと考えています。\n調査項目の設計や実施方法についてアドバイスをいただけないでしょうか。",
            "category_id": "cat1",
            "category_detail_id": "catd2",
            "days_ago": 10,
            "days_to_deadline": 20,
            "has_defect": False
        }
    ]
    
    # チケットのサンプル説明テンプレート
    description_templates = [
        "ユーザーから{0}について問い合わせがありました。具体的には、{1}という点について詳細を確認したいとのことです。",
        "{0}に関する問題が報告されています。症状としては、{1}という現象が発生しています。",
        "{0}機能について改善リクエストがあります。現状では{1}ですが、これを改善してほしいとの要望です。",
        "{0}の使用中に問題が発生したとの報告がありました。{1}の状況で再現するようです。",
        "{0}に関する情報を更新してほしいとの依頼がありました。具体的には{1}の部分を修正する必要があります。"
    ]
    
    # チケットのサンプルトピックと詳細
    ticket_topics = [
        {"topic": "ログイン機能", "details": "パスワードを忘れた場合のリセット方法"},
        {"topic": "ダッシュボード", "details": "表示されるグラフの期間設定方法"},
        {"topic": "ユーザー管理", "details": "アカウント情報の一括更新方法"},
        {"topic": "レポート機能", "details": "カスタムレポートの作成手順"},
        {"topic": "データエクスポート", "details": "CSVダウンロード時のエンコード設定"},
        {"topic": "アクセス権限", "details": "特定ページへのアクセス制限設定"},
        {"topic": "通知設定", "details": "メール通知の頻度変更方法"},
        {"topic": "API連携", "details": "サードパーティツールとの連携手順"},
        {"topic": "セキュリティ設定", "details": "二段階認証の有効化方法"},
        {"topic": "モバイル対応", "details": "スマートフォン表示時のレイアウト崩れ"}
    ]
    
    # チケットのリストを初期化
    tickets = []
    
    # まず検索関連の特定チケットを追加
    for i, ticket_data in enumerate(search_related_tickets):
        ticket_id, next_count = get_next_ticket_id(db)
        
        # カテゴリ情報を取得
        category = next((c for c in categories if c["id"] == ticket_data["category_id"]), None)
        category_detail = next((d for d in category["details"] if d["id"] == ticket_data["category_detail_id"]), None)
        
        # ステータスをランダムに選択（完了のステータスは一部のみ）
        status = random.choice(statuses)
        is_completed = status["id"] == "stat4"
        
        # チケットを生成
        ticket = generate_ticket(
            db=db,
            ticket_id=ticket_id,
            category_id=category["id"],
            category_name=category["name"],
            category_detail_id=category_detail["id"],
            category_detail_name=category_detail["name"],
            status_id=status["id"],
            status_name=status["name"],
            days_ago_created=ticket_data["days_ago"],
            days_to_deadline=ticket_data["days_to_deadline"],
            summary=ticket_data["summary"],
            description=ticket_data["description"],
            requestor_id=random.choice(["user3", "user4"]),
            person_in_charge_id=random.choice(["user1", "user2"]),
            request_channel_id=random.choice(["ch1", "ch2", "ch3", "ch4"]),
            completed=is_completed,
            has_defect=ticket_data["has_defect"]
        )
        
        # チケットをリストに追加
        tickets.append(ticket)
        update_ticket_counter(db, next_count)
    
    # 残りのチケットをランダムに生成
    remaining_count = count - len(search_related_tickets)
    for i in range(remaining_count):
        ticket_id, next_count = get_next_ticket_id(db)
        
        # カテゴリとカテゴリ詳細をランダムに選択
        category = random.choice(categories)
        category_detail = random.choice(category["details"])
        
        # ステータスをランダムに選択（完了のステータスは30%程度に）
        status = random.choice(statuses) if random.random() > 0.3 else statuses[3]  # statuses[3]は完了
        is_completed = status["id"] == "stat4"
        
        # チケットの内容をランダムに生成
        topic = random.choice(ticket_topics)
        description_template = random.choice(description_templates)
        description = description_template.format(topic["topic"], topic["details"])
        summary = f"{topic['topic']}に関する{category['name']}"
        
        # 対応開始からの経過日数をランダムに設定
        days_ago = random.randint(1, 30)
        
        # 対応予定日までの日数を設定（受付からの日数に応じて変動、完了済みは過去の日付）
        if is_completed:
            days_to_deadline = -random.randint(1, 5)  # 過去の日付
        else:
            days_to_deadline = random.randint(1, 15)  # 未来の日付
        
        # チケットを生成
        ticket = generate_ticket(
            db=db,
            ticket_id=ticket_id,
            category_id=category["id"],
            category_name=category["name"],
            category_detail_id=category_detail["id"],
            category_detail_name=category_detail["name"],
            status_id=status["id"],
            status_name=status["name"],
            days_ago_created=days_ago,
            days_to_deadline=days_to_deadline,
            summary=summary,
            description=description,
            requestor_id=random.choice(["user3", "user4"]),
            person_in_charge_id=random.choice(["user1", "user2"]),
            request_channel_id=random.choice(["ch1", "ch2", "ch3", "ch4"]),
            completed=is_completed,
            has_defect=random.random() < 0.2  # 20%の確率で不具合あり
        )
        
        # チケットをリストに追加
        tickets.append(ticket)
        update_ticket_counter(db, next_count)
    
    # Firestoreにチケットを登録
    batch_size = 20  # Firestoreの書き込み制限に配慮
    for i in range(0, len(tickets), batch_size):
        batch = db.batch()
        batch_tickets = tickets[i:i+batch_size]
        
        for ticket in batch_tickets:
            batch.set(db.collection('tickets').document(ticket["ticketId"]), ticket)
        
        batch.commit()
        print(f"チケットバッチ {i//batch_size + 1}/{(len(tickets) - 1)//batch_size + 1} を登録しました。")
    
    print(f"{len(tickets)}件のデモ用サンプルチケットを作成しました。")

def create_sample_attachments(db):
    """サンプル添付ファイルデータを作成"""
    # 簡易的なCloud Storageシミュレーション関数
    def generate_signed_url(ticket_id, file_name):
        return f"https://storage.example.com/mcp-attachments/{ticket_id}/{file_name}?token=sample"
    
    # いくつかのチケットに添付ファイルを追加
    ticket_ids = ["TCK-0001", "TCK-0003"]
    attachments = [
        {"ticketId": "TCK-0001", "fileName": "検索機能障害報告書.pdf", "description": "検索機能の詳細な調査レポート"},
        {"ticketId": "TCK-0001", "fileName": "error_screenshot.png", "description": "エラー画面のスクリーンショット"},
        {"ticketId": "TCK-0003", "fileName": "dashboard_error.jpg", "description": "ダッシュボードエラーの画像"},
        {"ticketId": "TCK-0003", "fileName": "system_logs.txt", "description": "障害発生時のシステムログ"}
    ]
    
    for attachment in attachments:
        ticket_id = attachment["ticketId"]
        ticket_ref = db.collection('tickets').document(ticket_id)
        ticket_doc = ticket_ref.get()
        
        if ticket_doc.exists:
            ticket_data = ticket_doc.to_dict()
            now = datetime.datetime.now(datetime.timezone.utc)
            
            new_attachment = {
                "fileName": attachment["fileName"],
                "fileUrl": generate_signed_url(ticket_id, attachment["fileName"]),
                "uploadedAt": now,
                "description": attachment.get("description", "")
            }
            
            # 既存の添付ファイルリストに追加
            current_attachments = ticket_data.get("attachments", [])
            current_attachments.append(new_attachment)
            
            # チケットを更新
            ticket_ref.update({
                "attachments": current_attachments,
                "updatedAt": now,
                "history": ticket_data.get("history", []) + [{
                    "timestamp": now,
                    "userId": "user1",
                    "userName": "山田 太郎",
                    "changedFields": [],
                    "comment": f"添付ファイル「{attachment['fileName']}」を追加しました。"
                }]
            })
    
    print(f"{len(attachments)}件のサンプル添付ファイルデータを追加しました。")

def main():
    parser = argparse.ArgumentParser(description='デモ用追加サンプルデータ生成スクリプト')
    parser.add_argument('--master-only', action='store_true', help='追加マスターデータのみを作成')
    parser.add_argument('--tickets-only', action='store_true', help='追加サンプルチケットのみを作成')
    parser.add_argument('--count', type=int, default=30, help='作成するサンプルチケットの数 (デフォルト: 30)')
    args = parser.parse_args()
    
    # Firestore初期化
    print("Firestoreの初期化を開始します...")
    db = init_firebase()
    print("Firestoreの初期化が完了しました。データベースクライアントを取得しました。")
    
    if args.tickets_only:
        print(f"追加サンプルチケットのみを作成します... (件数: {args.count})")
        create_demo_tickets(db, args.count)
        create_sample_attachments(db)
    elif args.master_only:
        print("追加マスターデータのみを作成します...")
        create_additional_master_data(db)
    else:
        print(f"追加マスターデータとサンプルチケットを作成します... (チケット件数: {args.count})")
        create_additional_master_data(db)
        create_demo_tickets(db, args.count)
        create_sample_attachments(db)
    
    print("すべての処理が完了しました。")

if __name__ == "__main__":
    main()