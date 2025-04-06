"""Key management commands."""

import click
from pathlib import Path
from typing import Optional
from ..utils.keys import KeyPair

@click.group(name='keys')
def group():
    """Manage keys."""
    pass

def generate_keypair():
    """Generate a new key pair and return it."""
    return KeyPair.generate()

@group.command(name='generate')
@click.option('--output', type=click.Path(dir_okay=False), help='Output file path')
@click.option('--no-update-env', is_flag=True, help='Do not update .env file with new keys')
@click.pass_context
def generate_keys(ctx, output: Optional[str], no_update_env: bool):
    """Generate a new keypair."""
    try:
        # Generate new key pair
        keypair = generate_keypair()
        
        if output:
            # Save to file
            output_path = Path(output)
            keypair.save(str(output_path))
            click.echo(click.style("✓", fg="green", bold=True) + f" Keys saved to {click.style(output, fg='blue')}")
            
        if not no_update_env:
            # Update .env file
            from dotenv import load_dotenv
            import os
            from pathlib import Path
            
            # Load existing .env content
            env_file = Path('.env')
            existing_env = {}
            if env_file.exists():
                with env_file.open('r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            existing_env[key.strip()] = value.strip()
            
            # Update keys in .env
            existing_env['AUTHED_PRIVATE_KEY'] = f'"{keypair.private_key}"'
            existing_env['AUTHED_PUBLIC_KEY'] = f'"{keypair.public_key}"'
            
            # Write back to .env file
            with env_file.open('w') as f:
                # Write Authed variables
                f.write("# Authed Configuration\n")
                for key, value in existing_env.items():
                    if key.startswith('AUTHED_'):
                        f.write(f"{key}={value}\n")
                        
            click.echo(click.style("✓", fg="green", bold=True) + " Updated keys in .env file")
            
        if not output and no_update_env:
            # Print to console only if not saving to file and not updating .env
            click.echo("\n" + "=" * 60)
            click.echo(click.style("Generated Keys", fg="blue", bold=True))
            click.echo("=" * 60 + "\n")
            
            click.echo(click.style("Public Key:", bold=True))
            click.echo(click.style(keypair.public_key, fg="bright_black"))
            
            click.echo("\n" + click.style("Private Key:", bold=True) + click.style(" (Keep this secure!)", fg="yellow"))
            click.echo(click.style(keypair.private_key, fg="bright_black"))
            click.echo()
            
    except Exception as e:
        click.echo(click.style("✗ Error: ", fg="red", bold=True) + str(e), err=True)
        ctx.exit(1)

@group.command(name='validate')
@click.option('--key-file', type=click.Path(exists=True), help='Path to key file (if not provided, will check .env)')
@click.pass_context
def validate_keys(ctx, key_file: Optional[str]):
    """Validate a key pair."""
    try:
        if key_file:
            # Load and validate from file
            keypair = KeyPair.from_file(key_file)
        else:
            # Load from .env
            from dotenv import load_dotenv
            import os
            
            # Load environment variables
            load_dotenv()
            
            # Get keys from environment
            private_key = os.getenv("AUTHED_PRIVATE_KEY")
            public_key = os.getenv("AUTHED_PUBLIC_KEY")
            
            if not private_key or not public_key:
                click.echo(click.style("✗", fg="red", bold=True) + " No keys found in .env file")
                ctx.exit(1)
                
            keypair = KeyPair(public_key, private_key)
            
        if keypair.is_valid():
            click.echo(click.style("✓", fg="green", bold=True) + " Key pair is valid")
        else:
            click.echo(click.style("✗", fg="red", bold=True) + " Invalid key pair")
            ctx.exit(1)
    except Exception as e:
        click.echo(click.style("✗ Error: ", fg="red", bold=True) + str(e), err=True)
        ctx.exit(1) 