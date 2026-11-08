import os
import json
import uuid
import random
from fastapi import APIRouter, Depends, HTTPException
from api.schemas import (
    PredictionRequest,
    PredictionResponse,
    ModelInfoResponse,
    SimulationRequest,
    SimulationResponse
)
from api.services.model_service import ModelService, get_model_service

router = APIRouter(tags=["Predictions & Model"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAMPLE_JSON_PATH = os.path.join(BASE_DIR, "tests", "sample_transaction.json")
_TEMPLATE_CACHE = None


def _get_base_template():
    global _TEMPLATE_CACHE
    if _TEMPLATE_CACHE is None and os.path.exists(SAMPLE_JSON_PATH):
        with open(SAMPLE_JSON_PATH, "r", encoding="utf-8") as f:
            _TEMPLATE_CACHE = json.load(f)
    return dict(_TEMPLATE_CACHE) if _TEMPLATE_CACHE else {}


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict transaction fraud probability",
    description="Validates all 432 input features, applies the saved XGBoost pipeline, calculates probability, and assigns fraud risk."
)
def predict_transaction(
    payload: PredictionRequest,
    service: ModelService = Depends(get_model_service)
) -> PredictionResponse:
    return service.predict(
        transaction_data=payload.transaction,
        transaction_id=payload.transaction_id,
        custom_timestamp=payload.timestamp
    )


@router.post(
    "/simulator/inject",
    response_model=SimulationResponse,
    summary="Inject simulated transactions for live dashboard demonstrations",
    description="Generates valid 432-feature IEEE-CIS transactions according to selected scenario profile and executes real-time inference."
)
def inject_simulated_transactions(
    req: SimulationRequest,
    service: ModelService = Depends(get_model_service)
) -> SimulationResponse:
    template = _get_base_template()
    if not template:
        raise HTTPException(status_code=500, detail="Transaction feature template not found on server.")

    results = []
    scenarios = ["legitimate", "suspicious", "fraud"]

    for _ in range(req.count):
        tx = dict(template)
        sim_id = f"TX-SIM-{uuid.uuid4().hex[:8].upper()}"

        active_scenario = req.scenario
        if active_scenario == "random":
            active_scenario = random.choices(scenarios, weights=[0.60, 0.25, 0.15])[0]

        if active_scenario == "fraud":
            tx["TransactionAmt"] = round(random.uniform(900.0, 4800.0), 2)
            tx["card1"] = random.choice([9500, 15066, 17188])
            tx["C1"] = float(random.randint(25, 60))
            tx["C2"] = float(random.randint(20, 50))
            tx["D1"] = float(random.randint(1, 5))
        elif active_scenario == "suspicious":
            tx["TransactionAmt"] = round(random.uniform(220.0, 480.0), 2)
            tx["card1"] = random.choice([4042, 7553])
            tx["C1"] = float(random.randint(5, 12))
            tx["C2"] = float(random.randint(4, 9))
            tx["D1"] = float(random.randint(5, 20))
        else:  # legitimate
            tx["TransactionAmt"] = round(random.uniform(15.0, 85.0), 2)
            tx["card1"] = random.choice([13926, 2755])
            tx["C1"] = 1.0
            tx["C2"] = 1.0
            tx["D1"] = float(random.randint(14, 60))

        tx["TransactionDT"] = int(tx.get("TransactionDT", 86400)) + random.randint(10, 3600)

        pred = service.predict(
            transaction_data=tx,
            transaction_id=sim_id
        )
        results.append(pred)

    return SimulationResponse(
        delivered=len(results),
        scenario=req.scenario,
        results=results
    )


@router.get(
    "/model/info",
    response_model=ModelInfoResponse,
    summary="Get model metadata and schema specification",
    description="Returns model pipeline configuration, decision threshold, and the 432 expected features."
)
def get_model_information(
    service: ModelService = Depends(get_model_service)
) -> ModelInfoResponse:
    return service.get_model_info()

