from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date
from typing import Optional, List, Union, Dict, Any # Added Any

# --- Token Schemas for Login ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[str] = None

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    username: str
    realname: Optional[str] = None
    student_id: Optional[str] = None
    group: Optional[str] = None

class UserOut(UserBase):
    id: int
    created_at: datetime
    is_admin: bool
    # Add fields expected by AdminStudentSummary that are common
    font_preference: Optional[str] = 'Inter' # Provide default
    notifications_enabled: Optional[bool] = False # Provide default

    class Config:
        from_attributes = True



