"""
CloudCore Consumer — Tumbling Window Metrics & AI Integration
─────────────────────────────────────────────────────────────
Đọc event từ Redpanda, tính metrics theo tumbling window 30s,
và expose metrics cho Prometheus scrape.

ĐỒNG THỜI: Tích hợp với AI Service (Phase 3)
1. Tự động nạp sản phẩm vào AI Catalog khi thấy sản phẩm mới.
2. Gọi AI Suggestion khi khách hàng thêm vào giỏ (cart).
"""
import json
import time
import threading
import os
import logging
import requests
from collections import defaultdict
from kafka import KafkaConsumer
from prometheus_client import Counter, Gauge, start_http_server

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

# ── Cấu hình AI Service ──
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai-inference.ai:8000")
cataloged_products = set()  # Lưu in-memory các ID đã nạp để tránh gọi API trùng

# ── Prometheus Metrics ──
events_total = Counter("ecom_events_total", "Total e-commerce events processed", ["event_type"])
revenue_gauge = Gauge("ecom_revenue_per_window", "Revenue in current 30s window (USD)")
conv_cart_view = Gauge("ecom_conversion_cart_to_view", "Cart-to-View conversion ratio")
conv_buy_cart = Gauge("ecom_conversion_purchase_to_cart", "Purchase-to-Cart conversion ratio")

# ── Tumbling Window State ──
window = defaultdict(int)
window_revenue = 0.0
WINDOW_SECONDS = 30

def flush_window():
    global window, window_revenue
    v, c, p = window.get("view", 1), window.get("cart", 0), window.get("purchase", 0)
    
    revenue_gauge.set(window_revenue)
    conv_cart_view.set(c / v if v else 0)
    conv_buy_cart.set(p / c if c else 0)

    logger.info(
        f"Window flush | views={v} carts={c} purchases={p} "
        f"revenue=${window_revenue:.2f} "
        f"cart/view={c/v:.3f} buy/cart={p/c if c else 0:.3f}"
    )

    window = defaultdict(int)
    window_revenue = 0.0

def flusher():
    while True:
        time.sleep(WINDOW_SECONDS)
        flush_window()

def sync_to_ai_catalog(product_id, brand, category):
    """Gửi thông tin sản phẩm sang kho nhớ của AI."""
    if not product_id or product_id in cataloged_products:
        return
    
    # LỌC DỮ LIỆU RÁC: Nếu không có brand và không có category thì bỏ qua luôn!
    if not brand and not category:
        return
    
    brand_str = str(brand) if brand else ""
    cat_str = str(category).replace(".", " ") if category else ""
    product_name = f"{brand_str} {cat_str}".strip()

    try:
        res = requests.post(
            f"{AI_SERVICE_URL}/catalog",
            json={"product_id": str(product_id), "name": product_name},
            timeout=2
        )
        if res.status_code == 200:
            cataloged_products.add(product_id)
            logger.info(f"[AI Catalog] Added: {product_id} - '{product_name}'")
    except Exception as e:
        logger.warning(f"[AI Catalog] Fail to add {product_id}: {e}")

def get_ai_recommendation(brand, category):
    """Hỏi AI gợi ý sản phẩm tương tự khi user thêm vào giỏ."""
    # LỌC DỮ LIỆU RÁC
    if not brand and not category:
        return
        
    brand_str = str(brand) if brand else ""
    cat_str = str(category).replace(".", " ") if category else ""
    query_text = f"{brand_str} {cat_str}".strip()

    try:
        res = requests.post(
            f"{AI_SERVICE_URL}/recommend",
            json={"text": query_text, "top_k": 3},
            timeout=2
        )
        if res.status_code == 200:
            recs = res.json().get("recommendations", [])
            names = [r["name"] for r in recs]
            logger.info(f"💡 [AI Suggestion] User added '{query_text}' to cart. AI suggests: {names}")
    except Exception as e:
        logger.warning(f"[AI Suggestion] Failed to get recommendations: {e}")

def main():
    global window_revenue
    start_http_server(8001)
    logger.info("Prometheus metrics server started on :8001")
    threading.Thread(target=flusher, daemon=True).start()

    KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "redpanda.streaming:19092")
    consumer = None
    for attempt in range(10):
        try:
            consumer = KafkaConsumer(
                "ecommerce-events",
                bootstrap_servers=KAFKA_BROKERS,
                group_id="cloudcore-consumer",
                value_deserializer=lambda m: json.loads(m.decode()),
                auto_offset_reset="earliest",
            )
            logger.info(f"Connected to Kafka: {KAFKA_BROKERS}")
            break
        except Exception as e:
            logger.warning(f"Attempt {attempt+1}: {e}")
            time.sleep(5)

    if not consumer:
        raise ConnectionError("Cannot connect to Kafka")

    count = 0
    for msg in consumer:
        event = msg.value
        etype = event.get("event_type", "unknown")
        pid = event.get("product_id")
        brand = event.get("brand")
        cat = event.get("category_code")

        # Đồng bộ sản phẩm sang AI Catalog
        sync_to_ai_catalog(pid, brand, cat)

        # Cập nhật Metrics
        events_total.labels(event_type=etype).inc()
        window[etype] += 1
        if etype == "purchase":
            window_revenue += event.get("price", 0)
            
        # Nếu thêm vào giỏ, hỏi AI gợi ý ngay lập tức
        if etype == "cart":
            get_ai_recommendation(brand, cat)

        count += 1
        if count % 1000 == 0:
            logger.info(f"Processed {count} events total")

if __name__ == "__main__":
    main()
