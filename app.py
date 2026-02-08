import os
import time
import json
import random
import logging
from datetime import datetime
from flask import Flask, jsonify, request, render_template

START_TIME = time.time()

APP_NAME = os.getenv("APP_NAME", "lab-app")
APP_ENV = os.getenv("APP_ENV", "dev")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
GIT_SHA = os.getenv("GIT_SHA", "local")
FEATURE_FLAG_FUN = os.getenv("FEATURE_FLAG_FUN", "true").lower() == "true"

QUOTES = [
    "Ship small, learn fast.",
    "Less ceremony, more delivery.",
    "Observability is a feature.",
    "Make it work, make it right, make it fast.",
    "Simplicity scales."
]

def create_app():
    app = Flask(__name__)

    # Logging (simples e útil em k8s)
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(message)s",
    )
    logger = logging.getLogger(APP_NAME)

    def log_event(event: str, extra: dict | None = None):
        payload = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "app": APP_NAME,
            "env": APP_ENV,
            "version": APP_VERSION,
            "sha": GIT_SHA,
            "event": event,
            "remote_addr": request.headers.get("X-Forwarded-For", request.remote_addr),
            "path": request.path,
            "method": request.method,
        }
        if extra:
            payload.update(extra)
        logger.info(json.dumps(payload, ensure_ascii=False))

    @app.route("/")
    def home():
        uptime = int(time.time() - START_TIME)
        return render_template(
            "index.html",
            app_name=APP_NAME,
            app_env=APP_ENV,
            app_version=APP_VERSION,
            git_sha=GIT_SHA,
            uptime=uptime,
            fun_enabled=FEATURE_FLAG_FUN,
        )

    @app.route("/api/info")
    def api_info():
        log_event("api_info")
        return jsonify({
            "name": APP_NAME,
            "env": APP_ENV,
            "version": APP_VERSION,
            "git_sha": GIT_SHA,
            "server_time_utc": datetime.utcnow().isoformat() + "Z",
            "uptime_seconds": int(time.time() - START_TIME),
        })

    @app.route("/api/echo", methods=["POST"])
    def api_echo():
        data = request.get_json(silent=True) or {}
        log_event("api_echo", {"payload_size": len(json.dumps(data))})
        return jsonify({
            "received": data,
            "hint": "Try POSTing {\"message\": \"hello\"}",
        })

    @app.route("/api/random-quote")
    def api_quote():
        log_event("api_random_quote")
        if not FEATURE_FLAG_FUN:
            return jsonify({"error": "Feature disabled"}), 403
        return jsonify({"quote": random.choice(QUOTES)})

    # K8s liveness: app está de pé
    @app.route("/healthz")
    def healthz():
        return jsonify({"status": "ok"}), 200

    # K8s readiness: app pronta (ex: poderia checar DB; aqui é simples)
    @app.route("/readyz")
    def readyz():
        return jsonify({"status": "ready"}), 200

    # Métricas simples (prometheus-like)
    @app.route("/metrics")
    def metrics():
        # Exemplo minimalista
        uptime = int(time.time() - START_TIME)
        return (
            "lab_app_uptime_seconds {}\n"
            "lab_app_build_info{{version=\"{}\",sha=\"{}\",env=\"{}\"}} 1\n"
        ).format(uptime, APP_VERSION, GIT_SHA, APP_ENV), 200, {"Content-Type": "text/plain"}

    @app.errorhandler(404)
    def not_found(_):
        log_event("not_found")
        return jsonify({"error": "not_found"}), 404

    @app.after_request
    def after(resp):
        # Loga apenas endpoints API (para não poluir com assets)
        if request.path.startswith("/api") or request.path in ["/healthz", "/readyz"]:
            log_event("request_done", {"status": resp.status_code})
        return resp

    return app

app = create_app()

if __name__ == "__main__":
    # dev only
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")), debug=True)
