"""The XML entry point refuses entity expansion and external entities (plan section 51).

These are regression tests for two known payload shapes. They do not prove
that every unsafe document is refused.
"""

import pytest

from evidence_dossier.ingest.xml import UnsafeXmlError, parse_xml

BILLION_LAUGHS = b"""<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;">
]>
<lolz>&lol2;</lolz>"""

EXTERNAL_ENTITY = b"""<?xml version="1.0"?>
<!DOCTYPE doc [
  <!ENTITY host SYSTEM "file:///etc/hostname">
]>
<doc>&host;</doc>"""

DOCTYPE_ONLY = b"""<?xml version="1.0"?>
<!DOCTYPE PubmedArticleSet PUBLIC "-//NLM//DTD PubMedArticle, 1st January 2024//EN" "https://dtd.nlm.nih.gov/ncbi/pubmed/out/pubmed_240101.dtd">
<PubmedArticleSet><PubmedArticle><PMID>90000001</PMID></PubmedArticle></PubmedArticleSet>"""


def test_nested_entity_declarations_are_refused() -> None:
    with pytest.raises(UnsafeXmlError, match="entity declarations"):
        parse_xml(BILLION_LAUGHS)


def test_external_entity_declarations_are_refused() -> None:
    with pytest.raises(UnsafeXmlError):
        parse_xml(EXTERNAL_ENTITY)


def test_a_doctype_without_declarations_still_parses() -> None:
    root = parse_xml(DOCTYPE_ONLY)

    assert root.tag == "PubmedArticleSet"
    assert root.findtext("PubmedArticle/PMID") == "90000001"


def test_a_plain_document_parses() -> None:
    assert parse_xml("<a><b>text</b></a>").findtext("b") == "text"
