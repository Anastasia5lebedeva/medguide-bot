import requests

client_id = "3feff912-79fc-4d0a-9687-b15a67f9c00c_2b80845e-e204-46d5-88f9-b414afb0e545"
client_secret = "cBKObAzZqHE93C69ROh6NiO0BYnajg03upZABhyovGc="

def get_token(client_id, client_secret):
    url = "https://icdaccessmanagement.who.int/connect/token"
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'icdapi_access'
    }
    r = requests.post(url, data=data)
    r.raise_for_status()
    return r.json()["access_token"]

access_token = get_token(client_id, client_secret)
print("TOKEN:", access_token)
