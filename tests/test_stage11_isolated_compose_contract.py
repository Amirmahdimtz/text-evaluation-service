"""Static offline guard for the opt-in isolated PostgreSQL Compose manifest."""
from pathlib import Path

import yaml


def test_stage11_database_compose_stays_scoped_and_opt_in():
    path = Path(__file__).resolve().parents[1] / "compose.stage11-isolated-db.yml"
    manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert manifest["name"] == "tes-stage11-isolated"
    assert set(manifest["services"]) == {"postgres"}
    pg = manifest["services"]["postgres"]
    assert pg["profiles"] == ["isolated"]
    assert pg["restart"] == "no"
    assert pg["image"] == "postgres:17"
    assert pg["ports"] == [
        "127.0.0.1:${TES_STAGE11_DB_PORT:?choose an unoccupied loopback port}:5432"
    ]
    env = pg["environment"]
    assert env["POSTGRES_USER"].startswith("${TES_STAGE11_DB_USER:?")
    assert env["POSTGRES_PASSWORD"].startswith("${TES_STAGE11_DB_PASSWORD:?")
    assert env["POSTGRES_DB"].startswith("${TES_STAGE11_DB_NAME:?")
    assert "scram-sha-256" in env["POSTGRES_INITDB_ARGS"]
    assert pg["networks"] == ["isolated"]
    assert manifest["networks"]["isolated"]["driver"] == "bridge"
    assert manifest["networks"]["isolated"]["internal"] is False
    assert set(manifest["volumes"]) == {"stage11_postgres_data"}
    assert all("external" not in values for values in manifest["networks"].values())
    assert not any("privileged" in service for service in manifest["services"].values())
