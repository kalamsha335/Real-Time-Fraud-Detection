import os
import json
import socket
import logging
from typing import Dict, Any, Optional
from confluent_kafka import Producer
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("kafka_producer")
logging.basicConfig(level=logging.INFO)

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TRANSACTIONS_TOPIC = os.getenv("KAFKA_TRANSACTIONS_TOPIC", "transactions")


def check_kafka_broker(host_port: str = BOOTSTRAP_SERVERS, timeout: float = 1.0) -> bool:
    """Verifies whether the Kafka broker socket is reachable."""
    try:
        parts = host_port.split(":")
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 9092
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


class FraudTransactionProducer:
    """Publishes transaction events to Kafka."""

    def __init__(self, bootstrap_servers: str = BOOTSTRAP_SERVERS):
        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[Producer] = None
        self._connected = False
        self.connect()

    def connect(self) -> bool:
        """Connect to broker if reachable."""
        if not check_kafka_broker(self.bootstrap_servers):
            logger.warning(
                "Kafka broker at %s is not reachable. Real-time streaming publisher is paused.",
                self.bootstrap_servers
            )
            self._connected = False
            return False

        try:
            conf = {
                "bootstrap.servers": self.bootstrap_servers,
                "client.id": "fraud-transaction-producer"
            }
            self.producer = Producer(conf)
            self._connected = True
            logger.info("Confluent Kafka Producer successfully initialized for %s", self.bootstrap_servers)
            return True
        except Exception as e:
            logger.error("Failed to connect Confluent Kafka Producer: %s", e)
            self._connected = False
            return False

    def is_connected(self) -> bool:
        """Check live broker connectivity."""
        if not self._connected:
            return False
        return check_kafka_broker(self.bootstrap_servers)

    def publish_transaction(self, transaction: Dict[str, Any], topic: str = TRANSACTIONS_TOPIC) -> bool:
        """Publish transaction payload to topic."""
        if not self.is_connected():
            raise ConnectionError(
                f"Kafka broker is unavailable at {self.bootstrap_servers}. Cannot publish event."
            )
        payload = json.dumps(transaction, default=str).encode("utf-8")
        self.producer.produce(topic, value=payload)
        self.producer.poll(0)
        logger.info("Published transaction to Kafka topic '%s'", topic)
        return True

    def flush(self, timeout: float = 2.0):
        if self.producer:
            self.producer.flush(timeout)

    def close(self):
        if self.producer:
            self.producer.flush(2.0)
            self._connected = False
