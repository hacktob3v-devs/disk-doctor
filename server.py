"""
EsnafDoktor - local web server.

Serves the web/ interface and exposes the local pipeline:
  GET  /api/health   which components are really running
  POST /api/analyze  classify + retrieve policy + risk + action card
  POST /api/reply    grounded reply from the local Ollama model (numbers checked against the policy)

Run: python server.py   (then open http://127.0.0.1:8000)
"""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core import assistant

ROOT = Path(__file__).resolve().parent

app = FastAPI(title="EsnafDoktor", docs_url="/api/docs", redoc_url=None)

_warm = {"ready": False, "seconds": None, "models": {}}


class Order(BaseModel):
    id: str = "TR-000000"
    amount: float = 0
    deliveryDays: int = 0
    pastOrders: int = 0
    pastReturns: int = 0
    unboxingVideo: bool = False
    boxDamaged: bool = False

    def features(self):
        return {
            "order_id": self.id,
            "order_amount_tl": float(self.amount),
            "delivery_days": int(self.deliveryDays),
            "past_orders_count": int(self.pastOrders),
            "past_returns_count": int(self.pastReturns),
            "unboxing_video_available": bool(self.unboxingVideo),
            "box_damaged_reported": bool(self.boxDamaged),
        }


class AnalyzeIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    order: Order = Order()
    mode: Literal["question", "review"] = "question"
    stars: int = Field(0, ge=0, le=5)
    customer: str = ""
    merchant: str = "Usta Deri"


class ReplyIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    policyTitle: str = ""
    policyText: str = ""
    mode: Literal["question", "review"] = "question"
    stars: int = Field(0, ge=0, le=5)
    customer: str = ""
    merchant: str = "Usta Deri"
    audience: Literal["customer", "merchant_draft"] = "customer"
    model: str | None = None


@app.get("/api/health")
def health():
    models = assistant.installed_models()
    return {
        "ready": _warm["ready"],
        "warmupSeconds": _warm["seconds"],
        "llm": {
            "available": bool(models),
            "model": assistant.pick_model(None, models),
            "installed": models,
        },
        "nlu": _warm["models"].get("nlu"),
        "risk": _warm["models"].get("risk"),
    }


@app.post("/api/analyze")
def analyze(body: AnalyzeIn):
    t0 = time.perf_counter()
    res = assistant.analyze_message(
        body.message, body.order.features(), body.mode, body.stars, body.merchant, body.customer
    )
    res["totalMs"] = round((time.perf_counter() - t0) * 1000)
    return res


@app.post("/api/reply")
def reply(body: ReplyIn):
    model = assistant.pick_model(body.model, assistant.installed_models())
    system, user = assistant.reply_prompt(
        body.message, body.policyTitle, body.policyText, body.merchant,
        body.customer, body.mode, body.stars, body.audience,
    )

    if not model:
        return {"text": None, "model": None, "grounded": False, "attempts": [], "reason": "no_local_model"}
    try:
        res = assistant.grounded_reply(system, user, body.policyText, body.message, model)
    except Exception as exc:  # Ollama stopped mid-request
        return {"text": None, "model": model, "grounded": False, "attempts": [], "reason": str(exc)}
    return {**res, "model": model}


def _warm_up():
    info = assistant.warm_up()
    _warm.update(ready=True, **info)
    print(f"[EsnafDoktor] Modeller hazır ({info['seconds']} sn): {info['models']}")


@app.on_event("startup")
def _startup():
    threading.Thread(target=_warm_up, daemon=True).start()


app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="web")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("ED_PORT", "8000")))
