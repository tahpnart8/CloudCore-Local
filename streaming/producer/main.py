"""
CloudCore Producer — Time-Compressed Event Replay
─────────────────────────────────────────────────
Đọc file CSV e-commerce và gửi event vào Redpanda topic
với tốc độ nén thời gian (SPEED_FACTOR).

Ví dụ: SPEED_FACTOR=120 → 2 giờ data thật = 1 phút replay
"""
import csv
import json
import time
import os
import logging
import os
import time
from datetime import datetime
from kafka import KafkaProducer

# ── Cấu hình ──
SPEED_FACTOR = int(os.getenv("SPEED_FACTOR", "120"))
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "redpanda.streaming:19092")
TOPIC = os.getenv("KAFKA_TOPIC", "ecommerce-events")
CSV_PATH = os.getenv("CSV_PATH", "/data/2019-Oct.csv")

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

def create_producer():
    """Tạo Kafka producer với retry logic."""
    max_retries = 10
    for attempt in range(max_retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',              # Đảm bảo message được ghi
                retries=3,               # Retry nếu gửi thất bại
            )
            logger.info(f"Connected to Kafka broker: {KAFKA_BROKERS}")
            return producer
        except Exception as e:
            logger.warning(f"Attempt {attempt+1}/{max_retries}: {e}")
            time.sleep(5)
    raise ConnectionError(f"Cannot connect to {KAFKA_BROKERS}")

def replay_events(csv_path: str):
    """
    Đọc CSV và replay event theo thời gian nén.
    """
    producer = create_producer()
    
    logger.info(f"⏳ Waiting for {csv_path} to be copied via kubectl cp...")
    while not os.path.exists(csv_path):
        time.sleep(5)
    logger.info(f"✅ Found {csv_path}! Starting replay...")

    prev_time = None
    count = 0

    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse timestamp
            t = datetime.fromisoformat(
                row["event_time"].replace(" UTC", "")
            )

            # Tính delay giữa 2 event (nén thời gian)
            if prev_time:
                gap = (t - prev_time).total_seconds()
                sleep_time = max(0, min(gap / SPEED_FACTOR, 1.0))
                time.sleep(sleep_time)

            # Gửi event vào Kafka topic
            event = {
                "event_time": row["event_time"],
                "event_type": row["event_type"],
                "product_id": row["product_id"],
                "category_code": row.get("category_code", ""),
                "brand": row.get("brand", ""),
                "price": float(row["price"] or 0),
                "user_id": row["user_id"],
            }
            producer.send(TOPIC, value=event)

            count += 1
            if count % 1000 == 0:
                logger.info(f"Sent {count} events | Latest: {row['event_time']}")

            prev_time = t

    producer.flush()
    logger.info(f"✅ Replay complete! Total: {count} events")

if __name__ == "__main__":
    logger.info(f"Starting producer | Speed: {SPEED_FACTOR}x | Topic: {TOPIC}")
    replay_events(CSV_PATH)
