from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from ..database import Session
from sqlalchemy import or_
from .. import database, schemas, models, security

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    """
    Handles admin user login.
    - Verifies username and password.
    - Ensures the user is an admin.
    - Returns a JWT access token on success.
    """
    # Find the user by their username
    user = db.query(models.User).filter(models.User.username == form_data.username).first()

    # If user doesn't exist, password doesn't match, or they are not an admin, raise an error
    if not user or not security.verify_password(form_data.password, user.hashed_password) or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password, or not an administrator",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create the access token
    access_token = security.create_access_token(
        data={"user_id": user.id}
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserOut)
def read_users_me(current_user: models.User = Depends(security.get_current_admin_user)):
    """
    Fetches the profile for the currently logged-in admin user.
    """
    return current_user
