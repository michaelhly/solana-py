"""Utils for security.txt."""

from dataclasses import dataclass, fields
from typing import Any

HEADER = "=======BEGIN SECURITY.TXT V1=======\0"
"""Header of the security.txt."""
FOOTER = "=======END SECURITY.TXT V1=======\0"
"""Footer of the security.txt."""


@dataclass
class SecurityTxt:
    """Security txt data."""

    # pylint: disable=too-many-instance-attributes
    name: str
    project_url: str
    contacts: str
    policy: str
    preferred_languages: str | None = None
    source_code: str | None = None
    encryption: str | None = None
    auditors: str | None = None
    acknowledgements: str | None = None
    expiry: str | None = None


# Build the set of known field names from the dataclass definition
_KNOWN_KEYS = {f.name for f in fields(SecurityTxt)}


class NoSecurityTxtFoundError(Exception):
    """Raise when security text is not found."""


def parse_security_txt(data: bytes) -> SecurityTxt:
    """Parse and extract security.txt section from the data section of the compiled program.

    Args:
        data: Program data in bytes from the ProgramAccount.

    Returns:
        The Security Txt.
    """
    if not isinstance(data, bytes):
        raise TypeError(
            f"data provided in parse(data) must be bytes, found: {type(data)}"
        )

    header_bytes = HEADER.encode("utf-8")
    footer_bytes = FOOTER.encode("utf-8")
    s_idx = data.find(header_bytes)
    if s_idx == -1:
        raise NoSecurityTxtFoundError("Program doesn't have security.txt section")

    e_idx = data.find(footer_bytes, s_idx + len(header_bytes))
    content_bytes = data[s_idx + len(header_bytes) : e_idx]

    # Split by null byte, convert each segment to string, strip trailing empty
    parts = [segment.decode("utf-8") for segment in content_bytes.split(b"\x00")]
    if parts and parts[-1] == "":
        parts.pop()

    # Walk key-value pairs: field names alternate with values
    content_dict: dict[str, Any] = {}
    for i, part in enumerate(parts):
        if part in _KNOWN_KEYS:
            if i + 1 < len(parts):
                content_dict[part] = parts[i + 1]

    try:
        security_txt = SecurityTxt(**content_dict)
    except TypeError as err:
        raise err
    return security_txt
