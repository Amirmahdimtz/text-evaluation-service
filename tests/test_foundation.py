"""Stage 04 local unit, security, and application smoke coverage."""

import io
import json
import logging

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.infrastructure.di.bootstrap import bootstrap_di, reset_bootstrap_for_tests
from src.infrastructure.di.inject import DependencyError, inject, register, resolve
from src.infrastructure.security.policy import Identity, ResourceScope, is_allowed, validate_internal_endpoint
from src.infrastructure.security.safe_logging import SafeFormatter, configure_logging
from src.infrastructure.security.secrets import SecretResolver
from src.infrastructure.utils.config_reader import ConfigReader, Settings


def test_config_synthetic_and_unknown_key(monkeypatch):
    monkeypatch.setenv("TES_ENVIRONMENT", "development")
    settings = ConfigReader()
    assert settings.get_api_prefix() == "/api/v1"
    assert settings.get("security.deny_external_egress") is True
    with pytest.raises(KeyError, match="CONFIG_KEY_UNKNOWN"):
        settings.get("database.password")


@pytest.mark.parametrize("env", ["production", "staging"])
def test_safe_environment_settings(monkeypatch, env):
    monkeypatch.setenv("TES_ENVIRONMENT", env)
    assert ConfigReader().environment == env


def test_invalid_config(monkeypatch):
    monkeypatch.setenv("TES_ENVIRONMENT", "unknown")
    with pytest.raises(ValueError, match="CONFIG_INVALID_ENVIRONMENT"):
        ConfigReader()
    bad = {"app": {"name": "svc", "version": "0"}, "server": {"host": "0.0.0.0", "port": 80}, "api": {"prefix": "/api/v1"}, "security": {"deny_external_egress": True}}
    with pytest.raises(ValueError):
        Settings.model_validate(bad)
    bad["server"]["host"] = "127.0.0.1"
    bad["security"]["deny_external_egress"] = False
    with pytest.raises(ValueError):
        Settings.model_validate(bad)
    bad["security"]["deny_external_egress"] = True
    bad["database"] = {"password": "not allowed"}
    with pytest.raises(ValueError):
        Settings.model_validate(bad)


def test_secret_ref(monkeypatch):
    monkeypatch.setenv("SYNTHETIC_STAGE04_TEST", "fake-test-only")
    assert SecretResolver().resolve_reference("env://SYNTHETIC_STAGE04_TEST") == "fake-test-only"
    with pytest.raises(ValueError, match="SECRET_REFERENCE_INVALID"):
        SecretResolver().resolve_reference("https://example.com/secret")
    with pytest.raises(ValueError, match="SECRET_UNAVAILABLE"):
        SecretResolver().resolve_reference("env://STAGE04_MISSING_TEST")


def test_di_bootstrap_singleton_and_discovery():
    reset_bootstrap_for_tests()
    with pytest.raises(DependencyError, match="DI_NOT_BOOTSTRAPPED"):
        resolve(ConfigReader)
    bootstrap_di()
    bootstrap_di()
    assert resolve(ConfigReader) is resolve(ConfigReader)
    assert isinstance(resolve(SecretResolver), SecretResolver)
    from src.application.web import WebService
    assert isinstance(resolve(WebService), WebService)


def test_inject_respects_explicit_argument_and_defaults():
    reset_bootstrap_for_tests()

    @inject
    class Dependency:
        pass

    @inject
    class Consumer:
        def __init__(self, dependency: Dependency, optional: str = "safe"):
            self.dependency = dependency
            self.optional = optional

    register(Dependency)
    register(Consumer)
    from src.infrastructure.di.inject import mark_ready
    mark_ready()
    instance = resolve(Consumer)
    assert isinstance(instance.dependency, Dependency)
    assert instance.optional == "safe"
    supplied = Dependency()
    assert Consumer(supplied, "given").dependency is supplied
    reset_bootstrap_for_tests()


