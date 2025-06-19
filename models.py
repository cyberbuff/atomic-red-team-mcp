# Modified file from https://github.com/redcanaryco/atomic-red-team/blob/master/atomic_red_team/models.py

import re
from functools import reduce
from typing import Dict, List, Literal, Optional, Union
from uuid import UUID

from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    IPvAnyAddress,
    StrictFloat,
    StringConstraints,
    conlist,
    constr,
    field_serializer,
    field_validator,
    model_validator,
)
from pydantic_core import PydanticCustomError
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import Annotated, TypedDict

InputArgType = Literal["url", "string", "float", "integer", "path"]
Platform = Literal[
    "windows",
    "macos",
    "linux",
    "office-365",
    "azure-ad",
    "google-workspace",
    "saas",
    "iaas",
    "containers",
    "iaas:gcp",
    "iaas:azure",
    "iaas:aws",
    "esxi",
]
ExecutorType = Literal["manual", "powershell", "sh", "bash", "command_prompt"]
DomainName = Annotated[
    str,
    StringConstraints(
        pattern=r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$"
    ),
]

AttackTechniqueID = Annotated[
    str, StringConstraints(pattern=r"T\d{4}(?:\.\d{3})?", min_length=5)
]


def extract_mustached_keys(commands: List[Optional[str]]) -> List[str]:
    result = []
    for command in commands:
        if command:
            matches = re.finditer(r"#{(.*?)}", command, re.MULTILINE)
            keys = [list(i.groups()) for i in matches]
            keys = list(reduce(lambda x, y: x + y, keys, []))
            result.extend(keys)
    return list(set(result))


def get_supported_platform(platform: Platform):
    platforms = {
        "macos": "macOS",
        "office-365": "Office 365",
        "windows": "Windows",
        "linux": "Linux",
        "azure-ad": "Azure AD",
        "iaas": "IaaS",
        "saas": "SaaS",
        "iaas:aws": "AWS",
        "iaas:azure": "Azure",
        "iaas:gcp": "GCP",
        "google-workspace": "Google Workspace",
        "containers": "Containers",
        "esxi": "ESXi",
    }
    return platforms[platform]


def get_language(executor: ExecutorType):
    if executor == "command_prompt":
        return "cmd"
    elif executor == "manual":
        return ""
    return executor


class BaseArgument(TypedDict):
    description: str


class UrlArg(BaseArgument):
    default: Optional[DomainName | AnyUrl | IPvAnyAddress]
    type: Literal["url", "Url"]

    @field_serializer("default")
    def serialize_url(self, value):
        return str(value)


class StringArg(BaseArgument):
    default: Optional[str]
    type: Literal["string", "path", "String", "Path"]


class IntArg(BaseArgument):
    default: Optional[int]
    type: Literal["integer", "Integer"]


class FloatArg(BaseArgument):
    default: Optional[StrictFloat]
    type: Literal["float", "Float"]


Argument = Annotated[
    Union[FloatArg, IntArg, UrlArg, StringArg], Field(discriminator="type")
]


class Executor(BaseModel):
    name: ExecutorType
    elevation_required: bool = Field(
        default=False,
        description="Set to true if using sudo or admin privileges. Required when using sudo commands on Linux/macOS.",
    )


class ManualExecutor(Executor):
    name: Literal["manual"]
    steps: str = Field(
        ...,
        min_length=10,
        description="Manual steps to execute the test. Should be clear and comprehensive, explaining what the test does and why.",
    )


class CommandExecutor(Executor):
    name: Literal["powershell", "sh", "bash", "command_prompt"]
    command: constr(min_length=1) = Field(
        ...,
        description="Command to execute the test. Use parameterized inputs (#{variable}) instead of hardcoded values. Do NOT include echo commands or print statements.",
    )
    cleanup_command: Optional[str] = Field(
        default=None,
        description="Command to restore the system to its original state after test execution. Always include cleanup commands when needed.",
    )


class Dependency(BaseModel):
    description: constr(min_length=1) = Field(
        ...,
        description="Clear description of the dependency requirement. Document any required tools, permissions, or system configurations.",
    )
    prereq_command: constr(min_length=1) = Field(
        ...,
        description="Command to check if the prerequisite is met. Keep external dependencies to a minimum for better portability and reliability.",
    )
    get_prereq_command: Optional[str] = Field(
        default=None,
        description="Command to install or set up the prerequisite if it's not already met.",
    )


