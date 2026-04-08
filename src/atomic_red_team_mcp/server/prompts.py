"""MCP prompt templates for common workflows."""

from fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Register all prompt templates with the MCP server."""

    @mcp.prompt(tags={"creation"})
    def create_atomic_test(technique_id: str, platform: str = "linux") -> str:
        """Generate a prompt for creating an atomic test for a MITRE ATT&CK technique.

        Args:
            technique_id: MITRE ATT&CK technique ID (e.g., T1059.001)
            platform: Target platform (windows, linux, macos)
        """
        return f"""Create an Atomic Red Team test for MITRE ATT&CK technique {technique_id} targeting {platform}.

Follow this workflow:
1. Call `get_validation_schema` to understand the required YAML structure
2. Research the technique and design a realistic test that mirrors adversary behavior
3. Write the atomic test YAML with proper name, description, executor, and cleanup
4. Call `validate_atomic` with your YAML to check for errors or warnings
5. Fix any issues and re-validate until clean
6. Call `server_info` to find the data directory, then save the test

Requirements:
- Use input_arguments for any hardcoded values
- Include cleanup_command to restore the system
- Set elevation_required appropriately
- Do NOT include auto_generated_guid
- Do NOT use echo/print in commands"""

    @mcp.prompt(tags={"query"})
    def find_tests_for_technique(technique_id: str) -> str:
        """Generate a prompt for finding atomic tests for a specific technique.

        Args:
            technique_id: MITRE ATT&CK technique ID (e.g., T1059.001)
        """
        return f"""Find all Atomic Red Team tests for MITRE ATT&CK technique {technique_id}.

Call `query_atomics` with:
- query: "{technique_id}"
- technique_id: "{technique_id}"

Then summarize the results, including:
- Number of tests found
- Supported platforms for each test
- What each test does (from name and description)
- Any input arguments required"""
