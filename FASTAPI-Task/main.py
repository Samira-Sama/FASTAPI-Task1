from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

app = FastAPI()

# Secret key to sign the JWT tokens
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

# Dependency to get the current user based on the JWT token
async def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="token"))):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Custom logic to fetch user data from a database or another source
    # For simplicity, returning a hardcoded user here
    return {"username": username, "roles": ["admin"]}

# Middleware for custom authorization based on user roles
async def authorize_user(current_user: dict = Depends(get_current_user), required_roles: list = None):
    if required_roles is None:
        return current_user

    user_roles = current_user.get("roles", [])
    for role in required_roles:
        if role in user_roles:
            return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You don't have access to this resource",
    )

@app.get("/secure-endpoint", dependencies=[Depends(authorize_user)])
def secure_endpoint(current_user: dict = Depends(get_current_user)):
    return {"message": "This is a secure endpoint", "user": current_user}

