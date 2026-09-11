import importlib
import inspect
import pkgutil
import typing
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

import evidence_dossier.model
from evidence_dossier.model import (
    Author,
    BiologyAttributes,
    Comparator,
    ComputerScienceAttributes,
    EvidenceClaim,
    EvidenceSpan,
    ExtractionRun,
    Measurement,
    Method,
    ResearchContext,
    ResearchWork,
    Result,
    Section,
    SourceDocument,
    Study,
    Term,
    WorkLink,
)

BIOMEDICAL_FIELDS = {
    "organism",
    "cell_line",
    "tissue",
    "disease_model",
    "intervention",
    "dose",
    "duration",
    "assay",
}


def _model_classes() -> set[type[BaseModel]]:
    """Every Pydantic class that a module under evidence_dossier.model defines."""
    classes: set[type[BaseModel]] = set()
    for module_info in pkgutil.walk_packages(
        evidence_dossier.model.__path__, prefix="evidence_dossier.model."
    ):
        module = importlib.import_module(module_info.name)
        for _, member in inspect.getmembers(module, inspect.isclass):
            if issubclass(member, BaseModel) and member.__module__ == module.__name__:
                classes.add(member)
    return classes


def _union_members(annotation: object) -> set[type[BaseModel]]:
    """The Pydantic classes inside an annotation, through Optional, Union and Annotated."""
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return {annotation}
    members: set[type[BaseModel]] = set()
    for argument in typing.get_args(annotation):
        members |= _union_members(argument)
    return members


def _attribute_classes() -> set[type[BaseModel]]:
    return _union_members(ResearchContext.model_fields["domain_attributes"].annotation)


def test_context_method_and_comparator_share_one_attribute_union() -> None:
    attribute_classes = _attribute_classes()

    assert attribute_classes == {BiologyAttributes, ComputerScienceAttributes}
    for cls in (Method, Comparator):
        assert _union_members(cls.model_fields["domain_attributes"].annotation) == attribute_classes


def test_generic_core_records_declare_no_biomedical_fields() -> None:
    core_classes = _model_classes() - _attribute_classes()

    # The walk must reach every core record, or the check below proves nothing.
    assert {
        Author,
        Comparator,
        EvidenceClaim,
        EvidenceSpan,
        ExtractionRun,
        Measurement,
        Method,
        ResearchContext,
        ResearchWork,
        Result,
        Section,
        SourceDocument,
        Study,
        Term,
        WorkLink,
    } <= core_classes
    for cls in core_classes:
        assert BIOMEDICAL_FIELDS.isdisjoint(cls.model_fields), cls.__name__


def test_biomedical_fields_exist_only_on_biology_attributes() -> None:
    owners = {cls for cls in _model_classes() if BIOMEDICAL_FIELDS & set(cls.model_fields)}

    assert owners == {BiologyAttributes}
    assert set(BiologyAttributes.model_fields) >= BIOMEDICAL_FIELDS


@pytest.mark.parametrize(
    ("model_class", "payload"),
    [
        (ResearchContext, {"domain": "CHEMISTRY"}),
        (Method, {"name": {"original": "electrocatalysis"}}),
        (Comparator, {"name": {"original": "standard catalyst"}}),
    ],
    ids=["research_context", "method", "comparator"],
)
def test_unknown_profile_tag_fails_validation(
    model_class: type[BaseModel], payload: dict[str, Any]
) -> None:
    attributes = {"profile": "chemistry", "catalyst": "nickel"}

    with pytest.raises(ValidationError) as caught:
        model_class.model_validate({**payload, "domain_attributes": attributes})

    assert [error["type"] for error in caught.value.errors()] == ["union_tag_invalid"]
