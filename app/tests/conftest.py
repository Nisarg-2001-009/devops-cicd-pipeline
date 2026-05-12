# app/tests/conftest.py
# pytest automatically discovers and loads this file before running any tests
# in the same directory (or sub-directories). Its purpose is to define shared
# fixtures — reusable pieces of setup/teardown logic — so that individual test
# modules stay focused on assertions rather than boilerplate.

import pytest

# Import the application factory from the sibling app module.
# Using the factory (create_app) rather than importing a pre-built app object
# ensures every test session gets a fresh, independently configured instance,
# preventing state from leaking between tests or test runs.
from app.app import create_app


# ---------------------------------------------------------------------------
# Fixture: client
# ---------------------------------------------------------------------------
# @pytest.fixture makes this function available as an injectable parameter to
# any test function that declares `client` in its signature. pytest handles
# the lifecycle: it calls this function before the test, passes the yielded
# value in, then resumes after `yield` for teardown.
#
# scope="function" (the default) means a new client is created for every
# single test. This is the safest scope because it prevents one test's
# side-effects from influencing another — important if future routes mutate
# state (sessions, caches, DB records).

@pytest.fixture
def client():
    # TESTING = True tells Flask to propagate exceptions instead of returning
    # 500 responses, which makes test failures far easier to diagnose — you
    # see the real traceback rather than a generic error page.
    app = create_app()
    app.config["TESTING"] = True

    # Flask's test client mimics a real HTTP client without spinning up a
    # network socket, so tests run quickly and work in any CI environment
    # without port conflicts or firewall rules.
    with app.test_client() as client:
        yield client
    # No explicit teardown is needed here; Flask cleans up the app context
    # automatically when the `with` block exits.
