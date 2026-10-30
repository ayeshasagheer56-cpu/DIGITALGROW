# DigitalGrow (digitalgrow.site)

Flask website with a SQLite backend. Visitors send a request through the contact form; you read leads at `/admin/leads`.

## Run locally
    pip install -r requirements.txt
    export ADMIN_USER=admin ADMIN_PASSWORD=choose-a-strong-password
    python app.py            # http://127.0.0.1:5000

## Deploy to digitalgrow.site
1. Put the folder on a VPS (or a host that runs Python, such as Render or Railway).
2. Set `ADMIN_PASSWORD` (and optionally `DB_PATH`) as environment variables. Do not leave the default password.
3. Run: `gunicorn -w 2 -b 127.0.0.1:8000 app:app`
4. Put Nginx (or the host's proxy) in front, point the domain's A record to the server, and enable HTTPS with Let's Encrypt.

## Edit content
Services are listed in the `SERVICES` list at the top of `app.py`; the page updates automatically.
