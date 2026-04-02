"""
Step 0: Session Management.

Manages cookie-based authentication and session storage.
Resolves user info (email, user_id, firstname, lastname) from:
1. User-provided cookie → API call to /api/auth/session
2. Stored session in sessions.json (by email lookup)
3. Fallback to .env configuration

Also auto-initializes quota records for new users.

Input:
    - cookie (optional, from CLI)
    - email (optional, from CLI)

Output:
    - Resolved Settings with updated cookie, email, user_id, firstname, lastname

API Endpoint: GET /api/auth/session
"""

import json
import os
import logging
import requests
from typing import Optional, List, Tuple

from config.settings import Settings
from core.http_client import HttpClient
from core.logger import log
from models.schemas import SessionRecord, QuotaRecord

logger = logging.getLogger(__name__)


def _load_sessions(sessions_file: str) -> List[dict]:
    """
    Load session records from the JSON file.

    Args:
        sessions_file: Path to the sessions JSON file.

    Returns:
        List of session record dictionaries.
    """
    if not os.path.exists(sessions_file):
        return []

    try:
        with open(sessions_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_sessions(sessions_file: str, records: List[dict]) -> None:
    """
    Save session records to the JSON file.

    Args:
        sessions_file: Path to the sessions JSON file.
        records: List of session record dictionaries.
    """
    dir_path = os.path.dirname(sessions_file)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(sessions_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def _find_session_by_email(
    records: List[dict], email: str
) -> Optional[SessionRecord]:
    """
    Find a session record by email.

    Args:
        records: List of session record dicts.
        email: Email to search for.

    Returns:
        SessionRecord if found, None otherwise.
    """
    for record in records:
        if record.get("email") == email:
            return SessionRecord.from_dict(record)
    return None


def _update_session_in_records(
    records: List[dict], session: SessionRecord
) -> List[dict]:
    """
    Update or insert a session record in the records list.

    Args:
        records: List of existing session record dicts.
        session: SessionRecord to save.

    Returns:
        Updated list of records.
    """
    for i, record in enumerate(records):
        if record.get("email") == session.email:
            records[i] = session.to_dict()
            return records

    records.append(session.to_dict())
    return records


def _fetch_session_from_api(
    settings: Settings, cookie: str
) -> Optional[SessionRecord]:
    """
    Call the auth/session API to get user info from a cookie.

    Makes a GET request to /api/auth/session with the provided cookie
    and extracts user information from the response.

    Args:
        settings: Application settings (for base_url, user_agent).
        cookie: Full cookie string for authentication.

    Returns:
        SessionRecord with user info, or None on failure.
    """
    step = 0

    # Create a temporary client with the provided cookie
    temp_settings = Settings(
        base_url=settings.base_url,
        cookie=cookie,
        user_agent=settings.user_agent,
        proxy_http=settings.proxy_http,
        proxy_https=settings.proxy_https,
    )
    client = HttpClient(temp_settings)
    try:
        response = client.get("/api/auth/session")
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError:
            log(logger, "ERROR", step, f"API returned non-JSON response: {response.text[:500]}")
            return None
    except requests.exceptions.HTTPError as e:
        log(logger, "ERROR", step, f"HTTP Error fetching session: {e.response.status_code} {e.response.reason}")
        if e.response.status_code == 403:
            log(logger, "ERROR", step, "Access Forbidden (403). Cookie might be invalid or IP blocked.")
        return None
    except Exception as e:
        log(logger, "ERROR", step, f"Unexpected error fetching session: {e}")
        return None

    # Parse response: { "user": { ... }, "expires": "..." }
    user_data = data.get("user")
    if not user_data:
        log(logger, "ERROR", step, f"No user data in session response: {data}")
        return None

    session = SessionRecord(
        cookie=cookie,
        email=user_data.get("email", ""),
        user_id=str(user_data.get("id", "")),
        firstname=user_data.get("first_name", ""),
        lastname=user_data.get("last_name", ""),
        expires=data.get("expires", ""),
    )

    log(
        logger,
        "INFO",
        step,
        f"Session fetched: email={session.email}, "
        f"user_id={session.user_id}, expires={session.expires}",
    )
    return session


def _init_quota_for_email(
    quota_file: str, email: str, limit_count: int, limit_file: int
) -> None:
    """
    Initialize a quota record for an email if it doesn't exist.

    Creates quota.json or appends a new record with count=0.

    Args:
        quota_file: Path to the quota JSON file.
        email: Email to initialize quota for.
        limit_count: Default limit_count for new records.
        limit_file: Default limit_file for new records.
    """
    step = 0

    # Load existing records
    records = []
    if os.path.exists(quota_file):
        try:
            with open(quota_file, "r", encoding="utf-8") as f:
                records = json.load(f)
        except (json.JSONDecodeError, IOError):
            records = []

    # Check if email already exists
    for record in records:
        if record.get("email") == email:
            log(logger, "INFO", step, f"Quota record {email} already exists")
            return

    # Create new record
    new_record = QuotaRecord(
        email=email,
        count=0,
        limit_count=limit_count,
        limit_file=limit_file,
    )
    records.append(new_record.to_dict())

    # Save
    dir_path = os.path.dirname(quota_file)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(quota_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    log(logger, "INFO", step, f"Khởi tạo quota record cho {email}")


def _ensure_directories(settings: Settings) -> None:
    """
    Pre-create all required directories to avoid file-not-found errors.

    Creates directories for:
    - system_dir (resources/system)
    - users_dir (resources/users)

    Args:
        settings: Application settings.
    """
    dirs_to_create = [
        settings.system_dir,
        settings.users_dir,
    ]

    for d in dirs_to_create:
        if d:
            os.makedirs(d, exist_ok=True)


def execute(
    settings: Settings,
    cookie: Optional[str] = None,
    email: Optional[str] = None,
) -> Settings:
    """
    Execute Step 0: Resolve user authentication and session info.

    Authentication resolution flow:
    1. If cookie provided → call API → get user info → save session → init quota
    2. If email provided → find in sessions.json → check expiry → use if valid
    3. If session expired → prompt for new cookie (return settings with empty cookie as signal)
    4. Fallback → use .env values
    5. If .env empty → return settings with empty cookie as signal to prompt

    Args:
        settings: Application settings loaded from .env.
        cookie: Optional cookie string from CLI.
        email: Optional email string from CLI (to lookup saved session).

    Returns:
        Updated Settings with resolved user info and cookie.
    """
    step = 0

    # Pre-create directories
    _ensure_directories(settings)

    sessions = _load_sessions(settings.sessions_file)

    # --- Case 1: Cookie provided by user ---
    if cookie:
        log(logger, "INFO", step, "Check cookie...")
        session = _fetch_session_from_api(settings, cookie)

        if session is None:
            log(logger, "ERROR", step, "Cookie authentication failed")
            return settings

        # Save session
        sessions = _update_session_in_records(sessions, session)
        _save_sessions(settings.sessions_file, sessions)

        # Init quota for this email
        _init_quota_for_email(
            settings.quota_file,
            session.email,
            settings.limit_count,
            settings.limit_file,
        )

        # Update settings
        settings.cookie = session.cookie
        settings.email = session.email
        settings.user_id = session.user_id
        settings.firstname = session.firstname
        settings.lastname = session.lastname

        log(logger, "INFO", step, f"Cookie authentication success: {session.email}")
        return settings

    # --- Case 2: Email provided → look up session ---
    if email:
        log(logger, "INFO", step, f"Check session for email: {email}")
        session = _find_session_by_email(sessions, email)

        if session:
            if session.is_expired():
                log(
                    logger,
                    "ERROR",
                    step,
                    f"Session for email {email} is expired. Please input your cookie",
                )
                # Return settings with empty cookie to signal need for new cookie
                settings.email = email
                settings.cookie = ""
                return settings

            # Session is valid
            settings.cookie = session.cookie
            settings.email = session.email
            settings.user_id = session.user_id
            settings.firstname = session.firstname
            settings.lastname = session.lastname

            log(
                logger,
                "INFO",
                step,
                f"Found session for email: {session.email}",
            )
            return settings

        # Not found in sessions → try env
        log(
            logger,
            "INFO",
            step,
            f"Not found session for email: {email}",
        )

    # --- Case 3: Fallback to env ---
    if settings.cookie:
        log(logger, "INFO", step, "Using cookie CHÙA")
        session = _fetch_session_from_api(settings, settings.cookie)
        if session:
            # Save session
            sessions = _update_session_in_records(sessions, session)
            _save_sessions(settings.sessions_file, sessions)
            
            # Init quota
            _init_quota_for_email(
                settings.quota_file,
                session.email,
                settings.limit_count,
                settings.limit_file,
            )
            
            # Update settings
            settings.email = session.email
            settings.user_id = session.user_id
            settings.firstname = session.firstname
            settings.lastname = session.lastname
            log(logger, "INFO", step, f"EMAIL CHÙA: {session.email}")
            return settings
        else:
            log(logger, "ERROR", step, "Cookie CHÙA invalid or expired")
            settings.cookie = "" # Reset to signal failure
            return settings

    # --- Case 4: Nothing available ---
    log(
        logger,
        "ERROR",
        step,
        "No authentication information. "
        "Please input your cookie",
    )
    return settings
