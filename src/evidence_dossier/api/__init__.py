"""FastAPI routes over the query pipeline (plan section 48).

This package imports query, model and store, and nothing else from
evidence_dossier.
"""

from evidence_dossier.api.app import create_app

__all__ = ["create_app"]
