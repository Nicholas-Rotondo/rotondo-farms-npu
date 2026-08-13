#!/usr/bin/env python3
"""
Rotondo Farms — Sensor -> NPU Narration Pipeline

Reads moisture data from capacitive sensors via ADS1115 (i2c-5, 0x48),
builds a prompt from the readings, and sends it to a local RKLLama server
(Qwen3-0.6B on the RK3588S NPU) for a natural-language plant health summary.

Hardware:
    ADS1115 on /dev/i2c-5, address 0x48
    A2 = Tomato, A3 = Pepper (A0/A1 still wired but pots currently empty)

Thresholds (raw ADC counts, 16-bit, +/-4.096V range):
    > 20,000        -> dry
    15,000-20,000   -> ok
    < 15,000        -> wet
"""

import time
import csv
import argparse
from datetime import datetime
from pathlib import Path

import requests
import smbus2

# ---- Config -----------------------------------------------------------

I2C_BUS = 5
ADS_ADDR = 0x48

# High byte of the ADS1115 config register per channel (single-ended,
# +/-4.096V PGA, single-shot mode). Low byte 0x83 = 128SPS, comparator
# disabled — standard default for single-shot reads.
CHANNEL_CONFIG_HIGH = [0xC3, 0xD3, 0xE3, 0xF3]
CONFIG_LOW = 0x83

CONFIG_REG = 0x01
CONVERSION_REG = 0x00

PLANTS = {2: "Tomato", 3: "Pepper"}  # A0/A1 still wired but pots are currently empty

DRY_THRESHOLD = 20000
WET_THRESHOLD = 15000

RKLLAMA_URL = "http://localhost:8080/api/chat"
LOAD_MODEL_URL = "http://localhost:8080/load_model"
MODEL_NAME = "qwen3-0.6b-npu"
NUM_PREDICT = 150  # max response tokens; Ollama-style APIs default to a short window otherwise

BENCHMARK_LOG = Path("npu_benchmark.csv")
BENCHMARK_FIELDS = [
    "timestamp", "model", "prompt_tokens", "response_tokens",
    "tokens_estimated", "elapsed_s", "tokens_per_sec",
]

# Fixed prompt for benchmark trials (--trials), so CPU vs NPU runs are apples-to-apples
# and not affected by real sensor drift between runs.
BENCHMARK_FIXED_READINGS = {
    "Tomato": {"raw": 21600, "status": "dry"},
    "Pepper": {"raw": 17650, "status": "ok"},
}

# ---- Sensor reading -----------------------------------------------------

def read_channel(bus: smbus2.SMBus, channel: int) -> int:
    """Trigger a single-shot conversion on the given channel and return the raw ADC value."""
    high = CHANNEL_CONFIG_HIGH[channel]
    bus.write_i2c_block_data(ADS_ADDR, CONFIG_REG, [high, CONFIG_LOW])
    time.sleep(0.1)  # conversion takes ~8ms at 128SPS; padded for safety
    data = bus.read_i2c_block_data(ADS_ADDR, CONVERSION_REG, 2)
    raw = (data[0] << 8) | data[1]
    if raw > 32767:  # two's complement negative (shouldn't happen for moisture, but be safe)
        raw -= 65536
    return raw


def classify(raw: int) -> str:
    if raw > DRY_THRESHOLD:
        return "dry"
    if raw < WET_THRESHOLD:
        return "wet"
    return "ok"


def read_all_sensors() -> dict:
    readings = {}
    with smbus2.SMBus(I2C_BUS) as bus:
        for channel, name in PLANTS.items():
            raw = read_channel(bus, channel)
            readings[name] = {"raw": raw, "status": classify(raw)}
    return readings


# ---- Prompt + NPU call -----------------------------------------------------

_model_load_checked = False  # module-level flag so we only load once per process, not every loop iteration


def ensure_model_loaded() -> None:
    """Explicitly tell RKLLama to load MODEL_NAME. Without this, /api/chat silently
    uses whatever model is already loaded in memory rather than switching to the
    one requested in the payload — this bit us once already."""
    global _model_load_checked
    if _model_load_checked:
        return
    response = requests.post(LOAD_MODEL_URL, json={"model_name": MODEL_NAME}, timeout=120)
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to load model '{MODEL_NAME}': {response.status_code} - {response.text}"
        )
    _model_load_checked = True


SYSTEM_PROMPT = (
    "You are a plant care assistant. You will be given live capacitive soil "
    "moisture readings from an indoor grow cabinet. Higher raw values mean drier "
    f"soil (dry > {DRY_THRESHOLD}, ok {WET_THRESHOLD}-{DRY_THRESHOLD}, wet < {WET_THRESHOLD}). "
    "Write a short, cohesive narration (3-5 sentences) summarizing the overall "
    "health of the cabinet, calling out any plant that needs attention."
)


def build_prompt(readings: dict) -> str:
    lines = [
        f"{name}: raw moisture reading {info['raw']} ({info['status']})"
        for name, info in readings.items()
    ]
    sensor_block = "\n".join(lines)
    return f"Sensor readings:\n{sensor_block}"


