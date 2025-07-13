"""TBA"""

import sys

from ...package.autocli import *
import pytest

# Standard typing imports for aps
import typing_extensions as _te
import collections.abc as _a
import typing as _ty

if _ty.TYPE_CHECKING:
    import _typeshed as _tsh
import types as _ts


def test_arg_struct_builder():
    builder = ArgStructBuilder()
    builder.add_command("build")
    builder.add_subcommand("build", "clean")
    builder.add_nested_command("build", "run", {"dev": {}, "prod": {}})
    result = builder.get_structure()
    assert result == {"build": {"clean": {}, "run": {"dev": {}, "prod": {}}}}


def test_argument_parsing_error():
    with pytest.raises(ArgumentParsingError) as exc:
        raise ArgumentParsingError("error", 2)
    assert exc.value.index == 2
    assert str(exc.value) == "error"


def test_endpoint_call_executes_function():
    called = {}

    def fn(x):
        called["result"] = x + 1

    ep = EndPoint(fn)
    assert ep.call(1) is None
    assert called["result"] == 2


def test_argumint_parse_and_replace(monkeypatch):
    called = {}

    def default_fn():
        called["used"] = "default"

    def other_fn():
        called["used"] = "other"

    # Step 1: Build arg_struct correctly
    builder = ArgStructBuilder()
    builder.add_command("base")
    builder.add_subcommand("base", "run")
    arg_struct = builder.get_structure()

    # Step 2: Create Argumint with structure
    default = EndPoint(default_fn)
    other = EndPoint(other_fn)
    arg = Argumint(default, arg_struct)
    arg.add_endpoint("base.run", other)

    # Step 3: Simulate CLI call
    monkeypatch.setattr(sys, "argv", ["base", "run"])
    arg.parse_cli()
    assert called["used"] == "other"

    monkeypatch.setattr(sys, "argv", ["base"])
    called.clear()
    arg.parse_cli()
    assert called["used"] == "default"

    # Step 4: Replace structure and verify
    new_struct = {"run2": {}}
    arg.replace_arg_struct(new_struct)
    assert arg._arg_struct == new_struct


def test_cli_dispatch(monkeypatch):
    builder = ArgStructBuilder()
    builder.add_command("cli")
    builder.add_nested_command("cli", "tool", "run")

    called = {}

    def dummy_endpoint(**kwargs):
        called.update({"called": True})

    arg_struct = builder.get_structure()
    argumint = Argumint(EndPoint(lambda: None), arg_struct)
    argumint.add_endpoint("cli.tool.run", EndPoint(dummy_endpoint))

    monkeypatch.setattr(sys, "argv", ["cli", "tool", "run"])
    argumint.parse_cli(mode="native_light")
    assert called.get("called") is True


def test_default_endpoint(monkeypatch):
    called = {}

    def fallback():
        called["used"] = True

    builder = ArgStructBuilder()
    builder.add_command("cli")
    builder.add_subcommand("cli", "run")
    arg_struct = builder.get_structure()

    argumint = Argumint(EndPoint(fallback), arg_struct)
    monkeypatch.setattr(sys, "argv", ["cli", "run"])
    argumint.parse_cli(mode="native_light")

    assert called.get("used") is True


def test_invalid_add_endpoint_raises():
    builder = ArgStructBuilder()
    builder.add_command("cli")
    arg_struct = builder.get_structure()
    argumint = Argumint(EndPoint(lambda: None), arg_struct)

    with pytest.raises(ValueError):
        argumint.add_endpoint("cli.invalid.path", EndPoint(lambda: None))


def test_analyze_function_metadata():
    def sample_function(x: int, y: str = "default") -> bool:
        """Do something."""
        return str(x) == y

    analysis = analyze_function(sample_function)

    assert analysis["name"] == "sample_function"
    assert any(
        arg["name"] == "x" and arg["type"] == int for arg in analysis["arguments"]
    )
    assert any(
        arg["name"] == "y" and arg["default"] == "default"
        for arg in analysis["arguments"]
    )
    assert analysis["return_type"] is bool
