# Engineering Log 05: Data Streaming Pipeline & Cleansing Layer

## 1. Mục tiêu kỹ thuật
Để hệ thống có khả năng tiêu thụ 4.1 triệu sự kiện E-commerce (View, Cart, Purchase), tôi xây dựng một Streaming Pipeline với **Redpanda** (Kafka-compatible) làm trái tim điều phối luồng dữ liệu.
Hệ thống gồm 2 thành phần chính:
- **Producer (Python):** Đọc dữ liệu từ file CSV khổng lồ (~460MB) và bắn vào Redpanda với tốc độ giả lập cực cao (Speed factor: 120x - 600x).
- **Consumer (Python):** Bắt dữ liệu từ luồng Redpanda, tính toán Real-time Analytics (Tumbling Windows 30 giây để tính Doanh thu và Phễu chuyển đổi) và đồng bộ với dịch vụ AI.

## 2. Quá trình thực thi

### Triển khai Redpanda trên Kubernetes
- Tôi quyết định triển khai Redpanda trực tiếp vào cụm k3d qua Helm Chart. Redpanda nhẹ và có độ trễ cực thấp so với Apache Kafka truyền thống do loại bỏ được Zookeeper, rất phù hợp cho kiến trúc Cloud-Native.

### Xây dựng Producer & Consumer
- Sử dụng thư viện `kafka-python` (sau chuyển sang `confluent_kafka` cho hiệu suất cao hơn).
- **Producer:** Được thiết kế để "Replay" dữ liệu lịch sử một cách có kiểm soát. Thay vì dump toàn bộ 4 triệu dòng vào queue cùng lúc, tôi viết logic tính toán `time_diff` để mô phỏng đúng thời gian khách hàng thực sự thao tác trên web, nhưng có tính năng Fast-forward (Tua nhanh) để phục vụ việc test.
- **Consumer:** Sử dụng cơ chế Prometheus Metrics Exporter (chạy port 8000) để trực tiếp expose các chỉ số kinh doanh: `ecom_events_total`, `ecom_revenue_per_window`, và các chỉ số phễu chuyển đổi (`view_to_cart`).

## 3. Trục trặc gặp phải & Cách giải quyết (Troubleshooting)

**Vấn đề 1: Giao tiếp nội mạng (Networking DNS) trong Kubernetes**
*Nguyên nhân:* Lúc đầu, Consumer báo lỗi `Broker: Node update pattern failed`, không thể tìm thấy máy chủ Redpanda do sai cấu hình địa chỉ.
*Cách giải quyết:* Thay vì dùng `localhost` (chỉ có tác dụng trên máy host), tôi áp dụng triệt để cơ chế Service Discovery của Kubernetes. Chuyển cấu hình Kafka Bootstrap Servers thành `redpanda-0.redpanda.streaming.svc.cluster.local:9093`, giải quyết hoàn toàn vấn đề giao tiếp giữa các Pods ở các namespace khác nhau.

**Vấn đề 2: "Rác" dữ liệu làm "ngu" AI (Data Cleansing Crisis)**
*Bối cảnh:* Khi ghép nối Consumer với AI Service, tôi phát hiện ra kết quả Recommendations trả về cực kỳ vô lý.
*Nguyên nhân Root Cause:* Khảo sát sâu vào tập dữ liệu Kaggle, tôi bàng hoàng nhận ra có tới **40-50% số lượng sự kiện bị thiếu hoàn toàn thuộc tính `brand` và `category_code`**. Khi bắn các giá trị `NULL` hoặc rỗng này vào mô hình Vector, AI không có dữ liệu ngữ nghĩa để tạo Embedding, dẫn đến việc nó "học sai" và gợi ý rác.
*Cách giải quyết (Data Cleansing Layer):* Tôi lập tức bổ sung một lớp "Rửa dữ liệu" trực tiếp vào mã nguồn của Consumer. Trước khi gọi API `/catalog` của AI, hệ thống sẽ kiểm tra:
```python
if not event.get('brand') and not event.get('category_code'):
    # Dropping noise event
    continue
```
Chỉ những sự kiện có đủ Metadata mới được nạp vào Vector Database. Sau khi áp dụng lớp Filter này, chất lượng gợi ý từ AI trở nên cực kỳ chính xác.

## 4. Kết quả (Outcome)
Pipeline Streaming vận hành ở tốc độ cao (hàng ngàn events/giây) một cách mượt mà. Hệ thống hoàn thành được vai trò luân chuyển dữ liệu từ tập tĩnh (Static CSV) thành luồng sự kiện thời gian thực (Real-time Stream), tự dọn dẹp dữ liệu và đưa vào tính toán AI thành công.
