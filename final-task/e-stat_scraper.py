import requests
from bs4 import BeautifulSoup
import time
import sqlite3

# --- 1. データベースの初期化 (課題要件: データベースへの保存) ---
def init_db():
    """
    SQLiteデータベースを作成し、テーブル構造を定義する関数
    """
    db_name = "estat_real_estate.db"
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # 既存のテーブルをリセットして新しく作成 (Schemaエラー防止)
    cursor.execute("DROP TABLE IF EXISTS ward_stats")
    cursor.execute("""
        CREATE TABLE ward_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT
        )
    """)
    conn.commit()
    conn.close()
    print(f"データベース {db_name} の初期化が完了しました。")

# --- 2. スクレイピングの実装 (課題要件: スクレイピングによるデータ取得) ---
def scrape_estat():
    """
    e-Statから住宅・土地統計調査のデータを取得し、DBに保存する関数
    """
    # 住宅・土地統計調査の検索結果ページ
    url = "https://www.e-stat.go.jp/stat-search/files?page=1&toukei=00200522"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # DB初期化を実行
    init_db()
    
    conn = sqlite3.connect("estat_real_estate.db")
    cursor = conn.cursor()

    print("e-Statからデータを取得中...")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 統計表のタイトルが含まれるリンクを抽出
        items = soup.find_all("a", string=True)
        count = 0

        for item in items:
            title = item.get_text(strip=True)
            # 「住宅」や「土地」に関連するキーワードでフィルタリング
            if any(key in title for key in ["住宅", "土地", "家賃"]):
                try:
                    # データベースへのインサート
                    cursor.execute("INSERT INTO ward_stats (title, url) VALUES (?, ?)", (title, url))
                    print(f"保存成功: {title[:30]}...")
                    count += 1
                except Exception as e:
                    print(f"インサートエラー: {e}")

        # サーバー負荷への配慮 (課題要件: 1秒以上の待機)
        time.sleep(2) 
        
        conn.commit()
        if count == 0:
            print("警告: 該当するデータが見つかりませんでした。セレクタを確認してください。")
        else:
            print(f"処理完了: 合計 {count} 件のデータを保存しました。")

    except Exception as e:
        print(f"通信エラーが発生しました: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # スクレイピングの実行
    scrape_estat()