# app/main.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from .db import init_db, get_session
from .models import Reading
from .ml import predict_water_usage
from sqlmodel import select

app = FastAPI(title="Water Footprint API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://waterfootprintcalc.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()

class ReadingIn(BaseModel):
    device_id: str = Field(..., example="esp32_01")
    flow_rate_lpm: float = Field(..., example=0.0, ge=0)
    total_liters: Optional[float] = Field(None, example=7.24, ge=0)
    reading_seconds: Optional[float] = None
    family_size: Optional[int] = Field(None, example=4, ge=1)
    appliances: Optional[int] = Field(None, example=3, ge=1)
    usage_hours: Optional[float] = Field(None, example=6, ge=0)
    primary_appliance: Optional[str] = Field(None, example="Sink")
    water_saving_device: Optional[bool] = Field(None, example=True)

@app.post("/readings", response_model=dict)
def create_reading(r: ReadingIn):
    with get_session() as session:
        db_obj = Reading(
            device_id=r.device_id,
            flow_rate_lpm=r.flow_rate_lpm,
            total_liters=r.total_liters or 0.0,
            reading_seconds=r.reading_seconds,
            family_size=r.family_size,
            appliances=r.appliances,
            usage_hours=r.usage_hours,
            primary_appliance=r.primary_appliance,
            water_saving_device=r.water_saving_device
        )
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
    return {"id": db_obj.id, "status": "saved"}

@app.get("/readings", response_model=List[Reading])
def list_readings(limit: int = 50):
    with get_session() as session:
        results = session.exec(select(Reading).order_by(Reading.timestamp.desc()).limit(limit)).all()
    return results

class PredictIn(BaseModel):
    family_size: int = Field(..., ge=1)
    usage_hours: float = Field(..., ge=0)
    appliances: int = Field(..., ge=1)
    primary_appliance: str
    water_saving_device: bool

@app.post("/predict")
def predict(payload: PredictIn):
    pred, savings = predict_water_usage(
        family_size=payload.family_size,
        usage_hours=payload.usage_hours,
        appliances=payload.appliances,
        primary_appliance=payload.primary_appliance,
        water_saving_device=payload.water_saving_device
    )
    return {
        "predicted_water_usage_liters": round(pred, 3),
        "predicted_savings_liters": round(savings, 3)
    }
