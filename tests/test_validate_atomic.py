"""Tests for validate_atomic tool."""

from unittest.mock import Mock

import pytest

from atomic_red_team_mcp.models import ValidationOutput
from atomic_red_team_mcp.tools.validate_atomic import validate_atomic


@pytest.fixture
def mock_context():
    """Create a mock context."""
    return Mock()


def test_validate_valid_atomic(mock_context):
    """Test validation of a valid atomic test."""
    yaml_string = """
name: Test PowerShell Execution
description: Execute a PowerShell command
supported_platforms:
  - windows
executor:
  name: powershell
  command: Get-Process
"""

    result = validate_atomic(yaml_string, mock_context)

    assert isinstance(result, ValidationOutput)
    assert result.valid
    assert result.atomic_name == "Test PowerShell Execution"
    assert "windows" in result.supported_platforms


def test_validate_with_warnings(mock_context):
    """Test validation with warnings."""
    yaml_string = """
name: Test with Echo
description: Test with echo command
supported_platforms:
  - linux
executor:
  name: bash
  command: echo "Hello World"
"""

    result = validate_atomic(yaml_string, mock_context)

    assert result.valid
    assert result.warnings is not None
    assert len(result.warnings) > 0
    assert any("echo" in warning.lower() for warning in result.warnings)


def test_validate_with_auto_guid_warning(mock_context):
    """Test validation warns about auto_generated_guid."""
    yaml_string = """
name: Test with GUID
description: Test with auto_generated_guid
supported_platforms:
  - windows
executor:
  name: powershell
  command: Get-Process
auto_generated_guid: a8c41029-8d2a-4661-ab83-e5104c1cb667
"""

    result = validate_atomic(yaml_string, mock_context)

    assert result.valid
    assert result.warnings is not None
    assert any("auto_generated_guid" in warning for warning in result.warnings)


def test_validate_empty_yaml(mock_context):
    """Test validation of empty YAML."""
    result = validate_atomic("", mock_context)

    assert not result.valid
    assert "empty" in result.error.lower()


def test_validate_invalid_yaml(mock_context):
    """Test validation of invalid YAML syntax."""
    yaml_string = """
name: Test
description: [invalid yaml syntax: }
"""

    result = validate_atomic(yaml_string, mock_context)

    assert not result.valid
    assert "yaml" in result.error.lower()


def test_validate_missing_required_fields(mock_context):
    """Test validation with missing required fields."""
    yaml_string = """
name: Incomplete Test
description: Missing supported_platforms
executor:
  name: bash
  command: ls
"""

    result = validate_atomic(yaml_string, mock_context)

    assert not result.valid
    assert result.error is not None


def test_validate_invalid_platform(mock_context):
    """Test validation with invalid platform."""
    yaml_string = """
name: Invalid Platform Test
description: Test with invalid platform
supported_platforms:
  - invalid_platform
executor:
  name: bash
  command: ls
"""

    result = validate_atomic(yaml_string, mock_context)

    assert not result.valid


def test_validate_incompatible_executor(mock_context):
    """Test validation of incompatible executor for platform."""
    yaml_string = """
name: Incompatible Executor
description: Bash on Windows
supported_platforms:
  - windows
executor:
  name: bash
  command: ls
"""

    result = validate_atomic(yaml_string, mock_context)

    assert not result.valid
    assert "incompatible" in result.error.lower()


def test_validate_with_input_arguments(mock_context):
    """Test validation with input arguments."""
    yaml_string = """
name: Test with Input Arguments
description: Test with parameterized inputs
supported_platforms:
  - windows
executor:
  name: powershell
  command: |
    Get-Process -Name #{process_name}
input_arguments:
  process_name:
    description: Name of the process
    type: string
    default: powershell
"""

    result = validate_atomic(yaml_string, mock_context)

    assert result.valid


def test_validate_missing_input_argument(mock_context):
    """Test validation with missing input argument definition."""
    yaml_string = """
name: Missing Input Arg
description: Command uses undefined variable
supported_platforms:
  - windows
executor:
  name: powershell
  command: |
    Get-Process -Name #{undefined_var}
"""

    result = validate_atomic(yaml_string, mock_context)

    assert not result.valid
    assert "undefined_var" in result.error
