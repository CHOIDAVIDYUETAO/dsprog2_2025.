import flet as ft
import requests
import sqlite3

# --- 【A：データベースの初期化とテーブル設計】 ---
def init_db():
    # weather_app.db という名前でSQLiteデータベースを作成
    conn = sqlite3.connect("weather_app.db")
    cursor = conn.cursor()
    
    # テーブル設計：地域コードと予報日を複合キー的に扱い、データの重複を防ぐ
    # 正規化を意識し、必要なカラム（地域名、日付、天気、気温）を定義
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_code TEXT,
            area_name TEXT,
            forecast_date TEXT,
            weather_text TEXT,
            temp_max TEXT,
            temp_min TEXT,
            UNIQUE(area_code, forecast_date)
        )
    """)
    conn.commit()
    conn.close()

# 地域リストを取得する関数
def get_areas():
    url = "http://www.jma.go.jp/bosai/common/const/area.json"
    return requests.get(url).json()

# --- 【B：APIデータをDBに保存する処理】 ---
def save_forecast_to_db(area_code, area_name, api_data):
    conn = sqlite3.connect("weather_app.db")
    cursor = conn.cursor()
    
    # JSONから情報を抽出してDBに格納
    time_series = api_data[0]["timeSeries"]
    times = time_series[0]["timeDefines"]
    weathers = time_series[0]["areas"][0]["weathers"]
    
    # 気温データの取得処理（データがある場合のみ）
    temps = []
    if len(time_series) > 2:
        temps = time_series[2]["areas"][0]["temps"]

    for i in range(len(times)):
        date_str = times[i][:10]
        weather_str = weathers[i]
        t_max = temps[i*2] if len(temps) > i*2 else "--"
        t_min = temps[i*2+1] if len(temps) > i*2+1 else "--"
        
        # INSERT OR REPLACE を使用して既存データを更新できるようにする
        cursor.execute("""
            INSERT OR REPLACE INTO weather_data 
            (area_code, area_name, forecast_date, weather_text, temp_max, temp_min)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (area_code, area_name, date_str, weather_str, t_max, t_min))
    
    conn.commit()
    conn.close()

# --- 【C：DBからデータを取得して表示する処理】 ---
def get_forecast_from_db(area_code):
    conn = sqlite3.connect("weather_app.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT forecast_date, weather_text, temp_max, temp_min 
        FROM weather_data 
        WHERE area_code = ? 
        ORDER BY forecast_date ASC
    """, (area_code,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def main(page: ft.Page):
    page.title = "天気予報アプリ (SQLite連携版)"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # 起動時にDBを初期化
    init_db()
    
    forecast_display = ft.Row(wrap=True, spacing=10, scroll=ft.ScrollMode.ADAPTIVE)

    # 地域を選択した時の処理
    def on_area_select(e, code, name):
        # 1. APIから最新データを取得
        api_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{code}.json"
        res = requests.get(api_url).json()
        
        # 2. データをDBに格納（移行）
        save_forecast_to_db(code, name, res)
        
        # 3. DBからデータを取得して画面に表示
        db_records = get_forecast_from_db(code)
        
        forecast_display.controls.clear()
        for rec in db_records:
            f_date, f_weather, f_max, f_min = rec
            forecast_display.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(f_date, weight=ft.FontWeight.BOLD),
                            ft.Icon(ft.Icons.WB_SUNNY, color=ft.Colors.ORANGE), # 引数を修正
                            ft.Text(f_weather, size=12, text_align=ft.TextAlign.CENTER),
                            ft.Text(f"{f_max}°C / {f_min}°C", size=14, color=ft.Colors.BLUE_700, weight=ft.FontWeight.BOLD)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=15, width=150
                    )
                )
            )
        page.update()

    # --- UIの構築（サイドバー） ---
    areas = get_areas()
    centers = areas["centers"]
    offices = areas["offices"]
    
    sidebar = ft.Column(scroll=ft.ScrollMode.ALWAYS, width=280)
    sidebar.controls.append(ft.Text("地域を選択", size=22, weight=ft.FontWeight.BOLD))

    for c_code, c_info in centers.items():
        # controls=[] を明示的に初期化してエラーを回避
        et = ft.ExpansionTile(title=ft.Text(c_info["name"]), controls=[]) 
        
        for o_code in c_info["children"]:
            if o_code in offices:
                et.controls.append(
                    ft.ListTile(
                        title=ft.Text(offices[o_code]["name"]),
                        on_click=lambda e, c=o_code, n=offices[o_code]["name"]: on_area_select(e, c, n)
                    )
                )
        sidebar.controls.append(et)

    page.add(
        ft.Row([
            ft.Container(content=sidebar, padding=10, bgcolor=ft.Colors.GREY_50),
            ft.VerticalDivider(width=1),
            ft.Container(content=forecast_display, expand=True, padding=10)
        ], expand=True)
    )

# 最新のFlet仕様に合わせて実行方法を微調整
ft.app(target=main)