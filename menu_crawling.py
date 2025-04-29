import os
import re
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ✅ 브라우저 옵션 설정
options = Options()
options.add_argument("window-size=1280x1000")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# WebDriver 설정
driver = webdriver.Chrome(options=options)

# ✅ 파일명 안전 처리 함수
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

# ✅ 메뉴 수집 함수 (직접 URL 접근 방식)
def crawl_menu_direct(place_id, store_name, driver):
    print(f"\n📌 {store_name} 메뉴 수집 시작 (place_id: {place_id})")
    
    # 직접 접근 URL
    direct_url = f"https://map.naver.com/p/entry/place/{place_id}?c=15.00,0,0,0,dh&placePath=/menu"
    
    print(f"직접 접근 URL: {direct_url}")
    driver.get(direct_url)
    time.sleep(5)  # 초기 로딩 대기
    
    menu_data = {"place_name": store_name, "menu": []}
    
    try:
        # 진입 iframe으로 전환
        print("진입 iframe 찾는 중...")
        
        # 모든 iframe 확인
        wait_attempts = 0
        found_iframe = False
        
        while wait_attempts < 3 and not found_iframe:
            wait_attempts += 1
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            print(f"발견된 iframe 수: {len(iframes)}")
            
            # 각 iframe의 정보 출력 (디버깅용)
            for idx, iframe in enumerate(iframes):
                try:
                    iframe_id = iframe.get_attribute("id") or "no-id"
                    iframe_src = iframe.get_attribute("src") or "no-src"
                    print(f"iframe[{idx}]: id={iframe_id}, src={iframe_src[:50]}...")
                except:
                    print(f"iframe[{idx}]: 속성 접근 실패")
            
            # entry iframe 찾기
            for idx, iframe in enumerate(iframes):
                try:
                    iframe_id = iframe.get_attribute("id") or ""
                    iframe_src = iframe.get_attribute("src") or ""
                    
                    if "entryIframe" in iframe_id or "place/entry" in iframe_src or "place" in iframe_src:
                        print(f"✅ 진입 iframe 찾음: id={iframe_id}, idx={idx}")
                        driver.switch_to.frame(iframe)
                        print("✅ 진입 iframe으로 전환 완료")
                        found_iframe = True
                        break
                except Exception as e:
                    print(f"iframe[{idx}] 확인 중 오류: {str(e)[:50]}")
                    continue
            
            if not found_iframe:
                print(f"⚠️ 진입 iframe을 아직 찾지 못했습니다. 대기 중... ({wait_attempts}/3)")
                time.sleep(3)  # 더 대기
        
        if not found_iframe:
            print("⚠️ 진입 iframe을 찾지 못했습니다. 스크린샷 저장 후 계속 진행...")
            debug_dir = "C:/TodayMenu/debug"
            os.makedirs(debug_dir, exist_ok=True)
            driver.save_screenshot(f"{debug_dir}/no_iframe_{sanitize_filename(store_name)}.png")
            
            # 진입 iframe을 찾지 못하더라도 계속 진행해 봅니다
            # JavaScript를 통해 현재 페이지에서 메뉴 정보 추출 시도
            try:
                # 상단바 닫기 버튼이 있으면 클릭 (방해될 수 있음)
                close_buttons = driver.find_elements(By.CSS_SELECTOR, "button.btn_close, button.Zvj_F")
                for btn in close_buttons:
                    try:
                        btn.click()
                        print("✅ 방해 요소 닫기 버튼 클릭")
                        time.sleep(1)
                    except:
                        pass
            except:
                pass
        
        # 메뉴 탭이 미리 선택되지 않았으면 클릭
        try:
            # 메뉴 관련 탭 찾기
            menu_tab_selectors = [
                "a[href*='menu']", 
                "a.tpj9w[role='tab']", 
                "span.veBoZ",
                "li.tpj9w a", 
                "div.place_fixed_tab a:nth-child(2)",
                "ul.ngGKH li:nth-child(2) a"
            ]
            
            menu_tab = None
            for selector in menu_tab_selectors:
                try:
                    tabs = driver.find_elements(By.CSS_SELECTOR, selector)
                    for tab in tabs:
                        tab_text = tab.text.strip()
                        if "메뉴" in tab_text:
                            menu_tab = tab
                            print(f"✅ 메뉴 탭 발견: '{tab_text}'")
                            break
                    if menu_tab:
                        break
                except:
                    continue
            
            if menu_tab:
                try:
                    menu_tab.click()
                    print("✅ 메뉴 탭 클릭 완료")
                    time.sleep(3)  # 메뉴 로딩 대기
                except Exception as e:
                    print(f"⚠️ 메뉴 탭 클릭 실패: {str(e)[:50]}")
                    
                    # JavaScript로 클릭 시도
                    try:
                        driver.execute_script("arguments[0].click();", menu_tab)
                        print("✅ JavaScript를 통해 메뉴 탭 클릭 완료")
                        time.sleep(3)
                    except Exception as js_e:
                        print(f"⚠️ JavaScript 클릭도 실패: {str(js_e)[:50]}")
            else:
                # XPath로 메뉴 탭 찾기 시도
                try:
                    menu_tab = driver.find_element(By.XPATH, "//a[contains(text(), '메뉴') or contains(@href, 'menu')]")
                    menu_tab.click()
                    print("✅ XPath로 메뉴 탭 클릭 완료")
                    time.sleep(3)
                except:
                    print("ℹ️ 메뉴 탭을 찾을 수 없거나 이미 메뉴 페이지에 있을 수 있습니다.")
        except Exception as e:
            print(f"⚠️ 메뉴 탭 처리 중 오류: {str(e)[:50]}")
            
        # 스크롤을 내려 더 많은 메뉴 로드
        try:
            for _ in range(3):
                driver.execute_script("window.scrollBy(0, 300);")
                time.sleep(0.5)
        except:
            print("⚠️ 스크롤 실패")
        
        # 현재 페이지 스크린샷 저장 (디버깅용)
        debug_dir = "C:/TodayMenu/debug"
        os.makedirs(debug_dir, exist_ok=True)
        driver.save_screenshot(f"{debug_dir}/before_menu_{sanitize_filename(store_name)}.png")
        
        # 메뉴 컨테이너 찾기
        try:
            print("메뉴 섹션 찾는 중...")
            menu_section_selectors = [
                "div.place_section_content", 
                "ul.place_section_content",
                "div.y5Vwl",
                "div.place_detail_wrapper",
                "div.place_section.no_margin"
            ]
            
            menu_section = None
            used_selector = None
            
            for selector in menu_section_selectors:
                sections = driver.find_elements(By.CSS_SELECTOR, selector)
                if sections:
                    for section in sections:
                        try:
                            section_text = section.text.strip()
                            # 일반적으로 메뉴 섹션은 가격 정보(숫자와 '원')를 포함
                            if re.search(r'\d+[,\d]*원', section_text):
                                menu_section = section
                                used_selector = selector
                                print(f"✅ 메뉴 섹션 발견: 선택자 '{selector}'")
                                break
                        except:
                            continue
                
                if menu_section:
                    break
            
            if not menu_section:
                # 메뉴 관련 섹션 헤더로 찾기
                menu_headers = driver.find_elements(By.XPATH, "//h2[contains(text(), '메뉴') or contains(@class, 'place_section_header')]")
                for header in menu_headers:
                    try:
                        # 헤더의 부모 요소가 섹션
                        parent_section = header.find_element(By.XPATH, "./..")
                        menu_section = parent_section
                        used_selector = "XPath: 메뉴 헤더 부모"
                        print("✅ 메뉴 헤더를 통해 메뉴 섹션 발견")
                        break
                    except:
                        continue
        except Exception as e:
            print(f"⚠️ 메뉴 섹션 찾기 실패: {str(e)[:50]}")
        
        # 다양한 메뉴 항목 선택자 시도
        menu_selectors = [
            {"container": "li.XyupO", "name": "span.name, div.name", "price": "span.price, div.price"},
            {"container": "li.sNyCZ", "name": "span.lPzAg", "price": "span.dz4xP"},
            {"container": "li.UwSIP", "name": "span.lPzAg", "price": "div.GXS1X, span.dz4xP"},
            {"container": "li.tCVOZ", "name": "div.MENyI", "price": "div.gl2cc, div.RtQi_"},
            {"container": "li.JFHbD", "name": "div.place_name, span.place_name", "price": "div.place_price, span.place_price"},
            {"container": "tr.PLGoz, tr.menu_list", "name": "div.PmIno, span.menu_name", "price": "div.GXS1X, span.menu_price"},
            {"container": "li.P_Yxm", "name": "div.MENyI", "price": "div.gl2cc, div._VDb0"}
        ]
        
        for selector in menu_selectors:
            print(f"메뉴 선택자 '{selector['container']}' 시도 중...")
            
            items = driver.find_elements(By.CSS_SELECTOR, selector["container"])
            if items:
                print(f"✅ 선택자 '{selector['container']}' 메뉴 항목 {len(items)}개 발견!")
                
                for item in items:
                    try:
                        # 이름과 가격 찾기 (여러 선택자 시도)
                        name = None
                        price = None
                        
                        # 이름 찾기
                        for name_selector in selector["name"].split(", "):
                            try:
                                name_elements = item.find_elements(By.CSS_SELECTOR, name_selector)
                                if name_elements:
                                    name = name_elements[0].text.strip()
                                    if name:
                                        break
                            except:
                                continue
                        
                        # 가격 찾기
                        for price_selector in selector["price"].split(", "):
                            try:
                                price_elements = item.find_elements(By.CSS_SELECTOR, price_selector)
                                if price_elements:
                                    price = price_elements[0].text.strip()
                                    if price:
                                        break
                            except:
                                continue
                        
                        # 유효한 메뉴 항목인지 확인하고 추가
                        if name and price and len(name.strip()) > 0 and len(price.strip()) > 0:
                            menu_data["menu"].append((name.strip(), price.strip()))
                            print(f"  - 메뉴 추가: {name} ({price})")
                    except Exception as e:
                        print(f"  ⚠️ 항목 파싱 오류: {str(e)[:50]}")
                        continue
            
            # 메뉴를 찾았으면 다음 선택자 세트를 시도하지 않음
            if menu_data["menu"]:
                break
        
        # 대안적 접근: 테이블 형태의 메뉴
        if not menu_data["menu"]:
            print("일반 메뉴 항목 선택자 실패. 테이블 메뉴 시도...")
            
            # 테이블 행에서 메뉴 추출 시도
            table_rows = driver.find_elements(By.CSS_SELECTOR, "table.KO9bq tr, table.menu_table tr")
            
            if table_rows:
                print(f"✅ 테이블 행 {len(table_rows)}개 발견!")
                
                for row in table_rows:
                    try:
                        row_text = row.text.strip()
                        if not row_text:
                            continue
                            
                        # 행에서 메뉴 이름과 가격 추출 시도
                        columns = row.find_elements(By.CSS_SELECTOR, "td")
                        
                        if len(columns) >= 2:
                            name = columns[0].text.strip()
                            price = columns[-1].text.strip()
                            
                            if name and price and any(c.isdigit() for c in price):
                                menu_data["menu"].append((name, price))
                                print(f"  - 테이블 메뉴 추가: {name} ({price})")
                    except Exception as e:
                        print(f"  ⚠️ 테이블 행 파싱 오류: {str(e)[:50]}")
                        continue
        
        # 텍스트 기반 메뉴 추출 (최종 대안)
        if not menu_data["menu"]:
            print("모든 선택자 실패. 텍스트 기반 메뉴 추출 시도...")
            
            try:
                # 페이지 전체에서 메뉴와 가격 패턴 찾기
                all_elements = driver.find_elements(By.XPATH, "//*[not(self::script) and not(self::style)]")
                
                for element in all_elements:
                    try:
                        element_text = element.text.strip()
                        if not element_text or len(element_text) < 3:
                            continue
                        
                        # 줄 단위로 분리
                        lines = element_text.split('\n')
                        
                        if len(lines) >= 2:
                            # 메뉴 이름과 가격 패턴 찾기
                            for i in range(len(lines) - 1):
                                name = lines[i].strip()
                                next_line = lines[i+1].strip()
                                
                                # 가격 패턴: 숫자와 '원' 또는 쉼표가 있는 줄
                                if re.search(r'\d+[,\d]*원|\d+[,\d]*$', next_line) and len(name) > 1:
                                    price = next_line
                                    menu_data["menu"].append((name, price))
                                    print(f"  - 텍스트 기반 메뉴 추가: {name} ({price})")
                    except:
                        continue
            except Exception as e:
                print(f"⚠️ 텍스트 기반 추출 실패: {str(e)[:50]}")
        
        # 메뉴 수집 최종 결과
        print(f"✅ {len(menu_data['menu'])}개 메뉴 수집 완료")
        
        # 디버깅 정보 저장
        if not menu_data["menu"]:
            debug_dir = "C:/TodayMenu/debug"
            os.makedirs(debug_dir, exist_ok=True)
            
            try:
                # 현재 URL 저장
                with open(f"{debug_dir}/current_url_{sanitize_filename(store_name)}.txt", "w", encoding="utf-8") as f:
                    f.write(f"Current URL: {driver.current_url}\n")
                
                # 페이지 소스 저장
                with open(f"{debug_dir}/page_source_{sanitize_filename(store_name)}.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                
                # 스크린샷 저장
                driver.save_screenshot(f"{debug_dir}/final_screenshot_{sanitize_filename(store_name)}.png")
                
                print(f"⚠️ 디버깅 정보가 {debug_dir} 폴더에 저장되었습니다.")
                
                # 페이지 구조 분석 시도
                try:
                    menu_related_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '메뉴') or contains(text(), '원')]")
                    with open(f"{debug_dir}/menu_elements_{sanitize_filename(store_name)}.txt", "w", encoding="utf-8") as f:
                        f.write(f"메뉴 관련 요소 수: {len(menu_related_elements)}\n\n")
                        for idx, elem in enumerate(menu_related_elements[:30]):  # 처음 30개만
                            try:
                                f.write(f"요소 {idx}:\n")
                                f.write(f"  태그: {elem.tag_name}\n")
                                f.write(f"  클래스: {elem.get_attribute('class')}\n")
                                f.write(f"  텍스트: {elem.text[:100]}...\n\n")
                            except:
                                f.write(f"요소 {idx}: 정보 추출 실패\n\n")
                except Exception as e:
                    print(f"⚠️ 페이지 구조 분석 실패: {str(e)[:50]}")
            except Exception as e:
                print(f"⚠️ 디버깅 정보 저장 실패: {str(e)[:50]}")
        
    except Exception as e:
        print(f"❌ 처리 중 오류 발생: {str(e)}")
    
    # 기본 프레임으로 복귀
    try:
        driver.switch_to.default_content()
    except:
        pass
    
    return menu_data

