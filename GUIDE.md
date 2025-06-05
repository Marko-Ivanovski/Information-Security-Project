# Implementation & Testing Checklist

Below is a recommended order in which to build & verify each piece. You can tick them off as you complete and test each item.

## Project Boilerplate & Environment

* Create the folder structure (as outlined earlier).
* Write a minimal `run.py` and `app/__init__.py` that instantiates Flask, loads `.env`, and hooks up SQLAlchemy.
* Create `docker-compose.yml` with `web`, `db`, and `files` services.
* Verify that `docker-compose up --build` spins up:

  * Flask container (port 5000),
  * Postgres container,
  * Files volume (no errors).
* Test in PyCharm: running `run.py` locally (without Docker) still loads Flask and prints “Hello, World” on `/`.

## Database Models

* In `app/models.py`, define:

  * `User` table with columns `(id, username TEXT UNIQUE, public_value TEXT)`.
  * `FileMetadata` table with `(id, owner_id FK→User.id, original_filename TEXT, stored_path TEXT, upload_timestamp TIMESTAMP, sha256_hash TEXT, description TEXT)`.
* Configure Flask-Migrate (optional) so you can `flask db init/migrate/upgrade`.
* **Test:** Run a quick script (or Flask shell) to create tables and do a “ping” to confirm Postgres connectivity:

  ```python
  >>> from app import db
  >>> db.create_all()
  >>> User(username="test", public_value="abc").save()
  ```
* Verify in `psql` that the tables exist and the row is inserted.

## ZKP Primitives Module (`app/zkp.py`)

* Select a simple protocol (e.g. Schnorr over a known safe prime).
* Implement functions:

  * `generate_keypair()` → returns `(secret_x, public_V)`
  * `create_commitment()` → returns `(R, r_nonce)`
  * `compute_challenge_response(r_nonce, secret_x, challenge_c)` → returns `s`
  * `verify_proof(public_V, R, s, challenge_c)` → returns `True/False`
* **Unit Tests:**

  * Test that `verify_proof(...)` returns `True` when you feed it correctly derived `(R, s, c)`.
  * Test that if you alter `s` or `c`, verification fails.
  * (If using “symmetric” parameters, store them in a config file or constants—e.g. `p, q, g`.)

## Authentication Blueprint (`app/auth.py`)

* **`/register` (POST)**

  * Reads JSON `{ username, public_value }`.
  * Inserts into `User` if no conflict; else returns `400 “Username taken.”`
* **`/login/initiate` (POST or GET)**

  * Takes `{ username }`; looks up `public_V`; generates a random challenge `c` (e.g. 128‐bit integer); stores `(username → c, R)` in a short‐lived in‐memory store (e.g. a Python dict keyed by session ID or a temporary table). Returns JSON `{ challenge: c }`.
* **`/login/verify` (POST)**

  * Takes `{ username, R, s }`. Looks up stored `(public_V, challenge c, R)` from the initiate step; runs `verify_proof(public_V, R, s, c)`.
  * If valid: create a Flask session, set `session["user_id"] = the user’s ID`; return `200` → redirect to `/dashboard`.
  * If invalid: return `401` → “Invalid proof.”
  * Protect all subsequent routes with a decorator that checks `session.get("user_id")`; if missing, redirect to `/login`.

## Basic Front‐End Templates (HTML)

* **`base.html`**

  * Contains a simple `<nav>` with conditional links (“Dashboard” / “Logout” if user is logged in; else “Login” / “Register”).
  * `{% block content %}{% endblock %}` for child templates.
* **`register.html`**

  * Form that asks “Username” and “Secret (passphrase).” JavaScript on the client will convert the passphrase into `public_V` (e.g. via a lightweight ECC or modular-exponentiation library).
  * When submitted, send AJAX (or normal POST) to `/register`.
* **`login.html`**

  * Form that asks “Username” and “Secret.”
  * JS step 1: send `{ username }` to `/login/initiate` to get challenge `c`.
  * JS step 2: client computes `(R, s)`, then POSTs `{ username, R, s }` to `/login/verify`.
  * If success, `window.location = /dashboard`.
  * **Test (manual):**

    * Visit `/register`, register a user.
    * Visit `/login`, attempt correct / incorrect secrets, verify success vs. failure flows.

## File Upload Logic (`app/routes.py`)

* Create a Flask blueprint (e.g. `main_bp`) in `routes.py`.
* **`/dashboard` (GET)**

  * Query DB for all files owned by `session["user_id"]`. Pass list to `dashboard.html`.
