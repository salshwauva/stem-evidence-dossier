"""Profile lookup by domain."""

from evidence_dossier.model import Domain
from evidence_dossier.profiles.base import DomainProfile
from evidence_dossier.profiles.biology import BiologyProfile
from evidence_dossier.profiles.chemistry import ChemistryProfile
from evidence_dossier.profiles.computer_science import ComputerScienceProfile
from evidence_dossier.profiles.engineering import EngineeringProfile
from evidence_dossier.profiles.generic import GenericProfile
from evidence_dossier.profiles.physics import PhysicsProfile


def get_profile(domain: Domain) -> DomainProfile:
    """Return the profile for a domain, or the generic profile when the domain has none."""
    match domain:
        case Domain.BIOLOGY:
            return BiologyProfile()
        case Domain.CHEMISTRY:
            return ChemistryProfile()
        case Domain.COMPUTER_SCIENCE:
            return ComputerScienceProfile()
        case Domain.PHYSICS:
            return PhysicsProfile()
        case Domain.ENGINEERING:
            return EngineeringProfile()
        case _:
            return GenericProfile(domain=domain)
