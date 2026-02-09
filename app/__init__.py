import logging
from flask import Flask
from app.config import Config


def create_app():
    Config.validate()

    app = Flask(__name__)
    app.config.from_object(Config)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    from app.webhook import webhook_bp

    app.register_blueprint(webhook_bp)

    return app
