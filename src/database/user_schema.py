"""
User Database Schema with Access Control.

Tables:
- Users: User accounts with encrypted passwords
- AccessTokens: API tokens for programmatic access
- UserRoles: Role definitions and permissions
- AccessLogs: Audit trail for data access
"""

import sqlite3
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from enum import Enum
from pathlib import Path

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class UserRole(Enum):
    """User role definitions with access levels."""
    ADMIN = "admin"              # Full access + user management
    ORGANIZATION = "organization" # Full access by location
    RESEARCHER = "researcher"     # Full national data access
    EDUCATOR = "educator"         # Summary data only
    PUBLIC = "public"             # Limited summary data


class AccessLevel(Enum):
    """Data access levels."""
    FULL = "full"           # All data including raw
    NATIONAL = "national"   # National-level data
    REGIONAL = "regional"   # State/region specific
    SUMMARY = "summary"     # Aggregated summaries only
    LIMITED = "limited"     # Basic public data


# Role to access level mapping
ROLE_ACCESS = {
    UserRole.ADMIN: AccessLevel.FULL,
    UserRole.ORGANIZATION: AccessLevel.FULL,
    UserRole.RESEARCHER: AccessLevel.NATIONAL,
    UserRole.EDUCATOR: AccessLevel.SUMMARY,
    UserRole.PUBLIC: AccessLevel.LIMITED
}


class UserDatabase:
    """
    User management database with encryption and access control.
    """
    
    def __init__(self, db_path: str = "processed_data.db"):
        self.db_path = db_path
        self._init_encryption()
        self._create_tables()
    
    def _init_encryption(self):
        """Initialize encryption key."""
        key_file = Path(self.db_path).parent / ".encryption_key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                self.encryption_key = f.read()
        else:
            self.encryption_key = Fernet.generate_key() if CRYPTO_AVAILABLE else b''
            with open(key_file, 'wb') as f:
                f.write(self.encryption_key)
        
        if CRYPTO_AVAILABLE and self.encryption_key:
            self.cipher = Fernet(self.encryption_key)
        else:
            self.cipher = None
    
    def _encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        if self.cipher:
            return self.cipher.encrypt(data.encode()).decode()
        return data
    
    def _decrypt(self, data: str) -> str:
        """Decrypt sensitive data."""
        if self.cipher:
            return self.cipher.decrypt(data.encode()).decode()
        return data
    
    def _create_tables(self):
        """Create user-related tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'public',
                organization TEXT,
                location_state TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_verified BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                api_key TEXT UNIQUE,
                api_key_created_at TIMESTAMP
            )
        """)
        
        # Access tokens for session management
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AccessTokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                token_type TEXT DEFAULT 'access',
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_revoked BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES Users(id)
            )
        """)
        
        # Access logs for audit
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AccessLogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                endpoint TEXT NOT NULL,
                method TEXT,
                ip_address TEXT,
                user_agent TEXT,
                request_data TEXT,
                response_status INTEGER,
                accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES Users(id)
            )
        """)
        
        # API rate limiting
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RateLimits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ip_address TEXT,
                endpoint TEXT,
                request_count INTEGER DEFAULT 1,
                window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES Users(id)
            )
        """)
        
        conn.commit()
        conn.close()
        
    def create_user(self, username: str, email: str, password: str,
                    role: UserRole = UserRole.PUBLIC,
                    organization: Optional[str] = None,
                    location_state: Optional[str] = None) -> Dict:
        """
        Create a new user with encrypted password.
        """
        # Hash password
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        
        # Generate API key
        api_key = secrets.token_urlsafe(32)
        api_key_encrypted = self._encrypt(api_key)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO Users (
                    username, email, password_hash, role,
                    organization, location_state, api_key, api_key_created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                username, email, password_hash, role.value,
                organization, location_state, api_key_encrypted, datetime.utcnow()
            ))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            return {
                'success': True,
                'user_id': user_id,
                'username': username,
                'api_key': api_key,  # Return plain API key only on creation
                'message': 'User created successfully'
            }
        except sqlite3.IntegrityError as e:
            return {
                'success': False,
                'error': 'Username or email already exists'
            }
        finally:
            conn.close()
    
    def verify_password(self, username: str, password: str) -> Optional[Dict]:
        """
        Verify user credentials.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, password_hash, role, 
                   organization, location_state, is_active
            FROM Users WHERE username = ? OR email = ?
        """, (username, username))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return None
        
        if not user['is_active']:
            return None
        
        if bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
            return {
                'user_id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role'],
                'organization': user['organization'],
                'location_state': user['location_state']
            }
        
        return None
    
    def verify_api_key(self, api_key: str) -> Optional[Dict]:
        """
        Verify API key and return user info.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, role, organization, location_state, api_key
            FROM Users WHERE is_active = 1
        """)
        
        for user in cursor.fetchall():
            try:
                stored_key = self._decrypt(user['api_key'])
                if stored_key == api_key:
                    conn.close()
                    return {
                        'user_id': user['id'],
                        'username': user['username'],
                        'role': user['role'],
                        'organization': user['organization'],
                        'location_state': user['location_state']
                    }
            except:
                continue
        
        conn.close()
        return None
    
    def get_user_access_level(self, user_id: int) -> AccessLevel:
        """
        Get access level for a user.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT role FROM Users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            role = UserRole(result[0])
            return ROLE_ACCESS.get(role, AccessLevel.LIMITED)
        
        return AccessLevel.LIMITED
    
    def can_access_state(self, user_id: int, state_name: str) -> bool:
        """
        Check if user can access data for a specific state.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT role, location_state FROM Users WHERE id = ?
        """, (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return False
        
        role = UserRole(user['role'])
        
        # Admin and researchers can access all states
        if role in [UserRole.ADMIN, UserRole.RESEARCHER]:
            return True
        
        # Organization users can access their location
        if role == UserRole.ORGANIZATION:
            if user['location_state']:
                return user['location_state'].lower() == state_name.lower()
            return True  # Full access if no location specified
        
        # Educators and public have limited access
        return True  # Allow view with filtered data
    
    def log_access(self, user_id: Optional[int], endpoint: str,
                   method: str = "GET", ip_address: str = "",
                   status: int = 200, request_data: str = ""):
        """
        Log data access for audit.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO AccessLogs (
                user_id, endpoint, method, ip_address, 
                response_status, request_data
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, endpoint, method, ip_address, status, request_data))
        
        conn.commit()
        conn.close()
    
    def update_last_login(self, user_id: int):
        """Update user's last login timestamp."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE Users SET last_login = ? WHERE id = ?
        """, (datetime.utcnow(), user_id))
        
        conn.commit()
        conn.close()
    
    def list_users(self, role_filter: Optional[str] = None) -> List[Dict]:
        """List all users (admin only)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if role_filter:
            cursor.execute("""
                SELECT id, username, email, role, organization, 
                       location_state, is_active, created_at, last_login
                FROM Users WHERE role = ?
            """, (role_filter,))
        else:
            cursor.execute("""
                SELECT id, username, email, role, organization,
                       location_state, is_active, created_at, last_login
                FROM Users
            """)
        
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return users
    
    def update_user_role(self, user_id: int, new_role: UserRole) -> bool:
        """Update user's role (admin only)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE Users SET role = ? WHERE id = ?
        """, (new_role.value, user_id))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0


