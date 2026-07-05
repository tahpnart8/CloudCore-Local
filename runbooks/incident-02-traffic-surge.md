# Incident 02: Traffic Surge — Tăng Tải 5x Đột Ngột

**Date:** 2026-07-05
**Duration:** ~5 minutes
**Severity:** P2

## Summary
Lưu lượng event tăng đột biến 500% (từ SPEED_FACTOR 120 lên 600) mô phỏng đợt Flash Sale lớn. Tốc độ đẩy tin nhắn vượt quá khả năng xử lý đơn luồng của 1 Pod Consumer. Đội ngũ đã thực hiện Scale ngang (Horizontal Scaling) Consumer từ 1 lên 3 Replicas để giải tỏa Consumer Lag và ổn định hệ thống.

## Timeline
- 22:13:07 — Tăng tốc Producer SPEED_FACTOR=600 (gấp 5 lần bình thường)
- 22:13:08 — Tốc độ sinh event tăng vọt, Consumer đơn lẻ bị quá tải
- 22:13:09 — Thực hiện scale Consumer deployment: `kubectl scale --replicas=3`
- 22:13:15 — 3 Pods Consumer đồng loạt kết nối Kafka, tự động rebalance partition và chia sẻ tải
- 22:13:19 — Khôi phục tải về mức bình thường (SPEED_FACTOR=120, replicas=1)

## Root Cause
Tốc độ đẩy dữ liệu từ Producer lớn hơn năng lực tính toán của 1 Consumer instance đơn lẻ.

## Impact
- Tăng Consumer Lag nhẹ trong khoảng 5 giây đầu.
- Không mất mát dữ liệu do Redpanda thực hiện lưu đệm (buffering) an toàn.

## Remediation
- Mở rộng quy mô bằng cách tăng số lượng Consumer Replicas lên 3.
- Kafka Consumer Group mechanism tự động phân bổ lại partition xử lý song song.

## Action Items
- [x] Thiết lập HPA (Horizontal Pod Autoscaler) tự động scale theo chỉ số CPU/Consumer Lag
- [x] Đặt ngưỡng cảnh báo Alertmanager khi Consumer Lag vượt quá 5,000 events
- [x] Benchmark giới hạn chịu tải tối đa của 1 đơn vị Consumer

## Lessons Learned
1. Kiến trúc Kafka Consumer Group cho phép mở rộng quy mô xử lý theo chiều ngang vô cùng linh hoạt.
2. Bộ đệm Redpanda đóng vai trò cực kỳ quan trọng trong việc bảo vệ hệ thống khỏi các đợt lưu lượng đột biến.
