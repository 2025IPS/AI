import requests
import csv
import json

# ✅ 카카오 API 설정
API_KEY = "API KEY"
headers = {"Authorization": f"KakaoAK {API_KEY}"}

# 청파동 중심 좌표
x, y = 126.96677012028513, 37.545067771838596
query = "식당"

# ✅ 키워드 검색 함수
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
    print(f"[DEBUG] Page {page} - status: {res.status_code}")
    try:
        return res.json()
    except Exception as e:
        print("[ERROR] JSON 디코딩 실패:", e)
        return {}

def crawl_keyword_places(query, x, y, radius=3000, max_count=None):
    collected = []
    seen_ids = set()
    for page in range(1, 100): 
        result = search_keyword_places(query, x, y, radius, page)
        documents = result.get("documents", [])
        print(f"📄 Page {page} - 수신된 가게 수: {len(documents)}")
        if not documents:
            break
        for place in documents:
            pid = place.get("id")
            if pid not in seen_ids:
                seen_ids.add(pid)
                collected.append(place)
    return collected


# ✅ CSV 저장
def save_to_csv(data, filename="청파동_맛집_50개.csv"):
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

# ✅ JSON 저장
def save_to_json(data, filename="청파동_맛집_50개.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ✅ 실행
if __name__ == "__main__":
    print(f"🔍 키워드 '{query}'로 청파동 맛집 50개 수집 중...")
    places = crawl_keyword_places(query, x, y, radius=3000, max_count=50)
    print(f"📦 청파동 맛집 수집 완료: {len(places)}개")

    save_to_csv(places)
    save_to_json(places)
    print("✅ 저장 완료! (CSV & JSON)")