# ✅ 테스트할 place_id 목록
places = [
    {"name": "남영돈", "place_id": "19774046"},
    {"name": "정", "place_id": "11600155"},
    {"name": "일신기사식당", "place_id": "18717848"},
    {"name": "우스블랑 본점", "place_id": "1699309891"}
]

# ✅ 저장 경로
output_dir = "C:/TodayMenu/menus"
os.makedirs(output_dir, exist_ok=True)

# ✅ 전체 통합 저장 리스트
all_menus = []

# ✅ 크롤링 반복
for place in places:
    result = crawl_menu_direct(place["place_id"], place["name"], driver)

    if result["menu"]:
        df = pd.DataFrame(result["menu"], columns=["menu_name", "menu_price"])
        df.insert(0, "place_name", result["place_name"])
        file_name = sanitize_filename(place["name"])
        df.to_csv(f"{output_dir}/{file_name}_menu.csv", index=False, encoding="utf-8-sig")
        all_menus.extend(df.to_dict("records"))
        print(f"💾 {file_name}_menu.csv 저장 완료")
    else:
        print(f"⚠️ {place['name']} 메뉴 없음 → 저장하지 않음")

# ✅ 통합 저장
if all_menus:
    df_total = pd.DataFrame(all_menus)
    df_total.to_csv("C:/TodayMenu/total_menu_data.csv", index=False, encoding="utf-8-sig")
    print("\n🎉 전체 메뉴가 'total_menu_data.csv'로 저장되었습니다!")
else:
    print("\n⚠️ 저장할 메뉴 데이터가 없습니다.")

# ✅ 브라우저 종료
driver.quit()