"""
Data models (schemas) for the AutoHDR pipeline.

Provides dataclasses used to pass data between pipeline steps
and to track download quotas.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class PresignedUrl:
    """
    Represents a single presigned URL from step1 response.

    Attributes:
        filename: Name of the file.
        url: Presigned S3 URL for uploading.
    """

    filename: str
    url: str


@dataclass
class PipelineContext:
    """
    Context object passed through the pipeline steps.

    Holds all state needed across the 7 steps, including user info,
    file paths, and intermediate results from each step.

    Attributes:
        file_paths: List of local file paths to upload.
        address: Address string for the photoshoot.
        email: User email address.
        firstname: User first name.
        lastname: User last name.
        user_id: AutoHDR user ID.
        unique_str: UUID generated in step1.
        presigned_urls: List of presigned URLs from step1.
        filenames: List of filenames extracted from file_paths.
        photoshoot_id: Photoshoot ID found in step5.
        processed_urls: List of cleaned processed photo URLs from step6.
    """

    file_paths: List[str]
    address: str
    email: str
    firstname: str
    lastname: str
    user_id: str
    auth_mode: str = "quota"  # "quota" or "key"
    unique_str: str = ""
    presigned_urls: List[PresignedUrl] = field(default_factory=list)
    filenames: List[str] = field(default_factory=list)
    photoshoot_id: Optional[int] = None
    processed_urls: List[str] = field(default_factory=list)


@dataclass
class QuotaRecord:
    """
    Quota tracking record stored in the JSON file.

    Tracks download usage per email to enforce limits.

    Attributes:
        email: User email address (unique key).
        unique_str: List of unique_str values that have been processed.
        count: Total number of files downloaded so far.
        limit_count: Maximum total download count allowed.
        limit_file: Maximum files allowed per single download batch.
    """

    email: str
    unique_str: List[str] = field(default_factory=list)
    count: int = 0
    limit_count: int = 1000
    limit_file: int = 50

    def to_dict(self) -> dict:
        """
        Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the quota record.
        """
        return {
            "email": self.email,
            "unique_str": self.unique_str,
            "count": self.count,
            "limit_count": self.limit_count,
            "limit_file": self.limit_file,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QuotaRecord":
        """
        Create QuotaRecord from a dictionary.

        Args:
            data: Dictionary with quota record fields.

        Returns:
            QuotaRecord instance.
        """
        return cls(
            email=data.get("email", ""),
            unique_str=data.get("unique_str", []),
            count=data.get("count", 0),
            limit_count=data.get("limit_count", 1000),
            limit_file=data.get("limit_file", 50),
        )


@dataclass
class SessionRecord:
    """
    Session record stored in sessions.json.

    Tracks cookie, user info, and session expiry for each user.
    Used by Step 0 to avoid re-entering cookie on every run.

    Attributes:
        cookie: Full cookie string for authentication.
        email: User email from API response.
        user_id: User ID from API response.
        firstname: First name from API response.
        lastname: Last name from API response.
        expires: Session expiry timestamp (ISO format).
    """

    cookie: str
    email: str
    user_id: str
    firstname: str
    lastname: str
    expires: str

    def is_expired(self) -> bool:
        """
        Check if the session has expired.

        Compares the expires timestamp against current UTC time.

        Returns:
            True if session is expired, False otherwise.
        """
        try:
            # Handle both formats: with and without 'Z' suffix
            expires_str = self.expires.replace("Z", "+00:00")
            expires_dt = datetime.fromisoformat(expires_str)
            now = datetime.now(expires_dt.tzinfo)
            return now >= expires_dt
        except (ValueError, TypeError):
            return True

    def to_dict(self) -> dict:
        """
        Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the session record.
        """
        return {
            "cookie": self.cookie,
            "email": self.email,
            "user_id": self.user_id,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "expires": self.expires,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionRecord":
        """
        Create SessionRecord from a dictionary.

        Args:
            data: Dictionary with session record fields.

        Returns:
            SessionRecord instance.
        """
        return cls(
            cookie=data.get("cookie", ""),
            email=data.get("email", ""),
            user_id=str(data.get("user_id", "")),
            firstname=data.get("firstname", ""),
            lastname=data.get("lastname", ""),
            expires=data.get("expires", ""),
        )

@dataclass
class KeyRecord:
    """
    Key tracking record stored in the keys JSON file.
    Tracks expiration and validity of a key.
    """
    key: str
    name: str = ""
    is_active: bool = True
    expires_at: Optional[str] = None # ISO format datetime
    machine_id: Optional[str] = None # Unique ID of the locked machine

    def is_expired(self) -> bool:
        if not self.is_active:
            return True
        if not self.expires_at:
            return False # No expiration means valid indefinitely

        try:
            expires_str = self.expires_at.replace("Z", "+00:00")
            expires_dt = datetime.fromisoformat(expires_str)
            now = datetime.now(expires_dt.tzinfo)
            return now >= expires_dt
        except (ValueError, TypeError):
            return True

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "name": self.name,
            "is_active": self.is_active,
            "expires_at": self.expires_at,
            "machine_id": self.machine_id
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "KeyRecord":
        return cls(
            key=data.get("key", ""),
            name=data.get("name", ""),
            is_active=data.get("is_active", True),
            expires_at=data.get("expires_at", None),
            machine_id=data.get("machine_id", None)
        )
