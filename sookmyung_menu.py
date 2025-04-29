import requests
import csv
import json
import random

# ✅ 카카오 API 설정
API_KEY = "815a330dcfb69987a6c219836b68598c"
headers = {"Authorization": f"KakaoAK {API_KEY}"}

# ✅ 대상 지역의 중심 좌표
locations = {
    "청파동": (126.9648, 37.5456),
    "효창동": (126.9633, 37.5405),
    "남영동": (126.9721, 37.5417),
    "갈월동": (126.9726, 37.5481),
}

# ✅ 사용자 프로필
user_profile = {
    "예산": 10000,
    "선호": ["덮밥", "파스타"],
    "비선호": ["마라", "양꼬치"],
    "음주": False
}

# ✅ 좌표 기반 검색 함수
def search_places_by_location(x, y, radius=1000, page=1):
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    params = {
        "category_group_code": "FD6",
        "x": x,
        "y": y,
        "radius": radius,
        "page": page,
        "size": 15
    }
    res = requests.get(url, headers=headers, params=params)
    try:
        return res.json()
    except Exception as e:
        print("[ERROR] JSON 디코딩 실패:", e)
        return {}

# ✅ 지역별 전체 수집 함수
def crawl_by_regions(location_dict):
    all_data = []
    seen_ids = set()
    for region, (x, y) in location_dict.items():
        print(f"📍 {region} 지역 수집 중...")
        for page in range(1, 46):  # 최대 45페이지
            result = search_places_by_location(x, y, page=page)
            documents = result.get("documents", [])
            if not documents:
                break
            for place in documents:
                pid = place.get("id")
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    all_data.append(place)
    return all_data

# ✅ 사용자 필터링
def filter_by_preferences(places, user):
    filtered = []
    for p in places:
        name = p['place_name']
        category = p['category_name']
        address = p['address_name']
        price_dummy = 8000  # 실제 가격 정보 없음
        if any(bad in name for bad in user["비선호"]):
            continue
        if not user["음주"] and "술집" in category:
            continue
        if price_dummy > user["예산"]:
            continue
        filtered.append(p)
    return filtered

# ✅ 퀵픽 기능
def quick_pick(places, user):
    filtered = filter_by_preferences(places, user)
    return random.choice(filtered) if filtered else None

# ✅ CSV 저장
def save_to_csv(data, filename="filtered_places.csv"):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["name", "address", "phone", "category", "lat", "lng", "id", "url"])
        for place in data:
            writer.writerow([
                place['place_name'],
                place['address_name'],
                place.get('phone', ''),
                place.get('category_name', ''),
                place['y'],
                place['x'],
                place.get('id', ''),
                place.get('place_url', '')
            ])

# ✅ JSON 저장
def save_to_json(data, filename="filtered_places.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ✅ 실행
if __name__ == "__main__":
    print("🔍 청파동·효창동·남영동·갈월동 맛집 수집 중...")
    places = crawl_by_regions(locations)
    print(f"📦 중복 제거 후 총 수집: {len(places)}개")

    user_filtered = filter_by_preferences(places, user_profile)

    save_to_csv(user_filtered)
    save_to_json(user_filtered)
    print("✅ 필터링된 결과 저장 완료!")

    pick = quick_pick(user_filtered, user_profile)
    if pick:
        print(f"\n🎲 퀵픽 추천: {pick['place_name']} ({pick['address_name']})")
    else:
        print("😢 조건에 맞는 퀵픽 결과가 없습니다.")