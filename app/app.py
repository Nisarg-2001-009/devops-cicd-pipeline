# app/app.py
# Entry point for the Flask REST API. This file defines the application
# factory, registers all routes, and runs the development server when
# executed directly. Keeping all route logic in one file is intentional
# at this stage; as the project grows, blueprints can split concerns.

import os
from datetime import datetime, timezone

from flask import Flask, jsonify

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
# create_app() is the standard Flask pattern for constructing the app object.
# It makes the app easier to test (each test can spin up a fresh instance)
# and easier to configure (settings can be injected at construction time).

def create_app():
    app = Flask(__name__)

    # -----------------------------------------------------------------------
    # Route: GET /
    # -----------------------------------------------------------------------
    # The root endpoint is a lightweight "is the server alive?" check.
    # It returns a plain welcome message so that anyone who hits the base URL
    # receives a human-readable confirmation that the API is running.

    @app.route("/", methods=["GET"])
    def index():
        return jsonify({"message": "Welcome to the devops-cicd-pipeline API - v1.0.0"}), 200

    # -----------------------------------------------------------------------
    # Route: GET /health
    # -----------------------------------------------------------------------
    # Health endpoints are polled by load balancers, container orchestrators
    # (Kubernetes liveness/readiness probes), and monitoring tools to decide
    # whether the instance is fit to serve traffic.
    #
    # Returning a UTC ISO-8601 timestamp lets operators confirm the process
    # is actively responding (not just TCP-open) and makes log correlation
    # easier when debugging incident timelines.

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }), 200

    # -----------------------------------------------------------------------
    # Route: GET /api/info
    # -----------------------------------------------------------------------
    # The info endpoint exposes metadata about the running service.
    # This is useful in multi-service environments where you need to confirm
    # which version of the app is deployed in a given environment without
    # SSH-ing into the host.
    #
    # APP_ENV is read from the process environment so that the same Docker
    # image can behave differently in dev / staging / production purely by
    # changing an environment variable — no code change required.
    # The default of "development" means local runs work out-of-the-box
    # without any extra setup.

    @app.route("/api/info", methods=["GET"])
    def info():
        return jsonify({
            "app_name": "devops-cicd-pipeline",
            "version": "1.0.0",
            "environment": os.getenv("APP_ENV", "development"),
        }), 200

    return app


# ---------------------------------------------------------------------------
# Development server entry point
# ---------------------------------------------------------------------------
# This block only runs when the file is executed directly (`python app.py`).
# It is NOT executed when the app is imported by a WSGI server (gunicorn,
# uWSGI) or by the test suite — which is the correct behaviour in both cases.
#
# debug=True enables Flask's interactive debugger and auto-reloader so that
# code changes are picked up immediately during local development without
# restarting the server manually. Never set debug=True in production.

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
