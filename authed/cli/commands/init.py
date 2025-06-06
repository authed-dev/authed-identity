"""Initialization and configuration commands."""

import click
import json
from pathlib import Path
from typing import Optional
from ..utils import async_command
import requests

CONFIG_DIR = Path.home() / '.authed'
CONFIG_FILE = CONFIG_DIR / 'config.json'

@click.group(name='init')
def group():
    """Initialize and configure the CLI."""
    pass

@group.command(name='config')
@click.option('--registry-url', help='Registry URL to save in config')
@click.option('--provider-id', help='Provider ID to save in config')
@click.option('--provider-secret', help='Provider secret to save in config')
def configure(
    registry_url: Optional[str] = None,
    provider_id: Optional[str] = None,
    provider_secret: Optional[str] = None
):
    """Configure CLI credentials interactively or via arguments."""
    # Create config directory if it doesn't exist
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load existing config if it exists
    config = {}
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open('r') as f:
            config = json.load(f)
    
    # If no arguments provided, use interactive mode
    if not any([registry_url, provider_id, provider_secret]):
        click.echo("\n" + "=" * 60)
        click.echo(click.style("Interactive Configuration", fg="blue", bold=True))
        click.echo("=" * 60 + "\n")
        
        # Registry URL
        default_url = config.get('registry_url', '')
        registry_url = click.prompt(
            click.style("Registry URL", bold=True),
            default=default_url,
            type=str
        )
        
        # Provider ID
        default_id = config.get('provider_id', '')
        provider_id = click.prompt(
            click.style("Provider ID", bold=True),
            default=default_id,
            type=str
        )
        
        # Provider Secret
        default_secret = config.get('provider_secret', '')
        if default_secret:
            default_display = '*' * len(default_secret)
            click.echo(f"\nCurrent provider secret: {click.style(default_display, fg='bright_black')}")
            if not click.confirm(click.style("Update provider secret?", fg="yellow", bold=True), default=False):
                provider_secret = default_secret
            else:
                provider_secret = click.prompt(
                    click.style("Provider Secret", bold=True),
                    hide_input=True,
                    confirmation_prompt=True
                )
        else:
            provider_secret = click.prompt(
                click.style("Provider Secret", bold=True),
                hide_input=True,
                confirmation_prompt=True
            )
    
    # Update config
    config.update({
        'registry_url': registry_url,
        'provider_id': provider_id,
        'provider_secret': provider_secret
    })
    
    # Save config
    with CONFIG_FILE.open('w') as f:
        json.dump(config, f, indent=2)
    
    # Print success message
    click.echo("\n" + "=" * 60)
    click.echo(click.style("✓", fg="green", bold=True) + " Configuration saved successfully")
    click.echo("=" * 60)
    click.echo(f"\nConfig file: {click.style(str(CONFIG_FILE), fg='blue')}")
    click.echo("\nYou can now use the CLI in the following ways:")
    click.echo("\n1. " + click.style("Without credentials", bold=True) + ":")
    click.echo(click.style("   authed agents list", fg="bright_black"))
    click.echo("\n2. " + click.style("Override saved config", bold=True) + ":")
    click.echo(click.style("   authed --registry-url=URL --provider-id=ID --provider-secret=SECRET agents list", fg="bright_black"))
    click.echo()

@group.command(name='show')
def show_config():
    """Show current configuration."""
    if not CONFIG_FILE.exists():
        click.echo("\n" + click.style("⚠️  No configuration found", fg="yellow", bold=True))
        click.echo("Run " + click.style("authed init config", fg="blue", bold=True) + " to configure.")
        click.echo()
        return
    
    with CONFIG_FILE.open('r') as f:
        config = json.load(f)
    
    click.echo("\n" + "=" * 60)
    click.echo(click.style("Current Configuration", fg="blue", bold=True))
    click.echo("=" * 60 + "\n")
    
    # Registry URL
    click.echo(click.style("Registry URL:", bold=True))
    if url := config.get('registry_url'):
        click.echo(f"  {click.style(url, fg='bright_blue')}")
    else:
        click.echo(click.style("  Not set", fg="yellow", italic=True))
    
    # Provider ID
    click.echo(f"\n{click.style('Provider ID:', bold=True)}")
    if pid := config.get('provider_id'):
        click.echo(f"  {click.style(pid, fg='magenta')}")
    else:
        click.echo(click.style("  Not set", fg="yellow", italic=True))
    
    # Provider Secret
    click.echo(f"\n{click.style('Provider Secret:', bold=True)}")
    if config.get('provider_secret'):
        secret_display = '*' * len(config['provider_secret'])
        click.echo(f"  {click.style(secret_display, fg='bright_black')}")
    else:
        click.echo(click.style("  Not set", fg="yellow", italic=True))
    
    click.echo(f"\nConfig file: {click.style(str(CONFIG_FILE), fg='blue')}")
    click.echo()

