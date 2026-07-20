# Rotondo Farms — RPi Zero 2W Sensor Node

This runs on the Raspberry Pi Zero 2W as the sensor/relay edge node. It reads moisture levels from 4 capacitive sensors via ADS1115 over I2C and controls 4 relay channels for automated watering.

## Hardware

| Component | Connection |
|-----------|-----------|
| ADS1115 ADC | I2C (SDA=GPIO2, SCL=GPIO3) |
| Chamomile moisture sensor | ADS1115 A0 |
| Borage moisture sensor | ADS1115 A1 |
| Lavender moisture sensor | ADS1115 A2 |
| Peppermint moisture sensor | ADS1115 A3 |
| Relay 1 (Chamomile) | GPIO 17 |
| Relay 2 (Borage) | GPIO 27 |
| Relay 3 (Lavender) | GPIO 22 |
| Relay 4 (Peppermint) | GPIO 23 |
| Float sensor (reservoir) | GPIO 24 |

## Plant Thresholds

| Plant | Dry | Wet |
|-------|-----|-----|
| Chamomile | 400 | 550 |
| Borage | 400 | 550 |
| English Lavender | 380 | 550 |
| Peppermint | 400 | 550 |

## Setup

```bash
pip install -r requirements.txt
```

## Run Flask API (for Orange Pi 5 integration)

```bash
python app.py
```

Exposes endpoints:
- `GET /sensors` — all moisture readings + float sensor
- `POST /relay/<plant>` — control relay (`{"state": "on"}` or `{"state": "off"}`)
- `GET /relays` — current relay states
- `POST /relay/all/off` — emergency stop
- `GET /health` — health check

## Run Autonomous Controller (standalone mode)

```bash
python controller.py
```

Runs independently without the Orange Pi — reads sensors every 30 seconds and waters automatically based on thresholds.
