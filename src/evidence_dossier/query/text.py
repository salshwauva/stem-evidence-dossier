"""Generic text handling for the query package.

The rules here stay generic on purpose. Canonical names and units belong to the
normalize subpackage, which query never imports. A caller injects a
canonicalizer to reach those rules (plan sections 33 and 35).
"""

import re
from collections.abc import Callable

# A function that maps a name to the canonical form that claims store.
type Canonicalizer = Callable[[str], str]

_WHITESPACE = re.compile(r"\s+")
# Punctuation that a sentence puts around a name, such as quotes or a final period.
_EDGE_PUNCTUATION = ".,;:!?\"'()[]{}"


def default_canonicalizer(text: str) -> str:
    """Return a lowercase form of a name, with one space between its words.

    This is the generic fallback. It folds case, collapses whitespace and drops
    the punctuation at the edges. It knows no synonyms and no domain vocabulary.
    """
    collapsed = _WHITESPACE.sub(" ", text).strip()
    return collapsed.strip(_EDGE_PUNCTUATION).casefold()
