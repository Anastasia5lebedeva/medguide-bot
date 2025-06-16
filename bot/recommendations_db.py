import requests

API_URL = "http://api:8000"

def search_recommendations_by_icd(icd_code: str):
    url = f"{API_URL}/recommendations/{icd_code.upper()}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Ошибка {response.status_code} при запросе рекомендаций: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {e}")
        return []
