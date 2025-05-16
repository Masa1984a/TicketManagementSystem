"""
MCP Server for Ticket Management System
This server connects Claude for desktop to Firebase Firestore database
for ticket management operations.
"""
import sys
import os
import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from mcp.server.fastmcp import FastMCP, Context, Image # Imageは未使用なら削除可
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union # Unionは未使用なら削除可

# Firebase initialization and AppContext definition
@dataclass
class AppContext:
    db: firestore.Client

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage Firebase connection lifecycle"""
    try:
        firebase_admin.get_app()
    except ValueError:
        cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'firebase-credentials.json')
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print(f"認証情報ファイル '{cred_path}' を使用してFirebaseアプリを初期化しました。 (lifespan)")
        else:
            print(f"警告: 認証情報ファイル '{cred_path}' が見つかりませんでした。(lifespan)")
            firebase_admin.initialize_app() # デフォルト認証を試みる
            print("アプリケーションのデフォルト認証情報を使用してFirebaseアプリを初期化しました。 (lifespan)")
    
    target_database_id = "mcp-status-test" # 接続したいデータベースID
    print(f"FirestoreクライアントをデータベースID '{target_database_id}' で取得します。 (lifespan)")
    db = firestore.client(database_id=target_database_id) 
    try:
        yield AppContext(db=db)
    finally:
        pass # Cleanup if needed

# Configure MCP server with lifespan
mcp = FastMCP("Ticket Management System", lifespan=app_lifespan) # ここで一度だけ初期化

# === Tools ===

@mcp.tool(description="チケット一覧を取得する - 検索条件に応じてチケットのリストを表示")
def get_ticket_list(
    personInChargeId: Optional[str] = None,
    accountId: Optional[str] = None,
    statusId: Optional[str] = None,
    scheduledCompletionDateFrom: Optional[str] = None,
    scheduledCompletionDateTo: Optional[str] = None,
    showCompleted: Optional[bool] = False,
    searchQuery: Optional[str] = None,
    sortBy: str = "receptionDateTime",
    sortOrder: str = "desc",
    limit: int = 20,
    offset: int = 0,
    ctx: Context = None
) -> str:
    """
    チケット一覧を検索条件に基づいて取得し、表形式で表示する

    Parameters:
    - personInChargeId: 担当者IDで絞り込み（指定がない場合は全担当者）
    - accountId: アカウントIDで絞り込み（指定がない場合は全アカウント）
    - statusId: ステータスIDで絞り込み（指定がない場合は全ステータス）
    - scheduledCompletionDateFrom: 対応予定日の開始日（YYYY-MM-DD形式）
    - scheduledCompletionDateTo: 対応予定日の終了日（YYYY-MM-DD形式）
    - showCompleted: 完了済みのチケットを表示するかどうか（デフォルト: False）
    - searchQuery: 検索キーワード（概要、アカウント名、リクエスタ名から検索）
    - sortBy: 並び替えるフィールド（デフォルト: "receptionDateTime"）
    - sortOrder: 並び替え順序（"asc" または "desc"、デフォルト: "desc"）
    - limit: 取得する最大件数（デフォルト: 20）
    - offset: 開始位置（ページネーション用、デフォルト: 0）

    Returns:
    - チケット一覧のMarkdown形式テーブル

    使用例:
    1. すべてのチケットを表示: get_ticket_list()
    2. 特定担当者のチケット: get_ticket_list(personInChargeId="user1")
    3. キーワード検索: get_ticket_list(searchQuery="エラー")
    4. 日付範囲指定: get_ticket_list(scheduledCompletionDateFrom="2023-01-01", scheduledCompletionDateTo="2023-12-31")
    """
    # Get Firestore database
    db = ctx.request_context.lifespan_context.db

    # Base query
    query = db.collection('tickets')

    # Apply filters
    if personInChargeId:
        query = query.where('personInChargeId', '==', personInChargeId)

    if accountId:
        query = query.where('accountId', '==', accountId)

    if statusId:
        query = query.where('statusId', '==', statusId)

    # Date filters
    if scheduledCompletionDateFrom:
        from_date = datetime.datetime.fromisoformat(scheduledCompletionDateFrom)
        query = query.where('scheduledCompletionDate', '>=', from_date)

    if scheduledCompletionDateTo:
        to_date = datetime.datetime.fromisoformat(scheduledCompletionDateTo)
        query = query.where('scheduledCompletionDate', '<=', to_date)

    # Show/hide completed tickets
    if not showCompleted:
        # Get completed status IDs
        completed_statuses = db.collection('statuses').where('name', '==', '完了').get()
        completed_status_ids = [status.id for status in completed_statuses]

        if completed_status_ids:
            # Using "not-in" filter (note: has limitations in Firestore)
            query = query.where('statusId', 'not-in', completed_status_ids)

    # Apply sorting
    if sortBy and sortOrder:
        direction = firestore.Query.DESCENDING if sortOrder.lower() == 'desc' else firestore.Query.ASCENDING
        query = query.order_by(sortBy, direction=direction)

    # Execute query
    results = query.limit(limit).offset(offset).get()

    # Process results
    tickets = []
    for doc in results:
        ticket = doc.to_dict()

        # Calculate remaining days for scheduled completion
        remaining_days = None
        if ticket.get('scheduledCompletionDate'):
            scheduled_date = ticket['scheduledCompletionDate']
            today = datetime.datetime.now().date()
            remaining_days = (scheduled_date.date() - today).days

        # Format dates for display
        reception_date = ticket.get('receptionDateTime')
        reception_date_str = reception_date.strftime('%Y-%m-%d %H:%M') if reception_date else None

        scheduled_date = ticket.get('scheduledCompletionDate')
        scheduled_date_str = scheduled_date.strftime('%Y-%m-%d') if scheduled_date else None

        # Add ticket to result list
        tickets.append({
            'ticketId': ticket.get('ticketId'),
            'receptionDateTime': reception_date_str,
            'requestorName': ticket.get('requestorName'),
            'accountName': ticket.get('accountName'),
            'categoryName': ticket.get('categoryName'),
            'categoryDetailName': ticket.get('categoryDetailName'),
            'summary': ticket.get('summary'),
            'personInChargeName': ticket.get('personInChargeName'),
            'statusName': ticket.get('statusName'),
            'scheduledCompletionDate': scheduled_date_str,
            'remainingDays': remaining_days,
            'externalTicketId': ticket.get('externalTicketId')
        })

    # For text search (client-side filtering)
    if searchQuery:
        search_terms = searchQuery.lower().split()
        filtered_tickets = []

        for ticket in tickets:
            text = f"{ticket.get('summary', '')} {ticket.get('accountName', '')} {ticket.get('requestorName', '')}".lower()
            if all(term in text for term in search_terms):
                filtered_tickets.append(ticket)

        tickets = filtered_tickets

    # Convert to formatted output
    # In a production app, consider using a proper templating system
    if not tickets:
        return "対象のチケットは見つかりませんでした。"

    # Format as a table
    output = "# チケット一覧\n\n"
    output += "| ID | 受付日時 | アカウント/リクエスタ | カテゴリ/詳細 | 概要 | 担当者 | ステータス | 対応予定日/残 |\n"
    output += "|---|---|---|---|---|---|---|---|\n"

    for t in tickets:
        remaining = f"あと{t['remainingDays']}日" if t['remainingDays'] is not None else ""
        scheduled = f"{t['scheduledCompletionDate']} {remaining}" if t['scheduledCompletionDate'] else ""

        output += f"| {t['ticketId']} | {t['receptionDateTime']} | {t['accountName']}/{t['requestorName']} | "
        output += f"{t['categoryName']}/{t['categoryDetailName']} | {t['summary']} | "
        output += f"{t['personInChargeName']} | {t['statusName']} | {scheduled} |\n"

    return output

@mcp.tool(description="チケットの詳細情報を取得する - 特定のチケットID指定で詳細表示")
def get_ticket_detail(
    ticketId: str,
    ctx: Context = None
) -> str:
    """
    特定のチケットIDに基づいて、そのチケットの詳細情報を取得し表示する

    Parameters:
    - ticketId: 表示対象のチケットID（例: "TCK-0001"）

    Returns:
    - チケット詳細情報のMarkdown形式レポート
      - 受付内容（日時、アカウント、リクエスタ、カテゴリ、概要、詳細、添付ファイル）
      - 対応内容（担当者、対応予定日、ステータス、完了日、実績工数、対応分類、対応内容詳細）
      - 対応履歴（日時順のコメント履歴）

    使用例:
    1. チケット詳細表示: get_ticket_detail(ticketId="TCK-0001")

    備考:
    - 存在しないチケットIDを指定した場合は、エラーメッセージを返します
    - 対応履歴は新しい順に表示されます
    """
    # Get Firestore database
    db = ctx.request_context.lifespan_context.db

    # Get ticket reference
    ticket_ref = db.collection('tickets').document(ticketId)
    ticket_doc = ticket_ref.get()

    # Check if ticket exists
    if not ticket_doc.exists:
        return f"チケット {ticketId} は見つかりませんでした。"

    # Get ticket data
    ticket = ticket_doc.to_dict()

    # Format dates for display
    reception_date = ticket.get('receptionDateTime')
    reception_date_str = reception_date.strftime('%Y-%m-%d %H:%M') if reception_date else "未設定"

    scheduled_date = ticket.get('scheduledCompletionDate')
    scheduled_date_str = scheduled_date.strftime('%Y-%m-%d') if scheduled_date else "未設定"

    completion_date = ticket.get('completionDate')
    completion_date_str = completion_date.strftime('%Y-%m-%d') if completion_date else "未完了"

    # Format history entries
    history = ticket.get('history', [])
    history_entries = []

    for entry in history:
        timestamp = entry.get('timestamp')
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M') if timestamp else "不明"

        history_entries.append({
            'timestamp': timestamp_str,
            'userName': entry.get('userName', '不明'),
            'comment': entry.get('comment', '')
        })

    # Sort history by timestamp (newest first)
    history_entries.sort(key=lambda x: x['timestamp'], reverse=True)

    # Format as markdown
    output = f"# チケット詳細: {ticket['ticketId']}\n\n"

    output += "## 受付内容\n\n"
    output += f"- **受付日時**: {reception_date_str}\n"
    output += f"- **アカウント**: {ticket.get('accountName', '未設定')}\n"
    output += f"- **リクエスタ**: {ticket.get('requestorName', '未設定')}\n"
    output += f"- **カテゴリ**: {ticket.get('categoryName', '未設定')}\n"
    output += f"- **カテゴリ詳細**: {ticket.get('categoryDetailName', '未設定')}\n"
    output += f"- **受付チャネル**: {ticket.get('requestChannelName', '未設定')}\n"
    output += f"- **概要**: {ticket.get('summary', '未設定')}\n"
    output += f"- **詳細**:\n\n{ticket.get('description', '未設定')}\n\n"

    # Add attachments if any
    attachments = ticket.get('attachments', [])
    if attachments:
        output += "- **添付ファイル**:\n"
        for attachment in attachments:
            file_name = attachment.get('fileName', '不明なファイル')
            file_url = attachment.get('fileUrl', '#')
            output += f"  - [{file_name}]({file_url})\n"
    else:
        output += "- **添付ファイル**: なし\n"

    output += "\n## 対応内容\n\n"
    output += f"- **担当者**: {ticket.get('personInChargeName', '未設定')}\n"
    output += f"- **対応予定日**: {scheduled_date_str}\n"
    output += f"- **ステータス**: {ticket.get('statusName', '未設定')}\n"
    output += f"- **完了日**: {completion_date_str}\n"
    output += f"- **実績工数**: {ticket.get('actualEffortHours', '未設定')} 時間\n"
    output += f"- **対応分類**: {ticket.get('responseCategoryName', '未設定')}\n"

    response_details = ticket.get('responseDetails', '')
    output += "- **対応内容詳細**:\n\n"
    output += f"{response_details if response_details else '未設定'}\n\n"

    output += f"- **不具合有無**: {'あり' if ticket.get('hasDefect') else 'なし'}\n"
    output += f"- **EEPチケット**: {ticket.get('externalTicketId', '未設定')}\n"
    output += f"- **備考**: {ticket.get('remarks', '未設定')}\n\n"

    # Add history
    output += "## 対応履歴\n\n"
    if history_entries:
        for entry in history_entries:
            output += f"### {entry['timestamp']} - {entry['userName']}\n\n"
            output += f"{entry['comment']}\n\n"
    else:
        output += "履歴はありません。\n"

    return output

@mcp.tool(description="新規チケットを作成する - 必要情報を指定して新しいチケットを登録")
def create_ticket(
    receptionDateTime: str,
    requestorId: str,
    accountId: str,
    categoryId: str,
    categoryDetailId: str,
    requestChannelId: str,
    summary: str,
    description: str,
    personInChargeId: str,
    statusId: str,
    scheduledCompletionDate: Optional[str] = None,
    externalTicketId: Optional[str] = None,
    remarks: Optional[str] = None,
    attachments: Optional[List[Dict[str, str]]] = None,
    ctx: Context = None
) -> Dict[str, str]:
    """
    新しいチケットをシステムに登録する

    Parameters:
    - receptionDateTime: 受付日時（ISO 8601形式: YYYY-MM-DDThh:mm:ss）
    - requestorId: リクエスタのID（usersコレクション参照、get_usersで確認可能）
    - accountId: アカウントID（accountsコレクション参照、get_accountsで確認可能）
    - categoryId: カテゴリID（categoriesコレクション参照、get_categoriesで確認可能）
    - categoryDetailId: カテゴリ詳細ID（categoryDetailsコレクション参照、get_category_detailsで確認可能）
    - requestChannelId: 受付チャネルID（例: "ch1"=Email、"ch2"=電話、"ch3"=Teams）
    - summary: チケットの概要（タイトル）
    - description: チケットの詳細内容
    - personInChargeId: 担当者ID（usersコレクション参照、get_usersで確認可能）
    - statusId: ステータスID（statusesコレクション参照、get_statusesで確認可能）
    - scheduledCompletionDate: 対応予定日（ISO 8601形式: YYYY-MM-DD、省略可）
    - externalTicketId: 外部チケット番号（例: EEP番号、省略可）
    - remarks: 備考（省略可）
    - attachments: 添付ファイル情報（省略可）、以下の形式:
      [
        {"fileName": "sample.png", "fileUrl": "https://example.com/files/sample.png"}
      ]

    Returns:
    - 結果を含むディクショナリ:
      - 成功時: {"ticketId": "新しいチケットID", "message": "チケットを作成しました。(ID: チケットID)"}
      - 失敗時: {"error": "エラーメッセージ"}

    使用例:
    1. 基本的なチケット作成:
       create_ticket(
           receptionDateTime="2023-04-01T09:00:00",
           requestorId="user3",
           accountId="acc1",
           categoryId="cat1",
           categoryDetailId="catd1",
           requestChannelId="ch1",
           summary="ログイン画面でエラーが発生",
           description="ログイン画面で認証エラーが表示されます。\n再現手順: ...",
           personInChargeId="user1",
           statusId="stat1",
           scheduledCompletionDate="2023-04-10"
       )

    備考:
    - チケット番号（ticketId）は自動採番されます（"TCK-XXXX"形式）
    - 作成時の履歴に「新規チケット作成」というコメントが自動追加されます
    - 必須項目が欠けている場合はエラーが返されます
    """
    # Get Firestore database
    db = ctx.request_context.lifespan_context.db
    
    # Fetch related data for non-normalized fields
    requestor_ref = db.collection('users').document(requestorId)
    requestor_doc = requestor_ref.get()
    if not requestor_doc.exists:
        return {"error": f"Requestor with ID {requestorId} not found"}
    requestor_name = requestor_doc.to_dict().get('name', '')
    
    account_ref = db.collection('accounts').document(accountId)
    account_doc = account_ref.get()
    if not account_doc.exists:
        return {"error": f"Account with ID {accountId} not found"}
    account_name = account_doc.to_dict().get('name', '')
    
    category_ref = db.collection('categories').document(categoryId)
    category_doc = category_ref.get()
    if not category_doc.exists:
        return {"error": f"Category with ID {categoryId} not found"}
    category_name = category_doc.to_dict().get('name', '')
    
    category_detail_ref = db.collection('categoryDetails').document(categoryDetailId)
    category_detail_doc = category_detail_ref.get()
    if not category_detail_doc.exists:
        return {"error": f"Category detail with ID {categoryDetailId} not found"}
    category_detail_name = category_detail_doc.to_dict().get('name', '')
    
    request_channel_ref = db.collection('requestChannels').document(requestChannelId)
    request_channel_doc = request_channel_ref.get()
    if not request_channel_doc.exists:
        return {"error": f"Request channel with ID {requestChannelId} not found"}
    request_channel_name = request_channel_doc.to_dict().get('name', '')
    
    person_in_charge_ref = db.collection('users').document(personInChargeId)
    person_in_charge_doc = person_in_charge_ref.get()
    if not person_in_charge_doc.exists:
        return {"error": f"Person in charge with ID {personInChargeId} not found"}
    person_in_charge_name = person_in_charge_doc.to_dict().get('name', '')
    
    status_ref = db.collection('statuses').document(statusId)
    status_doc = status_ref.get()
    if not status_doc.exists:
        return {"error": f"Status with ID {statusId} not found"}
    status_name = status_doc.to_dict().get('name', '')
    
    # Generate ticket number
    # In a production system, you might want to use a transaction to ensure uniqueness
    tickets_ref = db.collection('tickets')
    ticket_count_doc = db.collection('counters').document('tickets')
    
    # Use a transaction to atomically update the counter
    transaction = db.transaction()
    
    @firestore.transactional
    def create_ticket_in_transaction(transaction, ticket_count_ref):
        ticket_count_snapshot = ticket_count_ref.get(transaction=transaction)
        current_count = 1
        
        if ticket_count_snapshot.exists:
            current_count = ticket_count_snapshot.get('count') + 1
        
        transaction.set(ticket_count_ref, {'count': current_count})
        
        # Format ticket ID (eg. TCK-0001)
        ticket_id = f"TCK-{current_count:04d}"
        
        # Prepare ticket data
        now = datetime.datetime.now()
        reception_datetime = datetime.datetime.fromisoformat(receptionDateTime)
        scheduled_completion_date = datetime.datetime.fromisoformat(scheduledCompletionDate) if scheduledCompletionDate else None
        
        ticket_data = {
            'ticketId': ticket_id,
            'receptionDateTime': reception_datetime,
            'requestorId': requestorId,
            'requestorName': requestor_name,
            'accountId': accountId,
            'accountName': account_name,
            'categoryId': categoryId,
            'categoryName': category_name,
            'categoryDetailId': categoryDetailId,
            'categoryDetailName': category_detail_name,
            'requestChannelId': requestChannelId,
            'requestChannelName': request_channel_name,
            'summary': summary,
            'description': description,
            'attachments': attachments or [],
            'personInChargeId': personInChargeId,
            'personInChargeName': person_in_charge_name,
            'statusId': statusId,
            'statusName': status_name,
            'scheduledCompletionDate': scheduled_completion_date,
            'completionDate': None,
            'actualEffortHours': None,
            'responseCategoryId': None,
            'responseCategoryName': None,
            'responseDetails': None,
            'hasDefect': False,
            'externalTicketId': externalTicketId,
            'remarks': remarks,
            'createdAt': now,
            'updatedAt': now,
            'history': [
                {
                    'timestamp': now,
                    'userId': personInChargeId,
                    'userName': person_in_charge_name,
                    'changedFields': [],
                    'comment': '新規チケット作成'
                }
            ]
        }
        
        # Create new ticket document
        transaction.set(tickets_ref.document(ticket_id), ticket_data)
        return ticket_id
    
    # Execute the transaction
    ticket_id = create_ticket_in_transaction(transaction, ticket_count_doc)
    
    # Return success response
    return {
        "ticketId": ticket_id,
        "message": f"チケットを作成しました。(ID: {ticket_id})"
    }

@mcp.tool(description="既存チケットを更新する - チケットIDと更新内容を指定してチケット情報を更新")
def update_ticket(
    ticketId: str,
    updatedFields: Dict[str, Any],
    changeLog: Optional[Dict[str, str]] = None,
    ctx: Context = None
) -> Dict[str, str]:
    """
    既存のチケット情報を更新する

    Parameters:
    - ticketId: 更新対象のチケットID（例: "TCK-0001"）
    - updatedFields: 更新するフィールドのディクショナリ
      {
        "summary": "更新されたタイトル",
        "description": "更新された詳細内容",
        "personInChargeId": "user2",
        "statusId": "stat2",
        "scheduledCompletionDate": "2023-05-15",
        "completionDate": "2023-05-10",
        "actualEffortHours": 5.5,
        "responseCategoryId": "resp1",
        "responseDetails": "対応内容の詳細",
        "hasDefect": true,
        "remarks": "備考",
        "externalTicketId": "EXT-456"
      }
    - changeLog: 変更に関するログ情報（省略可）
      {
        "userId": "更新者のユーザーID",
        "comment": "更新コメント"
      }

    Returns:
    - 結果を含むディクショナリ:
      - 成功時: {"ticketId": "更新したチケットID", "message": "チケットを更新しました。(ID: チケットID)"}
      - 失敗時: {"error": "エラーメッセージ"}

    使用例:
    1. ステータスと担当者の更新:
       update_ticket(
           ticketId="TCK-0001",
           updatedFields={
               "statusId": "stat2",
               "personInChargeId": "user2"
           },
           changeLog={
               "userId": "user1",
               "comment": "新担当者に引き継ぎました"
           }
       )

    2. 完了処理:
       update_ticket(
           ticketId="TCK-0001",
           updatedFields={
               "statusId": "stat4",
               "completionDate": "2023-05-10",
               "actualEffortHours": 3.5,
               "responseCategoryId": "resp1",
               "responseDetails": "問題を特定し修正を完了しました"
           },
           changeLog={
               "userId": "user2",
               "comment": "対応完了"
           }
       )

    備考:
    - 存在しないチケットIDを指定した場合はエラー
    - 更新されたフィールドのみ変更され、指定されていないフィールドは変更されません
    - 更新履歴は自動的に記録され、変更前と変更後の値が保存されます
    - changeLogを省略した場合、デフォルトで「情報更新」というコメントで履歴に追加されます
    """
    # Get Firestore database
    db = ctx.request_context.lifespan_context.db
    
    # Get ticket reference
    ticket_ref = db.collection('tickets').document(ticketId)
    ticket_doc = ticket_ref.get()
    
    # Check if ticket exists
    if not ticket_doc.exists:
        return {"error": f"Ticket with ID {ticketId} not found"}
    
    # Get current ticket data
    ticket_data = ticket_doc.to_dict()
    
    # Prepare update data
    update_data = {}
    changed_fields = []
    
    # Handle each updatable field
    if 'summary' in updatedFields:
        update_data['summary'] = updatedFields['summary']
        changed_fields.append({
            'field': 'summary',
            'oldValue': ticket_data.get('summary'),
            'newValue': updatedFields['summary']
        })
    
    if 'description' in updatedFields:
        update_data['description'] = updatedFields['description']
        changed_fields.append({
            'field': 'description',
            'oldValue': ticket_data.get('description'),
            'newValue': updatedFields['description']
        })
    
    if 'personInChargeId' in updatedFields:
        person_id = updatedFields['personInChargeId']
        person_ref = db.collection('users').document(person_id)
        person_doc = person_ref.get()
        
        if not person_doc.exists:
            return {"error": f"Person in charge with ID {person_id} not found"}
        
        person_name = person_doc.to_dict().get('name', '')
        update_data['personInChargeId'] = person_id
        update_data['personInChargeName'] = person_name
        
        changed_fields.append({
            'field': 'personInCharge',
            'oldValue': ticket_data.get('personInChargeName'),
            'newValue': person_name
        })
    
    if 'statusId' in updatedFields:
        status_id = updatedFields['statusId']
        status_ref = db.collection('statuses').document(status_id)
        status_doc = status_ref.get()
        
        if not status_doc.exists:
            return {"error": f"Status with ID {status_id} not found"}
        
        status_name = status_doc.to_dict().get('name', '')
        update_data['statusId'] = status_id
        update_data['statusName'] = status_name
        
        changed_fields.append({
            'field': 'status',
            'oldValue': ticket_data.get('statusName'),
            'newValue': status_name
        })
    
    if 'scheduledCompletionDate' in updatedFields:
        completion_date = datetime.datetime.fromisoformat(updatedFields['scheduledCompletionDate']) if updatedFields['scheduledCompletionDate'] else None
        update_data['scheduledCompletionDate'] = completion_date
        
        old_date = ticket_data.get('scheduledCompletionDate')
        old_date_str = old_date.isoformat() if old_date else None
        new_date_str = completion_date.isoformat() if completion_date else None
        
        changed_fields.append({
            'field': 'scheduledCompletionDate',
            'oldValue': old_date_str,
            'newValue': new_date_str
        })
    
    if 'completionDate' in updatedFields:
        completion_date = datetime.datetime.fromisoformat(updatedFields['completionDate']) if updatedFields['completionDate'] else None
        update_data['completionDate'] = completion_date
        
        old_date = ticket_data.get('completionDate')
        old_date_str = old_date.isoformat() if old_date else None
        new_date_str = completion_date.isoformat() if completion_date else None
        
        changed_fields.append({
            'field': 'completionDate',
            'oldValue': old_date_str,
            'newValue': new_date_str
        })
    
    if 'actualEffortHours' in updatedFields:
        update_data['actualEffortHours'] = updatedFields['actualEffortHours']
        changed_fields.append({
            'field': 'actualEffortHours',
            'oldValue': ticket_data.get('actualEffortHours'),
            'newValue': updatedFields['actualEffortHours']
        })
    
    if 'responseCategoryId' in updatedFields:
        category_id = updatedFields['responseCategoryId']
        
        if category_id:
            category_ref = db.collection('responseCategories').document(category_id)
            category_doc = category_ref.get()
            
            if not category_doc.exists:
                return {"error": f"Response category with ID {category_id} not found"}
            
            category_name = category_doc.to_dict().get('name', '')
            update_data['responseCategoryId'] = category_id
            update_data['responseCategoryName'] = category_name
        else:
            update_data['responseCategoryId'] = None
            update_data['responseCategoryName'] = None
        
        changed_fields.append({
            'field': 'responseCategory',
            'oldValue': ticket_data.get('responseCategoryName'),
            'newValue': update_data.get('responseCategoryName')
        })
    
    if 'responseDetails' in updatedFields:
        update_data['responseDetails'] = updatedFields['responseDetails']
        changed_fields.append({
            'field': 'responseDetails',
            'oldValue': ticket_data.get('responseDetails'),
            'newValue': updatedFields['responseDetails']
        })
    
    if 'hasDefect' in updatedFields:
        update_data['hasDefect'] = updatedFields['hasDefect']
        changed_fields.append({
            'field': 'hasDefect',
            'oldValue': ticket_data.get('hasDefect'),
            'newValue': updatedFields['hasDefect']
        })
    
    if 'remarks' in updatedFields:
        update_data['remarks'] = updatedFields['remarks']
        changed_fields.append({
            'field': 'remarks',
            'oldValue': ticket_data.get('remarks'),
            'newValue': updatedFields['remarks']
        })
    
    if 'externalTicketId' in updatedFields:
        update_data['externalTicketId'] = updatedFields['externalTicketId']
        changed_fields.append({
            'field': 'externalTicketId',
            'oldValue': ticket_data.get('externalTicketId'),
            'newValue': updatedFields['externalTicketId']
        })
    
    # Handle attachments separately if needed
    if 'attachments' in updatedFields:
        update_data['attachments'] = updatedFields['attachments']
        # Not including attachments in changed_fields for simplicity
    
    # Update timestamp
    now = datetime.datetime.now()
    update_data['updatedAt'] = now
    
    # Prepare history entry
    user_id = changeLog.get('userId') if changeLog else ticket_data.get('personInChargeId')
    comment = changeLog.get('comment') if changeLog else '情報更新'
    
    # Get user name
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()
    user_name = user_doc.to_dict().get('name', '不明') if user_doc.exists else '不明'
    
    history_entry = {
        'timestamp': now,
        'userId': user_id,
        'userName': user_name,
        'changedFields': changed_fields,
        'comment': comment
    }
    
    # Add to history array using array_union
    ticket_ref.update({
        **update_data,
        'history': firestore.ArrayUnion([history_entry])
    })
    
    # Return success response
    return {
        "ticketId": ticketId,
        "message": f"チケットを更新しました。(ID: {ticketId})"
    }

@mcp.tool(description="チケットにコメントや履歴を追加する - チケットの対応履歴を記録")
def add_ticket_history(
    ticketId: str,
    userId: str,
    comment: str,
    changedFields: Optional[List[Dict[str, Any]]] = None,
    ctx: Context = None
) -> Dict[str, str]:
    """
    チケットにコメントや変更履歴を追加する

    Parameters:
    - ticketId: 対象のチケットID（例: "TCK-0001"）
    - userId: コメント記入者のユーザーID（usersコレクション参照）
    - comment: コメント内容
    - changedFields: 変更されたフィールド情報（省略可）、以下の形式:
      [
        {
          "field": "フィールド名",
          "oldValue": "変更前の値",
          "newValue": "変更後の値"
        }
      ]

    Returns:
    - 結果を含むディクショナリ:
      - 成功時: {"ticketId": "チケットID", "historyEntryId": "履歴エントリID", "message": "コメントを追加しました。(チケットID: チケットID)"}
      - 失敗時: {"error": "エラーメッセージ"}

    使用例:
    1. 単純なコメント追加:
       add_ticket_history(
           ticketId="TCK-0001",
           userId="user2",
           comment="お客様にメールで状況を報告しました。"
       )

    2. 変更履歴付きコメント:
       add_ticket_history(
           ticketId="TCK-0001",
           userId="user1",
           comment="優先度を上げて対応します。",
           changedFields=[
               {
                   "field": "priority",
                   "oldValue": "中",
                   "newValue": "高"
               }
           ]
       )

    備考:
    - チケットの状態を変更する場合は update_ticket 関数を使用することを推奨
    - このツールは主にコメントの追加や履歴の記録を目的としています
    - 変更履歴のタイムスタンプは自動的に現在時刻が設定されます

    """
    # Get Firestore database
    db = ctx.request_context.lifespan_context.db
    
    # Get ticket reference
    ticket_ref = db.collection('tickets').document(ticketId)
    ticket_doc = ticket_ref.get()
    
    # Check if ticket exists
    if not ticket_doc.exists:
        return {"error": f"Ticket with ID {ticketId} not found"}
    
    # Get user name
    user_ref = db.collection('users').document(userId)
    user_doc = user_ref.get()
    user_name = user_doc.to_dict().get('name', '不明') if user_doc.exists else '不明'
    
    # Prepare history entry
    now = datetime.datetime.now()
    history_entry = {
        'timestamp': now,
        'userId': userId,
        'userName': user_name,
        'changedFields': changedFields or [],
        'comment': comment
    }
    
    # Update ticket with new history entry
    ticket_ref.update({
        'updatedAt': now,
        'history': firestore.ArrayUnion([history_entry])
    })
    
    # Generate history entry ID (timestamp-based)
    history_id = now.strftime('%Y%m%d%H%M%S')
    
    # Return success response
    return {
        "ticketId": ticketId,
        "historyEntryId": history_id,
        "message": f"コメントを追加しました。(チケットID: {ticketId})"
    }

# Master data reference tools
@mcp.tool(description="ユーザー一覧を取得する - チケット作成時に必要なユーザー情報を参照")
def get_users(
    role: Optional[str] = None,
    ctx: Context = None
) -> str:
    """
    システムに登録されているユーザー（担当者、リクエスタなど）の一覧を取得し表示する

    Parameters:
    - role: 特定の役割でフィルタリング（例: "担当者", "リクエスタ"）（省略可）

    Returns:
    - ユーザー一覧のMarkdown形式テーブル

    使用例:
    1. すべてのユーザーを表示: get_users()
    2. 担当者のみ表示: get_users(role="担当者")
    3. リクエスタのみ表示: get_users(role="リクエスタ")

    備考:
    - ユーザーIDはチケット作成時の requestorId や personInChargeId として必要です
    - 表示される情報: ID、名前、メールアドレス、役割
    """
    # Get Firestore database
    db = ctx.request_context.lifespan_context.db

    # Base query
    query = db.collection('users')

    # Apply role filter if specified
    if role:
        query = query.where('role', '==', role)

    # Execute query
    results = query.get()

    # Process results
    users = []
    for doc in results:
        user_data = doc.to_dict()
        users.append({
            'id': doc.id,
            'name': user_data.get('name', ''),
            'email': user_data.get('email', ''),
            'role': user_data.get('role', '')
        })

    # Sort by name
    users.sort(key=lambda x: x['name'])

    # Format as markdown
    if not users:
        return "ユーザーは登録されていません。"

    output = "# ユーザー一覧\n\n"
    output += "| ID | 名前 | メールアドレス | 役割 |\n"
    output += "|---|---|---|---|\n"

    for user in users:
        output += f"| {user['id']} | {user['name']} | {user['email']} | {user['role']} |\n"

    return output

@mcp.tool(description="アカウント一覧を取得する - チケット作成時に必要なアカウント情報を参照")
def get_accounts(ctx: Context = None) -> str:
    """
    システムに登録されているアカウント（顧客企業など）の一覧を取得し表示する

    Returns:
    - アカウント一覧のMarkdown形式テーブル

    使用例:
    1. アカウント一覧を表示: get_accounts()

    備考:
    - アカウントIDはチケット作成時の accountId として必要です
    - 表示される情報: ID、アカウント名
    - アカウント名順にソートされて表示されます
    """
    # Get Firestore database
    db = ctx.request_context.lifespan_context.db

    # Query accounts, ordered by name
    results = db.collection('accounts').order_by('name').get()

    # Process results
    accounts = []
    for doc in results:
        account_data = doc.to_dict()
        accounts.append({
            'id': doc.id,
            'name': account_data.get('name', '')
        })

    # Format as markdown
    if not accounts:
        return "アカウントは登録されていません。"

    output = "# アカウント一覧\n\n"
    output += "| ID | アカウント名 |\n"
    output += "|---|---|\n"

    for account in accounts:
        output += f"| {account['id']} | {account['name']} |\n"

    return output

@mcp.tool(description="リクエストチャネル一覧を取得する - チケット作成時に必要なチャネル情報を参照")
def get_request_channels(ctx: Context = None) -> str:
    """
    システムで使用される受付チャネルの一覧を取得し表示する
    
    Returns:
    - 受付チャネル一覧のMarkdown形式テーブル
    """
    db = ctx.request_context.lifespan_context.db
    results = db.collection('requestChannels').order_by('orderNo').get()
    channels = []
    for doc in results:
        channel_data = doc.to_dict()
        channels.append({
            'id': doc.id,
            'name': channel_data.get('name', '')
        })
        
    if not channels:
        return "受付チャネルは登録されていません。"
        
    output = "# 受付チャネル一覧\n\n"
    output += "| ID | チャネル名 |\n"
    output += "|---|---|\n"
    
    for channel in channels:
        output += f"| {channel['id']} | {channel['name']} |\n"
        
    return output

@mcp.tool(description="ステータス一覧を取得する - チケット作成・更新時に必要なステータス情報を参照")
def get_statuses(ctx: Context = None) -> str:
    """
    システムで使用されるチケットステータスの一覧を取得し表示する

    Returns:
    - ステータス一覧のMarkdown形式テーブル

    使用例:
    1. ステータス一覧を表示: get_statuses()

    備考:
    - ステータスIDはチケット作成・更新時の statusId として必要です
    - 表示される情報: ID、ステータス名
    - ステータスは一般的なワークフロー順（順番）に表示されます
    """
    # Get Firestore database
    db = ctx.request_context.lifespan_context.db

    # Query statuses, ordered by orderNo
    results = db.collection('statuses').order_by('orderNo').get()

    # Process results
    statuses = []
    for doc in results:
        status_data = doc.to_dict()
        statuses.append({
            'id': doc.id,
            'name': status_data.get('name', '')
        })

    # Format as markdown
    if not statuses:
        return "ステータスは登録されていません。"

    output = "# ステータス一覧\n\n"
    output += "| ID | ステータス名 |\n"
    output += "|---|---|\n"

    for status in statuses:
        output += f"| {status['id']} | {status['name']} |\n"

    return output

@mcp.tool(description="カテゴリ一覧を取得する - チケット作成時に必要なカテゴリ情報を参照")
def get_categories(ctx: Context = None) -> str:
    """
    システムで使用されるチケットカテゴリの一覧を取得し表示する

    Returns:
    - カテゴリ一覧のMarkdown形式テーブル

    使用例:
    1. カテゴリ一覧を表示: get_categories()

    備考:
    - カテゴリIDはチケット作成時の categoryId として必要です
    - カテゴリを選択した後に、関連するカテゴリ詳細を get_category_details(categoryId="...") で取得してください
    - 表示される情報: ID、カテゴリ名
    """
    # Get Firestore database
    db = ctx.request_context.lifespan_context.db

    # Query categories, ordered by orderNo
    results = db.collection('categories').order_by('orderNo').get()

    # Process results
    categories = []
    for doc in results:
        category_data = doc.to_dict()
        categories.append({
            'id': doc.id,
            'name': category_data.get('name', '')
        })

    # Format as markdown
    if not categories:
        return "カテゴリは登録されていません。"

    output = "# カテゴリ一覧\n\n"
    output += "| ID | カテゴリ名 |\n"
    output += "|---|---|\n"

    for category in categories:
        output += f"| {category['id']} | {category['name']} |\n"

    return output

@mcp.tool(description="カテゴリ詳細一覧を取得する - チケット作成時に必要なカテゴリ詳細情報を参照")
def get_category_details(
    categoryId: Optional[str] = None,
    ctx: Context = None
) -> str:
    """
    システムで使用されるチケットカテゴリの詳細一覧を取得し表示する

    Parameters:
    - categoryId: 特定の親カテゴリIDでフィルタリング（省略可）

    Returns:
    - カテゴリ詳細一覧のMarkdown形式テーブル

    使用例:
    1. すべてのカテゴリ詳細を表示: get_category_details()
    2. 特定のカテゴリに属する詳細のみ表示: get_category_details(categoryId="cat1")

    備考:
    - カテゴリ詳細IDはチケット作成時の categoryDetailId として必要です
    - カテゴリIDは get_categories() で確認できます
    - 表示される情報: ID、詳細名、親カテゴリ
    """
    # Get Firestore database
    db = ctx.request_context.lifespan_context.db

    # Base query
    query = db.collection('categoryDetails')

    # Apply category filter if specified
    if categoryId:
        query = query.where('categoryId', '==', categoryId)

    # Add ordering
    query = query.order_by('orderNo')

    # Execute query
    results = query.get()

    # Process results
    category_details = []
    for doc in results:
        detail_data = doc.to_dict()
        category_details.append({
            'id': doc.id,
            'name': detail_data.get('name', ''),
            'categoryId': detail_data.get('categoryId', ''),
            'categoryName': detail_data.get('categoryName', '')
        })

    # Format as markdown
    if not category_details:
        return "カテゴリ詳細は登録されていません。"

    output = "# カテゴリ詳細一覧\n\n"
    output += "| ID | 詳細名 | 親カテゴリ |\n"
    output += "|---|---|---|\n"

    for detail in category_details:
        output += f"| {detail['id']} | {detail['name']} | {detail['categoryName']} |\n"

    return output

# === Resources ===

# Remove the test resource as we've now implemented proper tools


# Run the server
if __name__ == "__main__":
    print("MCPサーバーを起動します...")
    mcp.run()
    print("MCPサーバーが停止しました。")
