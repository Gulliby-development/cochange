from collections.abc import Sequence


def quote(value: str) -> str:
    """Return a double-quoted display-safe representation of a value."""
    return '"' + "".join(char if "!" <= char <= "~" else "?" for char in value) + '"'


def percent(part: int, whole: int) -> str:
    """Format part / whole as a percentage rounded half up to one decimal."""
    if whole <= 0:
        return "0.0%"

    tenths = (2 * part * 1000 + whole) // (2 * whole)
    return f"{tenths // 10}.{tenths % 10}%"


def table(rows: Sequence[Sequence[object]], align: Sequence[bool]) -> str:
    """Render rows as a padded table; True entries in align mark right columns."""
    if not rows:
        return ""

    column_count = max(len(row) for row in rows)
    widths = [
        max((len(str(row[index])) for row in rows if index < len(row)), default=0)
        for index in range(column_count)
    ]
    rendered_rows = []

    for row in rows:
        cells = []
        for index, value in enumerate(row):
            cell = str(value)
            if index < column_count - 1:
                if index < len(align) and align[index]:
                    cell = cell.rjust(widths[index])
                else:
                    cell = cell.ljust(widths[index])
            cells.append(cell)
        rendered_rows.append("  ".join(cells))

    return "\n".join(rendered_rows)
