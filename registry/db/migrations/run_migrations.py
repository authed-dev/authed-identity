"""
Script to run all database migrations.
This script should be run once to update the database schema.
"""

from registry.db.migrations import add_claimed_to_providers, make_provider_name_nullable

def run_all_migrations():
    """Run all database migrations"""
    print("Starting database migrations")
    
    # Run migrations in order
    add_claimed_to_providers()
    make_provider_name_nullable()
    
    print("All migrations completed successfully")

if __name__ == "__main__":
    run_all_migrations() 