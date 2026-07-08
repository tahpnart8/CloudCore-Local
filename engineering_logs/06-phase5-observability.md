# Engineering Log 06: Full-stack Observability & Executive Dashboard

## 1. Mục tiêu kỹ thuật
Một hệ thống Cloud-Native nếu chạy "mù" (không có công cụ giám sát) thì như một quả bom nổ chậm. Ở Phase này, tôi thiết lập **Observability Stack** (Giám sát toàn diện) theo tiêu chuẩn SRE bao gồm:
- **Prometheus:** Kéo (Scrape) dữ liệu Metrics từ K8s nodes và ứng dụng.
- **Grafana:** Trực quan hóa dữ liệu bằng biểu đồ.
- **Alertmanager:** Gửi cảnh báo khi có sự cố.

## 2. Quá trình thực thi

### Triển khai Kube-Prometheus-Stack
Tôi sử dụng Helm chart `kube-prometheus-stack`. Đây là một bộ cài đặt hoàn chỉnh và chuyên nghiệp nhất hiện nay cho hệ sinh thái K8s. 
Thay vì cặm cụi cấu hình tay từng dòng YAML, tôi tận dụng `ServiceMonitor` (một Custom Resource Definition - CRD của Prometheus Operator). Tôi viết file `servicemonitor.yaml` để chỉ định Prometheus tự động dò tìm và "hút" dữ liệu từ cổng `8000` của Pod Consumer, biến số liệu E-commerce (view, cart, revenue) thành Time-series data.

### Thiết kế Grafana Executive Dashboard
Thay vì tạo những bảng Dashboard mặc định nhàm chán, tôi thiết kế một **Executive Dashboard** phân tầng rõ ràng:
1. **Executive Summary:** Thể hiện bằng chữ to, màu sắc nổi bật (Stat/Gauge) về Tổng Doanh thu, Events/s, Tỷ lệ chuyển đổi. Giúp C-level hoặc Product Owner nhìn lướt là hiểu sức khỏe kinh doanh.
2. **Business Insights:** Phễu bán hàng (Sales Funnel Drop-off) và dòng tiền Live (Live Revenue Stream).
3. **Infrastructure Health:** Bảng theo dõi RAM, CPU của Server Node và Agent Node, cùng bảng "bôi đỏ" các Pod bị Crash.

## 3. Trục trặc gặp phải & Cách giải quyết (Troubleshooting)

**Vấn đề 1: Port Conflict trên Host Windows (Address already in use)**
*Bối cảnh:* Khi tôi chạy lệnh `kubectl port-forward` để đưa giao diện Grafana (Port 3000) và Prometheus (Port 9090) ra ngoài Windows host, hệ thống báo lỗi không thể tạo Listeners.
*Nguyên nhân:* Cổng 3000 và 9090 trên máy tính Windows đã bị một tiến trình/ứng dụng khác chiếm giữ từ trước.
*Cách giải quyết:* Thay vì mất thời gian tìm và kill tiến trình cũ của Windows, tôi áp dụng Dynamic Port-mapping. Chuyển hướng `3001:80` cho Grafana và `9091:9090` cho Prometheus, linh hoạt giải quyết xung đột mạng cục bộ.

**Vấn đề 2: Dữ liệu bị gộp cục (Aggregation Issue) trên biểu đồ**
*Bối cảnh:* Khi hiển thị lượng CPU hoặc Memory, các đường biểu đồ bị gộp lại thành các chuỗi số IP dài ngoằng (ví dụ: `172.20.0.3:9100`), rất khó phân biệt đâu là Server, đâu là Agent.
*Cách giải quyết:* Tôi sử dụng PromQL nâng cao (`sort_desc`) để sắp xếp dữ liệu biểu đồ Bar Gauge tạo thành hình chiếc phễu. Đồng thời, tôi áp dụng tính năng **Transformations > Rename by regex** của Grafana để viết Regex bắt IP và tự động đổi tên thành `Server Node` và `Agent Node`. Điều này làm Dashboard trở nên thân thiện và chuyên nghiệp hơn rất nhiều.

## 4. Kết quả (Outcome)
Một trung tâm Giám sát (Control Center) cực kỳ mạnh mẽ đã được hoàn thiện. Mọi số liệu từ kỹ thuật (Tài nguyên phần cứng) cho đến nghiệp vụ (Doanh thu) đều được theo dõi theo thời gian thực với độ phân giải tính bằng giây, chuẩn bị sẵn sàng cho Phase cuối cùng: Chaos Engineering.
