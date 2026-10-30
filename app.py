import os
import re
import sqlite3
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, Response, g, jsonify, render_template, request

app = Flask(__name__)
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "leads.db"))
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-me-now")

SERVICES = [
    {"slug": "social-media-management", "name": "Social media management",
     "summary": "We plan, post and reply on your accounts so your audience keeps hearing from you.",
     "includes": ["Content calendar", "Posting and community replies", "Monthly performance report"]},
    {"slug": "marketing", "name": "Marketing strategy",
     "summary": "A clear plan for who you sell to, where to reach them and what to spend.",
     "includes": ["Audience and competitor research", "Channel plan and budget", "Quarterly review"]},
    {"slug": "seo", "name": "SEO",
     "summary": "Get found on Google by people already searching for what you sell.",
     "includes": ["Keyword research", "Ranking and traffic tracking", "Link building"]},
    {"slug": "on-page-seo", "name": "On-page SEO",
     "summary": "We fix titles, headings, copy, images and internal links on each page.",
     "includes": ["Page-by-page audit", "Meta titles and descriptions", "Internal linking"]},
    {"slug": "technical-seo", "name": "Technical SEO",
     "summary": "We make your site fast, crawlable and error-free so search engines can index it.",
     "includes": ["Site speed and Core Web Vitals", "Sitemap, robots and indexing", "Schema markup"]},
    {"slug": "content-writing", "name": "Content writing",
     "summary": "Blog posts, web pages and product copy written to rank and to convert.",
     "includes": ["SEO blog articles", "Website and landing page copy", "Social captions"]},
    {"slug": "meta-tiktok-ads", "name": "Meta and TikTok ads",
     "summary": "Paid campaigns on Facebook, Instagram and TikTok built to bring in leads and sales.",
     "includes": ["Creative and ad copy", "Audience targeting", "Weekly optimisation"]},
    {"slug": "google-ads", "name": "Google Ads",
     "summary": "Search, Shopping and Display campaigns that put you in front of buyers right now.",
     "includes": ["Campaign setup", "Conversion tracking", "Bid and budget management"]},
    {"slug": "complete-digital-marketing", "name": "Complete digital marketing",
     "summary": "All of the above under one team, one plan and one monthly report.",
     "includes": ["SEO, content and ads together", "Social media included", "One point of contact"]},
]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                service TEXT,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )


def require_admin(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != ADMIN_USER or auth.password != ADMIN_PASSWORD:
            return Response("Login required", 401, {"WWW-Authenticate": 'Basic realm="DigitalGrow admin"'})
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def index():
    return render_template("index.html", services=SERVICES)


@app.post("/api/contact")
def contact():
    data = request.get_json(silent=True) or request.form
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()
    service = (data.get("service") or "").strip()
    message = (data.get("message") or "").strip()

    errors = {}
    if len(name) < 2:
        errors["name"] = "Enter your name."
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        errors["email"] = "Enter a valid email address."
    if len(message) < 10:
        errors["message"] = "Tell us a little about what you need (10+ characters)."
    if service and service not in {s["name"] for s in SERVICES}:
        errors["service"] = "Choose a service from the list."
    if data.get("website"):  # honeypot field: real visitors leave it empty
        return jsonify(ok=True)
    if errors:
        return jsonify(ok=False, errors=errors), 400

    db = get_db()
    db.execute(
        "INSERT INTO leads (name, email, phone, service, message, created_at) VALUES (?,?,?,?,?,?)",
        (name[:120], email[:200], phone[:40], service, message[:3000],
         datetime.now(timezone.utc).isoformat(timespec="seconds")),
    )
    db.commit()
    return jsonify(ok=True)


@app.route("/admin/leads")
@require_admin
def leads():
    rows = get_db().execute("SELECT * FROM leads ORDER BY id DESC").fetchall()
    return render_template("leads.html", leads=rows)


@app.route("/sitemap.xml")
def sitemap():
    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           '<url><loc>https://digitalgrow.site/</loc></url></urlset>')
    return Response(xml, mimetype="application/xml")


@app.route("/robots.txt")
def robots():
    return Response("User-agent: *\nDisallow: /admin/\nSitemap: https://digitalgrow.site/sitemap.xml\n",
                    mimetype="text/plain")


init_db()

if __name__ == "__main__":
    app.run(debug=True)
