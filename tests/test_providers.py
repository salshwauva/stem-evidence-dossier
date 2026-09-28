import json
import os
from pathlib import Path

import pytest

from evidence_dossier.extract import (
    ClaudeCliProvider,
    ProviderError,
    ProviderResponse,
    RecordedProvider,
    RecordingProvider,
    prompt_key,
)
from evidence_dossier.extract.providers import DENIED_TOOLS, DETAIL_LIMIT, run_command

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


def test_a_recording_provider_saves_a_reply_that_recorded_provider_replays(
    tmp_path: Path,
) -> None:
    live = RecordedProvider({prompt_key(PROMPT): RESPONSE})

    assert RecordingProvider(live, tmp_path).complete(PROMPT) == RESPONSE
    assert RecordedProvider(fixture_dir=tmp_path).complete(PROMPT) == RESPONSE


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
    assert args[args.index("--setting-sources") + 1] == ""
    assert "--no-session-persistence" in args
    settings = json.loads(args[args.index("--settings") + 1])
    assert settings["permissions"]["allow"] == []
    assert set(settings["permissions"]["deny"]) == set(DENIED_TOOLS)


@pytest.mark.skipif(
    os.environ.get("CLAUDE_CLI_LIVE") != "1",
    reason="set CLAUDE_CLI_LIVE=1 to call the logged in claude command line tool",
)
def test_the_installed_claude_cli_accepts_every_isolation_flag() -> None:
    """One short live call. The command line tool stops with status 1 on a flag or tool
    name that it does not know, so a reply proves the argument list still works."""
    response = ClaudeCliProvider("claude-haiku-4-5-20251001").complete(
        "Reply with the single word: ok"
    )
    assert response.text.strip()


def test_run_command_reports_a_missing_command() -> None:
    with pytest.raises(ProviderError, match="is not on PATH"):
        run_command(["evidence-dossier-no-such-command"], PROMPT)


def test_run_command_reports_a_failed_command() -> None:
    with pytest.raises(ProviderError, match="exited with status 3: boom"):
        run_command(["sh", "-c", "echo boom >&2; exit 3"], PROMPT)


def test_run_command_reports_stdout_when_stderr_is_empty() -> None:
    with pytest.raises(ProviderError, match="exited with status 1: Failed to authenticate"):
        run_command(["sh", "-c", "echo Failed to authenticate; exit 1"], PROMPT)


def test_run_command_cuts_long_output_in_the_error() -> None:
    with pytest.raises(ProviderError) as raised:
        run_command(["sh", "-c", "printf 'x%.0s' $(seq 2000); exit 1"], PROMPT)
    detail = str(raised.value).split(": ", 1)[1]
    assert detail == "x" * DETAIL_LIMIT + f" (cut at {DETAIL_LIMIT} characters)"


def test_run_command_returns_stdout() -> None:
    assert run_command(["cat"], PROMPT) == PROMPT
