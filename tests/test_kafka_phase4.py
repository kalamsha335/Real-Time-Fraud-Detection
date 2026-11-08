import unittest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from kafka.producer import FraudTransactionProducer, check_kafka_broker
from kafka.consumer import FraudStreamingService
from kafka.simulator import TransactionSimulator


class TestPhase4KafkaStreaming(unittest.TestCase):

    def test_01_broker_connectivity_check(self):
        """Verify broker availability detection returns boolean without hanging."""
        available = check_kafka_broker("localhost:9092", timeout=0.5)
        self.assertIsInstance(available, bool)

    def test_02_producer_handles_offline_broker_accurately(self):
        """Producer must accurately report disconnected status when broker is down."""
        producer = FraudTransactionProducer(bootstrap_servers="localhost:9099")
        self.assertFalse(producer.is_connected())

        # Must raise ConnectionError rather than faking success
        with self.assertRaises(ConnectionError):
            producer.publish_transaction({"test": 123})

    def test_03_consumer_fails_fast_when_broker_offline(self):
        """Consumer must raise ConnectionError if broker is unavailable."""
        consumer_service = FraudStreamingService(bootstrap_servers="localhost:9099")
        self.assertFalse(consumer_service.is_broker_available())

        with self.assertRaises(ConnectionError):
            consumer_service.start(inference_fn=lambda x: x, max_messages=1)

    def test_04_simulator_loads_sample_records(self):
        """Simulator correctly loads and prepares authentic sample records."""
        sim = TransactionSimulator(sample_size=10)
        self.assertGreater(len(sim.records), 0)

        # Ensure no NaN values exist in records
        first_record = sim.records[0]
        self.assertIn("TransactionAmt", first_record)
        for k, v in first_record.items():
            if isinstance(v, float):
                import math
                self.assertFalse(math.isnan(v), f"Key {k} contains NaN float")

    def test_05_simulator_stream_generator(self):
        """Simulator stream generator yields unique simulated transaction IDs."""
        sim = TransactionSimulator(sample_size=5)
        gen = sim.stream_generator()
        first = next(gen)
        second = next(gen)

        self.assertIn("_simulated_id", first)
        self.assertIn("_simulated_id", second)
        self.assertNotEqual(first["_simulated_id"], second["_simulated_id"])

    def test_06_simulator_http_streaming(self):
        """Simulator streams transactions directly to FastAPI server over HTTP or TestClient."""
        sim = TransactionSimulator(sample_size=3)
        delivered = sim.run_http_stream(
            api_url="http://127.0.0.1:8000/predict",
            rate_per_sec=20.0,
            total_events=3
        )
        if delivered == 0:
            # Fallback to TestClient if standalone background uvicorn server is not active
            from fastapi.testclient import TestClient
            from api.main import app
            client = TestClient(app)
            client_delivered = 0
            for tx in sim.stream_generator():
                resp = client.post("/predict", json={"transaction": tx})
                if resp.status_code == 200:
                    client_delivered += 1
                if client_delivered >= 3:
                    break
            self.assertEqual(client_delivered, 3)
        else:
            self.assertEqual(delivered, 3)


if __name__ == "__main__":
    unittest.main()
