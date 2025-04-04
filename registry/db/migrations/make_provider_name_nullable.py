"""Make provider name column nullable

This migration modifies the providers table to make the name column nullable,
aligning with the updated Pydantic models where name is optional.
"""

from sqlalchemy import MetaData, Table, Column, String, text
from sqlalchemy.engine import Engine

from ...db import engine

def upgrade(engine: Engine):
    """Upgrade: Make name column nullable"""
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    # Get the providers table
    providers = Table('providers', metadata, extend_existing=True)
    
    # Modify the name column to be nullable
    with engine.begin() as connection:
        connection.execute(
            text('ALTER TABLE providers ALTER COLUMN name DROP NOT NULL')
        )

def downgrade(engine: Engine):
    """Downgrade: Make name column NOT NULL again"""
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    # Get the providers table
    providers = Table('providers', metadata, extend_existing=True)
    
    # Modify the name column to be NOT NULL
    with engine.begin() as connection:
        # First set any NULL values to a default value to avoid constraint violation
        connection.execute(
            text("UPDATE providers SET name = 'unnamed-provider-' || id WHERE name IS NULL")
        )
        # Then add the NOT NULL constraint
        connection.execute(
            text('ALTER TABLE providers ALTER COLUMN name SET NOT NULL')
        )

def run_migration():
    """Run the migration"""
    print("Starting migration: Make provider name column nullable")
    try:
        upgrade(engine)
        print("Successfully made provider name column nullable")
    except Exception as e:
        print(f"Error making provider name column nullable: {str(e)}")
        raise 