import requests

BASE_URL = "http://0.0.0.0:8000/rest"

# -----------------------
# LOGIN
# -----------------------
login_data = {
    "username": "Derven",
    "password": "admin123"
}

response = requests.post(
    f"{BASE_URL}/login",
    data=login_data  # OAuth2PasswordRequestForm requires form data
)

tokens = response.json()

access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

print("Access Token:", access_token)
print("Refresh Token:", refresh_token)


# -----------------------
# CALL PROTECTED ENDPOINT
# -----------------------
headers = {
    "Authorization": f"Bearer {access_token}"
}

response = requests.get(
    f"{BASE_URL}/user",
    headers=headers
)

print("Current User:", response.json())


# -----------------------
# REFRESH TOKEN
# -----------------------
refresh_body = {
    "refresh_token": refresh_token
}

response = requests.post(
    f"{BASE_URL}/refresh",
    json=refresh_body
)

new_tokens = response.json()

print("New Access Token:", new_tokens["access_token"])