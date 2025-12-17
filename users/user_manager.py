"""
User Management - Profile CRUD and authentication.

BUG INVENTORY:
- BUG-036: Password stored with weak hashing (MD5)
- BUG-037: No input sanitization (XSS in profile fields)
- BUG-038: User enumeration via different error messages
- BUG-039: Session tokens never expire
"""

import hashlib
import time
import secrets
from datetime import datetime
from typing import Dict, Optional, List


class User:
    def __init__(self, username: str, email: str, display_name: str = ""):
        self.id = f"USR-{int(time.time() * 1000)}"
        self.username = username
        self.email = email
        self.display_name = display_name or username
        self.bio = ""
        self.avatar_url = ""
        self.password_hash = ""
        self.created_at = datetime.utcnow()
        self.last_login = None
        self.is_active = True
        self.followers_count = 0
        self.following_count = 0
        self.post_count = 0


class UserManager:
    """Handles user registration, authentication, and profile management."""

    def __init__(self):
        self.users: Dict[str, User] = {}
        self._email_index: Dict[str, str] = {}
        self._username_index: Dict[str, str] = {}
        self._sessions: Dict[str, str] = {}  # token -> user_id

    def register(self, username: str, email: str, password: str,
                 display_name: str = "") -> Optional[User]:
        """
        Register a new user.

        BUG-036: Uses MD5 for password hashing (cryptographically broken).
        Should use bcrypt, scrypt, or argon2.
        """
        if username in self._username_index:
            return None
        if email in self._email_index:
            return None

        user = User(username, email, display_name)

        # BUG-036: MD5 is NOT suitable for password hashing
        # - No salt
        # - Fast to brute-force
        # - Rainbow table vulnerable
        user.password_hash = hashlib.md5(password.encode()).hexdigest()

        self.users[user.id] = user
        self._username_index[username] = user.id
        self._email_index[email] = user.id
        return user

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """
        Authenticate user and return session token.

        BUG-038: Different error messages for "user not found" vs
        "wrong password" allows user enumeration attacks.

        BUG-039: Session tokens created but never expired.
        """
        # BUG-038: Reveals whether username exists
        if username not in self._username_index:
            return None  # Attacker knows: "username doesn't exist"

        user_id = self._username_index[username]
        user = self.users[user_id]

        password_hash = hashlib.md5(password.encode()).hexdigest()

        # BUG-038: Different code path for wrong password
        if user.password_hash != password_hash:
            return None  # Attacker knows: "username exists but wrong password"

        # BUG-039: Token created but never expires
        token = secrets.token_hex(32)
        self._sessions[token] = user.id
        user.last_login = datetime.utcnow()
        return token

    def get_user_by_token(self, token: str) -> Optional[User]:
        """Get user from session token."""
        # BUG-039: Never checks if token is expired
        user_id = self._sessions.get(token)
        if user_id:
            return self.users.get(user_id)
        return None

    def update_profile(self, user_id: str, updates: dict) -> bool:
        """
        Update user profile fields.

        BUG-037: No sanitization on bio, display_name fields.
        User can inject HTML/JavaScript that will be rendered unsafely.
        """
        user = self.users.get(user_id)
        if not user:
            return False

        # BUG-037: Direct assignment without sanitization
        if "bio" in updates:
            user.bio = updates["bio"]  # Could contain <script>alert('xss')</script>
        if "display_name" in updates:
            user.display_name = updates["display_name"]  # XSS vector
        if "avatar_url" in updates:
            user.avatar_url = updates["avatar_url"]  # Could be javascript: URL

        return True

    def search_users(self, query: str) -> List[User]:
        """Search users by username or display name."""
        results = []
        query_lower = query.lower()
        for user in self.users.values():
            if (query_lower in user.username.lower() or
                    query_lower in user.display_name.lower()):
                results.append(user)
        return results

    def get_stats(self) -> dict:
        """Get user management stats."""
        return {
            "total_users": len(self.users),
            "active_users": sum(1 for u in self.users.values() if u.is_active),
            "active_sessions": len(self._sessions),
        }