@group.command(name='clear')
@click.option('--force', is_flag=True, help='Clear without confirmation')
def clear_config(force: bool):
    """Clear saved configuration."""
    if not CONFIG_FILE.exists():
        click.echo("\n" + click.style("⚠️  No configuration found", fg="yellow", bold=True))
        click.echo()
        return
    
    if not force:
        click.echo("\n" + click.style("⚠️  Warning", fg="yellow", bold=True))
        click.echo("You are about to clear all saved configuration.")
        click.echo(click.style("This action cannot be undone!", fg="yellow"))
        click.echo()
        
        if not click.confirm(click.style("Are you sure?", fg="yellow", bold=True)):
            click.echo(click.style("\nOperation cancelled", fg="bright_black", italic=True))
            click.echo()
            return
    
    CONFIG_FILE.unlink()
    click.echo("\n" + click.style("✓", fg="green", bold=True) + " Configuration cleared successfully")
    click.echo()

@group.command(name='setup')
@click.option('--provider-id', help='Provider ID (optional - will create unclaimed provider if not provided)')
@click.option('--provider-secret', help='Provider secret (optional - will create unclaimed provider if not provided)')
@click.pass_context
@async_command
async def setup(ctx, provider_id: Optional[str], provider_secret: Optional[str]):
    """Quick setup: configure provider, create agent, and set up environment.
    
    There are two ways to use this command:
    
    1. Unclaimed Provider (Limited Capabilities):
       Run without parameters: authed init setup
       This creates a new unclaimed provider with limited capabilities.
       
    2. Claimed Provider (Full Capabilities):
       Run with provider credentials: authed init setup --provider-id "your-id" --provider-secret "your-secret"
       This uses an existing claimed provider with full capabilities.
    """
    # Create unclaimed provider if credentials not provided
    if not provider_id or not provider_secret:
        click.echo("\n" + click.style("Creating unclaimed provider...", fg="blue"))
        try:
            response = requests.post(
                "https://api.getauthed.dev/providers/register",
                headers={"Content-Type": "application/json"},
                json={}
            )
            response.raise_for_status()
            result = response.json()
            provider_id = result['id']
            provider_secret = result['provider_secret']
            click.echo(click.style("✓", fg="green") + " Provider created successfully")
        except requests.exceptions.RequestException as e:
            raise click.UsageError(f"Failed to create provider: {str(e)}")

    # Save provider config
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config = {
        'registry_url': 'https://api.getauthed.dev',
        'provider_id': provider_id,
        'provider_secret': provider_secret
    }
    with CONFIG_FILE.open('w') as f:
        json.dump(config, f, indent=2)

    # Generate keys
    from ..commands.keys import generate_keypair
    key_pair = generate_keypair()
    public_key = key_pair.public_key
    private_key = key_pair.private_key

    # Initialize auth with saved config
    from ..auth import CLIAuth
    auth = CLIAuth(
        registry_url=config['registry_url'],
        provider_id=provider_id,
        provider_secret=provider_secret
    )

    # Create first agent
    response = await auth.request(
        'POST',
        '/agents/register',
        json={
            "provider_id": provider_id,
            "name": "default-agent",
            "dpop_public_key": public_key
        }
    )

    if response.status_code != 200:
        raise click.UsageError(f"Failed to create agent: {response.text}")

    result = response.json()
    agent_id = result['agent_id']
    agent_secret = result['agent_secret']

    # Create or update .env file
    env_file = Path('.env')
    
    # Load existing env file content
    existing_env = {}
    if env_file.exists():
        with env_file.open('r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    existing_env[key.strip()] = value.strip()
    
    # Check if we have valid key pair
    def is_valid_key(key: str) -> bool:
        key = key.strip('"\' ')
        # Basic format check - should have proper PEM headers and content
        if key.startswith('-----BEGIN') and key.endswith('-----'):
            # Should have some content between the headers
            parts = key.split('-----')
            return len(parts) >= 4 and parts[2].strip()  # Middle part should have content
        return False

    has_valid_keys = (
        'AUTHED_PRIVATE_KEY' in existing_env and 
        'AUTHED_PUBLIC_KEY' in existing_env and
        is_valid_key(existing_env['AUTHED_PRIVATE_KEY']) and
        is_valid_key(existing_env['AUTHED_PUBLIC_KEY'])
    )
    
    # Generate new keys if needed
    if not has_valid_keys:
        from ..commands.keys import generate_keypair
        key_pair = generate_keypair()
        public_key = key_pair.public_key
        private_key = key_pair.private_key
        click.echo(click.style("✓", fg="green") + " Generated new key pair (existing keys were invalid)")
    else:
        # Use existing keys
        public_key = existing_env['AUTHED_PUBLIC_KEY'].strip('"\' ')
        private_key = existing_env['AUTHED_PRIVATE_KEY'].strip('"\' ')
        click.echo(click.style("→", fg="blue") + " Using existing key pair")
    
    # Only add new values if they don't exist
    new_env = {
        'AUTHED_REGISTRY_URL': '"https://api.getauthed.dev"',
        'AUTHED_PROVIDER_ID': f'"{provider_id}"',
        'AUTHED_PROVIDER_SECRET': f'"{provider_secret}"',
        'AUTHED_AGENT_ID': f'"{agent_id}"',
        'AUTHED_AGENT_SECRET': f'"{agent_secret}"',
        'AUTHED_PRIVATE_KEY': f'"{private_key}"',
        'AUTHED_PUBLIC_KEY': f'"{public_key}"'
    }
    
    # Update values that don't exist or need updating
    for key, value in new_env.items():
        if key not in existing_env or (key in ['AUTHED_PRIVATE_KEY', 'AUTHED_PUBLIC_KEY'] and not has_valid_keys):
            existing_env[key] = value
    
    # Write back to .env file
    with env_file.open('w') as f:
        f.write("# Authed Environment Variables\n\n")
        # Write non-Authed variables first
        for key, value in existing_env.items():
            if not key.startswith('AUTHED_'):
                f.write(f"{key}={value}\n")
        # Write Authed variables
        f.write("\n# Authed Configuration\n")
        for key, value in existing_env.items():
            if key.startswith('AUTHED_'):
                f.write(f"{key}={value}\n")

    # Success output
    click.echo("\n" + "=" * 60)
    click.echo(click.style("✓ Setup Complete!", fg="green", bold=True))
    click.echo("=" * 60)
    click.echo(f"\n{click.style('Provider ID:', bold=True)}     {click.style(provider_id, fg='yellow')}")
    click.echo(f"{click.style('Provider Secret:', bold=True)}  {click.style(provider_secret, fg='yellow')}")
    click.echo(f"{click.style('Agent ID:', bold=True)}     {click.style(agent_id, fg='yellow')}")
    click.echo(f"{click.style('Environment:', bold=True)}  {click.style('.env', fg='blue')} file created with all credentials")
    
    if not provider_id or not provider_secret:
        click.echo(f"\n{click.style('Note:', fg='yellow', bold=True)} This is an unclaimed provider with limited capabilities:")
        click.echo("  - Maximum of 3 agents")
        click.echo("  - No access to logs")
        click.echo("\nTo claim this provider and get full access, run:")
        click.echo(click.style("  authed providers register --name \"Your Name\" --email \"your.email@example.com\"", fg="blue"))
        click.echo("\nThen use the returned provider ID and secret with:")
        click.echo(click.style("  authed init setup --provider-id \"your-id\" --provider-secret \"your-secret\"", fg="blue"))
    
    click.echo(f"\n{click.style('Note:', fg='yellow', bold=True)} Add .env to your .gitignore file") 