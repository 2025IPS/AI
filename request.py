import requests

KAKAO_API_KEY = "815a330dcfb69987a6c219836b68598c"
headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
query = "먼데이피크닉"  # 음식점 이름

url = "https://dapi.kakao.com/v2/local/search/keyword.json"
params = {"query": query}

response = requests.get(url, headers=headers, params=params)
data = response.json()

if data['documents']:
    place = data['documents'][0]
    
    name = place.get("place_name", "")
    address = place.get("address_name", "")
    phone = place.get("phone", "")
    category = place.get("category_name", "")
    lat = place.get("y", "")
    lng = place.get("x", "")
    place_id = place.get("id", "")
    url = place.get("place_url", "")
    
    print("name:", name)
    print("address:", address)
    print("phone:", phone)
    print("category:", category)
    print("lat:", lat)
    print("lng:", lng)
    print("id:", place_id)
    print("url:", url)

    # CSV 형식으로도 출력
    print("\nCSV Format:")
    print(f"{name},{address},{phone},{category},{lat},{lng},{place_id},{url}")
else:
    print("장소를 찾을 수 없습니다.")
