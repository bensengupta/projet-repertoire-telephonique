from flask import Flask, render_template, g, abort, request, redirect, url_for
from flask_assets import Environment, Bundle
from pathlib import Path
import sqlite3

app = Flask(__name__)

DATABASE = "./telephones.db"
LISTINGS_PER_PAGE = 10

# Tailwind CSS bundle
assets = Environment(app)
assets.config[
    "POSTCSS_BIN"
] = f"{Path(__file__).parent.absolute()}/node_modules/.bin/postcss"

tailwindcss = Bundle(
    "css/tailwind.css", filters="postcss", output="dist/css/tailwind.css"
)
assets.register("tailwindcss", tailwindcss)


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def seed_database():
    """Reset database and create all tables."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DROP TABLE PHONE_DIR")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS PHONE_DIR (id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, name TEXT, email TEXT, address TEXT, region TEXT, phone TEXT)"
    )
    data = [
        (
            "Alex",
            "alex@gmail.com",
            "72 avenue des Choux bleux, 07320 Nullepart-sur-rien",
            "Alpes Maritimes, France",
            "+33 6 98 08 75 64",
        ),
        (
            "Ben",
            "ben@gmail.com",
            "72 avenue des Choux bleux, 07320 Nullepart-sur-rien",
            "Alpes Maritimes, France",
            "+33 7 75 03 56 63",
        ),
        (
            "Nathan",
            "nathan@gmail.com",
            "72 avenue des Choux bleux, 07320 Nullepart-sur-rien",
            "Ontario, Canada",
            "+1 3 65 73 92 37",
        ),
        (
            "Suzie",
            "suzie@gmail.com",
            "72 avenue des Choux bleux, 07320 Nullepart-sur-rien",
            "Stuttgart, Allemagne",
            "+46 3 65 73 94 37",
        ),
    ]
    cur.executemany(
        "INSERT INTO PHONE_DIR(name, email, address, region, phone) VALUES(?, ?, ?, ?, ?)",
        data,
    )
    conn.commit()
    cur.close()


@app.route("/resetDB")
def resetDB():
    # 1. erase database
    # 2. create table
    # 3. insert sample data
    seed_database()
    return "Successfully reset db"


@app.route("/")
def index():
    return render_template("menu.html")


@app.route("/ajouter", methods=["GET", "POST"])
def ajouter():
    if request.method == "GET":
        return render_template("ajouter.html")

    if request.method == "POST":
        prenom = request.form.get("first_name")
        nom = request.form.get("last_name")
        email = request.form.get("email_address")
        tel = request.form.get("phone_number")
        pays = request.form.get("country")
        rue = request.form.get("street_address")
        ville = request.form.get("city")
        departement = request.form.get("state")
        code_postal = request.form.get("postal_code")

        if prenom and nom and email and tel and pays and rue and ville and code_postal:
            nom = f"{prenom} {nom}"  # prenom + " " + nom
            adresse = f"{rue}, {code_postal} {ville}"
            region = ""
            if departement:
                region = f"{departement}, {pays}"
            else:
                region = pays

            conn = get_db()
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO PHONE_DIR(name, email, address, region, phone) VALUES(?, ?, ?, ?, ?)",
                (nom, email, adresse, region, tel),
            )
            conn.commit()

            return redirect(url_for("liste", page=1))
        else:
            abort(400)


@app.route("/supprimer/<int:id>", methods=["POST"])
def supprimer(id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM PHONE_DIR WHERE id=?", (id,))

    conn.commit()

    return redirect(url_for("liste", page=1))


@app.route("/recherche", methods=["GET", "POST"])
def recherche():
    if request.method == "GET":
        return render_template("recherche.html")

    if request.method == "POST":
        search = request.form.get("search")
        if search:
            return redirect(url_for("liste", page=1, q=search))


@app.route("/liste/<int:page>")
def liste(page):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM PHONE_DIR")
    conn.commit()

    listings = cur.fetchone()[0]
    current_page = page
    max_page = listings // LISTINGS_PER_PAGE + 1
    listings_page_start = LISTINGS_PER_PAGE * (page - 1) + 1
    listings_page_end = min(LISTINGS_PER_PAGE * page, listings)

    stats = {
        "listings": listings,
        "current_page": current_page,
        "max_page": max_page,
        "listings_page_start": listings_page_start,
        "listings_page_end": listings_page_end,
    }

    if page > listings // LISTINGS_PER_PAGE + 1 or page <= 0:
        abort(404)

    query = f"""
SELECT  id, name, email, address, region, phone
FROM    ( SELECT    ROW_NUMBER() OVER ( ORDER BY name ) AS RowNum, *
          FROM      PHONE_DIR
        ) AS RowConstrainedResult
WHERE   RowNum >= ?
    AND RowNum <= ?
ORDER BY RowNum
    """
    query_params = (listings_page_start, listings_page_end)

    if request.args.get("q"):
        q = f"%{request.args.get('q')}%"
        query = f"""
SELECT  id, name, email, address, region, phone
FROM    ( SELECT    ROW_NUMBER() OVER ( ORDER BY name ) AS RowNum, *
        FROM      PHONE_DIR
        WHERE name LIKE ? OR email LIKE ? OR phone LIKE ? OR address LIKE ? OR region LIKE ?
        ) AS RowConstrainedResult
WHERE   RowNum >= ?
    AND RowNum <= ?
ORDER BY RowNum
        """
        query_params = (q, q, q, q, q, listings_page_start, listings_page_end)

        cur.execute(
            "SELECT COUNT(*) FROM PHONE_DIR WHERE name LIKE ? OR email LIKE ? OR phone LIKE ? OR address LIKE ? OR region LIKE ?",
            (q, q, q, q, q),
        )
        conn.commit()

        listings = cur.fetchone()[0]
        current_page = page
        max_page = listings // LISTINGS_PER_PAGE + 1
        listings_page_start = LISTINGS_PER_PAGE * (page - 1) + 1
        listings_page_end = min(LISTINGS_PER_PAGE * page, listings)

        stats = {
            "listings": listings,
            "current_page": current_page,
            "max_page": max_page,
            "listings_page_start": listings_page_start,
            "listings_page_end": listings_page_end,
        }

    # from https://stackoverflow.com/a/109290/13218424

    cur.execute(query, query_params)
    conn.commit()

    data = cur.fetchall()

    return render_template("liste.html", data=data, pages=stats)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",  # Establishes the host, required for repl to detect the site
        port=3000,
        debug=True,
    )
