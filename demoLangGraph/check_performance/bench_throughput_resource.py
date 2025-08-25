# --- load .env ---
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

import os, sys, time, argparse, random, asyncio, statistics, threading
import psutil
print("ROOT path:", ROOT)
print("GOOGLE_API_KEY?", bool(os.getenv("GOOGLE_API_KEY")))
print("GEMINI_MODEL?", os.getenv("GEMINI_MODEL"))
# === 1) Nhập graph như main.py của bạn ===
# main.py đang dùng: from demoLangGraph.travel_bot.graph import create_travel_bot
from demoLangGraph.travel_bot.graph import create_travel_bot  # giữ nguyên như project của bạn

# === 2) (Tuỳ chọn) MOCK LLM để không tốn tiền ===
def enable_mock_llm():
    try:
        import demoLangGraph.rule_agent.detech_intent as di
        import demoLangGraph.rule_agent.general as gr
    except Exception:
        di = gr = None

    class FakeLLM:
        def invoke(self, msg):
            # detect: luôn trả JSON intent=general
            return type("Obj", (), {"content": '{"intent": "general", "entities": {}, "missing_entities": []}'})

    class FakeLLMText:
        def invoke(self, msg):
            # general: trả về text đơn giản
            return type("Obj", (), {"content": "Mock travel answer"})

    if di and hasattr(di, "_llm"):
        di._llm = lambda: FakeLLM()
    if gr and hasattr(gr, "_llm"):
        gr._llm = lambda: FakeLLMText()

# === 3) Tạo payload đa dạng để tránh cache vô tình ===
TXT = [
    "du lịch đà nẵng 3 ngày 2 đêm cho 4 người",
    "đặt vé máy bay hà nội đi sài gòn 1 chiều",
    "xin chào, tư vấn giúp mình đi sapa cuối tuần",
    "đặt khách sạn ở nha trang, 2 người, trung bình"
]
def make_payload(i: int):
    return {"messages": [{"type": "human", "content": random.choice(TXT)}]}

# === 4) Sampler resource mỗi giây ===
class ResourceSampler(threading.Thread):
    def __init__(self, interval=1.0):
        super().__init__(daemon=True)
        self.proc = psutil.Process()
        self.interval = interval
        self.running = True
        self.snapshots = []  # (cpu, rss_mb, sent_mb, recv_mb)

    def run(self):
        last = psutil.net_io_counters()
        while self.running:
            cpu = self.proc.cpu_percent(None)
            rss_mb = self.proc.memory_info().rss / (1024*1024)
            now = psutil.net_io_counters()
            sent_mb = (now.bytes_sent - last.bytes_sent) / 1e6
            recv_mb = (now.bytes_recv - last.bytes_recv) / 1e6
            last = now
            self.snapshots.append((cpu, rss_mb, sent_mb, recv_mb))
            print(f"[RES] cpu%={cpu:.1f} rssMB={rss_mb:.1f} netΔ sent/recv MB={sent_mb:.2f}/{recv_mb:.2f}")
            time.sleep(self.interval)

    def stop(self):
        self.running = False

    def summary(self):
        if not self.snapshots:
            return {}
        cpus = [x[0] for x in self.snapshots]
        rss  = [x[1] for x in self.snapshots]
        snt  = [x[2] for x in self.snapshots]
        rcv  = [x[3] for x in self.snapshots]
        def pct(xs, p):
            xs2 = sorted(xs);
            k = int(round((p/100)*(len(xs2)-1)));
            return xs2[max(0, min(k, len(xs2)-1))]
        return {
            "cpu%": {"avg": round(sum(cpus)/len(cpus),1), "p95": round(pct(cpus,95),1)},
            "rssMB": {"avg": round(sum(rss)/len(rss),1),  "max": round(max(rss),1)},
            "net_MB_per_s": {"sent_avg": round(sum(snt)/len(snt),2), "recv_avg": round(sum(rcv)/len(rcv),2)},
        }

# === 5) 1 request E2E ===
async def one_call(app, payload):
    t0 = time.perf_counter()
    await app.ainvoke(payload)
    return (time.perf_counter() - t0) * 1000.0  # ms

# === 6) Chạy benchmark ===
async def run_bench(total: int, concurrency: int, warmup: int):
    app = create_travel_bot()
    sem = asyncio.Semaphore(concurrency)
    latencies, errors = [], 0
    inflight, peak_inflight = 0, 0

    async def worker(i):
        nonlocal errors, inflight, peak_inflight
        async with sem:
            try:
                inflight += 1
                peak_inflight = max(peak_inflight, inflight)
                ms = await one_call(app, make_payload(i))
                latencies.append(ms)
            except Exception:
                errors += 1
            finally:
                inflight -= 1

    # warmup
    if warmup > 0:
        await asyncio.gather(*(worker(-i) for i in range(warmup)))
        latencies.clear(); errors = 0; peak_inflight = 0

    t0 = time.perf_counter()
    await asyncio.gather(*(worker(i) for i in range(total)))
    elapsed = time.perf_counter() - t0
    qps = total/elapsed if elapsed > 0 else 0.0

    def pct(xs, p):
        if not xs: return 0.0
        xs2 = sorted(xs)
        k = int(round((p/100) * (len(xs2)-1)))
        return xs2[max(0, min(k, len(xs2)-1))]

    return {
        "total": total,
        "concurrency": concurrency,
        "elapsed_s": round(elapsed,3),
        "qps": round(qps,2),
        "errors": errors,
        "latency_ms": {
            "p50": round(pct(latencies,50),1),
            "p90": round(pct(latencies,90),1),
            "p95": round(pct(latencies,95),1),
            "p99": round(pct(latencies,99),1),
            "max": round(max(latencies) if latencies else 0.0,1),
        },
        "concurrent_inflight_peak": peak_inflight
    }

# === 7) CLI ===
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--total", type=int, default=300)
    ap.add_argument("--concurrency", type=int, default=30)
    ap.add_argument("--warmup", type=int, default=20)
    ap.add_argument("--mock", action="store_true", help="Mock LLM để benchmark không tốn phí")
    args = ap.parse_args()

    if args.mock:
        enable_mock_llm()

    # Resource sampler
    sampler = ResourceSampler(interval=1.0)
    sampler.start()
    try:
        report = asyncio.run(run_bench(args.total, args.concurrency, args.warmup))
    finally:
        sampler.stop()
        sampler.join()

    print("\n=== THROUGHPUT REPORT ===")
    for k, v in report.items():
        print(f"{k}: {v}")

    rsum = sampler.summary()
    if rsum:
        print("\n=== RESOURCE SUMMARY ===")
        for k, v in rsum.items():
            print(f"{k}: {v}")
