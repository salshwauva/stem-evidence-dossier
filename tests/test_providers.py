import json
from pathlib import Path

import pytest

from evidence_dossier.extract import (
    ClaudeCliProvider,
    ProviderError,
    ProviderResponse,
    RecordedProvider,
    prompt_key,
)
from evidence_dossier.extract.providers import DENIED_TOOLS, run_command

PROMPT = "Extract the claims of document x."
RESPONSE = ProviderResponse(
    model_identifier="recorded-model-a", text='{"studies": [], "claims": []}'
)


def test_recorded_provider_serves_a_dict_response() -> None:
    provider = RecordedProvider({prompt_key(PROMPT): RESPONSE})

    assert provider.complete(PROMPT) == RESPONSE


def test_recorded_provider_serves_a_fixture_file(tmp_path: Path) -> None:
    (tmp_path / f"{prompt_key(PROMPT)}.json").write_text(RESPONSE.model_dump_json())

    assert RecordedProvider(fixture_dir=tmp_path).complete(PROMPT) == RESPONSE


def test_recorded_provider_names_the_missing_key(tmp_path: Path) -> None:
    provider = RecordedProvider({prompt_key(PROMPT): RESPONSE}, fixture_dir=tmp_path)

    with pytest.raises(ProviderError, match=prompt_key("another prompt")):
        provider.complete("another prompt")


def test_claude_cli_provider_sends_the_prompt_on_stdin_to_the_claude_command() -> None:
    calls: list[tuple[list[str], str]] = []

    def fake_runner(args: list[str], stdin: str) -> str:
        calls.append((args, stdin))
        return "  {}\n"

    response = ClaudeCliProvider("claude-test-1", runner=fake_runner).complete(PROMPT)

    ((args, stdin),) = calls
    assert stdin == PROMPT
    assert args[:6] == ["claude", "-p", "--output-format", "text", "--model", "claude-test-1"]
    assert response == ProviderResponse(model_identifier="claude-cli/claude-test-1", text="  {}\n")


def test_claude_cli_provider_grants_no_tool_and_loads_no_settings() -> None:
    """The prompt carries paper text (plan section 51), so the command line isolates the run."""
    calls: list[list[str]] = []

    def fake_runner(args: list[str], stdin: str) -> str:
        calls.append(args)
        return "{}"

    ClaudeCliProvider("claude-test-1", runner=fake_runner).complete(PROMPT)

    (args,) = calls
    assert args[args.index("--tools") + 1] == ""
    start = args.index("--disallowed-tools") + 1
    assert tuple(args[start : start + len(DENIED_TOOLS)]) == DENIED_TOOLS
    assert {"Bash", "Write", "Edit", "WebFetch", "Agent"} <= set(DENIED_TOOLS)
    assert "--strict-mcp-config" in args
    settings = json.loads(args[args.index("--settings") + 1])
    assert settings["permissions"]["allow"] == []
    assert set(settings["permissions"]["deny"]) == set(DENIED_TOOLS)


def test_run_command_reports_a_missing_command() -> None:
    with pytest.raises(ProviderError, match="is not on PATH"):
        run_command(["evidence-dossier-no-such-command"], PROMPT)


def test_run_command_reports_a_failed_command() -> None:
    with pytest.raises(ProviderError, match="exited with status 3: boom"):
        run_command(["sh", "-c", "echo boom >&2; exit 3"], PROMPT)


def test_run_command_returns_stdout() -> None:
    assert run_command(["cat"], PROMPT) == PROMPT
