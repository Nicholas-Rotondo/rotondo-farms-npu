# Rotondo Farms NPU — Arm AI Optimization Challenge

An edge AI plant health monitoring system running on the Orange Pi 5 (Rockchip RK3588S), demonstrating LLM inference optimization from CPU to NPU.

## Project Overview

Rotondo Farms is an autonomous plant monitoring system that uses capacitive moisture sensors and relay modules to track and manage plant health. This submission extends the project by running a quantized LLM (Qwen3-0.6B) on the RK3588S NPU to generate natural language plant health narrations from live sensor data.

## Benchmark Results

| Mode | Prompt Processing | Token Generation |
|------|------------------|-----------------|
| CPU (llama.cpp, Q4_K_M) | 91.5 t/s | 34.3 t/s |
| NPU (RKLLama/RKLLM, W8A8) | ~354 t/s | ~29 t/s |

**3.9x faster prompt processing on NPU vs CPU.**

Token generation speed is comparable between CPU and NPU (~34 vs ~29 t/s). This is expected — the CPU runs Q4_K_M (4-bit) quantization which is highly optimized for fast generation, while the NPU runs W8A8 (8-bit) quantization which uses more precision per weight. The NPU's dramatic advantage shows in prompt processing (3.9x), where its 6 TOPS parallel compute architecture processes the input context far faster than the CPU cores can.

## Hardware

- Orange Pi 5 4GB (Rockchip RK3588S, 6 TOPS NPU)
- Raspberry Pi Zero 2W (sensor edge node)
- Capacitive moisture sensors x4
- ADS1115 ADC (I2C)
- 4-channel relay module
- Float sensor (reservoir safety)
- 12V LiFePO4 battery + Renogy solar charge controller

## Stack

- OS: Armbian Ubuntu 26.04, vendor kernel 6.1.115
- NPU Driver: RKNPU v0.9.8
- LLM Runtime: RKLLama v0.0.75 + RKLLM v1.3.0
- CPU Baseline: llama.cpp
- Model: Qwen3-0.6B (W8A8 quantization for NPU, Q4_K_M for CPU)

## Architecture

The Zero 2W runs as a sensor edge node, reading moisture levels and controlling relays via a Flask REST API. The Orange Pi 5 polls the Zero 2W for sensor data, feeds it into the Qwen3-0.6B model running on the NPU, and generates natural language plant health narrations.

## Setup

Coming soon.

## License

MIT
