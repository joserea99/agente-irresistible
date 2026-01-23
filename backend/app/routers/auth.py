from fastapi import APIRouter, HTTPException, Depends
from ..models.auth import UserLogin, UserRegister, Token
from ..services.auth_service import verify_user, add_user, init_db
from datetime import datetime, timedelta
from jose import jwt

router = APIRouter()

# Secret key for JWT (should be in env)
SECRET_KEY = "supersecretkey" # TODO: Move to .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    user, status = verify_user(user_data.username, user_data.password, user_data.device_fingerprint)
    
    if not user:
        if status == "trial_expired":
            raise HTTPException(status_code=403, detail="Trial expired. Please subscribe.")
        if status == "subscription_expired":
            raise HTTPException(status_code=403, detail="Subscription expired.")
        if status == "new_device_2fa":
             # In a real scenario, trigger email sending here
            raise HTTPException(status_code=401, detail="New device detected. 2FA code sent.")
        
        # Generic error fallback
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # user is (full_name, role, subscription_status)
    full_name, role, subscription_status = user
    user_info = {"username": user_data.username, "full_name": full_name, "role": role, "subscription_status": subscription_status}
    access_token = create_access_token(data={"sub": user_data.username, "role": role, "subscription_status": subscription_status})
    
    return {"access_token": access_token, "token_type": "bearer", "user": user_info}

@router.post("/register")
async def register(user_data: UserRegister):
    success = add_user(user_data.username, user_data.password, user_data.full_name, user_data.role)
    if not success:
        raise HTTPException(status_code=400, detail="Username already registered")
    return {"message": "User created successfully"}

@router.get("/users")
async def list_users():
    # In a real app, verify admin role from token here
    from ..services.auth_service import get_all_users
    return get_all_users()

@router.delete("/users/{username}")
async def remove_user(username: str):
    # In a real app, verify admin role from token here
    from ..services.auth_service import delete_user
    if delete_user(username):
        return {"message": "User deleted"}
    raise HTTPException(status_code=400, detail="Failed to delete user")

