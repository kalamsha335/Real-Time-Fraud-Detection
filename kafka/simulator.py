import os
import sys
import json
import time
import uuid
import logging
import argparse
from typing import List, Dict, Any, Generator

import pandas as pd
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from kafka.producer import FraudTransactionProducer, check_kafka_broker

logger = logging.getLogger("transaction_simulator")
logging.basicConfig(level=logging.INFO)


class TransactionSimulator:
    """
    Simulates real-time financial transaction streams for demonstrations,
    sampling authentic IEEE-CIS dataset records.
    """

    def __init__(self, sample_size: int = 100):
        self.sample_size = sample_size
        self.records: List[Dict[str, Any]] = []
        self._load_sample_data()

    def _load_sample_data(self):
        """Load sample transaction records."""
        trans_csv = os.path.join(BASE_DIR, "dataset", "train_transaction.csv")
        ident_csv = os.path.join(BASE_DIR, "dataset", "train_identity.csv")
        sample_json = os.path.join(BASE_DIR, "tests", "sample_transaction.json")

        if os.path.exists(trans_csv) and os.path.exists(ident_csv):
            try:
                logger.info("Sampling %d records from IEEE-CIS dataset...", self.sample_size)
                df_t = pd.read_csv(trans_csv, nrows=self.sample_size)
                df_i = pd.read_csv(ident_csv, nrows=self.sample_size)
                df = df_t.merge(df_i, on="TransactionID", how="left")

                # Clean NaN values to None for valid JSON serialization
                for rec in df.to_dict(orient="records"):
                    clean = {k: (None if pd.isna(v) else v) for k, v in rec.items()}
                    self.records.append(clean)
                logger.info("Successfully loaded %d authentic transaction records.", len(self.records))
                return
            except Exception as e:
                logger.warning("Could not read raw CSVs, falling back to sample JSON: %s", e)

        if os.path.exists(sample_json):
            with open(sample_json, "r", encoding="utf-8") as f:
                template = json.load(f)
            # Create variations
            for i in range(self.sample_size):
                rec = dict(template)
                rec["TransactionDT"] = 86400 + (i * 300)
                rec["TransactionAmt"] = round(20.0 + (i * 15.5) % 800, 2)
                self.records.append(rec)
            logger.info("Generated %d simulated transaction records from template.", len(self.records))

    def stream_generator(self) -> Generator[Dict[str, Any], None, None]:
        """Yield transaction payloads indefinitely or through records."""
        idx = 0
        while True:
            if not self.records:
                break
            record = dict(self.records[idx % len(self.records)])
            record["_simulated_id"] = f"TX-SIM-{uuid.uuid4().hex[:8].upper()}"
            record["_event_time"] = time.time()
            yield record
            idx += 1

    def run_kafka_stream(self, rate_per_sec: float = 1.0, total_events: int = 50):
        """Stream events to Kafka broker."""
        producer = FraudTransactionProducer()
        if not producer.is_connected():
            logger.error("Cannot run Kafka stream: broker at %s is unavailable.", producer.bootstrap_servers)
            return False

        logger.info("Starting Kafka transaction simulator: %d events at %.1f events/sec...", total_events, rate_per_sec)
        delay = 1.0 / max(rate_per_sec, 0.1)

        count = 0
        for tx in self.stream_generator():
            producer.publish_transaction(tx)
            count += 1
            if count >= total_events:
                break
            time.sleep(delay)

        producer.flush()
        producer.close()
        logger.info("Simulator completed. Emitted %d transactions to Kafka.", count)
        return True

    def run_http_stream(self, api_url: str = "http://127.0.0.1:8000/predict", rate_per_sec: float = 2.0, total_events: int = 20):
        """Stream events directly to FastAPI endpoint over HTTP."""
        logger.info("Starting HTTP transaction simulator to %s: %d events at %.1f events/sec...", api_url, total_events, rate_per_sec)
        delay = 1.0 / max(rate_per_sec, 0.1)

        count = 0
        success_count = 0
        for tx in self.stream_generator():
            sim_id = tx.pop("_simulated_id", None)
            tx.pop("_event_time", None)

            payload = {
                "transaction": tx,
                "transaction_id": sim_id
            }

            try:
                r = requests.post(api_url, json=payload, timeout=5)
                if r.status_code == 200:
                    res = r.json()
                    logger.info("[%d/%d] %s => Prob: %.4f | Prediction: %s | Risk: %s",
                                count + 1, total_events, sim_id, res["fraud_probability"], res["status"], res["risk_level"])
                    success_count += 1
                else:
                    logger.warning("[%d/%d] %s returned status %d: %s", count + 1, total_events, sim_id, r.status_code, r.text[:100])
            except Exception as e:
                logger.error("Request failed: %s", e)

            count += 1
            if count >= total_events:
                break
            time.sleep(delay)

        logger.info("Simulator completed. Successfully delivered %d/%d transactions to API.", success_count, count)
        return success_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transaction Stream Simulator")
    parser.add_argument("--mode", choices=["kafka", "http"], default="http", help="Stream delivery target")
    parser.add_argument("--rate", type=float, default=2.0, help="Events per second")
    parser.add_argument("--count", "--events", dest="count", type=int, default=10, help="Total transactions to simulate")
    parser.add_argument("--api-url", "--url", dest="api_url", default="http://127.0.0.1:8000/predict", help="API URL for HTTP mode")
    args = parser.parse_args()

    sim = TransactionSimulator(sample_size=max(50, args.count))
    if args.mode == "kafka":
        sim.run_kafka_stream(rate_per_sec=args.rate, total_events=args.count)
    else:
        sim.run_http_stream(api_url=args.api_url, rate_per_sec=args.rate, total_events=args.count)
