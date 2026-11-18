
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# ---------------- CONFIGURATION ----------------

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

BASE_URL = "https://api.themoviedb.org/3"
IMAGE_URL = "https://image.tmdb.org/t/p/w500"

MOVIES_PER_PAGE = 20

# Cache results while Flask is running
MOVIE_CACHE = {}


# ---------------- TMDB REQUEST ----------------

def tmdb_request(endpoint, params=None):

    if not TMDB_API_KEY:
        print("TMDB API key is missing!")
        return None

    if params is None:
        params = {}

    params = params.copy()
    params["api_key"] = TMDB_API_KEY

    try:
        response = requests.get(
            BASE_URL + endpoint,
            params=params,
            timeout=20
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print("TMDB Error:", e)
        return None


# ---------------- SEARCH MOVIE ----------------

def search_movies(movie_name):

    data = tmdb_request(
        "/search/movie",
        {
            "query": movie_name,
            "language": "en-US",
            "include_adult": "false",
            "page": 1
        }
    )

    if data is None:
        return None

    return data.get("results", [])


# ---------------- NORMALIZE TITLE ----------------

def normalize_title(title):

    return " ".join(
        (title or "").lower().strip().split()
    )


# ---------------- GET MOVIE COLLECTION ----------------

def get_collection_movies(movie_id):

    movies = []

    # Get movie details
    details = tmdb_request(
        f"/movie/{movie_id}",
        {"language": "en-US"}
    )

    if not details:
        return movies

    collection = details.get("belongs_to_collection")

    if not collection:
        return movies

    collection_id = collection.get("id")

    if not collection_id:
        return movies

    # Get all movies in the collection
    data = tmdb_request(
        f"/collection/{collection_id}",
        {"language": "en-US"}
    )

    if not data:
        return movies

    parts = data.get("parts", [])

    # Sort collection movies by release date
    parts.sort(
        key=lambda item: item.get("release_date") or "9999"
    )

    return parts


# ---------------- GET SIMILAR MOVIES ----------------

def get_similar_movies(movie_id):

    movies = []

    # TMDB recommendations
    recommendations = tmdb_request(
        f"/movie/{movie_id}/recommendations",
        {
            "language": "en-US",
            "page": 1
        }
    )

    if recommendations:
        movies.extend(recommendations.get("results", []))

    # TMDB similar movies
    similar = tmdb_request(
        f"/movie/{movie_id}/similar",
        {
            "language": "en-US",
            "page": 1
        }
    )

    if similar:
        movies.extend(similar.get("results", []))

    return movies


# ---------------- BUILD MOVIE LIST ----------------

def build_movie_list(movie_name):

    search_results = search_movies(movie_name)

    if search_results is None:
        return None, None

    if not search_results:
        return None, []

    query = normalize_title(movie_name)

    # Find exact movie first
    selected_movie = None

    for item in search_results:

        if normalize_title(item.get("title")) == query:
            selected_movie = item
            break

        if normalize_title(item.get("original_title")) == query:
            selected_movie = item
            break

    # If no exact match, use TMDB's first search result
    if selected_movie is None:
        selected_movie = search_results[0]

    movie_id = selected_movie["id"]

    all_movies = []

    # 1. Exact searched movie
    all_movies.append(selected_movie)

    # 2. Movies from the same collection
    collection_movies = get_collection_movies(movie_id)
    all_movies.extend(collection_movies)

    # 3. Movies with matching names
    for item in search_results:

        title = normalize_title(item.get("title"))
        original_title = normalize_title(
            item.get("original_title")
        )

        if query in title or query in original_title:
            all_movies.append(item)

    # 4. Similar and recommended movies
    similar_movies = get_similar_movies(movie_id)
    all_movies.extend(similar_movies)

    # Remove duplicate movies
    unique_movies = []
    seen_ids = set()

    for item in all_movies:

        item_id = item.get("id")
        title = item.get("title")

        if not item_id or not title or not item.get("poster_path"):
         continue

        if item_id in seen_ids:
            continue

        seen_ids.add(item_id)
        unique_movies.append(item)

    return selected_movie, unique_movies


# ---------------- MAIN RECOMMEND FUNCTION ----------------

def recommend(movie_name, page=1, source="auto"):

    movie_name = movie_name.strip()

    if not movie_name:
        return None

    try:
        page = max(1, int(page))
    except (ValueError, TypeError):
        page = 1

    # Cache based on searched movie name
    cache_key = normalize_title(movie_name)

    if cache_key in MOVIE_CACHE:

        selected_movie, all_movies = MOVIE_CACHE[cache_key]

    else:

        selected_movie, all_movies = build_movie_list(movie_name)

        if selected_movie is None and all_movies is None:
            return {
                "found": None,
                "error": "TMDB connection error",
                "recommendations": []
            }

        if not all_movies:
            return {
                "found": False,
                "recommendations": [],
                "page": 1,
                "total_pages": 1,
                "total_results": 0,
                "source": "auto"
            }

        MOVIE_CACHE[cache_key] = (
            selected_movie,
            all_movies
        )

    # Pagination
    total_results = len(all_movies)

    total_pages = max(
        1,
        (total_results + MOVIES_PER_PAGE - 1)
        // MOVIES_PER_PAGE
    )

    page = min(page, total_pages)

    start = (page - 1) * MOVIES_PER_PAGE
    end = start + MOVIES_PER_PAGE

    page_movies = all_movies[start:end]

    # Prepare results for result.html
    recommendations = []

    for item in page_movies:

        poster_path = item.get("poster_path")

        poster = (
            IMAGE_URL + poster_path
            if poster_path
            else None
        )

        recommendations.append({
            "title": item.get("title"),
            "poster": poster
        })

    return {
        "found": True,
        "movie_title": selected_movie.get("title"),
        "recommendations": recommendations,
        "page": page,
        "total_pages": total_pages,
        "total_results": total_results,
        "source": "auto"
    }