* **`/upload` (GET & POST)**

  * **GET:** render `upload.html` (simple form).
  * **POST:**

    * Access `request.files["file"]`; read bytes.
    * Compute `sha256_hash` of the plaintext (to detect duplicates).
    * (Optional) Encrypt bytes via `cryptography.Fernet` (requiring a per‐user/key storage strategy).
    * Save the file under `storage/<user_id>/<uuid4()>.bin`.
    * Insert metadata row: `(owner_id, original_filename, stored_path, now(), sha256_hash, description)`.
    * Redirect to `/dashboard`.
* **`/download/<int:file_id>` (GET)**

  * Verify `session["user_id"] == owner_id`.
  * Read the file bytes, decrypt (if encrypted), then return `send_file(...)`.
* **`/delete/<int:file_id>` (POST or DELETE)**

  * Verify owner; delete from disk + delete row in DB; return JSON or redirect.

## Front‐End for Dashboard & Upload

* **`dashboard.html`**

  * Loop through each file (passed in as a Jinja list). For each:

    * Show `{{ file.original_filename }}` and `{{ file.upload_timestamp }}`.
    * Buttons:

      ```html
      <a href="{{ url_for('main.download', file_id=file.id) }}">Download</a>
      <form method="post" action="{{ url_for('main.delete', file_id=file.id) }}">
        <button>Delete</button>
      </form>
      ```
  * A visible `[Upload New File]` button linking to `/upload`.
* **`upload.html`**

  * Form with `<input type="file" name="file">` and “Description” field.
  * Submit button.
  * Add simple CSS in `static/css/styles.css` to center forms and add basic spacing.

## Encryption (Optional, but recommended for “secure” storage)

* Pick a symmetric scheme (e.g. Fernet from `cryptography`).
* Generate (and persist) a per-user encryption key in the database or derive it from the user’s secret during login (with strict care—avoid storing the secret).
* Modify the upload route to encrypt `file.read()` before writing to disk.
* Modify the download route to decrypt before sending.
* **Test:** Upload a small text file, then manually examine its stored bytes on disk—ensure it’s not plaintext. Try downloading and confirm you get the original.

## Session Security & Edge Cases

* Enforce HTTPS in production (set `SESSION_COOKIE_SECURE = True` in config).
* Add a timeout on the login challenge (e.g. if the user never sends a response within 2 minutes, drop the stored `(R, c)`).
* Sanitize/validate file names: avoid directory traversal.
* Limit max upload size (e.g. `app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024` for 50 MB).
* Handle Postgres connection errors gracefully (retry or show “Service Unavailable”).
* **Write tests (or manual checks) for:**

  * Attempting to download a file you don’t own (should return 403).
  * Trying to register an existing username (should 400).
  * Trying to log in with a wrong proof (should 401).

## Docker & Deployment Checks

* Confirm that in `Dockerfile` you install all dependencies (`requirements.txt`).
* Confirm environment variables from `.env` are read by Flask (via `python-dotenv`).
* Run `docker-compose up`, register a user, upload a file, shut down containers, restart, and ensure data persists (i.e., the file remains in the volume and metadata still in Postgres).
* Confirm that if you change Python code in PyCharm (mounted volume), the Flask container sees updates (if using `FLASK_ENV=development` + `flask run --reload`).

## Automated Tests (Unit & Integration)

* **Unit‐Test ZKP functions:**

  * For multiple random secrets, verify that `verify_proof(...)` returns true.
  * Test edge cases: wrong `challenge_c`, wrong `s`, wrong `R`.
* **Integration Test for Registration/Login** (can be a small pytest script or Postman collection):

  * Register a test user, then attempt login flow (initiate → verify).
  * Attempt invalid login → expect 401.
* **Integration Test for File Routes:**

  * Log in as test user, POST to `/upload` with a small dummy file, then GET `/dashboard` and check that the filename shows up.
  * GET `/download/<id>` and verify contents match.
  * POST `/delete/<id>`, verify it’s gone from dashboard.
  * **Edge Case Tests:**

    * Two simultaneous challenge initiations (ensure stored `R, c` are per‐user or per‐session).
    * Session expiration test: try accessing `/dashboard` after clearing cookies → should redirect to `/login`.

## Polish & Documentation

* Write up a concise README section summarizing:

  * What ZKP scheme you chose (and a link to background).
  * How to create users and log in.
  * The directory structure (so new developers know where to find models vs. routes).
  * How to run migrations.
* Inline comments in `app/zkp.py`, `auth.py`, and `routes.py` to explain “why” you’re doing each step.
* Add basic CSS so that forms & tables look neat (not required, but helps for demos).
* If you plan to extend “sharing” so User A can grant User B access, define a new permissions table and add a “Share” button in the dashboard. (This can come after the MVP is done.)
