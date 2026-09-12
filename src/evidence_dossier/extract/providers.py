"""Extraction providers: the adapter that hides the model call (plan section 52).

ProviderResponse is the boundary record for one model reply. RecordedProvider
serves stored replies, so tests run without a network call (plan section 51).
ClaudeCliProvider runs the claude command line tool as a subprocess, so the
repository never handles an API key.
"""

import hashlib
import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Protocol

from evidence_dossier.model import FrozenModel


class ProviderResponse(FrozenModel):
    """One model reply with the identifier of the model that produced it."""

    model_identifier: str
    text: str


class ExtractionProvider(Protocol):
    """Anything that turns a prompt into a model reply."""

    def complete(self, prompt: str) -> ProviderResponse: ...


class ProviderError(RuntimeError):
    """The provider could not produce a reply."""


def prompt_key(prompt: str) -> str:
    """Return the sha256 hex digest that keys a recorded reply to its prompt."""
    return hashlib.sha256(prompt.encode()).hexdigest()


class RecordedProvider:
    """Serves recorded replies keyed by prompt_key(prompt).

    A fixture directory holds one JSON file per reply, named "<prompt key>.json",
    with the fields of ProviderResponse. A miss raises ProviderError and names
    the key, so a changed prompt is easy to spot.
    """

    def __init__(
        self,
        responses: Mapping[str, ProviderResponse] | None = None,
        fixture_dir: Path | None = None,
    ) -> None:
        self._responses = dict(responses or {})
        self._fixture_dir = fixture_dir

    def complete(self, prompt: str) -> ProviderResponse:
        key = prompt_key(prompt)
        response = self._responses.get(key)
        if response is not None:
            return response
        if self._fixture_dir is not None:
            path = self._fixture_dir / f"{key}.json"
            if path.is_file():
                return ProviderResponse.model_validate_json(path.read_text(encoding="utf-8"))
        raise ProviderError(f"no recorded response for prompt key {key}")


type CommandRunner = Callable[[list[str], str], str]
"""Runs a command with the given text on stdin and returns its stdout."""


def run_command(args: list[str], stdin: str) -> str:
    """Run a command and return its stdout. A missing command or a failure raises ProviderError."""
    try:
        completed = subprocess.run(args, input=stdin, capture_output=True, text=True, check=True)
    except FileNotFoundError as error:
        raise ProviderError(f"{args[0]} is not on PATH") from error
    except subprocess.CalledProcessError as error:
        detail = str(error.stderr).strip()
        raise ProviderError(f"{args[0]} exited with status {error.returncode}: {detail}") from error
    return completed.stdout


class ClaudeCliProvider:
    """Runs "claude -p --output-format text --model <model>" with the prompt on stdin.

    The command needs a logged in claude command line tool on PATH. The
    repository holds no API key. Tests inject a fake runner in place of
    run_command.
    """

    def __init__(self, model: str, runner: CommandRunner = run_command) -> None:
        self._model = model
        self._runner = runner

    def complete(self, prompt: str) -> ProviderResponse:
        args = ["claude", "-p", "--output-format", "text", "--model", self._model]
        text = self._runner(args, prompt)
        return ProviderResponse(model_identifier=f"claude-cli/{self._model}", text=text)
