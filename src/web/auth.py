"""
User Authentication and Management System
JWT-based authentication with secure password hashing
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, validator
import json
from pathlib import Path
import uuid

# Configuration
SECRET_KEY = "YOUR_SECRET_KEY_HERE_CHANGE_IN_PRODUCTION"  # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database file (simple JSON storage for now, use PostgreSQL in production)
USER_DB_FILE = Path("data/users.json")
USER_DB_FILE.parent.mkdir(parents=True, exist_ok=True)


class User(BaseModel):
    """User model"""
    id: str
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    disabled: bool = False
    created_at: str
    last_login: Optional[str] = None
    preferences: Dict = {}
    watchlist: List[str] = []  # List of asteroid SPKIDs
    alert_settings: Dict = {
        "email_enabled": False,
        "sms_enabled": False,
        "min_threat_score": 0.7,
        "notify_new_detections": True
    }


class UserInDB(User):
    """User with hashed password"""
    hashed_password: str


class UserCreate(BaseModel):
    """User registration model"""
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('username')
    def username_valid(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v


class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str
    user: User


class AuthManager:
    """Handles user authentication and authorization"""
    
    def __init__(self):
        self.users_db: Dict[str, UserInDB] = {}
        self.load_users()
    
    def load_users(self):
        """Load users from JSON file"""
        if USER_DB_FILE.exists():
            try:
                with open(USER_DB_FILE, 'r') as f:
                    data = json.load(f)
                    for user_data in data.values():
                        user = UserInDB(**user_data)
                        self.users_db[user.email] = user
            except Exception as e:
                print(f"Error loading users: {e}")
    
    def save_users(self):
        """Save users to JSON file"""
        try:
            data = {email: user.dict() for email, user in self.users_db.items()}
            with open(USER_DB_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    def get_user(self, email: str) -> Optional[UserInDB]:
        """Get user by email"""
        return self.users_db.get(email)
    
    def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """Get user by username"""
        for user in self.users_db.values():
            if user.username == username:
                return user
        return None
    
    def create_user(self, user_create: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        if self.get_user(user_create.email):
            raise ValueError("Email already registered")
        
        if self.get_user_by_username(user_create.username):
            raise ValueError("Username already taken")
        
        # Create user
        user_id = str(uuid.uuid4())
        hashed_password = self.get_password_hash(user_create.password)
        
        user_in_db = UserInDB(
            id=user_id,
            email=user_create.email,
            username=user_create.username,
            full_name=user_create.full_name,
            hashed_password=hashed_password,
            disabled=False,
            created_at=datetime.utcnow().isoformat(),
            preferences={},
            watchlist=[],
            alert_settings={
                "email_enabled": False,
                "sms_enabled": False,
                "min_threat_score": 0.7,
                "notify_new_detections": True
            }
        )
        
        self.users_db[user_create.email] = user_in_db
        self.save_users()
        
        # Return user without password hash
        return User(**user_in_db.dict())
    
    def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with email and password"""
        user = self.get_user(email)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow().isoformat()
        self.save_users()
        
        return user
    
    def login(self, user_login: UserLogin) -> Token:
        """Login user and return JWT token"""
        user = self.authenticate_user(user_login.email, user_login.password)
        if not user:
            raise ValueError("Incorrect email or password")
        
        if user.disabled:
            raise ValueError("User account is disabled")
        
        # Create access token
        access_token = self.create_access_token(
            data={"sub": user.email, "username": user.username}
        )
        
        # Return token and user info
        user_data = User(**user.dict())
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=user_data
        )
    
    def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from JWT token"""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        email = payload.get("sub")
        if not email:
            return None
        
        user = self.get_user(email)
        if not user:
            return None
        
        return User(**user.dict())
    
    def update_watchlist(self, email: str, asteroid_id: str, action: str) -> User:
        """Add or remove asteroid from user's watchlist"""
        user = self.get_user(email)
        if not user:
            raise ValueError("User not found")
        
        if action == "add":
            if asteroid_id not in user.watchlist:
                user.watchlist.append(asteroid_id)
        elif action == "remove":
            if asteroid_id in user.watchlist:
                user.watchlist.remove(asteroid_id)
        else:
            raise ValueError("Invalid action. Use 'add' or 'remove'")
        
        self.save_users()
        return User(**user.dict())
    
    def update_preferences(self, email: str, preferences: Dict) -> User:
        """Update user preferences"""
        user = self.get_user(email)
        if not user:
            raise ValueError("User not found")
        
        user.preferences.update(preferences)
        self.save_users()
        return User(**user.dict())
    
    def update_alert_settings(self, email: str, alert_settings: Dict) -> User:
        """Update user alert settings"""
        user = self.get_user(email)
        if not user:
            raise ValueError("User not found")
        
        user.alert_settings.update(alert_settings)
        self.save_users()
        return User(**user.dict())


# Singleton instance
auth_manager = AuthManager()


# Convenience functions
def create_user(user_create: UserCreate) -> User:
    """Create a new user account"""
    return auth_manager.create_user(user_create)


def login_user(user_login: UserLogin) -> Token:
    """Login user and get JWT token"""
    return auth_manager.login(user_login)


def get_current_user(token: str) -> Optional[User]:
    """Get current user from token"""
    return auth_manager.get_current_user(token)


def add_to_watchlist(email: str, asteroid_id: str) -> User:
    """Add asteroid to user's watchlist"""
    return auth_manager.update_watchlist(email, asteroid_id, "add")


def remove_from_watchlist(email: str, asteroid_id: str) -> User:
    """Remove asteroid from user's watchlist"""
    return auth_manager.update_watchlist(email, asteroid_id, "remove")
