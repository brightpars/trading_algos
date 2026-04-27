from __future__ import annotations

from typing import Any, cast

from trading_algos_dashboard.services.server_control_service import (
    ServerControlService,
)


class _Repository:
    def get_settings(self):
        return None


def test_data_service_uses_dashboard_service_runtime_by_default():
    service = ServerControlService(repository=cast(Any, _Repository()))
    definition = service._definition_by_name("data")

    command, source = service._start_command_details(definition)

    assert source == "dashboard default"
    assert (
        command == "./.venv/bin/python -m trading_algos_dashboard.service_runtime data"
    )


def test_data_service_uses_repo_root_as_default_workdir():
    service = ServerControlService(repository=cast(Any, _Repository()))
    definition = service._definition_by_name("data")

    workdir = service._default_workdir_for_definition(definition)

    assert workdir.endswith("/trading_algos")


def test_data_service_environment_contains_dashboard_service_fields():
    service = ServerControlService(repository=cast(Any, _Repository()))
    definition = service._definition_by_name("data")

    environment = service._service_environment(definition, port=6010)

    assert environment["SERVICE_NAME"] == "data"
    assert environment["SERVICE_PORT"] == "6010"
    assert environment["SERVICE_HOST"] == "127.0.0.1"
    assert environment["SERVICE_USER_ID"] == "1"


def test_engines_control_uses_dashboard_service_runtime_by_default() -> None:
    service = ServerControlService(repository=cast(Any, _Repository()))
    definition = service._definition_by_name("engines_control")

    command, source = service._start_command_details(definition)

    assert source == "dashboard default"
    assert (
        command
        == "./.venv/bin/python -m trading_algos_dashboard.service_runtime engines_control"
    )


def test_engines_control_is_controllable_from_dashboard() -> None:
    service = ServerControlService(repository=cast(Any, _Repository()))
    definition = service._definition_by_name("engines_control")

    assert definition["controllable"] is True
