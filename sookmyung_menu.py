import requests
import csv
import json
import time

# 카카오 API 설정
API_KEY = {API_KEY}
headers = {"Authorization": f"KakaoAK {API_KEY}"}

# 청파동 중심 좌표
x, y = 126.97220831510235, 37.545505260572455

# 검색 키워드 리스트
queries = ["술집", "호프", "식당", "맛집", "카페", "주점", "포차", "양식", "한식", "중식", "일식", "퓨전", "와인바", "펍", "맥주"]

# 키워드 검색 함수
def search_keyword_places(query, x, y, radius=3000, page=1):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    params = {
        "query": query,
        "x": x,
        "y": y,
        "radius": radius,
        "page": page,
        "size": 15
    }
    res = requests.get(url, headers=headers, params=params)
    print(f"[DEBUG] {query} - Page {page} - status: {res.status_code}")
    try:
        return res.json()
    except Exception as e:
        print("[ERROR] JSON 디코딩 실패:", e)
        return {}

# 크롤링 함수
def crawl_keyword_places(queries, x, y, radius=3000):
    collected = []
    seen_ids = set()
    
    for query in queries:
        for page in range(1, 100):
            result = search_keyword_places(query, x, y, radius, page)
            documents = result.get("documents", [])
            print(f"📄 {query} - Page {page} - 수신된 가게 수: {len(documents)}")
            if not documents:
                break
            for place in documents:
                pid = place.get("id")
                if pid not in seen_ids:
                    seen_ids.add(pid)
                    collected.append(place)
            time.sleep(0.3)  # 너무 빠른 요청 방지 (rate limit)
    
    return collected

# ✅ CSV 저장
def save_to_csv(data, filename="갈월동_술집_식당_통합.csv"):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["name", "address", "phone", "category", "lat", "lng", "id", "url"])
        for place in data:
            writer.writerow([
                place.get('place_name', ''),
                place.get('address_name', ''),
                place.get('phone', ''),
                place.get('category_name', ''),
                place.get('y', ''),
                place.get('x', ''),
                place.get('id', ''),
                place.get('place_url', '')
            ])

# JSON 저장
def save_to_json(data, filename="갈월동_술집_식당_통합.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 실행
if __name__ == "__main__":
    print(f"🔍 여러 키워드로 갈월동 식당 및 술집 수집 중...")
    places = crawl_keyword_places(queries, x, y, radius=3000)
    print(f"총 수집된 가게 수: {len(places)}개")

    save_to_csv(places)
    save_to_json(places)
    print("저장 완료! (CSV & JSON)")
