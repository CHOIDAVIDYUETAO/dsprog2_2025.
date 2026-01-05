import flet as ft
import requests

# 1. 地域リストをJSONで取得
def get_areas():
    url = "http://www.jma.go.jp/bosai/common/const/area.json"
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        print(f"Error fetching areas: {e}")
        return {}

# 2. 地域ごとの天気情報を取得
def get_forecast(area_code):
    url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        print(f"Error fetching forecast: {e}")
        return None

def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 900
    page.window_height = 700

    # 天気表示用のエリア
    forecast_display = ft.Row(wrap=True, spacing=20, scroll=ft.ScrollMode.ADAPTIVE)

    # 地域が選択された時の処理
    def on_area_select(e, code, name):
        data = get_forecast(code)
        if not data: return
        
        forecast_display.controls.clear()
        
        # 天気・日付データの取得 (index 0)
        time_series = data[0]["timeSeries"][0]
        times = time_series["timeDefines"]
        weathers = time_series["areas"][0]["weathers"]
        
        # 気温データの取得 (通常 index 2 に入っています)
        temps = []
        try:
            if len(data[0]["timeSeries"]) > 2:
                temps = data[0]["timeSeries"][2]["areas"][0]["temps"]
        except (IndexError, KeyError):
            temps = []

        # 予報カードの生成
        for i in range(len(times)):
            # 気温の判定（データがある場合のみ表示）
            t_min = "--"
            t_max = "--"
            if len(temps) >= 2 and i == 0: # 当日の気温データがある場合
                t_min = temps[0]
                t_max = temps[1]

            card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(times[i][:10], weight=ft.FontWeight.BOLD, size=16),
                        ft.Icon(name=ft.Icons.WB_SUNNY, color=ft.Colors.ORANGE, size=50),
                        ft.Text(weathers[i], size=13, text_align=ft.TextAlign.CENTER),
                        ft.Text(f"{t_min}°C / {t_max}°C", color=ft.Colors.BLUE_700, weight=ft.FontWeight.BOLD),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, width=160),
                    padding=20,
                )
            )
            forecast_display.controls.append(card)
        page.update()

    # 地域選單的建立
    areas_data = get_areas()
    centers = areas_data.get("centers", {})
    offices = areas_data.get("offices", {})
    
    sidebar_items = [ft.Text("地域を選択", size=24, weight=ft.FontWeight.BOLD)]

    for c_code, c_info in centers.items():
        et = ft.ExpansionTile(
            title=ft.Text(c_info["name"]),
            subtitle=ft.Text(c_code),
            controls=[]
        )
        for o_code in c_info.get("children", []):
            if o_code in offices:
                et.controls.append(
                    ft.ListTile(
                        title=ft.Text(offices[o_code]["name"]),
                        on_click=lambda e, code=o_code, name=offices[o_code]["name"]: on_area_select(e, code, name)
                    )
                )
        sidebar_items.append(et)

    # レイアウトの構築
    page.add(
        ft.Row(
            [
                ft.Container(
                    content=ft.Column(sidebar_items, scroll=ft.ScrollMode.ALWAYS),
                    width=280, bgcolor=ft.Colors.GREY_50, padding=10
                ),
                ft.VerticalDivider(width=1),
                ft.Container(content=forecast_display, expand=True, padding=10)
            ],
            expand=True
        )
    )

ft.app(target=main)