def init_default_admin():
    """Create default admin user if none exists."""
    db = UserDatabase()
    
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM Users WHERE role = 'admin'")
    admin_count = cursor.fetchone()[0]
    conn.close()
    
    if admin_count == 0:
        result = db.create_user(
            username="admin",
            email="admin@environmental.ai",
            password="admin123",  # Change this in production!
            role=UserRole.ADMIN
        )
        print(f"[OK] Default admin created: {result}")
        return result
    
    return None


if __name__ == "__main__":
    # Initialize database and create default admin
    db = UserDatabase()
    admin = init_default_admin()
    
    # Create sample users
    print("\nCreating sample users...")
    
    db.create_user(
        username="researcher1",
        email="researcher@university.edu",
        password="research123",
        role=UserRole.RESEARCHER,
        organization="University Research Lab"
    )
    
    db.create_user(
        username="delhi_org",
        email="org@delhi.gov.in",
        password="delhi123",
        role=UserRole.ORGANIZATION,
        organization="Delhi Environment Dept",
        location_state="Delhi"
    )
    
    db.create_user(
        username="teacher1",
        email="teacher@school.edu",
        password="teach123",
        role=UserRole.EDUCATOR,
        organization="Green School"
    )
    
    print("[OK] Sample users created")
    print("\nUsers in database:")
    for user in db.list_users():
        print(f"  - {user['username']} ({user['role']})")
