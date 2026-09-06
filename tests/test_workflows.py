"""CI/CD properties worth holding still — chiefly that the deploy is secretless.

These read the workflow YAML rather than running it, so they are cheap and catch
the regressions that matter: a stored credential creeping back in, an unpinned
action, or a permission widened past what the job needs.
"""
from __future__ import annotations

import pathlib
import re

import pytest
import yaml

WORKFLOWS = pathlib.Path(__file__).resolve().parent.parent / ".github" / "workflows"
SHA_PINNED = re.compile(r"^[\w.-]+/[\w.-]+(?:/[\w.-]+)*@[0-9a-f]{40}$")

# Azure credentials the deploy must never read from `secrets`.
AZURE_CREDENTIAL_HINTS = ("AZURE_CLIENT_ID", "AZURE_TENANT_ID", "AZURE_SUBSCRIPTION_ID",
                          "AZURE_CREDENTIALS", "AZURE_STATIC_WEB_APPS_API_TOKEN")


def load(name: str) -> dict:
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


def steps_of(workflow: dict):
    for job in workflow["jobs"].values():
        for step in job.get("steps", []):
            yield job, step


@pytest.fixture(scope="module")
def swa() -> dict:
    return load("azure-swa.yml")


def test_every_workflow_parses():
    files = sorted(WORKFLOWS.glob("*.yml"))
    assert files, "expected workflows"
    for path in files:
        assert yaml.safe_load(path.read_text(encoding="utf-8")), path.name


def test_azure_deploy_uses_oidc_not_a_stored_credential(swa):
    deploy = swa["jobs"]["deploy"]
    assert deploy["permissions"]["id-token"] == "write", (
        "federated OIDC needs id-token: write"
    )
    raw = (WORKFLOWS / "azure-swa.yml").read_text(encoding="utf-8")
    for hint in AZURE_CREDENTIAL_HINTS:
        assert f"secrets.{hint}" not in raw, (
            f"secrets.{hint} means a stored credential; use OIDC + vars instead"
        )


def test_azure_identity_comes_from_variables(swa):
    login = next(
        step for _, step in steps_of(swa)
        if str(step.get("uses", "")).startswith("azure/login@")
    )
    for field in ("client-id", "tenant-id", "subscription-id"):
        value = login["with"][field]
        assert "vars." in value, f"{field} should be a repository variable, not a secret"


def test_deployment_token_is_fetched_just_in_time_and_masked(swa):
    raw = (WORKFLOWS / "azure-swa.yml").read_text(encoding="utf-8")
    assert "az staticwebapp secrets list" in raw, (
        "the deployment token should be fetched at run time, not stored"
    )
    assert "::add-mask::" in raw, "mask the token so it cannot land in a log"


def test_deploy_is_gated_on_the_production_environment(swa):
    """The federated credential's subject is scoped to this environment."""
    assert swa["jobs"]["deploy"]["environment"]["name"] == "production"


def test_deploy_runs_only_after_the_suite_passes(swa):
    assert swa["jobs"]["deploy"]["needs"] == "verify"


def test_no_workflow_grants_blanket_write(swa):
    assert swa["permissions"] == {"contents": "read"}, (
        "keep the workflow default read-only; widen per job"
    )


def test_third_party_actions_are_pinned_to_a_sha(swa):
    unpinned = [
        step["uses"] for _, step in steps_of(swa)
        if "uses" in step and not SHA_PINNED.match(step["uses"])
    ]
    assert not unpinned, f"pin these to a commit SHA: {unpinned}"