def test_auth_default_deny_and_scope():
    owner = Identity("u1", "org1", frozenset({"evaluation:read", "evaluation:submit"}), True)
    outsider = Identity("u2", "org2", frozenset({"evaluation:read"}), True)
    reviewer = Identity("u3", "org1", frozenset({"evaluation:read", "feedback:create"}), True, frozenset({"r1"}))
    resource = ResourceScope("r1", "u1", "org1")
    assert is_allowed(owner, "evaluation:read", resource)
    assert is_allowed(owner, "evaluation:submit")
    assert not is_allowed(None, "evaluation:read", resource)
    assert not is_allowed(outsider, "evaluation:read", resource)
    assert not is_allowed(owner, "evaluation:read", ResourceScope("r2", "u2", "org1"))
    assert is_allowed(reviewer, "feedback:create", resource)
    assert not is_allowed(owner, "feedback:create", resource)
    assert not is_allowed(reviewer, "feedback:create", ResourceScope("r2", "u1", "org1"))
    assert not is_allowed(owner, "unrecognized:admin")
    assert not is_allowed(Identity("u1", "org1", frozenset({"evaluation:submit"})), "evaluation:submit")


@pytest.mark.parametrize("url,env", [
    ("https://example.com:443", "production"),
    ("http://10.0.0.1:8000", "production"),
    ("https://8.8.8.8:443", "production"),
    ("https://127.0.0.1:443", "production"),
    ("https://10.1.2.3:443/?text=private", "production"),
    ("https://user:pass@10.1.2.3:443", "production"),
    ("https://10.0.0.1:443", "invalid"),
    ("ftp://10.0.0.1:21", "production"),
])
def test_external_endpoints_blocked(url, env):
    with pytest.raises(ValueError, match="ENDPOINT_NOT_ALLOWED"):
        validate_internal_endpoint(url, environment=env)


def test_private_endpoints_allowed():
    assert validate_internal_endpoint("https://10.20.30.40:443", environment="production")
    assert validate_internal_endpoint("http://127.0.0.1:8001", environment="development")


def test_logs_never_render_message_or_exception():
    secret = "synthetic-secret-marker"
    logger = configure_logging()
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(SafeFormatter())
    logger.addHandler(handler)
    try:
        try:
            raise RuntimeError(secret)
        except RuntimeError:
            logger.exception("submitted text: %s", secret)
        output = stream.getvalue()
        assert secret not in output
        assert "submitted text" not in output
        assert json.loads(output)["event_code"] == "UNCLASSIFIED_EVENT"
    finally:
        logger.removeHandler(handler)


def test_import_startup_shutdown_routes_and_error_sanitization():
    reset_bootstrap_for_tests()
    from src.host.app import create_app
    app = create_app()

    @app.get("/synthetic-error")
    async def error():
        raise RuntimeError("synthetic-secret-marker")

    @app.get("/synthetic-http-error")
    async def http_error():
        raise HTTPException(status_code=403, detail="synthetic-secret-marker")

    @app.get("/synthetic-validation/{value}")
    async def validation(value: int):
        return {"value": value}

    with TestClient(app, raise_server_exceptions=False) as client:
        assert client.get("/health/live").json() == {"status": "alive"}
        ready = client.get("/health/ready")
        assert ready.status_code == 200
        assert ready.json() == {"status": "ready"}
        assert client.get("/api/v1/evaluations").status_code == 404
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404
        for path, status in (("/synthetic-error", 500), ("/synthetic-http-error", 403), ("/synthetic-validation/not-number", 422)):
            response = client.get(path)
            assert response.status_code == status
            assert "synthetic-secret-marker" not in response.text
            assert "X-Correlation-ID" in response.headers
            assert response.headers["Cache-Control"] == "no-store"
            assert "correlation_id" in response.json()
    assert app.state.ready is False


def test_invalid_or_missing_yaml_is_redacted(monkeypatch, tmp_path):
    import src.infrastructure.utils.config_reader as settings_module
    monkeypatch.setenv("TES_ENVIRONMENT", "development")
    monkeypatch.setattr(settings_module, "_CONFIG_DIR", tmp_path)
    with pytest.raises(ValueError, match="^CONFIG_INVALID$"):
        ConfigReader()
    (tmp_path / "appsettings.development.yaml").write_text("!!python/object/apply:os.system ['true']", encoding="utf-8")
    with pytest.raises(ValueError, match="^CONFIG_INVALID$"):
        ConfigReader()
    (tmp_path / "appsettings.development.yaml").write_text("security: {deny_external_egress: false}\nsecret: synthetic-secret-marker", encoding="utf-8")
    with pytest.raises(ValueError, match="^CONFIG_INVALID$") as error:
        ConfigReader()
    assert "synthetic-secret-marker" not in str(error.value)


