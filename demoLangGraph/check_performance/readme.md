- Throughput (QPS)
- Latency (p50, p90, p95, p99, max)
- Error rate
- Concurrency thực tế
- CPU%, RAM (RSS MB), Network I/O


Ví dụ: chạy 10 request, tối đa 5 request song song
python -m demoLangGraph.check_performance.bench_throughput_resource --total 10 --concurrency 5 --warmup 0
Tham số
--total: tổng số request benchmark.

--concurrency: số request chạy đồng thời.

--warmup: số request chạy làm nóng trước (không tính vào kết quả).

--mock: bật mock LLM (fake), để test nhanh không tốn tiền.

Metrics đo được
1. QPS (Queries Per Second / Throughput)
Công thức:

QPS = Tổng số request / Tổng thời gian chạy (giây)
Ví dụ: 10 request trong 5s → QPS = 2.0.

2. Latency percentiles
p50 (median): 50% request nhanh hơn giá trị này.

p90: 90% request nhanh hơn, 10% chậm hơn.

p95: 95% request nhanh hơn, 5% chậm hơn.

p99: 99% request nhanh hơn, 1% chậm hơn.

max: request chậm nhất.

Cách tính: sort danh sách latency, lấy phần tử tại chỉ số:

k = round( (p/100) * (n-1) )
với n là số request.

3. Errors
Error rate:


Error Rate (%) = (Số request lỗi / Tổng số request) * 100
4. Concurrent in-flight peak
Số request đồng thời cao nhất trong quá trình benchmark:


Peak Inflight = max_t( Số request đang xử lý tại thời điểm t )
5. CPU%
Đo bằng psutil.Process().cpu_percent().
% thời gian CPU mà process Python chiếm so với thời gian thực.

6. RAM (RSS MB)
Resident Set Size = lượng RAM thật sự process dùng:


rssMB = rss_bytes / 1024^2
7. Network I/O (MB/s)
Chênh lệch byte gửi/nhận giữa hai lần đo:

Δsent_MB  = (bytes_sent[t] - bytes_sent[t-1]) / 1e6
Δrecv_MB  = (bytes_recv[t] - bytes_recv[t-1]) / 1e6


QPS → đo công suất hệ thống.

Latency percentiles → đo trải nghiệm người dùng & kiểm soát đuôi chậm.

Errors → đo độ ổn định.

Concurrent peak → đo mức độ song song thực tế.

CPU% → xem có bị nghẽn compute không.

RSS MB → phát hiện memory leak.

Network I/O → đo áp lực băng thông khi gọi API ngoài.


Ví dụ kết quả

=== THROUGHPUT REPORT ===
total: 10
concurrency: 5
elapsed_s: 6.429
qps: 1.56
errors: 0
latency_ms: {'p50': 1544.1, 'p90': 22423.1, 'p95': 103106.3, 'p99': 103106.3, 'max': 103106.3}
concurrent_inflight_peak: 5

=== RESOURCE SUMMARY ===
cpu%: {'avg': 1.8, 'p95': 7.8}
rssMB: {'avg': 90.2, 'max': 90.6}
net_MB_per_s: {'sent_avg': 0.01, 'recv_avg': 0.0}
Ý nghĩa:

QPS ~1.5 req/s.

p50 ~1.5s: đa số request nhanh.

p95/p99 ~100s: có outlier cực chậm → “đuôi dài”.

CPU thấp, RAM ổn định (~90 MB).


