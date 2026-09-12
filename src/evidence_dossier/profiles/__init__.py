"""Domain profiles: plain data that enriches the generic core for one domain.

This package imports model and nothing else from evidence_dossier.
"""

from evidence_dossier.profiles.base import (
    GENERIC_COMPARABILITY_DIMENSIONS,
    GENERIC_EVIDENCE_GAP_DIMENSIONS,
    AttributeModel,
    DomainProfile,
)
from evidence_dossier.profiles.biology import BiologyProfile
from evidence_dossier.profiles.chemistry import ChemistryProfile
from evidence_dossier.profiles.computer_science import ComputerScienceProfile
from evidence_dossier.profiles.generic import GenericProfile
from evidence_dossier.profiles.registry import get_profile

__all__ = [
    "GENERIC_COMPARABILITY_DIMENSIONS",
    "GENERIC_EVIDENCE_GAP_DIMENSIONS",
    "AttributeModel",
    "BiologyProfile",
    "ChemistryProfile",
    "ComputerScienceProfile",
    "DomainProfile",
    "GenericProfile",
    "get_profile",
]
