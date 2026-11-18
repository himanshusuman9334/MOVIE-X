
from flask import Flask, render_template, request
from recommender import recommend

app = Flask(__name__)


# Homepage 1 - Black and Red
@app.route("/")
def home():
    return render_template("MOVIE-X — Red_Black.html")


# Homepage 2 - White and Red
@app.route("/2")
def home2():
    return render_template("MOVIE-X.html")


# Movie recommendations with pagination
@app.route("/recommend", methods=["POST"])
def recommendation():

    movie_name = request.form.get("movie", "").strip()

    theme = request.form.get("theme", "light")

    try:
        page = int(request.form.get("page", 1))
    except (ValueError, TypeError):
        page = 1

    page = max(1, min(page, 500))

    source = request.form.get("source", "auto")

    if not movie_name:
        return render_template(
            "result.html",
            recommendations=[],
            message="Please enter a movie name.",
            theme=theme
        )

    result = recommend(movie_name, page, source)

    if result is None:
        return render_template(
            "result.html",
            recommendations=[],
            message="Unable to connect to TMDB. Please try again.",
            theme=theme
        )

    '''if not result["found"]:
        return render_template(
            "result.html",
            recommendations=[],
            message="Movie not found. Please try another title.",
            theme=theme
        )'''

    if result is None or result["found"] is None:
     return render_template(
         "result.html",
         recommendations=[],
          message="TMDB connection error. Please try again.",
         theme=theme
        )

    if not result["found"]:
     return render_template(
        "result.html",
        recommendations=[],
        message="Movie not found. Please try another title.",
        theme=theme
        )

    

    if not result["recommendations"]:
        message = "No recommendations available on this page."
    else:
        message = None

    return render_template(
        "result.html",
        recommendations=result["recommendations"],
        message=message,
        theme=theme,
        movie_name=movie_name,
        movie_title=result["movie_title"],
        current_page=result["page"],
        total_pages=result["total_pages"],
        total_results=result["total_results"],
        source=result["source"]
    )


if __name__ == "__main__":
    app.run(debug=True)
