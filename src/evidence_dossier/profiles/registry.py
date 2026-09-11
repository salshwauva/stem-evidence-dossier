"""Profile lookup by domain."""

from evidence_dossier.model import Domain
from evidence_dossier.profiles.base import DomainProfile
from evidence_dossier.profiles.biology import BiologyProfile
from evidence_dossier.profiles.computer_science import ComputerScienceProfile
from evidence_dossier.profiles.generic import GenericProfile


def get_profile(domain: Domain) -> DomainProfile:
    """Return the profile for a domain, or the generic profile when the domain has none."""
    match domain:
        case Domain.BIOLOGY:
            return BiologyProfile()
        case Domain.COMPUTER_SCIENCE:
            return ComputerScienceProfile()
        case _:
            return GenericProfile(domain=domain)
