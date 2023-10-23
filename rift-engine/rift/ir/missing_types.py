import os
from dataclasses import dataclass, field
from typing import List, Tuple

import rift.ir.IR as IR
import rift.ir.parser as parser


@dataclass
class MissingType:
    function_declaration: IR.Symbol
    parameters: List[str] = field(default_factory=list)
    return_type: bool = False

    def __str__(self) -> str:
        s = f"Function `{self.function_declaration.name}` is missing type annotations"
        if self.parameters != []:
            if len(self.parameters) == 1:
                s += f" in parameter '{self.parameters[0]}'"
            else:
                s += f" in parameters {self.parameters}"
        if self.return_type:
            if self.parameters != []:
                s += " and"
            s += " in return type"
        return s

    def __repr__(self) -> str:
        return self.__str__()

    def __int__(self) -> int:
        return len(self.parameters) + int(self.return_type)


def functions_missing_types_in_file(file: IR.File) -> List[MissingType]:
    """Find function declarations that are missing types in the parameters or the return type."""
    functions_missing_types: List[MissingType] = []
    function_declarations = file.get_function_declarations()
    for d in function_declarations:
        if d.language not in ["javascript", "ocaml", "python", "rescript", "tsx", "typescript"]:
            continue
        function_kind = d.symbol_kind
        if not isinstance(function_kind, IR.FunctionKind):
            raise Exception(f"Expected function kind, got {function_kind}")
        missing_parameters: List[str] = []
        missing_return = False
        parameters = function_kind.parameters
        if parameters != []:
            if (
                parameters[0].name in ["self", "cls"]
                and d.language == "python"
                and d.scope != ""
            ):
                parameters = parameters[1:]
            missing_parameters.extend(p.name for p in parameters if p.type is None)
        if d.language in ["javascript", "typescript", "tsx"]:
            if function_kind.return_type is None:
                if function_kind.has_return:
                    missing_return = True
        elif d.language in ["ocaml", "python"]:
            if function_kind.return_type is None:
                missing_return = True
        if missing_parameters != [] or missing_return:
            functions_missing_types.append(
                MissingType(
                    function_declaration=d,
                    parameters=missing_parameters,
                    return_type=missing_return,
                )
            )
    return functions_missing_types


def functions_missing_types_in_path(
    root: str, path: str
) -> Tuple[List[MissingType], IR.Code, IR.File]:
    """Given a file path, parse the file and find function declarations that are missing types in the parameters or the return type."""
    full_path = os.path.join(root, path)
    file = IR.File(path)
    language = IR.language_from_file_extension(path)
    missing_types: List[MissingType] = []
    if language is None:
        missing_types = []
        code = IR.Code(b"")
    else:
        with open(full_path, "r", encoding="utf-8") as f:
            code = IR.Code(f.read().encode("utf-8"))
        parser.parse_code_block(file, code, language)
        missing_types = functions_missing_types_in_file(file)
    return (missing_types, code, file)


@dataclass
class FileMissingTypes:
    code: IR.Code  # code of the file
    file: IR.File  # ir of the file
    language: IR.Language  # language of the file
    missing_types: List[MissingType]  # list of missing types in the file


def files_missing_types_in_project(project: IR.Project) -> List[FileMissingTypes]:
    """ "Return a list of files with missing types, and the missing types in each file."""
    files_with_missing_types: List[FileMissingTypes] = []
    for file in project.get_files():
        missing_types = functions_missing_types_in_file(file)
        if missing_types != []:
            decl = missing_types[0].function_declaration
            language = decl.language
            code = decl.code
            files_with_missing_types.append(FileMissingTypes(code, file, language, missing_types))
    return files_with_missing_types
