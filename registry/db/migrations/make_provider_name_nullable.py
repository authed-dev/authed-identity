"""Make provider fields nullable

This migration modifies the providers table to make the name and contact_email columns nullable,
aligning with the updated Pydantic models where these fields are optional.
"""

from sqlalchemy import MetaData, Table, Column, String, text
from sqlalchemy.engine import Engine

from ...db import engine

def upgrade(engine: Engine):
    """Upgrade: Make name and contact_email columns nullable"""
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    # Get the providers table
    providers = Table('providers', metadata, extend_existing=True)
    
    # Modify the columns to be nullable
    with engine.begin() as connection:
        connection.execute(
            text('ALTER TABLE providers ALTER COLUMN name DROP NOT NULL')
        )
        connection.execute(
            text('ALTER TABLE providers ALTER COLUMN contact_email DROP NOT NULL')
        )

def downgrade(engine: Engine):
    """Downgrade: Make name and contact_email columns NOT NULL again"""
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    # Get the providers table
    providers = Table('providers', metadata, extend_existing=True)
    
    # Modify the columns to be NOT NULL
    with engine.begin() as connection:
        # First set any NULL values to default values to avoid constraint violation
        connection.execute(
            text("UPDATE providers SET name = 'unnamed-provider-' || id WHERE name IS NULL")
        )
        connection.execute(
            text("UPDATE providers SET contact_email = 'no-email-' || id || '@placeholder.com' WHERE contact_email IS NULL")
        )
        # Then add the NOT NULL constraints
        connection.execute(
            text('ALTER TABLE providers ALTER COLUMN name SET NOT NULL')
        )
        connection.execute(
            text('ALTER TABLE providers ALTER COLUMN contact_email SET NOT NULL')
        )

def run_migration():
    """Run the migration"""
    print("Starting migration: Make provider fields nullable")
    try:
        upgrade(engine)
        print("Successfully made provider fields nullable")
    except Exception as e:
        print(f"Error making provider fields nullable: {str(e)}")
        raise 