from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from database import get_db
from models import Customer
import random

SECRET_KEY = "your_secret_key_here"  # Keep this consistent
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer()

# In-memory OTP store for development
OTP_STORE = {}

def request_otp_logic(mobile: str, db: Session):
    customer = db.query(Customer).filter(Customer.mobile_number == mobile).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found with this mobile number.")
    
    otp = str(random.randint(100000, 999999))
    OTP_STORE[mobile] = {
        "otp": otp,
        "expires_at": datetime.utcnow() + timedelta(minutes=5)
    }
    
    # Print to terminal for development/testing
    print(f"\n[DEV OTP SERVICE] OTP for {mobile}: {otp}\n")
    return {"message": "OTP sent successfully. Check server terminal."}

def verify_otp_logic(mobile: str, otp: str, db: Session):
    record = OTP_STORE.get(mobile)
    if not record or record["otp"] != otp or datetime.utcnow() > record["expires_at"]:
        raise HTTPException(status_code=400, detail="No OTP requested or OTP expired.")
    
    customer = db.query(Customer).filter(Customer.mobile_number == mobile).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")
    
    # Generate JWT Token using mobile number as subject
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": customer.mobile_number, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    # Clear OTP after successful use
    del OTP_STORE[mobile]
    
    return {"access_token": encoded_jwt, "token_type": "bearer"}

def get_current_customer(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        mobile: str = payload.get("sub")
        if mobile is None:
            raise credentials_exception
    except JWTError as e:
        print(f"\n[DEBUG] JWT Error: {e}\n")
        raise credentials_exception
        
    customer = db.query(Customer).filter(Customer.mobile_number == mobile).first()
    if customer is None:
        print(f"\n[DEBUG] Customer not found for mobile: {mobile}\n")
        raise credentials_exception
    return customer