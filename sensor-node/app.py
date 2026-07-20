# app.py — Rotondo Farms Flask API (runs on RPi Zero 2W)
# Exposes sensor readings and relay control to the Orange Pi 5

from flask import Flask, jsonify, request
import RPi.GPIO as GPIO
from sensors import read_all_moisture, read_float_sensor
from relays import relay_on, relay_off, relay_off_all, get_relay_states
from config import API_PORT

app = Flask(__name__)


@app.route("/sensors", methods=["GET"])
def get_sensors():
    """Return all moisture sensor readings and float sensor status."""
    try:
        moisture = read_all_moisture()
        float_ok = read_float_sensor()
        return jsonify({
            "moisture": moisture,
            "reservoir": {
                "float_ok": float_ok,
                "status": "ok" if float_ok else "low — refill needed"
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/relay/<plant>", methods=["POST"])
def control_relay(plant):
    """Turn a plant's relay on or off.
    Body: { "state": "on" } or { "state": "off" }
    """
    # Safety check — don't water if reservoir is low
    if not read_float_sensor():
        relay_off_all()
        return jsonify({
            "error": "Reservoir low — all relays disabled for safety"
        }), 400

    data = request.get_json()
    if not data or "state" not in data:
        return jsonify({"error": "Missing 'state' in request body"}), 400

    state = data["state"].lower()
    if state == "on":
        success = relay_on(plant)
    elif state == "off":
        success = relay_off(plant)
    else:
        return jsonify({"error": "state must be 'on' or 'off'"}), 400

    if not success:
        return jsonify({"error": f"Unknown plant: {plant}"}), 404

    return jsonify({
        "plant": plant,
        "relay": state,
        "status": "ok"
    })


@app.route("/relay/all/off", methods=["POST"])
def all_off():
    """Emergency stop — turn off all relays."""
    relay_off_all()
    return jsonify({"status": "all relays off"})


@app.route("/relays", methods=["GET"])
def relay_states():
    """Return current state of all relays."""
    return jsonify(get_relay_states())


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "device": "RPi Zero 2W"})


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=API_PORT, debug=False)
    finally:
        GPIO.cleanup()