class Atomic(BaseModel):
    model_config = ConfigDict(
        validate_default=True, extra="forbid", validate_assignment=True
    )

    name: constr(min_length=1) = Field(
        ...,
        description="Clear, descriptive name that indicates the technique being tested. Should mirror actual adversary behavior and real-world attack patterns.",
    )
    description: constr(min_length=1) = Field(
        ...,
        description="Comprehensive description explaining what the test does and why. Include external references if you used any online resources. Keep it concise and to the point.",
    )
    supported_platforms: conlist(Platform, min_length=1) = Field(
        ...,
        description="List of platforms where this test can be executed. Choose platforms appropriate for the technique being tested.",
    )
    executor: Union[ManualExecutor, CommandExecutor] = Field(
        ...,
        discriminator="name",
        description="Execution method for the test. Ensure tests are fully functional and can be executed without errors.",
    )
    dependencies: Optional[List[Dependency]] = Field(
        default=[],
        description="List of prerequisites required for the test. If there are no prerequisites, remove this section entirely.",
    )
    input_arguments: Dict[constr(min_length=2, pattern=r"^[\w_-]+$"), Argument] = Field(
        default={},
        description="Parameterized inputs for flexibility and reusability. Use these instead of hardcoded values in commands. If there are no input arguments, remove this section entirely.",
    )
    dependency_executor_name: ExecutorType = Field(
        default="manual",
        description="Executor type for dependency commands. Remove this section if there are no dependencies.",
    )
    auto_generated_guid: Optional[UUID] = Field(
        default=None,
        description="Unique identifier for the atomic test. This will be auto-generated. Do not provide this value when creating the atomic test.",
    )

    @classmethod
    def extract_mustached_keys(cls, value: dict) -> List[str]:
        commands = []
        executor = value.get("executor")
        if isinstance(executor, CommandExecutor):
            commands = [executor.command, executor.cleanup_command]
        if isinstance(executor, ManualExecutor):
            commands = [executor.steps]
        for d in value.get("dependencies") or []:
            commands.extend([d.get_prereq_command, d.prereq_command])
        return extract_mustached_keys(commands)

    @field_validator("dependency_executor_name", mode="before")  # noqa
    @classmethod
    def validate_dep_executor(cls, v, info: ValidationInfo):
        if v is None:
            raise PydanticCustomError(
                "empty_dependency_executor_name",
                "'dependency_executor_name' shouldn't be empty. Provide a valid value ['manual','powershell', 'sh', "
                "'bash', 'command_prompt'] or remove the key from YAML",
                {"loc": ["dependency_executor_name"], "input": None},
            )
        if info.data.get("dependencies") is None:
            raise PydanticCustomError(
                "empty_dependencies",
                "'dependency_executor_name' is provided but there are no dependencies. This field can be removed if there are no dependencies.",
                {"loc": ["dependency_executor_name"], "input": None},
            )
        return v

    @model_validator(mode="after")
    def validate_elevation_required(self):
        if (
            ("linux" in self.supported_platforms or "macos" in self.supported_platforms)
            and not self.executor.elevation_required
            and isinstance(self.executor, CommandExecutor)
        ):
            commands = [self.executor.command]
            if self.executor.cleanup_command:
                commands.append(self.executor.cleanup_command)

            if any(["sudo" in cmd for cmd in commands]):
                raise PydanticCustomError(
                    "elevation_required_but_not_provided",
                    "'elevation_required' shouldn't be empty/false. Since `sudo` is used, set `elevation_required` to true`",
                    {
                        "loc": ["executor", "elevation_required"],
                        "input": self.executor.elevation_required,
                    },
                )
        return self

    @field_validator("input_arguments", mode="before")  # noqa
    @classmethod
    def validate(cls, v, info: ValidationInfo):
        if v is None:
            raise PydanticCustomError(
                "empty_input_arguments",
                "'input_arguments' shouldn't be empty. Provide a valid value or remove the key from YAML",
                {"loc": ["input_arguments"], "input": None},
            )

        atomic = info.data
        keys = cls.extract_mustached_keys(atomic)
        for key, _value in v.items():
            if key not in keys:
                raise PydanticCustomError(
                    "unused_input_argument",
                    f"'{key}' is not used in any of the commands",
                    {"loc": ["input_arguments", key], "input": key},
                )
            else:
                keys.remove(key)

        if len(keys) > 0:
            for x in keys:
                raise PydanticCustomError(
                    "missing_input_argument",
                    f"{x} is not defined in input_arguments",
                    {"loc": ["input_arguments"]},
                )
        return v


class MetaAtomic(Atomic):
    technique_id: Optional[AttackTechniqueID] = None
    technique_name: Optional[str] = None


class Technique(BaseModel):
    attack_technique: AttackTechniqueID = Field(
        ...,
        description="MITRE ATT&CK technique ID (e.g., T1234 or T1234.001) that this atomic test implements.",
    )
    display_name: str = Field(
        ...,
        min_length=5,
        description="Human-readable name of the MITRE ATT&CK technique. Should be descriptive and match the official technique name.",
    )
    atomic_tests: List[MetaAtomic] = Field(
        min_length=1,
        description="Collection of atomic tests that implement this technique. Each test should mirror actual adversary behavior and real-world attack patterns.",
    )

    def model_post_init(self, __context) -> None:
        for index in range(len(self.atomic_tests)):
            self.atomic_tests[index].technique_id = self.attack_technique
            self.atomic_tests[index].technique_name = self.display_name

