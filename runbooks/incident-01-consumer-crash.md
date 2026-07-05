# Incident 01: Consumer Pod Crash

**Date:** 2026-07-05
**Duration:** ~8 seconds
**Severity:** P2

## Summary
Consumer pod bị crash đột ngột (mô phỏng bị xóa thủ công). Kubernetes Deployment controller tự động phát hiện và khởi tạo Pod mới. Consumer mới kết nối lại Redpanda và tiếp tục đọc từ Kafka offset đã commit trước đó mà không bị mất dữ liệu.

## Timeline
- 22:12:08 — Consumer pod deleted (`kubectl delete pod`)
- 22:12:10 — Kubernetes Controller phát hiện thiếu Pod và khởi tạo Pod mới (`ecom-consumer-86c4fcf49b-892sl`)
- 22:12:14 — Pod mới hoàn tất việc kéo image và đạt trạng thái `1/1 Running`
- 22:12:16 — Consumer mới re-join Kafka Consumer Group và tiếp tục xử lý event

## Root Cause
- **Mô phỏng:** Pod bị xóa thủ công bằng lệnh `kubectl delete pod`.
- **Thực tế Production:** OOMKilled (tràn bộ nhớ), Liveness Probe thất bại, hoặc Node chứa Pod bị lỗi phần cứng.

## Impact
- Gián đoạn ghi nhận Metrics trong khoảng 8 giây trên Grafana.
- Không mất mát dữ liệu (Data Loss = 0) do các event đã được Redpanda đệm an toàn.

## Remediation
- Kubernetes Deployment tự động thực hiện Self-Healing.
- Kafka Consumer Group rebalance và khôi phục xử lý tự động.

## Action Items
- [x] Cấu hình Liveness & Readiness Probes cho Consumer Pod
- [x] Bổ sung PodDisruptionBudget (PDB) đảm bảo luôn có tối thiểu 1 Pod khả dụng
- [x] Đặt cảnh báo (Alert) trên Prometheus khi số lần Restart của Consumer tăng

## Lessons Learned
1. Cơ chế Self-Healing của Kubernetes phản ứng cực nhanh (MTTR < 10 giây).
2. Kafka Consumer Group đảm bảo tính toàn vẹn của dữ liệu trong quá trình failover.
