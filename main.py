from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from dotenv import dotenv_values

app = FastAPI()
security = HTTPBasic()

cfg = dotenv_values(".env")  # loads DEVELOPER_USERNAME and PASSWORD

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, cfg["DEV_USERNAME"])
    correct_password = secrets.compare_digest(credentials.password, cfg["DEV_PASSWORD"])

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access denied",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/")
def root(user: str = Depends(get_current_user)):
    return {"message": f"Hello {user}, your dev access is granted ✅"}

@app.get("/status")
def status_check(user: str = Depends(get_current_user)):
    return {"status": "Bot is running 🔄"}
