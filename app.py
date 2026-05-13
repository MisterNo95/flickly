from __future__ import annotations

import sqlite3
from datetime import datetime
import html
import re
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, send_from_directory, url_for
from urllib.parse import unquote
from markupsafe import Markup

DB_PATH = Path("reviews.db")
IMG_PATH = Path("img")

app = Flask(__name__)


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA busy_timeout = 5000")
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
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS featurettes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            image_url TEXT NOT NULL,
            body TEXT NOT NULL,
            tags TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            body TEXT,
            note_type TEXT,
            note_date TEXT,
            content TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    migrate_updates_table(connection)
    count = connection.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    if count == 0:
        seed_reviews(connection)
    updates_count = connection.execute("SELECT COUNT(*) FROM updates").fetchone()[0]
    if updates_count == 0:
        seed_updates(connection)
    featurettes_count = connection.execute(
        "SELECT COUNT(*) FROM featurettes"
    ).fetchone()[0]
    if featurettes_count == 0:
        seed_featurettes(connection)
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


def seed_updates(connection: sqlite3.Connection) -> None:
    sample_updates = [
        {
            "title": "Late-night screening",
            "body": "Tonight's watch: a 90s thriller marathon. I'll post quick notes after the credits.",
            "note_type": "Quick rant",
            "note_date": "Aug 20, 2024",
            "content": "Tonight's watch: a 90s thriller marathon. I'll post quick notes after the credits.",
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "title": "Practical beats digital",
            "body": "Hot take: practical sets still beat CGI when it comes to mood and texture.",
            "note_type": "Editorial",
            "note_date": "Aug 18, 2024",
            "content": "Hot take: practical sets still beat CGI when it comes to mood and texture.",
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "title": "Festival season",
            "body": "Festival season is here—send me your hidden gems.",
            "note_type": "Update",
            "note_date": "Aug 10, 2024",
            "content": "Festival season is here—send me your hidden gems.",
            "created_at": datetime.utcnow().isoformat(),
        },
    ]
    connection.executemany(
        """
        INSERT INTO updates (title, body, note_type, note_date, content, created_at)
        VALUES (:title, :body, :note_type, :note_date, :content, :created_at)
        """,
        sample_updates,
    )


def seed_featurettes(connection: sqlite3.Connection) -> None:
    sample_featurettes = [
        {
            "title": "The art of silence in cinema",
            "image_url": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=900&q=80",
            "body": "## The hush before the score\nSilence gives a scene room to breathe. When directors trust stillness, every footstep and breath becomes part of the story.\n\n## Why it matters\nWe remember the quiet moments because they let the audience step inside the frame.",
            "tags": "Analysis, Sound, Craft",
            "created_at": datetime.utcnow().isoformat(),
        }
    ]
    connection.executemany(
        "INSERT INTO featurettes (title, image_url, body, tags, created_at) VALUES (:title, :image_url, :body, :tags, :created_at)",
        sample_featurettes,
    )


def migrate_updates_table(connection: sqlite3.Connection) -> None:
    existing_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(updates)").fetchall()
    }
    migrations = {
        "title": "ALTER TABLE updates ADD COLUMN title TEXT",
        "body": "ALTER TABLE updates ADD COLUMN body TEXT",
        "note_type": "ALTER TABLE updates ADD COLUMN note_type TEXT",
        "note_date": "ALTER TABLE updates ADD COLUMN note_date TEXT",
    }
    for column, statement in migrations.items():
        if column not in existing_columns:
            connection.execute(statement)


