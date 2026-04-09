import requests
import json

def test_chat():
    url = "http://127.0.0.1:8000/api/chat"
    payload = {
        "message": "Làm sao để xuất hóa đơn VAT cho chuyến đi?"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print("Response Body:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_chat()