def test_cycle_and_missing_providers_are_sanitized():
    from src.infrastructure.di.inject import mark_ready
    reset_bootstrap_for_tests()

    @inject
    class Cycle:
        def __init__(self, dependency: "Cycle"):
            self.dependency = dependency

    register(Cycle)
    mark_ready()
    with pytest.raises(DependencyError, match="DI_CIRCULAR_DEPENDENCY"):
        resolve(Cycle)
    with pytest.raises(DependencyError, match="DI_UNKNOWN_PROVIDER"):
        resolve(ConfigReader)
    reset_bootstrap_for_tests()


def test_app_does_not_initialize_external_resources(monkeypatch):
    import socket
    from src.host.app import create_app
    def forbid_connection(*args, **kwargs):
        raise AssertionError("unapproved network access")
    monkeypatch.setattr(socket, "create_connection", forbid_connection)
    reset_bootstrap_for_tests()
    app = create_app()
    assert app.state.ready is False
    assert len([r for r in app.routes if "/api/v1/" in r.path]) == 0


def test_controller_auto_discovery_with_synthetic_fixture(monkeypatch, tmp_path):
    from types import SimpleNamespace
    from fastapi import APIRouter
    import src.application.web as web_module
    from src.application.web import WebService

    root = tmp_path / "application"
    feature = root / "fixture"
    feature.mkdir(parents=True)
    (feature / "fixture_controller.py").write_text("# synthetic fixture\n", encoding="utf-8")
    monkeypatch.setattr(web_module, "__file__", str(root / "web.py"))

    @inject
    class FixtureController:
        def __init__(self, config: ConfigReader):
            self._config = config

        def api(self):
            router = APIRouter()

            @router.get("/probe")
            def probe():
                return {"prefix": self._config.get_api_prefix()}

            return router

    reset_bootstrap_for_tests()
    bootstrap_di()
    monkeypatch.setattr(web_module, "import_module", lambda _: SimpleNamespace(FixtureController=FixtureController))
    routes = resolve(WebService).api()
    assert any(route.path == "/api/v1/fixture/probe" for route in routes.routes)


def test_controller_discovery_fails_closed(monkeypatch, tmp_path):
    import src.application.web as web_module
    from src.application.web import WebService
    root = tmp_path / "application"
    feature = root / "fixture"
    feature.mkdir(parents=True)
    (feature / "fixture_controller.py").write_text("# invalid synthetic fixture\n", encoding="utf-8")
    monkeypatch.setattr(web_module, "__file__", str(root / "web.py"))
    def missing_module(name):
        raise ModuleNotFoundError("synthetic-secret-marker")
    monkeypatch.setattr(web_module, "import_module", missing_module)
    reset_bootstrap_for_tests()
    bootstrap_di()
    with pytest.raises(DependencyError, match="^CONTROLLER_DISCOVERY_FAILED$") as exc:
        resolve(WebService).api()
    assert "synthetic-secret-marker" not in str(exc.value)


def test_application_import_fails_safely_when_environment_invalid(monkeypatch):
    from src.host.app import create_app
    reset_bootstrap_for_tests()
    monkeypatch.setenv("TES_ENVIRONMENT", "unrecognized")
    with pytest.raises(ValueError, match="^CONFIG_INVALID_ENVIRONMENT$"):
        create_app()
    reset_bootstrap_for_tests()


def test_di_singleton_is_thread_safe():
    from concurrent.futures import ThreadPoolExecutor
    reset_bootstrap_for_tests()
    bootstrap_di()
    with ThreadPoolExecutor(max_workers=12) as executor:
        services = list(executor.map(lambda _: resolve(ConfigReader), range(64)))
    assert all(service is services[0] for service in services)
