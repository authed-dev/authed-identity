"""Provider management commands."""

import click
import requests
from uuid import UUID

@click.group(name='providers')
def group():
    """Manage providers."""
    pass

@group.command('register')
@click.option('--name', help='Name of the provider (for claimed accounts)')
@click.option('--email', help='Email of the provider (for claimed accounts)')
def register(name, email):
    """Register a new provider with Authed.
    
    If name and email are provided, the account will be claimed.
    If no credentials are provided, an unclaimed account will be created.
    """
    data = {}
    
    # If name and email are provided, add them to the request
    if name and email:
        data = {
            "name": name,
            "email": email
        }
    
    try:
        response = requests.post(
            "https://api.getauthed.dev/providers/register",
            headers={"Content-Type": "application/json"},
            json=data
        )
        response.raise_for_status()
        click.echo(f"Success! Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: {str(e)}", err=True) 