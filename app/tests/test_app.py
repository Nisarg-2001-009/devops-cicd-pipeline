# app/tests/test_app.py
# Unit tests for the Flask REST API defined in app/app.py.
#
# Each test function is intentionally narrow: it tests one behaviour of one
# route. This makes failures self-documenting (the test name tells you exactly
# what broke) and makes tests cheap to maintain as the codebase evolves.
#
# The `client` parameter in every test is injected by pytest from the fixture
# defined in conftest.py — no manual setup is required here.

import os


# ---------------------------------------------------------------------------
# Tests for GET /
# ---------------------------------------------------------------------------

def test_index_returns_200(client):
    # Confirm the root endpoint is reachable and does not return an error
    # status. A 200 is the minimal requirement for a load-balancer health check
    # that targets the root path.
    response = client.get("/")
    assert response.status_code == 200


def test_index_contains_welcome_message(client):
    # Confirm the response body carries a "message" key so callers can display
    # a human-readable greeting. We check key presence and that the value is
    # a non-empty string rather than asserting an exact string, which would
    # make the test brittle to minor wording changes.
    data = response = client.get("/").get_json()
    assert "message" in data
    assert isinstance(data["message"], str)
    assert len(data["message"]) > 0


# ---------------------------------------------------------------------------
# Tests for GET /health
# ---------------------------------------------------------------------------

def test_health_returns_200(client):
    # The health endpoint must always return 200 when the app is running.
    # Orchestrators (Kubernetes, ECS) use this status code — not the body —
    # to decide whether to route traffic to this instance.
    response = client.get("/health")
    assert response.status_code == 200


def test_health_status_is_healthy(client):
    # Confirm the body reports status "healthy". Monitoring tools often parse
    # this field to distinguish an app that is "up but degraded" from one that
    # is fully operational. Testing the exact string prevents a typo
    # ("healhty", "ok") from silently breaking downstream consumers.
    data = client.get("/health").get_json()
    assert data["status"] == "healthy"


def test_health_contains_timestamp(client):
    # A timestamp in the response lets operators verify the process is actively
    # responding (not just TCP-open) and helps correlate health-check logs with
    # application logs during incident investigations.
    data = client.get("/health").get_json()
    assert "timestamp" in data
    assert isinstance(data["timestamp"], str)
    assert len(data["timestamp"]) > 0


# ---------------------------------------------------------------------------
# Tests for GET /api/info
# ---------------------------------------------------------------------------

def test_info_returns_200(client):
    # Basic reachability check for the info endpoint.
    response = client.get("/api/info")
    assert response.status_code == 200


def test_info_app_name(client):
    # Verify the app_name field matches the canonical project identifier.
    # In a microservices fleet, this field is how log aggregators and tracing
    # systems know which service emitted a record.
    data = client.get("/api/info").get_json()
    assert data["app_name"] == "devops-cicd-pipeline"


def test_info_version(client):
    # Pin the version to "1.0.0" so that any unintentional version bump
    # (e.g. an accidental edit to the route handler) is caught immediately
    # rather than silently rolling out the wrong version string to consumers.
    data = client.get("/api/info").get_json()
    assert data["version"] == "1.0.0"


def test_info_default_environment(client):
    # When APP_ENV is not set, the endpoint should fall back to "development".
    # We remove the variable from the environment (if present) to guarantee
    # the test exercises the default-value code path rather than whatever
    # happens to be in the CI runner's environment.
    os.environ.pop("APP_ENV", None)
    data = client.get("/api/info").get_json()
    assert data["environment"] == "development"


def test_info_reads_app_env_variable(client, monkeypatch):
    # Verify that the endpoint reflects a custom APP_ENV value.
    # monkeypatch is a built-in pytest fixture that sets/restores environment
    # variables safely: it automatically undoes the change after the test,
    # so later tests are not affected by the value we inject here.
    monkeypatch.setenv("APP_ENV", "production")
    data = client.get("/api/info").get_json()
    assert data["environment"] == "production"
