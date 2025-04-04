"""
Database migrations package.
This package contains scripts to update the database schema.
"""

from registry.db.migrations.add_claimed_to_providers import run_migration as add_claimed_to_providers
from registry.db.migrations.make_provider_name_nullable import run_migration as make_provider_name_nullable

__all__ = ['add_claimed_to_providers', 'make_provider_name_nullable'] 