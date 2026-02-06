from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, url_for

DB_PATH = Path("reviews.db")

app = Flask(__name__)


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    connection = get_connection()
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            director TEXT NOT NULL,
            length INTEGER NOT NULL,
            genre TEXT NOT NULL,
            year INTEGER NOT NULL,
            image_url TEXT NOT NULL,
            score_overall REAL NOT NULL,
            review_title TEXT NOT NULL,
            review_body TEXT NOT NULL,
            tags TEXT NOT NULL,
            score_cinematography REAL NOT NULL,
            score_acting REAL NOT NULL,
            score_story REAL NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    count = connection.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    if count == 0:
        seed_reviews(connection)
    connection.commit()
    connection.close()


def seed_reviews(connection: sqlite3.Connection) -> None:
    sample_reviews = [
        {
            "title": "Midnight Overdrive",
            "director": "Ava Lin",
            "length": 128,
            "genre": "Neo-noir",
            "year": 2024,
            "image_url": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=900&q=80",
            "score_overall": 4.8,
            "review_title": "Neon, noir, and a relentless chase",
            "review_body": "Rain-slicked asphalt, a low synth note, and a camera glide that whispers, 'stay in the dark.' The opening minutes establish the stakes with confident visual storytelling and a score that sticks like neon on a windshield. The midsection lingers on exposition, but the payoff is sharp and stylish.",
            "tags": "2024, Movie, USA, Noir, Thriller",
            "score_cinematography": 5,
            "score_acting": 4.5,
            "score_story": 4.5,
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "title": "Theatre of the Tides",
            "director": "Mateo Cruz",
            "length": 112,
            "genre": "Drama",
            "year": 2023,
            "image_url": "https://images.unsplash.com/photo-1497032628192-86f99bcd76bc?auto=format&fit=crop&w=900&q=80",
            "score_overall": 4.5,
            "review_title": "Waves of emotion and quiet power",
            "review_body": "Gentle, emotional storytelling that rolls like waves. Performances are intimate and luminous, and the sound design makes every sea breeze feel close enough to touch. It holds a steady pace and closes with a soft, satisfying grace note.",
            "tags": "2023, Movie, Mexico, Drama, Romance",
            "score_cinematography": 4.5,
            "score_acting": 4.5,
            "score_story": 4.0,
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "title": "Velvet Projector",
            "director": "Kira Sol",
            "length": 98,
            "genre": "Mystery",
            "year": 2022,
            "image_url": "https://images.unsplash.com/photo-1460881680858-30d872d5b530?auto=format&fit=crop&w=900&q=80",
            "score_overall": 4.2,
            "review_title": "A classic whodunit with theatrical flair",
            "review_body": "A classic whodunit with theatrical flair. The set design feels like an old playhouse, and the twists keep the audience leaning into the aisle. It never rushes, letting every clue breathe before the final curtain fall.",
            "tags": "2022, Movie, France, Mystery, Noir",
            "score_cinematography": 4.0,
            "score_acting": 4.0,
            "score_story": 4.0,
            "created_at": datetime.utcnow().isoformat(),
        },
    ]
    connection.executemany(
        """
        INSERT INTO reviews (
            title,
            director,
            length,
            genre,
            year,
            image_url,
            score_overall,
            review_title,
            review_body,
            tags,
            score_cinematography,
            score_acting,
            score_story,
            created_at
        ) VALUES (
            :title,
            :director,
            :length,
            :genre,
            :year,
            :image_url,
            :score_overall,
            :review_title,
            :review_body,
            :tags,
            :score_cinematography,
            :score_acting,
            :score_story,
            :created_at
        )
        """,
        sample_reviews,
    )


def fetch_reviews() -> list[sqlite3.Row]:
    connection = get_connection()
    reviews = connection.execute(
        "SELECT * FROM reviews ORDER BY created_at DESC"
    ).fetchall()
    connection.close()
    return reviews


@app.route("/")
def home() -> str:
    reviews = fetch_reviews()
    return render_template("index.html", reviews=reviews)


@app.route("/reviews/<int:review_id>")
def review_detail(review_id: int) -> str:
    connection = get_connection()
    review = connection.execute(
        "SELECT * FROM reviews WHERE id = ?", (review_id,)
    ).fetchone()
    connection.close()
    if review is None:
        abort(404)
    return render_template("review.html", review=review)


@app.route("/opinion")
def opinion() -> str:
    return render_template("opinion.html")


@app.route("/tags")
def tags() -> str:
    reviews = fetch_reviews()
    tag_set: set[str] = set()
    years: set[str] = set()
    genres: set[str] = set()
    for review in reviews:
        years.add(str(review["year"]))
        genres.add(review["genre"])
        for tag in review["tags"].split(","):
            tag_set.add(tag.strip())
    return render_template(
        "tags.html",
        all_tags=sorted(tag_set),
        years=sorted(years),
        genres=sorted(genres),
    )


@app.route("/admin", methods=["GET", "POST"])
def admin() -> str:
    if request.method == "POST":
        payload = {
            "title": request.form["title"].strip(),
            "director": request.form["director"].strip(),
            "length": int(request.form["length"]),
            "genre": request.form["genre"].strip(),
            "year": int(request.form["year"]),
            "image_url": request.form["image_url"].strip(),
            "score_overall": float(request.form["score_overall"]),
            "review_title": request.form["review_title"].strip(),
            "review_body": request.form["review_body"].strip(),
            "tags": request.form["tags"].replace("/", ",").strip(),
            "score_cinematography": float(request.form["score_cinematography"]),
            "score_acting": float(request.form["score_acting"]),
            "score_story": float(request.form["score_story"]),
            "created_at": datetime.utcnow().isoformat(),
        }
        connection = get_connection()
        cursor = connection.execute(
            """
            INSERT INTO reviews (
                title,
                director,
                length,
                genre,
                year,
                image_url,
                score_overall,
                review_title,
                review_body,
                tags,
                score_cinematography,
                score_acting,
                score_story,
                created_at
            ) VALUES (
                :title,
                :director,
                :length,
                :genre,
                :year,
                :image_url,
                :score_overall,
                :review_title,
                :review_body,
                :tags,
                :score_cinematography,
                :score_acting,
                :score_story,
                :created_at
            )
            """,
            payload,
        )
        connection.commit()
        review_id = cursor.lastrowid
        connection.close()
        return redirect(url_for("review_detail", review_id=review_id))
    return render_template("admin.html")


init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
