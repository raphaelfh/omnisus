"""SQL composition at positions where DuckDB does not accept value binding."""


def quote_identifier(value: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ValueError("SQL identifier must be nonempty and contain no NUL")
    return '"' + value.replace('"', '""') + '"'


def quote_literal(value: str) -> str:
    if not isinstance(value, str) or "\x00" in value:
        raise ValueError("SQL literal must be a string containing no NUL")
    return "'" + value.replace("'", "''") + "'"


def qualified(catalog: str, table: str) -> str:
    return f"{quote_identifier(catalog)}.{quote_identifier(table)}"
