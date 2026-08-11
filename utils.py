import os
import re
import difflib
from datetime import date

from flask import current_app
from werkzeug.utils import secure_filename

from extensions import db
from models import Notification, VisitorLog


# ---------------------------------------------------------------------------
# File upload helpers
# ---------------------------------------------------------------------------

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]
    )


def save_upload(file_storage, folder, prefix=""):
    """Saves an uploaded file with a safe, unique name. Returns the filename or None."""
    if not file_storage or file_storage.filename == "":
        return None
    if not allowed_file(file_storage.filename):
        return None

    filename = secure_filename(file_storage.filename)
    ext = filename.rsplit(".", 1)[1].lower()
    unique_name = f"{prefix}{os.urandom(6).hex()}.{ext}"

    os.makedirs(folder, exist_ok=True)
    file_storage.save(os.path.join(folder, unique_name))
    return unique_name


# ---------------------------------------------------------------------------
# Email validation - only Gmail addresses are accepted for Room Owner signup
# ---------------------------------------------------------------------------

GMAIL_REGEX = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._%+-]*@gmail\.com$")


def is_valid_gmail(email):
    return bool(GMAIL_REGEX.match(email.strip()))


# ---------------------------------------------------------------------------
# Notification helper
# ---------------------------------------------------------------------------

def notify(message, category="general", recipient_role="admin", recipient_id=None):
    note = Notification(
        message=message,
        category=category,
        recipient_role=recipient_role,
        recipient_id=recipient_id,
    )
    db.session.add(note)
    db.session.commit()
    return note


# ---------------------------------------------------------------------------
# Visitor tracking
# ---------------------------------------------------------------------------

def log_visit():
    today = date.today()
    entry = VisitorLog.query.filter_by(visit_date=today).first()
    if entry is None:
        entry = VisitorLog(visit_date=today, count=1)
        db.session.add(entry)
    else:
        entry.count += 1
    db.session.commit()


# ---------------------------------------------------------------------------
# Fuzzy / tolerant search
# ---------------------------------------------------------------------------
# Lightweight, no external AI libraries: combines substring matching with
# difflib's SequenceMatcher so minor typos ("Katmandu" -> "Kathmandu",
# "single rom" -> "Single Room") still return relevant results.

def _similar(a, b, threshold=0.72):
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio() >= threshold


def _tokens(text):
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def room_matches_query(room, query):
    """Returns True if the room is a match for the free-text search query."""
    if not query:
        return True

    query = query.strip().lower()
    haystacks = [room.title or "", room.location or "", str(room.price)]
    combined = " ".join(haystacks).lower()

    # 1) Direct substring match (fast path, handles partial words)
    if query in combined:
        return True

    # 2) Token-by-token fuzzy match (handles typos / minor misspellings)
    query_tokens = _tokens(query)
    haystack_tokens = _tokens(combined)
    if not query_tokens:
        return False

    for q_tok in query_tokens:
        matched = False
        for h_tok in haystack_tokens:
            if q_tok in h_tok or h_tok in q_tok or _similar(q_tok, h_tok):
                matched = True
                break
        if not matched:
            return False
    return True


def filter_rooms(rooms, query=None, location=None, min_price=None, max_price=None):
    results = []
    for room in rooms:
        if query and not room_matches_query(room, query):
            continue
        if location and not room_matches_query(room, location):
            continue
        if min_price is not None and room.price < min_price:
            continue
        if max_price is not None and room.price > max_price:
            continue
        results.append(room)
    return results
