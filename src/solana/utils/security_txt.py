"""Utils for security.txt."""

HEADER = "=======BEGIN SECURITY.TXT V1=======\0"
FOOTER = "=======END SECURITY.TXT V1=======\0"

VALID_KEYS = [
    "name",
    "project_url",
    "contacts",
    "policy",
    "preferred_languages",
    "source_code",
    "encryption",
    "auditors",
    "acknowledgements",
    "expiry",
]

REQUIRED_KEYS = ["name", "project_url", "contacts", "policy"]


def parse(data: bytes):
    """Parse and extract security.txt section from the data section of the compiled program.

    :param data: Program data from the ProgramAccount
    """
    assert isinstance(data, bytes), "data provided in parse(data) must be bytes, found: {}".format(type(data))

    s_idx = data.find(bytes(HEADER, "utf-8"))
    e_idx = data.find(bytes(FOOTER, "utf-8"))

    assert s_idx > 0 and e_idx > 0 and e_idx - s_idx > 0, "Program doesn't have security.txt section"

    content_arr = data[s_idx + len(HEADER) : e_idx]
    content_da = [[]]

    for char in content_arr:
        if char == 0:
            content_da.append([])
        else:
            content_da[len(content_da) - 1].append(chr(char))

    content_da.pop()

    for idx in range(len(content_da)):
        content_da[idx] = "".join(content_da[idx])

    content_dict = {}
    prev_key = None

    for idx in content_da:
        if any(idx == x for x in VALID_KEYS):
            content_dict.update({str(idx): None})
            prev_key = idx
        else:
            content_dict.update({str(prev_key): idx})
            prev_key = None

    for key in REQUIRED_KEYS:
        assert any(
            key == _key for _key in content_dict.keys()
        ), "Some required fields {} are missing in the security.txt section".format(REQUIRED_KEYS)

    return content_dict
