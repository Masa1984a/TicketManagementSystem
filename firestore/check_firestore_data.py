"""
Firestoreデータ確認スクリプト

このスクリプトは、Firestoreのデータを確認するためのユーティリティです。
マスターデータやチケットの件数を表示します。
"""

import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import os
import argparse
from prettytable import PrettyTable
from collections import Counter

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

def show_collection_summary(db):
    """コレクションごとのドキュメント数を表示"""
    collections = [
        "users",
        "accounts",
        "categories",
        "categoryDetails", 
        "statuses",
        "requestChannels",
        "responseCategories",
        "tickets",
        "counters"
    ]
    
    table = PrettyTable()
    table.field_names = ["コレクション名", "ドキュメント数"]
    
    for collection_name in collections:
        docs = db.collection(collection_name).stream()
        count = len(list(docs))
        table.add_row([collection_name, count])
    
    print("\n=== コレクション概要 ===")
    print(table)

def show_ticket_stats(db):
    """チケット統計情報を表示"""
    tickets = list(db.collection('tickets').stream())
    
    if not tickets:
        print("チケットデータが存在しません。")
        return
    
    # カテゴリ別件数
    category_counter = Counter()
    # ステータス別件数
    status_counter = Counter()
    # 担当者別件数
    person_counter = Counter()
    # 対応予定日の分布
    deadline_count = {"期限切れ": 0, "本日期限": 0, "1日以内": 0, "7日以内": 0, "8日以上": 0}
    
    today = datetime.datetime.now(datetime.timezone.utc).date()
    
    for ticket_doc in tickets:
        ticket = ticket_doc.to_dict()
        
        # カテゴリ集計
        category_counter[ticket.get("categoryName", "不明")] += 1
        
        # ステータス集計
        status_counter[ticket.get("statusName", "不明")] += 1
        
        # 担当者集計
        person_counter[ticket.get("personInChargeName", "不明")] += 1
        
        # 対応予定日集計
        if "scheduledCompletionDate" in ticket and ticket["scheduledCompletionDate"]:
            scheduled_date = ticket["scheduledCompletionDate"].date()
            days_diff = (scheduled_date - today).days
            
            if days_diff < 0:
                deadline_count["期限切れ"] += 1
            elif days_diff == 0:
                deadline_count["本日期限"] += 1
            elif days_diff <= 1:
                deadline_count["1日以内"] += 1
            elif days_diff <= 7:
                deadline_count["7日以内"] += 1
            else:
                deadline_count["8日以上"] += 1
    
    # カテゴリ別表示
    category_table = PrettyTable()
    category_table.field_names = ["カテゴリ", "件数"]
    for category, count in category_counter.most_common():
        category_table.add_row([category, count])
    
    # ステータス別表示
    status_table = PrettyTable()
    status_table.field_names = ["ステータス", "件数"]
    for status, count in status_counter.most_common():
        status_table.add_row([status, count])
    
    # 担当者別表示
    person_table = PrettyTable()
    person_table.field_names = ["担当者", "件数"]
    for person, count in person_counter.most_common():
        person_table.add_row([person, count])
    
    # 対応予定日表示
    deadline_table = PrettyTable()
    deadline_table.field_names = ["期限", "件数"]
    for deadline, count in deadline_count.items():
        deadline_table.add_row([deadline, count])
    
    print("\n=== チケット統計 (合計: {}件) ===".format(len(tickets)))
    print("\n--- カテゴリ別件数 ---")
    print(category_table)
    print("\n--- ステータス別件数 ---")
    print(status_table)
    print("\n--- 担当者別件数 ---")
    print(person_table)
    print("\n--- 対応予定日分布 ---")
    print(deadline_table)

def show_search_related_tickets(db):
    """検索機能関連のチケットを表示"""
    query = db.collection('tickets').where('summary', '>=', '検索').where('summary', '<=', '検索' + '\uf8ff').stream()
    tickets = list(query)
    
    if not tickets:
        print("検索機能関連のチケットが見つかりませんでした。")
        return
    
    table = PrettyTable()
    table.field_names = ["チケットID", "概要", "ステータス", "対応予定日", "担当者"]
    
    for ticket_doc in tickets:
        ticket = ticket_doc.to_dict()
        scheduled_date = ticket.get("scheduledCompletionDate", None)
        scheduled_date_str = scheduled_date.strftime("%Y-%m-%d") if scheduled_date else "-"
        
        table.add_row([
            ticket.get("ticketId", "-"),
            ticket.get("summary", "-"),
            ticket.get("statusName", "-"),
            scheduled_date_str,
            ticket.get("personInChargeName", "-")
        ])
    
    print("\n=== 検索機能関連のチケット ===")
    print(table)

def main():
    parser = argparse.ArgumentParser(description='Firestoreデータ確認スクリプト')
    parser.add_argument('--tickets', action='store_true', help='チケット統計を詳細表示')
    parser.add_argument('--search', action='store_true', help='検索機能関連のチケットを表示')
    args = parser.parse_args()
    
    # Firestore初期化
    db = init_firebase()
    
    # コレクション概要を表示
    show_collection_summary(db)
    
    # チケット統計表示
    if args.tickets:
        show_ticket_stats(db)
    
    # 検索関連チケット表示
    if args.search:
        show_search_related_tickets(db)

if __name__ == "__main__":
    main()