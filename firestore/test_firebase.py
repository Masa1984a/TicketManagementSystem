import firebase_admin
from firebase_admin import credentials
import os

def test_firebase_connection():
    """
    Firebaseへの基本的な接続をテストします。
    """
    try:
        # 既に初期化されているか確認
        firebase_admin.get_app()
        print("Firebaseアプリは既に初期化されています。")
    except ValueError:
        # 初期化されていない場合
        cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'firebase-credentials.json')
        
        print(f"認証情報ファイルのパス: {cred_path}")

        if os.path.exists(cred_path):
            print(f"認証情報ファイル '{cred_path}' が見つかりました。")
            try:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print("Firebaseアプリの初期化に成功しました。接続テストOKです。")
            except Exception as e:
                print(f"認証情報ファイルを使用してFirebaseアプリの初期化に失敗しました。")
                print(f"エラー詳細: {e}")
        else:
            print(f"認証情報ファイル '{cred_path}' が見つかりません。")
            print("デフォルトの認証情報（Google Cloud環境など）で初期化を試みます...")
            try:
                # GOOGLE_APPLICATION_CREDENTIALS が設定されておらず、
                # firebase-credentials.json もない場合、
                # App Engine, Cloud Functions, GCEなどの環境であれば
                # デフォルトのサービスアカウントで初期化できる可能性がある
                firebase_admin.initialize_app()
                print("Firebaseアプリのデフォルト初期化に成功しました（Google Cloud環境など）。")
                print("ローカル環境でこのメッセージが表示された場合、認証設定が不十分な可能性があります。")
            except Exception as e:
                print(f"Firebaseアプリのデフォルト初期化に失敗しました。")
                print(f"エラー詳細: {e}")
                print("\n考えられる原因:")
                print("- 認証情報ファイルへのパスが正しくない、またはファイルが存在しない。")
                print("- 認証情報ファイルの内容が正しくない。")
                print("- ネットワーク接続に問題がある（ファイアウォールなど）。")
                print("- Firebaseプロジェクトの設定に問題がある。")

if __name__ == "__main__":
    test_firebase_connection()