"""One XML entry point for untrusted literature responses (plan section 51).

The stdlib expat parser expands internal entities, so a small payload with
nested entity declarations can grow into a large document. This module scans
a document with expat handlers that refuse every entity declaration and every
external entity reference, and only then hands it to ElementTree. A DOCTYPE
without declarations stays allowed, because the NCBI responses carry one.
"""

import xml.etree.ElementTree as ET
from xml.parsers import expat


class UnsafeXmlError(ValueError):
    """The document declares an entity or references an external one."""


def _entity_decl(*args: object) -> None:
    raise UnsafeXmlError("entity declarations are not accepted")


def _external_entity(*args: object) -> int:
    raise UnsafeXmlError("external entity references are not accepted")


def parse_xml(body: bytes | str) -> ET.Element:
    """Parse XML and return its root, or raise UnsafeXmlError on an entity declaration."""
    scanner = expat.ParserCreate()
    scanner.EntityDeclHandler = _entity_decl
    scanner.UnparsedEntityDeclHandler = _entity_decl
    scanner.ExternalEntityRefHandler = _external_entity
    try:
        scanner.Parse(body, True)
    except expat.ExpatError as error:
        raise ET.ParseError(str(error)) from error
    return ET.fromstring(body)
