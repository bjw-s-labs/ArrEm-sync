"""Error handling utilities for ArrEm-sync."""

import click
from pydantic import ValidationError


def format_validation_error(error: ValidationError) -> str:
    """Convert a pydantic ValidationError into a human-readable error message.

    Args:
        error: The ValidationError to format

    Returns:
        A human-readable error message string
    """
    if not error.errors():
        return "Configuration validation failed"

    messages = []
    for err in error.errors():
        field_name = ".".join(str(loc) for loc in err["loc"]) if err["loc"] else "unknown field"

        # Extract the actual error message, removing pydantic technical details
        msg = err["msg"]
        if msg.startswith("Value error, "):
            msg = msg[13:]  # Remove "Value error, " prefix
        elif msg.startswith("String should "):
            msg = f"'{field_name}' {msg.lower()}"
        elif "Field required" in msg:
            msg = f"'{field_name}' is required"
        elif "Input should be" in msg:
            msg = f"'{field_name}' should be {msg.split('Input should be ')[1]}"

        # Format the final message
        if field_name != "unknown field":
            messages.append(f"❌ {field_name}: {msg}")
        else:
            messages.append(f"❌ {msg}")

    return "\n".join(messages)


def format_missing_env_vars(missing_vars: list[str]) -> str:
    """Format missing environment variables into a helpful error message.

    Args:
        missing_vars: List of missing environment variable names

    Returns:
        A formatted error message with suggestions
    """
    if not missing_vars:
        return ""

    formatted_vars = [f"ARREM_{var.upper()}" for var in missing_vars]

    message_parts = [
        "❌ Missing required configuration:",
        "",
        "The following environment variables are required:",
    ]

    for var in formatted_vars:
        message_parts.append(f"  • {var}")

    # Add example configuration
    message_parts.extend(["", "💡 Example configuration:", ""])

    # Add example export commands for each missing variable
    example_values = {
        "ARREM_ARR_TYPE": "radarr",
        "ARREM_ARR_URL": "http://localhost:7878",
        "ARREM_ARR_API_KEY": "your_radarr_api_key",
        "ARREM_EMBY_URL": "http://localhost:8096",
        "ARREM_EMBY_API_KEY": "your_emby_api_key",
    }

    for var in formatted_vars:
        example_value = example_values.get(var, "your_value_here")
        message_parts.append(f"export {var}={example_value}")

    message_parts.extend(["", "🔗 See the README.md for complete configuration details."])

    return "\n".join(message_parts)


def handle_config_error(e: Exception) -> None:
    """Handle configuration errors with user-friendly messages.

    Args:
        e: The exception to handle
    """
    if isinstance(e, ValidationError):
        error_msg = format_validation_error(e)
        click.echo("\n📋 Configuration Error:", err=True)
        click.echo(error_msg, err=True)

        # Check if this looks like missing required fields
        missing_fields = []
        for err in e.errors():
            if "Field required" in err.get("msg", ""):
                field_name = ".".join(str(loc) for loc in err["loc"]) if err["loc"] else ""
                if field_name:
                    missing_fields.append(field_name)

        if missing_fields:
            click.echo("", err=True)
            missing_msg = format_missing_env_vars(missing_fields)
            click.echo(missing_msg, err=True)
    else:
        # Handle other configuration errors
        click.echo(f"\n❌ Configuration Error: {e}", err=True)
        click.echo("\n💡 Check your environment variables and configuration.", err=True)