def get_narration(prompt: str, debug: bool = False) -> dict:
    """Call RKLLama's chat endpoint and return the narration plus benchmark data."""
    ensure_model_loaded()
    start = time.monotonic()
    response = requests.post(
        RKLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {"num_predict": NUM_PREDICT},
        },
        timeout=60,
    )
    elapsed = time.monotonic() - start
    response.raise_for_status()
    data = response.json()

    if debug:
        import json as _json
        print("=== RAW RESPONSE JSON ===")
        print(_json.dumps(data, indent=2))
        print()

    # Ollama-style /api/chat responses nest the reply under message.content.
    narration = data.get("message", {}).get("content") or data.get("response") or str(data)

    prompt_tokens = data.get("prompt_eval_count")
    response_tokens = data.get("eval_count")
    tokens_estimated = response_tokens is None
    if tokens_estimated:
        response_tokens = max(1, len(narration.split()))

    tokens_per_sec = response_tokens / elapsed if elapsed > 0 else 0.0

    return {
        "narration": narration,
        "elapsed_s": elapsed,
        "prompt_tokens": prompt_tokens,
        "response_tokens": response_tokens,
        "tokens_estimated": tokens_estimated,
        "tokens_per_sec": tokens_per_sec,
    }


def log_benchmark(result: dict, log_path: Path = BENCHMARK_LOG) -> None:
    """Append one benchmark row to a CSV log — Track 1 optimization evidence for the writeup."""
    is_new = not log_path.exists()
    with log_path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=BENCHMARK_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "model": MODEL_NAME,
            "prompt_tokens": result["prompt_tokens"],
            "response_tokens": result["response_tokens"],
            "tokens_estimated": result["tokens_estimated"],
            "elapsed_s": round(result["elapsed_s"], 3),
            "tokens_per_sec": round(result["tokens_per_sec"], 2),
        })


def run_benchmark_trials(n: int) -> None:
    """Run N trials with a fixed prompt (not live sensor data) so CPU vs NPU
    comparisons are apples-to-apples. Logs every trial and prints a summary average."""
    prompt = build_prompt(BENCHMARK_FIXED_READINGS)
    results = []

    print(f"=== Benchmark: {n} trials on model '{MODEL_NAME}' ===\n")
    for i in range(1, n + 1):
        result = get_narration(prompt)
        log_benchmark(result)
        results.append(result)
        est_flag = " (estimated)" if result["tokens_estimated"] else ""
        print(
            f"  trial {i}/{n}: {result['response_tokens']} tokens{est_flag} in "
            f"{result['elapsed_s']:.2f}s -> {result['tokens_per_sec']:.2f} tok/s"
        )

    speeds = [r["tokens_per_sec"] for r in results]
    avg = sum(speeds) / len(speeds)
    print(f"\n=== Summary: {MODEL_NAME} ===")
    print(f"  avg tok/s: {avg:.2f}")
    print(f"  min tok/s: {min(speeds):.2f}")
    print(f"  max tok/s: {max(speeds):.2f}")
    print(f"  logged to: {BENCHMARK_LOG}")


# ---- Main -----------------------------------------------------

def run_once(verbose: bool = True, log: bool = True, debug: bool = False) -> str:
    readings = read_all_sensors()
    prompt = build_prompt(readings)

    if verbose:
        print("=== Sensor Readings ===")
        for name, info in readings.items():
            print(f"  {name:<10} raw={info['raw']:<6} status={info['status']}")
        print()

    result = get_narration(prompt, debug=debug)

    if log:
        log_benchmark(result)

    if verbose:
        print("=== NPU Narration ===")
        print(result["narration"])
        est_flag = " (estimated)" if result["tokens_estimated"] else ""
        print(
            f"\n[benchmark] {result['response_tokens']} tokens{est_flag} in "
            f"{result['elapsed_s']:.2f}s -> {result['tokens_per_sec']:.2f} tok/s"
        )

    return result["narration"]


def main():
    global MODEL_NAME

    parser = argparse.ArgumentParser(description="Rotondo Farms sensor -> NPU narration pipeline")
    parser.add_argument("--loop", type=int, default=0, help="Repeat every N seconds (0 = run once)")
    parser.add_argument(
        "--no-log", action="store_true",
        help=f"Skip writing benchmark rows to {BENCHMARK_LOG}",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Print the raw RKLLama JSON response (for diagnosing early stopping / done_reason)",
    )
    parser.add_argument(
        "--model", type=str, default=None,
        help=f"Override the model name to use (default: {MODEL_NAME}). "
             "e.g. 'qwen3-0.6b' for the CPU/GGUF path, 'qwen3-0.6b-npu' for native NPU.",
    )
    parser.add_argument(
        "--trials", type=int, default=0,
        help="Run N benchmark trials with a fixed prompt instead of live sensor data "
             "(for CPU vs NPU comparison). Ignores --loop.",
    )
    args = parser.parse_args()

    if args.model:
        MODEL_NAME = args.model

    if args.trials > 0:
        run_benchmark_trials(args.trials)
        return

    if args.loop > 0:
        while True:
            run_once(log=not args.no_log, debug=args.debug)
            print(f"\n--- sleeping {args.loop}s ---\n")
            time.sleep(args.loop)
    else:
        run_once(log=not args.no_log, debug=args.debug)


if __name__ == "__main__":
    main()
