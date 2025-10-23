"""Atomic validation tools."""

import logging

import yaml
from fastmcp import Context

from atomic_red_team_mcp.models import Atomic

logger = logging.getLogger(__name__)


def get_validation_schema() -> dict:
    """Get the JSON schema that defines the structure and requirements for atomic tests.

    This schema provides the complete specification for creating valid atomic tests. It defines
    all fields (required and optional), data types, validation rules, and constraints. Use this
    as a reference when creating or modifying atomic tests to ensure they meet quality standards.

    The schema follows the Atomic Red Team YAML format and is automatically generated from
    the Pydantic models, ensuring it's always in sync with validation rules.

    Returns:
        dict: JSON Schema (Draft 7) containing:
            - definitions: Nested object definitions (Executor, Dependency, etc.)
            - properties: Field definitions with types and constraints
            - required: List of mandatory fields
            - additionalProperties: Whether extra fields are allowed
            - field descriptions: Human-readable explanations for each field

    Schema Structure:
        The schema defines these main sections:
        - name: Test name (required, min 1 character)
        - description: Test explanation (required, min 1 character)
        - supported_platforms: Platform list (required, min 1 platform)
        - executor: Execution method (required, CommandExecutor or ManualExecutor)
        - input_arguments: Parameterized inputs (optional, dict)
        - dependencies: Prerequisites (optional, list)
        - dependency_executor_name: Executor for dependencies (optional)
        - auto_generated_guid: Unique ID (optional, auto-generated)

    Examples:
        # Get the schema
        schema = get_validation_schema()

        # Check required fields
        required_fields = schema['required']
        print(f"Required fields: {required_fields}")

        # View field definitions
        properties = schema['properties']
        print(f"Available fields: {list(properties.keys())}")

        # Check platform options
        platform_enum = schema['definitions']['Platform']['enum']
        print(f"Valid platforms: {platform_enum}")

    Common Use Cases:
        1. **Creating new tests**: Reference required fields and formats
        2. **Understanding validation**: See what rules will be enforced
        3. **Tool development**: Use schema for code generation
        4. **Documentation**: Generate field descriptions automatically

    Notes:
        - Schema is generated from Pydantic models at runtime
        - Always reflects current validation rules
        - Includes custom validators and constraints
        - Follows JSON Schema Draft 7 specification
        - Can be used with JSON Schema validators in any language
        - Do not add comments to the created atomic test
    """
    return Atomic.model_json_schema()


def validate_atomic(yaml_string: str, ctx: Context) -> dict:
    """Validate an atomic test YAML string against the official Atomic Red Team schema.

    This tool checks if your atomic test follows the correct structure and includes all
    required fields. Use this before finalizing any atomic test to ensure it meets
    the quality standards and can be properly parsed by Atomic Red Team tools.

    The validator performs two levels of checks:
    1. **Structural validation**: Ensures all required fields are present and properly typed
    2. **Best practice warnings**: Flags common issues that should be addressed

    Args:
        yaml_string: The complete YAML string of the atomic test to validate.
                    Should include all fields like name, description, supported_platforms,
                    executor, etc. as defined in the schema.

    Returns:
        dict: Validation result containing:
            - valid (bool): Whether the atomic test passes validation
            - message (str): Human-readable success/error message with warnings prominently displayed
            - atomic_name (str): Name of the atomic test (only if valid)
            - supported_platforms (list): Platforms the test supports (only if valid)
            - warnings (list): List of warning messages for best practice violations (only if present)
            - error (str): Detailed error message (only if invalid)

    Validation Warnings:
        The tool will flag these common issues with ⚠️  warnings:
        - Presence of 'auto_generated_guid' field (should be auto-generated, not manually set)
        - Use of echo/print/Write-Host commands (discouraged in test commands)

        Warnings do not cause validation to fail, but should be addressed before finalizing.

    Examples:
        # Valid atomic test
        yaml_str = '''
        name: Test PowerShell Execution
        description: Execute a PowerShell command
        supported_platforms:
          - windows
        executor:
          name: powershell
          command: Get-Process
        '''
        result = validate_atomic(yaml_str, ctx)
        # Returns: {"valid": True, "message": "✅ Atomic test validation successful...", ...}

        # Test with warnings (still valid but needs improvement)
        yaml_str = '''
        name: Test with Echo
        description: Test with echo command
        supported_platforms:
          - linux
        executor:
          name: bash
          command: echo "Hello World"
        '''
        result = validate_atomic(yaml_str, ctx)
        # Returns: {"valid": True, "message": "✅ Atomic test validation successful
        #          ⚠️  WARNING: Avoid echo/print/Write-Host statements...", "warnings": [...]}

        # Invalid atomic test (missing required field)
        yaml_str = '''
        name: Incomplete Test
        description: Missing supported_platforms
        executor:
          name: bash
          command: ls
        '''
        result = validate_atomic(yaml_str, ctx)
        # Returns: {"valid": False, "error": "Validation error: ..."}

    Raises:
        No exceptions are raised - all errors are returned in the result dictionary.

    Notes:
        - Always check the 'valid' field before using the atomic test
        - Address all warnings even if validation succeeds
        - Warnings are displayed with ⚠️  emoji for visibility
        - The 'message' field contains formatted text with warnings prominently shown
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

            # Build success message with warnings prominently displayed
            if validation_warnings:
                warning_text = "\n⚠️  " + "\n⚠️  ".join(validation_warnings)
                message = f"✅ Atomic test validation successful\n{warning_text}\n\nPlease address these warnings before finalizing the atomic test."
            else:
                message = "✅ Atomic test validation successful - no issues found!"

            result = {
                "valid": True,
                "message": message,
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
