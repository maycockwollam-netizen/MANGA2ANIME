"""Integration Layer.

Provides orchestration above Core modules while maintaining Core isolation.
Does not import into Core - only Core imports this layer.
"""

from integration.context import ProjectContext
from integration.exceptions import (
    DanglingReferenceError,
    DuplicateRegistrationError,
    EntityNotFoundError,
    IntegrationError,
    IntegrationValidationError,
    ReferenceResolutionError,
)
from integration.registry import Registry
from integration.resolver import ReferenceResolver
from integration.validator import IntegrationValidator

__all__ = [
    # Context
    "ProjectContext",
    # Registry
    "Registry",
    # Resolver
    "ReferenceResolver",
    # Validator
    "IntegrationValidator",
    # Exceptions
    "IntegrationError",
    "DuplicateRegistrationError",
    "EntityNotFoundError",
    "ReferenceResolutionError",
    "IntegrationValidationError",
    "DanglingReferenceError",
]