def fetch_reviews(offset: int = 0, limit: int | None = None) -> list[sqlite3.Row]:
    connection = get_connection()
    base_query = "SELECT * FROM reviews ORDER BY created_at DESC"
    if limit is None:
        reviews = connection.execute(base_query).fetchall()
    else:
        reviews = connection.execute(
            f"{base_query} LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    connection.close()
    return reviews


def count_reviews() -> int:
    connection = get_connection()
    total = connection.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    connection.close()
    return total


def fetch_updates(limit: int | None = 3) -> list[sqlite3.Row]:
    connection = get_connection()
    query = """
        SELECT
            id,
            COALESCE(title, 'Lobby note') AS title,
            COALESCE(body, content, '') AS body,
            COALESCE(note_type, 'Update') AS note_type,
            COALESCE(note_date, '') AS note_date,
            created_at
        FROM updates
        ORDER BY created_at DESC
    """
    if limit is None:
        updates = connection.execute(query).fetchall()
    else:
        updates = connection.execute(f"{query} LIMIT ?", (limit,)).fetchall()
    connection.close()
    return updates


def fetch_featurettes() -> list[sqlite3.Row]:
    connection = get_connection()
    featurettes = connection.execute(
        "SELECT * FROM featurettes ORDER BY created_at DESC"
    ).fetchall()
    connection.close()
    return featurettes


def parse_tags(raw: str) -> list[str]:
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def normalize_tag(tag: str) -> str:
    return tag.strip().lower()


def review_tag_set(review: sqlite3.Row) -> set[str]:
    tags = {normalize_tag(tag) for tag in parse_tags(review["tags"])}
    tags.add(normalize_tag(review["genre"]))
    tags.add(normalize_tag(str(review["year"])))
    return tags


def featurette_tag_set(featurette: sqlite3.Row) -> set[str]:
    return {normalize_tag(tag) for tag in parse_tags(featurette["tags"])}


def normalize_image_path(raw_image: str) -> str:
    image = raw_image.strip()
    if image.startswith(("http://", "https://", "/")):
        return image
    return f"/img/{Path(image).name}"


def build_tag_catalog(reviews: list[sqlite3.Row], featurettes: list[sqlite3.Row]) -> dict:
    tag_counts: dict[str, int] = {}
    years: dict[str, int] = {}
    genres: dict[str, int] = {}
    for review in reviews:
        years[str(review["year"])] = years.get(str(review["year"]), 0) + 1
        genres[review["genre"]] = genres.get(review["genre"], 0) + 1
        for tag in parse_tags(review["tags"]):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    for featurette in featurettes:
        for tag in parse_tags(featurette["tags"]):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    return {
        "tags": dict(sorted(tag_counts.items(), key=lambda item: item[0].lower())),
        "years": dict(sorted(years.items(), key=lambda item: item[0])),
        "genres": dict(sorted(genres.items(), key=lambda item: item[0].lower())),
    }


def format_review_body(text: str) -> Markup:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
    escaped = re.sub(r"__(.+?)__", r"<u>\1</u>", escaped)
    lines = []
    for line in escaped.splitlines():
        if line.startswith("## "):
            lines.append(f"<span class=\"review-heading\">{line[3:]}</span>")
        elif line.startswith("### "):
            lines.append(f"<span class=\"review-heading small\">{line[4:]}</span>")
        else:
            lines.append(line)
    return Markup("<br>".join(lines))


@app.route("/")
def home() -> str:
    reviews = fetch_reviews()
    return render_template(
        "index.html",
        reviews=reviews[:8],
        reviews_count=len(reviews),
        updates=fetch_updates(),
        featurettes=fetch_featurettes()[:3],
    )


@app.route("/reviews")
def reviews() -> str:
    page = int(request.args.get("page", 1))
    per_page = 9
    total = count_reviews()
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    offset = (page - 1) * per_page
    return render_template(
        "reviews.html",
        reviews=fetch_reviews(offset=offset, limit=per_page),
        page=page,
        total_pages=total_pages,
    )


@app.route("/featurettes")
def featurettes() -> str:
    return render_template("featurettes.html", featurettes=fetch_featurettes())


@app.route("/featurettes/<int:featurette_id>")
def featurette_detail(featurette_id: int) -> str:
    connection = get_connection()
    featurette = connection.execute(
        "SELECT * FROM featurettes WHERE id = ?", (featurette_id,)
    ).fetchone()
    connection.close()
    if featurette is None:
        abort(404)
    return render_template(
        "featurette.html",
        featurette=featurette,
        formatted_body=format_review_body(featurette["body"]),
    )


@app.route("/reviews/<int:review_id>")
def review_detail(review_id: int) -> str:
    connection = get_connection()
    review = connection.execute(
        "SELECT * FROM reviews WHERE id = ?", (review_id,)
    ).fetchone()
    connection.close()
    if review is None:
        abort(404)
    return render_template(
        "review.html",
        review=review,
        formatted_body=format_review_body(review["review_body"]),
    )


@app.route("/updates")
def updates() -> str:
    return render_template("opinion.html", updates=fetch_updates(limit=None))


@app.route("/about")
def about() -> str:
    return render_template("about.html")


@app.route("/tags")
def tags() -> str:
    reviews = fetch_reviews()
    featurettes = fetch_featurettes()
    catalog = build_tag_catalog(reviews, featurettes)
    return render_template(
        "tags.html",
        all_tags=catalog["tags"],
        years=catalog["years"],
        genres=catalog["genres"],
        selected_tag=None,
        filtered_reviews=[],
        filtered_featurettes=[],
    )


@app.route("/tags/<tag>")
def tag_filter(tag: str) -> str:
    reviews = fetch_reviews()
    featurettes = fetch_featurettes()
    catalog = build_tag_catalog(reviews, featurettes)
    selected = normalize_tag(unquote(tag))
    filtered_reviews = [
        review for review in reviews if selected in review_tag_set(review)
    ]
    filtered_featurettes = [
        featurette
        for featurette in featurettes
        if selected in featurette_tag_set(featurette)
    ]
    return render_template(
        "tags.html",
        all_tags=catalog["tags"],
        years=catalog["years"],
        genres=catalog["genres"],
        selected_tag=unquote(tag),
        filtered_reviews=filtered_reviews,
        filtered_featurettes=filtered_featurettes,
    )


@app.route("/admin", methods=["GET", "POST"])
def admin() -> str:
    if request.method == "POST":
        if request.form.get("form_type") == "update":
            title = request.form["title"].strip()
            body = request.form["body"].strip()
            note_type = request.form["note_type"].strip()
            note_date = request.form["note_date"].strip()
            if body:
                connection = get_connection()
                connection.execute(
                    """
                INSERT INTO updates (
                        title,
                        body,
                        note_type,
                        note_date,
                        content,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        title,
                        body,
                        note_type,
                        note_date,
                        body,
                        datetime.utcnow().isoformat(),
                    ),
                )
                connection.commit()
                connection.close()
            return redirect(url_for("home"))
        if request.form.get("form_type") == "featurette":
            payload = {
                "title": request.form["title"].strip(),
                "image_url": normalize_image_path(request.form["image_url"]),
                "body": request.form["body"].strip(),
                "tags": request.form["tags"].replace("/", ",").strip(),
                "created_at": datetime.utcnow().isoformat(),
            }
            connection = get_connection()
            cursor = connection.execute(
                """
                INSERT INTO featurettes (
                    title,
                    image_url,
                    body,
                    tags,
                    created_at
                ) VALUES (
                    :title,
                    :image_url,
                    :body,
                    :tags,
                    :created_at
                )
                """,
                payload,
            )
            connection.commit()
            featurette_id = cursor.lastrowid
            connection.close()
            return redirect(url_for("featurette_detail", featurette_id=featurette_id))
        payload = {
            "title": request.form["title"].strip(),
            "director": request.form["director"].strip(),
            "length": int(request.form["length"]),
            "genre": request.form["genre"].strip(),
            "year": int(request.form["year"]),
            "image_url": normalize_image_path(request.form["image_url"]),
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


@app.route("/img/<path:filename>")
def uploaded_image(filename: str):
    return send_from_directory(IMG_PATH, filename)


init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
