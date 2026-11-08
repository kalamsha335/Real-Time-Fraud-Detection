import os
import json
import logging
from typing import Optional, Callable, Dict, Any
from confluent_kafka import Consumer, Producer, KafkaError
from dotenv import load_dotenv

from .producer import check_kafka_broker

load_dotenv()
logger = logging.getLogger("kafka_consumer")
logging.basicConfig(level=logging.INFO)

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TRANSACTIONS_TOPIC = os.getenv("KAFKA_TRANSACTIONS_TOPIC", "transactions")
PREDICTIONS_TOPIC = os.getenv("KAFKA_PREDICTIONS_TOPIC", "fraud-predictions")
ALERTS_TOPIC = os.getenv("KAFKA_ALERTS_TOPIC", "fraud-alerts")


class FraudStreamingService:
    """
    Consumes transactions from Kafka, executes fraud inference,
    and publishes prediction and alert events.
    """

    def __init__(self, bootstrap_servers: str = BOOTSTRAP_SERVERS):
        self.bootstrap_servers = bootstrap_servers
        self.consumer: Optional[Consumer] = None
        self.producer: Optional[Producer] = None
        self._running = False

    def is_broker_available(self) -> bool:
        return check_kafka_broker(self.bootstrap_servers)

    def start(self, inference_fn: Callable[[Dict[str, Any]], Dict[str, Any]], max_messages: Optional[int] = None):
        """Start consumption loop."""
        if not self.is_broker_available():
            raise ConnectionError(
                f"Kafka broker unreachable at {self.bootstrap_servers}. Stream consumer cannot start."
            )

        try:
            conf_consumer = {
                "bootstrap.servers": self.bootstrap_servers,
                "group.id": "fraud-detection-inference-group",
                "auto.offset.reset": "latest"
            }
            conf_producer = {
                "bootstrap.servers": self.bootstrap_servers,
                "client.id": "fraud-prediction-publisher"
            }

            self.consumer = Consumer(conf_consumer)
            self.producer = Producer(conf_producer)
            self.consumer.subscribe([TRANSACTIONS_TOPIC])
            self._running = True

            logger.info("Kafka consumer subscribed to '%s'. Forwarding predictions to '%s' and alerts to '%s'...",
                        TRANSACTIONS_TOPIC, PREDICTIONS_TOPIC, ALERTS_TOPIC)

            processed = 0
            while self._running:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error("Consumer error: %s", msg.error())
                        break

                payload = json.loads(msg.value().decode("utf-8"))
                result = inference_fn(payload)

                # Send prediction event
                pred_bytes = json.dumps(result, default=str).encode("utf-8")
                self.producer.produce(PREDICTIONS_TOPIC, value=pred_bytes)

                # Send alert event if high risk or fraud
                if result.get("prediction") == 1 or result.get("risk_level") in ["HIGH", "MEDIUM"]:
                    self.producer.produce(ALERTS_TOPIC, value=pred_bytes)

                self.producer.poll(0)
                processed += 1
                if max_messages and processed >= max_messages:
                    break

        except Exception as e:
            logger.error("Consumer streaming error: %s", e)
            raise
        finally:
            self.stop()

    def stop(self):
        self._running = False
        if self.consumer:
            self.consumer.close()
            self.consumer = None
        if self.producer:
            self.producer.flush(2.0)
            self.producer = None
        logger.info("Kafka streaming consumer stopped.")
