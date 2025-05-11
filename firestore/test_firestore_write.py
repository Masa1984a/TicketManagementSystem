import firebase_admin
from firebase_admin import credentials, firestore
import os
import datetime

def simple_firestore_write_test_with_db_id(database_id): # データベースIDを引数で受け取る
    """
    指定されたデータベースIDのFirestoreへのシンプルな書き込みをテストします。
    """
    try:
        app = firebase_admin.get_app()
        print("Firebaseアプリは既に初期化されています。")
    except ValueError:
        cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'firebase-credentials.json')
        if not os.path.exists(cred_path):
            print(f"認証情報ファイル '{cred_path}' が見つかりません。処理を終了します。")
            return
        
        try:
            cred = credentials.Certificate(cred_path)
            app = firebase_admin.initialize_app(cred)
            print(f"Firebaseアプリの初期化に成功しました。")
        except Exception as e:
            print(f"Firebaseアプリの初期化に失敗しました: {e}")
            return

    try:
        # ここでデータベースIDを指定します
        db = firestore.client(app=app, database_id=database_id)
        print(f"FirestoreクライアントをデータベースID '{database_id}' で初期化しました。")
        
        doc_ref = db.collection('test_connection_collection').document('test_doc_named_db')
        
        print(f"Firestoreへ '{doc_ref.path}' (データベースID: {database_id}) への書き込みを試みます...")
        doc_ref.set({
            'message': f'Hello from Python simple test to DB {database_id}!',
            'timestamp': datetime.datetime.now(datetime.timezone.utc)
        })
        print(f"Firestoreへの書き込みに成功しました！")

    except Exception as e:
        print(f"Firestore (データベースID: {database_id}) への処理中にエラーが発生しました。")
        print(f"エラーの種類: {type(e).__name__}")
        print(f"エラー詳細: {e}")

if __name__ == "__main__":
    # ここに接続したいデータベースのIDを指定してください
    # 例: もしデータベースIDが "mcp-status-test" なら
    target_database_id = "mcp-status-test"  
    # もしデフォルトデータベースを使いたい場合は "(default)" または指定なし（ただしSDKの挙動による）
    # target_database_id = "(default)"

    print(f"テスト対象のデータベースID: {target_database_id}")
    simple_firestore_write_test_with_db_id(target_database_id)