from fastapi import FastAPI, WebSocket
from twelvedata import TDClient
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Float, DateTime
from datetime import datetime
from uuid import uuid4
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

API_KEY = "d1a5tapr01qltimvd880d1a5tapr01qltimvd88g"
SYMBOLS = ["EUR/USD", "GBP/USD", "USD/JPY"]

td = TDClient(apikey=API_KEY)

DATABASE_URL = "sqlite+aiosqlite:///./prices.db"
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class Price(Base):
    __tablename__ = "prices"
    id = Column(String, primary_key=True)
    symbol = Column(String)
    price = Column(Float)
    timestamp = Column(DateTime)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI(on_startup=[init_db])

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    streams = td.websocket.streams(["FOREX:" + s for s in SYMBOLS])
    async for msg in streams:
        sym = msg["symbol"].split(":")[1]
        price = float(msg["price"])
        ts = datetime.utcnow()
        await ws.send_json({"symbol": sym, "price": price, "timestamp": ts.isoformat()})
        async with SessionLocal() as session:
            session.add(Price(id=str(uuid4()), symbol=sym, price=price, timestamp=ts))
            await session.commit()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_home():
    return FileResponse("static/index.html")