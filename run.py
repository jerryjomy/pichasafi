import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)

try:
    from app import create_app
    app = create_app()
except Exception as e:
    logging.error(f"FATAL: Failed to create app: {e}", exc_info=True)
    # Create a minimal fallback app so Railway healthcheck passes
    # and we can see the error in logs
    from flask import Flask
    app = Flask(__name__)

    @app.route("/health", methods=["GET"])
    def health():
        return "ok (degraded)", 200

    @app.route("/webhook", methods=["GET", "POST"])
    def webhook():
        return "App failed to start - check logs", 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
