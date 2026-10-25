import json

MAX_JSON_BYTES = 2 * 1024 * 1024


class JsonInputError(ValueError):
    def __init__(self, message: str, *, line: int | None = None, column: int | None = None):
        super().__init__(message)
        self.line = line
        self.column = column


def parse_json(source: str):
    if not source.strip():
        raise JsonInputError("Escribe o pega un documento JSON.")
    if len(source.encode("utf-8")) > MAX_JSON_BYTES:
        raise JsonInputError("El documento JSON supera el límite de 2 MB.")

    def reject_constant(value: str):
        raise ValueError(f"El valor {value} no está permitido en JSON estándar.")

    try:
        return json.loads(source, parse_constant=reject_constant)
    except json.JSONDecodeError as error:
        raise JsonInputError(
            error.msg,
            line=error.lineno,
            column=error.colno,
        ) from error
    except ValueError as error:
        raise JsonInputError(str(error)) from error


def format_json(source: str, *, indent: int = 2) -> str:
    return json.dumps(parse_json(source), ensure_ascii=False, indent=indent)


def minify_json(source: str) -> str:
    return json.dumps(parse_json(source), ensure_ascii=False, separators=(",", ":"))
