"""Atomic validation tools."""

import logging

import yaml
from fastmcp import Context

from atomic_red_team_mcp.models import Atomic

logger = logging.getLogger(__name__)


def get_validation_schema() -> dict:
    """Get the JSON schema that defines the structure and requirements for atomic tests.

    This schema defines all required and optional fields for creating valid atomic tests.
    Use this to understand what fields are needed when creating a new atomic test.
    The schema follows the official Atomic Red Team format.

    Returns:
        A JSON schema dictionary containing field definitions, types, and validation rules.
    """
    return Atomic.model_json_schema()


def validate_atomic(yaml_string: str, ctx: Context) -> dict:
    """Validate an atomic test YAML string against the official Atomic Red Team schema.

    This tool checks if your atomic test follows the correct structure and includes all
    required fields. Use this before finalizing any atomic test to ensure it meets
    the quality standards and can be properly parsed by Atomic Red Team tools.

    Args:
        yaml_string: The complete YAML string of the atomic test to validate.
                    Should include all fields like name, description, supported_platforms,
                    executor, etc. as defined in the schema.

    Returns:
        Dictionary with validation result containing:
        - valid (bool): Whether the atomic test is valid
        - message/error (str): Success message or detailed error information
        - atomic_name (str): Name of the atomic test (if valid)
        - supported_platforms (list): Platforms the test supports (if valid)
    """
    try:
        if not yaml_string or not yaml_string.strip():
            return {"valid": False, "error": "YAML string cannot be empty"}

        # Parse YAML
        try:
            atomic_data = yaml.safe_load(yaml_string)
        except yaml.YAMLError as e:
            return {"valid": False, "error": f"Invalid YAML format: {e}"}

        if not atomic_data:
            return {"valid": False, "error": "YAML parsed to empty data"}

        # Check for common mistakes before validation
        validation_warnings = []

        if "auto_generated_guid" in atomic_data:
            validation_warnings.append(
                "WARNING: Remove 'auto_generated_guid' - system generates this automatically"
            )

        if atomic_data.get("executor", {}).get("command"):
            command = atomic_data["executor"]["command"]
            if (
                "echo" in command.lower()
                or "print" in command.lower()
                or "write-host" in command.lower()
            ):
                validation_warnings.append(
                    "WARNING: Avoid echo/print/Write-Host statements in test commands"
                )

        # Validate with Pydantic model
        try:
            atomic = Atomic(**atomic_data)
            result = {
                "valid": True,
                "message": "Atomic test validation successful",
                "atomic_name": atomic.name,
                "supported_platforms": atomic.supported_platforms,
            }
            if validation_warnings:
                result["warnings"] = validation_warnings
            return result
        except Exception as validation_error:
            return {"valid": False, "error": f"Validation error: {validation_error}"}

    except Exception as e:
        logger.error(f"Unexpected error in validate_atomic: {e}")
        return {"valid": False, "error": f"Unexpected validation error: {e}"}
