from typing import Union

from fastapi import FastAPI, HTTPException # type: ignore
from pydantic import BaseModel # type: ignore
from databases import Database # type: ignore
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, BigInteger # type: ignore
from datetime import datetime

DATABASE_URL = "postgres://swiftychairs:yJj0kOcX4FHv@ep-cold-snow-a41pb3ht.us-east-1.pg.koyeb.app/koyebdb"

# Set up the database connection
database = Database(DATABASE_URL)
metadata = MetaData()

# Define the license_keys table
license_keys = Table(
    "license_keys",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("key", String(255), unique=True, nullable=False),
    Column("expiry", BigInteger, nullable=True),
    Column("hwid", String(255), nullable=True)
)

app = FastAPI()

class LicenseRequest(BaseModel):
    license_key: str
    hwid: str  # Include HWID in the request

# Connect to the database when the app starts
@app.on_event("startup")
async def startup():
    await database.connect()

# Disconnect from the database when the app shuts down
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Define the endpoint to validate the license key
@app.post("/validate-key/")
async def validate_key(request: LicenseRequest):
    # Query to find the license key
    query = license_keys.select().where(license_keys.c.key == request.license_key)
    result = await database.fetch_one(query)
    
    if result is None:
        raise HTTPException(status_code=404, detail="License key not found")
    
    # Check if the license has expired
    current_time = int(datetime.utcnow().timestamp())
    if current_time > result['expiry']:
        raise HTTPException(status_code=403, detail="License key expired")
    
    # Check if HWID matches (if HWID is recorded)
    if result['hwid'] and result['hwid'] != request.hwid:
        raise HTTPException(status_code=403, detail="HWID does not match")
    
    return {"message": "License key is valid"}  