from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from typing import Annotated, Optional
from database import SessionLocal
from models import Users
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt


router = APIRouter()

# Password hashing settings
bcrypt_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# Use OAuth2 bearer tokens for login
OAuth2_bearer = OAuth2PasswordBearer(
    tokenUrl='login'
)

# Secret key and algorithm for JWT tokens
SECRET_KEY = '1107c977dd07554fa55dcf709a03d2ce03251ed33b651d63f66fc0515b5e683e'
ALGORITHM = 'HS256'


# =========================
# Pydantic Model
# =========================

class CreateUsers(BaseModel):
    email: str
    username: str
    firstname: str
    lastname: str
    password: str
    role: str
    # phone_number: str  # for downgrade

# This model is used when updating an existing user item
class UpdateUser(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    # phone_number: Optional[str] = None # for downgrade

# This model is used when updating an existing user password
class UpdatePassword(BaseModel):
    current_password: str
    new_password: str



# =========================
# Authenticate User
# =========================

def authenticate_user(username, password, db):
    # Check username and password from the database
    user = db.query(Users).filter(Users.username == username).first()
    if user is None:
        return False
    if bcrypt_context.verify(password, user.hash_password):
        return user
    return False


# =========================
# Create JWT Access Token
# =========================

def create_access_token(username: str, user_id: int, role : str, expires_delta: timedelta):
    encode = {'sub' : username, 'id' : user_id, 'role' : role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(
        encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# =========================
# Decode Token
# =========================

def get_current_user(token: Annotated[str, Depends(OAuth2_bearer)]):
    # Decode bearer token and return logged-in user data
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        role: str = payload.get('role')

        if username is None or user_id is None:
            raise HTTPException(status_code=404, detail='Username and user id is not match.')
        # Change this line in get_current_user
        return {'Username': username, 'id': user_id, 'role': role}
    except:
        raise HTTPException(status_code=404, detail='Invalid, User Not found.')



# =========================
# Database Dependency
# =========================

def get_db():
    # Open a database session for each request
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
# Get current user from token before handling request
user_dependency = Annotated[dict, Depends(get_current_user)]

# =========================
# Create User
# =========================

@router.post("/createuser")
def create_user(
    db: db_dependency,
    new_user: CreateUsers
):

    # 1. Check if the user already exists by username or email
    existing_user = db.query(Users).filter(
        (Users.username == new_user.username) | (Users.email == new_user.email)
    ).first()

    # 2. If a user is found, raise an exception
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="A user with this username or email already exists."
        )

    user_model = Users(
        email=new_user.email,
        username=new_user.username,
        firstname=new_user.firstname,
        lastname=new_user.lastname,
        hash_password=bcrypt_context.hash(new_user.password),
        is_active=True,
        role=new_user.role,
        # phone_number=new_user.phone_number
    )

    db.add(user_model)
    db.commit()
    db.refresh(user_model)

    return JSONResponse(
        status_code=201,
        content={
            "message": "User created successfully."
        }
    )


# =========================
# Login User
# =========================

@router.post("/login")
def login_user(db: db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=404, detail='Failed Authentication.')

    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=30))
    return {
    "access_token": token,
    "token_type": "bearer"
    }

# =========================
# UPDATE USERS
# =========================

@router.put("/edituser")
def update_user(
    user: user_dependency,
    db: db_dependency,
    update_user: UpdateUser
):
    # Update an existing todo owned by the current user
    if user is None:
        raise HTTPException(status_code=404, detail='Failed Authentication.')

    user = (
        db.query(Users)
        .filter(Users.id == user.get('id'))
        .first()
    )

    update_data = update_user.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return JSONResponse(
        status_code=200,
        content={
            "message": "User updated successfully."
        }
    )

# =========================
# UPDATE PASSWORD
# =========================

@router.put("/editpassword")
def update_password(
    user: user_dependency,
    db: db_dependency,
    update_password: UpdatePassword
):
    # Update an existing todo owned by the current user
    if user is None:
        raise HTTPException(status_code=404, detail='Failed Authentication.')

    user = (
        db.query(Users)
        .filter(Users.id == user.get('id'))
        .first()
    )

    if not bcrypt_context.verify(update_password.current_password , user.hash_password) :
        raise HTTPException(status_code=401, detail='Wrong Password. Please input correct password.')
    user.hash_password = bcrypt_context.hash(update_password.new_password)
    
    db.commit()
    db.refresh(user)

    return JSONResponse(
        status_code=200,
        content={
            "message": "Password updated successfully."
        }
    )




    