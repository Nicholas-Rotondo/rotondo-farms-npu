# Rotondo Farms NPU — Arm AI Optimization Challenge

An edge AI plant health monitoring system running on the Orange Pi 5 (Rockchip RK3588S), demonstrating LLM 
inference optimization from CPU to NPU.

## Project Overview

Rotondo Farms is an autonomous plant monitoring system that uses capacitive moisture sensors and relay 
modules to track and manage plant health. This submission extends the project by running a quantized LLM 
(Qwen3-0.6B) on the RK3588S NPU to generate natural language plant health narrations from live sensor data.

## Benchmark Results

| Mode | Prompt Processing | Token Generation |
|------|------------------|-----------------|
| CPU (llama.cpp) | 91.5 t/s | 34.3 t/s |
| NPU (RKLLama/RKLLM) | ~354 t/s | ~29 t/s |

**3.9x faster prompt processing on NPU vs CPU.**

## Hardware

- Orange Pi 5 4GB (Rockchip RK3588S, 6 TOPS NPU)
- Capacitive moisture sensors
- ADS1115 ADC (I2C)
- Relay module
- Raspberry Pi Zero 2W (sensor edge node)

## Stack

- OS: Armbian Ubuntu 26.04, vendor kernel 6.1.115
- NPU Driver: RKNPU v0.9.8
- LLM Runtime: RKLLama v0.0.75 + RKLLM v1.3.0
- CPU Baseline: llama.cpp
- Model: Qwen3-0.6B (W8A8 quantization for NPU)

## Setup

Coming soon.

## License

MIT
