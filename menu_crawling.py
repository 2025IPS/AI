import os
import re
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# ✅ 브라우저 옵션 설정
options = Options()
options.add_argument("window-size=1280x1000")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
driver = webdriver.Chrome(options=options)

# ✅ 파일명 안전 처리 함수
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

# ✅ 메뉴 수집 함수
def crawl_menu_direct(place_id, store_name, driver):
    print(f"\n📌 {store_name} 메뉴 수집 시작 (place_id: {place_id})")
    
    # entryIframe이 있는 메인 페이지로 이동
    url = f"https://map.naver.com/p/entry/place/{place_id}?c=15.00,0,0,0,dh&placePath=/menu"
    driver.get(url)
    time.sleep(3)

    # iframe URL 추출
    iframe = None
    for _ in range(5):
        try:
            iframe = driver.find_element(By.CSS_SELECTOR, "iframe#entryIframe")
            break
        except:
            time.sleep(1)

    if iframe is None:
        print("❌ iframe을 찾지 못했습니다.")
        return {"place_name": store_name, "menu": []}

    iframe_url = iframe.get_attribute("src")
    if not iframe_url:
        print("❌ iframe URL이 없습니다.")
        return {"place_name": store_name, "menu": []}

    # ✅ iframe URL로 새 페이지 열기
    driver.get(iframe_url)
    time.sleep(3)

    # ✅ 메뉴 가져오기 (.place_section_content 안의 li.E2jtL)
    menu_data = {"place_name": store_name, "menu": []}

    try:
        items = driver.find_elements(By.CSS_SELECTOR, ".place_section_content li.E2jtL")
        for item in items:
            try:
                name = item.find_element(By.CSS_SELECTOR, ".lPzHi").text.strip()
                price = item.find_element(By.CSS_SELECTOR, ".v4l2H").text.strip() if len(item.find_elements(By.CSS_SELECTOR, ".v4l2H")) > 0 else "-"
                menu_data["menu"].append((name, price))
                print(f"  - {name} ({price})")
            except Exception as e:
                continue

    except Exception as e:
        print(f"❌ 메뉴 수집 실패: {e}")

    return menu_data

# ✅ CSV에서 식당 목록 불러오기
csv_path = "C:\TodayMenu\청파동_키워드맛집 copy.csv"
places_df = pd.read_csv(csv_path)

# name -> store_name / id -> place_id 사용
places = places_df.rename(columns={'name': 'store_name', 'id': 'place_id'}).to_dict("records")

# ✅ 저장 경로
output_dir = "C:/TodayMenu/menus"
os.makedirs(output_dir, exist_ok=True)

# ✅ 전체 메뉴 데이터 저장 리스트
all_menus = []

# ✅ 크롤링 실행
for place in places:
    result = crawl_menu_direct(place["place_id"], place["store_name"], driver)

    if result["menu"]:
        df = pd.DataFrame(result["menu"], columns=["menu_name", "menu_price"])
        df.insert(0, "place_name", result["place_name"])
        file_name = sanitize_filename(place["store_name"])
        df.to_csv(f"{output_dir}/{file_name}_menu.csv", index=False, encoding="utf-8-sig")
        all_menus.extend(df.to_dict("records"))
        print(f"💾 {file_name}_menu.csv 저장 완료")
    else:
        print(f"⚠️ {place['store_name']} 메뉴 없음")

# ✅ 전체 데이터 저장
if all_menus:
    df_total = pd.DataFrame(all_menus)
    df_total.to_csv("C:/TodayMenu/total_menu_data.csv", index=False, encoding="utf-8-sig")
    print("\n🎉 전체 메뉴가 total_menu_data.csv로 저장되었습니다!")
else:
    print("\n⚠️ 저장할 메뉴 데이터가 없습니다.")

# ✅ 브라우저 종료
driver.quit()
