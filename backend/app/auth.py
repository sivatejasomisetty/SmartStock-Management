from fastapi import Header, HTTPException, Depends
from firebase_admin import auth

def verify_firebase_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    token = authorization.split(" ")[1]

    try:
        return auth.verify_id_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_role(required_role: str):
    def checker(user=Depends(verify_firebase_token)):
        if user.get("role") != required_role:
            raise HTTPException(status_code=403, detail="Access denied")
        return user
    return checker
