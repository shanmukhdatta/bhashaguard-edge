import argparse
import json
import statistics
import time
from pathlib import Path

from .core import Guard, DEFAULT_PACK


def main():
    parser = argparse.ArgumentParser(description="BhashaGuard Edge local CPU prototype")
    parser.add_argument("--pack", default=str(DEFAULT_PACK))
    parser.add_argument("--embedding-model", help="Optional local multilingual-e5-small model directory")
    sub = parser.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--llm-endpoint", help="Loopback /v1/chat/completions URL")
    serve.add_argument("--llm-model", default="local-model")
    analyze = sub.add_parser("analyze")
    analyze.add_argument("--text-file", required=True)
    analyze.add_argument("--language", choices=["te", "ta", "kn"], default="te")
    analyze.add_argument("--locale", default="fictional:vennela")
    analyze.add_argument("--allow-latin", action="store_true")
    analyze.add_argument("--output")
    bench = sub.add_parser("benchmark")
    bench.add_argument("--runs", type=int, default=30)
    bench.add_argument("--output")
    args = parser.parse_args()
    embedder = None
    if args.embedding_model:
        from .models import E5Retriever
        embedder = E5Retriever(args.embedding_model)
    guard = Guard(args.pack, embedder)
    if args.command == "serve":
        from .server import make_server
        server = make_server(guard, args.port, args.llm_endpoint, args.llm_model)
        print(f"BhashaGuard Edge: http://127.0.0.1:{server.server_port} (CPU)", flush=True)
        print(f"Evidence: {guard.pack['kind']}. Press Ctrl+C to stop.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
        return
    if args.command == "analyze":
        result = guard.analyze(Path(args.text_file).read_text(encoding="utf-8"), args.language,
                               args.locale, allow_latin=args.allow_latin)
    else:
        if not 1 <= args.runs <= 10000:
            parser.error("runs must be between 1 and 10000")
        cases = json.loads((Path(__file__).parent / "data" / "demo_cases.json").read_text(encoding='utf-8'))
        for _ in range(5):
            guard.analyze(cases[0]["text"])
        elapsed = []
        for _ in range(args.runs):
            for case in cases:
                start = time.perf_counter()
                report = guard.analyze(case["text"], case["language"], case["locale"])
                elapsed.append((time.perf_counter()-start)*1000)
        result = {"kind": "measured_local_synthetic_fixture_latency", "backend": "CPU",
                  "npu_used": False, "runs_per_case": args.runs, "samples": len(elapsed),
                  "median_ms": statistics.median(elapsed),
                  "p95_ms": sorted(elapsed)[max(0, __import__('math').ceil(.95*len(elapsed))-1)],
                  "runtime": report["runtime"], "pack": report["pack"],
                  "scope": "Warm whole-analysis latency on bundled synthetic cases. Excludes process/model load. Not an accuracy evaluation or Snapdragon benchmark."}
    encoded = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    else:
        print(encoded)


if __name__ == "__main__":
    main()
