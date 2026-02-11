"""
Authentication and Authorization Framework for Nyayamrit API

This module implements role-based access control (RBAC) with JWT token authentication
for the Nyayamrit judicial assistant system.

Roles:
- citizen: Basic query access, anonymous allowed
- lawyer: Advanced search, citation validation, API access
- judge: Secure case analysis, precedent search, audit logging

Features:
- JWT token-based authentication
- Role-based permissions
- Session management
- Audit logging for sensitive operations
"""

import os
from jose import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from fastapi import HTTPException, status
from pydantic import BaseModel, Field


class UserRole(Enum):
    """User roles with hierarchical permissions."""
    CITIZEN = "citizen"
    LAWYER = "lawyer"
    JUDGE = "judge"


class Permission(Enum):
    """System permissions."""
    QUERY = "query"                           # Basic query access
    ADVANCED_SEARCH = "advanced_search"       # Complex search queries
    CITATION_VALIDATION = "citation_validation"  # Bulk citation validation
    API_ACCESS = "api_access"                 # REST API access
    CASE_ANALYSIS = "case_analysis"           # Judge-only case analysis
    PRECEDENT_SEARCH = "precedent_search"     # Precedent analysis
    AUDIT_ACCESS = "audit_access"             # Access to audit logs
    USER_MANAGEMENT = "user_management"       # Manage other users


# Role-based permissions mapping
ROLE_PERMISSIONS = {
    UserRole.CITIZEN: [
        Permission.QUERY
    ],
    UserRole.LAWYER: [
        Permission.QUERY,
        Permission.ADVANCED_SEARCH,
        Permission.CITATION_VALIDATION,
        Permission.API_ACCESS
    ],
    UserRole.JUDGE: [
        Permission.QUERY,
        Permission.ADVANCED_SEARCH,
        Permission.CITATION_VALIDATION,
        Permission.API_ACCESS,
        Permission.CASE_ANALYSIS,
        Permission.PRECEDENT_SEARCH,
        Permission.AUDIT_ACCESS
    ]
}


