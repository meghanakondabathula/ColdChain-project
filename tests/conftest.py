
import importlib
import sys
import os
import pytest


# ------------------------------------------
# 1. TEST ENVIRONMENT
# ------------------------------------------

@pytest.fixture(scope="session")
def test_environment(tmp_path_factory):
    import auth
    import deviation_manager

    test_dir = tmp_path_factory.mktemp("coldchain_tests")

    # Redirect writable databases to temporary files
    auth.AUTH_DB = test_dir / "test_auth.sqlite"
    deviation_manager.DB_PATH = test_dir / "test_deviations.sqlite"

    # Set a test-only secret key before importing app.py
    os.environ["FLASK_SECRET_KEY"] = (
        "test-only-secret-key-not-for-production"
    )

    # app.py initializes databases when imported
    if "app" in sys.modules:
        raise RuntimeError(
            "Import app only through the test_environment fixture"
        )

    application_module = importlib.import_module("app")

    application_module.app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=True
    )

    # Create temporary test users
    for username, role in [
        ("testadmin", "ADMIN"),
        ("testmanager", "QUALITY_MANAGER"),
        ("testanalyst", "QUALITY_ANALYST"),
        ("testviewer", "VIEWER")
    ]:
        auth.create_user(
            username,
            "TestingPassword123!",
            role
        )

    yield application_module


# ------------------------------------------
# 2. FLASK TEST CLIENT
# ------------------------------------------

@pytest.fixture
def client(test_environment):
    with test_environment.app.test_client() as test_client:
        yield test_client


# ------------------------------------------
# 3. TEST LOGIN HELPER
# ------------------------------------------

@pytest.fixture
def login_as(client):
    import auth

    def login(username):
        user = auth.authenticate(
            username,
            "TestingPassword123!"
        )

        if user is None:
            raise ValueError(
                f"Test user not found: {username}"
            )

        with client.session_transaction() as session:
            session["_user_id"] = str(user.id)
            session["_fresh"] = True

    return login


# ------------------------------------------
# 4. VALID CSRF TOKEN HELPER
# ------------------------------------------

@pytest.fixture
def csrf_headers(client, test_environment):
    from flask_wtf.csrf import generate_csrf
    from flask import session

    # Generate a valid CSRF token in a request context
    with test_environment.app.test_request_context():
        token = generate_csrf()
        raw_token = session["csrf_token"]

    # Store the matching token value in the client session
    with client.session_transaction() as test_session:
        test_session["csrf_token"] = raw_token

    # Return the header required for POST requests
    return {
        "X-CSRFToken": token
    }
