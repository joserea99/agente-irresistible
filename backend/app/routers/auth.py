from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from ..models.auth import UserLogin, UserRegister, Token
from ..services.auth_service import verify_user, add_user, init_db
from datetime import datetime, timedelta
from jose import jwt

router = APIRouter()

# Secret key for JWT (should be in env)
SECRET_KEY = "supersecretkey" # TODO: Move to .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_admin_role(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
        if role != "admin":
            raise HTTPException(status_code=403, detail="Admin privileges required")
        return payload
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

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
async def list_users(admin: dict = Depends(verify_admin_role)):
    from ..services.auth_service import get_all_users
    return get_all_users()

@router.delete("/users/{username}")
async def remove_user(username: str, admin: dict = Depends(verify_admin_role)):
    from ..services.auth_service import delete_user
    if delete_user(username):
        return {"message": "User deleted"}
    raise HTTPException(status_code=400, detail="Failed to delete user")

@router.get("/bootstrap-admin")
async def bootstrap_admin(username: str, secret: str):
    # Temporary backdoor for first setup
    if secret != "irresistible-secret-setup-2026":
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    from ..services.auth_service import update_user_role
    update_user_role(username, "admin")
    return {"message": f"User {username} is now an admin. Please logout and login again."}


@router.put("/users/{username}/role")
async def change_role(username: str, role_data: dict, admin: dict = Depends(verify_admin_role)):
    from ..services.auth_service import update_user_role
    new_role = role_data.get("role")
    if new_role not in ["admin", "member"]:
       raise HTTPException(status_code=400, detail="Invalid role")
    update_user_role(username, new_role)
    return {"message": "Role updated"}