@dataclass
class User:
    """User model with role and permissions."""
    user_id: str
    email: Optional[str]
    role: UserRole
    permissions: List[Permission]
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission."""
        return permission in self.permissions
    
    def can_access_endpoint(self, required_permissions: List[Permission]) -> bool:
        """Check if user can access endpoint requiring specific permissions."""
        return any(perm in self.permissions for perm in required_permissions)


class UserCreate(BaseModel):
    """User creation request model."""
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8)
    role: UserRole
    full_name: Optional[str] = None
    organization: Optional[str] = None


class UserLogin(BaseModel):
    """User login request model."""
    email: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    role: str
    permissions: List[str]


class AuthConfig:
    """Authentication configuration."""
    
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        self.refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class AuthManager:
    """Manages authentication and authorization operations."""
    
    def __init__(self, config: AuthConfig = None):
        self.config = config or AuthConfig()
        # In production, this would be a proper database
        self._users: Dict[str, Dict[str, Any]] = {}
        self._sessions: Dict[str, str] = {}  # token -> user_id
        
        # Create default users for development
        self._create_default_users()
    
    def _create_default_users(self):
        """Create default users for development and testing."""
        default_users = [
            {
                "user_id": "citizen_001",
                "email": "citizen@example.com",
                "password": "citizen123",
                "role": UserRole.CITIZEN,
                "full_name": "Test Citizen"
            },
            {
                "user_id": "lawyer_001",
                "email": "lawyer@example.com",
                "password": "lawyer123",
                "role": UserRole.LAWYER,
                "full_name": "Test Lawyer",
                "organization": "Legal Associates"
            },
            {
                "user_id": "judge_001",
                "email": "judge@example.com",
                "password": "judge123",
                "role": UserRole.JUDGE,
                "full_name": "Hon. Test Judge",
                "organization": "District Court"
            }
        ]
        
        for user_data in default_users:
            password_hash = self._hash_password(user_data["password"])
            self._users[user_data["user_id"]] = {
                "user_id": user_data["user_id"],
                "email": user_data["email"],
                "password_hash": password_hash,
                "role": user_data["role"],
                "full_name": user_data.get("full_name"),
                "organization": user_data.get("organization"),
                "is_active": True,
                "created_at": datetime.now(),
                "last_login": None
            }
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user account.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user object
            
        Raises:
            HTTPException: If user already exists or validation fails
        """
        # Check if user already exists
        for user in self._users.values():
            if user["email"] == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
        
        # Generate user ID
        user_id = f"{user_data.role.value}_{len(self._users) + 1:03d}"
        
        # Hash password
        password_hash = self._hash_password(user_data.password)
        
        # Get permissions for role
        permissions = ROLE_PERMISSIONS.get(user_data.role, [])
        
        # Store user
        self._users[user_id] = {
            "user_id": user_id,
            "email": user_data.email,
            "password_hash": password_hash,
            "role": user_data.role,
            "full_name": user_data.full_name,
            "organization": user_data.organization,
            "is_active": True,
            "created_at": datetime.now(),
            "last_login": None
        }
        
        return User(
            user_id=user_id,
            email=user_data.email,
            role=user_data.role,
            permissions=permissions,
            is_active=True,
            created_at=datetime.now()
        )
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        # Find user by email
        user_data = None
        for user in self._users.values():
            if user["email"] == email and user["is_active"]:
                user_data = user
                break
        
        if not user_data:
            return None
        
        # Verify password
        if not self._verify_password(password, user_data["password_hash"]):
            return None
        
        # Update last login
        user_data["last_login"] = datetime.now()
        
        # Get permissions for role
        permissions = ROLE_PERMISSIONS.get(user_data["role"], [])
        
        return User(
            user_id=user_data["user_id"],
            email=user_data["email"],
            role=user_data["role"],
            permissions=permissions,
            is_active=user_data["is_active"],
            created_at=user_data["created_at"],
            last_login=user_data["last_login"]
        )
    
    def create_access_token(self, user: User) -> str:
        """
        Create JWT access token for user.
        
        Args:
            user: User object
            
        Returns:
            JWT access token string
        """
        expire = datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes)
        
        payload = {
            "sub": user.user_id,
            "email": user.email,
            "role": user.role.value,
            "permissions": [perm.value for perm in user.permissions],
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        token = jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)
        
        # Store session
        self._sessions[token] = user.user_id
        
        return token
    
    def verify_token(self, token: str) -> Optional[User]:
        """
        Verify JWT token and return user.
        
        Args:
            token: JWT token string
            
        Returns:
            User object if token is valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.config.secret_key, algorithms=[self.config.algorithm])
            
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            # Check if session exists
            if token not in self._sessions:
                return None
            
            # Get user data
            user_data = self._users.get(user_id)
            if not user_data or not user_data["is_active"]:
                return None
            
            # Get permissions for role
            permissions = ROLE_PERMISSIONS.get(user_data["role"], [])
            
            return User(
                user_id=user_data["user_id"],
                email=user_data["email"],
                role=user_data["role"],
                permissions=permissions,
                is_active=user_data["is_active"],
                created_at=user_data["created_at"],
                last_login=user_data["last_login"]
            )
            
        except jwt.ExpiredSignatureError:
            # Token has expired
            if token in self._sessions:
                del self._sessions[token]
            return None
        except jwt.JWTError:
            # Invalid token
            return None
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke (logout) a token.
        
        Args:
            token: JWT token to revoke
            
        Returns:
            True if token was revoked, False if token not found
        """
        if token in self._sessions:
            del self._sessions[token]
            return True
        return False
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object if found, None otherwise
        """
        user_data = self._users.get(user_id)
        if not user_data:
            return None
        
        permissions = ROLE_PERMISSIONS.get(user_data["role"], [])
        
        return User(
            user_id=user_data["user_id"],
            email=user_data["email"],
            role=user_data["role"],
            permissions=permissions,
            is_active=user_data["is_active"],
            created_at=user_data["created_at"],
            last_login=user_data["last_login"]
        )
    
    def create_anonymous_user(self) -> User:
        """
        Create anonymous user for public access.
        
        Returns:
            Anonymous user with citizen permissions
        """
        return User(
            user_id="anonymous",
            email=None,
            role=UserRole.CITIZEN,
            permissions=ROLE_PERMISSIONS[UserRole.CITIZEN],
            is_active=True
        )
    
    def log_access(self, user: User, endpoint: str, method: str, success: bool):
        """
        Log user access for audit purposes.
        
        Args:
            user: User who accessed the endpoint
            endpoint: API endpoint accessed
            method: HTTP method
            success: Whether access was successful
        """
        # In production, this would write to a proper audit log
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user.user_id,
            "role": user.role.value,
            "endpoint": endpoint,
            "method": method,
            "success": success,
            "ip_address": None  # Would be populated from request
        }
        
        # For now, just log to console
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Access log: {log_entry}")


# Global auth manager instance
auth_manager = AuthManager()


def get_auth_manager() -> AuthManager:
    """Get the global auth manager instance."""
    return auth_manager