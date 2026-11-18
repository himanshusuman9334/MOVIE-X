import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")

print("API KEY FOUND:", API_KEY is not None)
print("API KEY LENGTH:", len(API_KEY) if API_KEY else 0)

url = "https://api.themoviedb.org/3/search/movie"

params = {
    "api_key": API_KEY,
    "query": "Thor"
}

response = requests.get(url, params=params, timeout=20)

print("STATUS:", response.status_code)
print(response.text[:500])