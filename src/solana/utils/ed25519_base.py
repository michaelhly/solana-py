"""Curve25519/ed25519 helpers.

Sourced from https://github.com/warner/python-pure25519/blob/master/pure25519/basic.py
"""
# pylint: disable = invalid-name
Q = 2 ** 255 - 19
L = 2 ** 252 + 27742317777372353535851937790883648493


def _inv(x):
    return pow(x, Q - 2, Q)


d = -121665 * _inv(121666)
I = pow(2, (Q - 1) // 4, Q)  # noqa: E741


def _xrecover(y):
    xx = (y * y - 1) * _inv(d * y * y + 1)
    x = pow(xx, (Q + 3) // 8, Q)
    if (x * x - xx) % Q != 0:
        x = (x * I) % Q
    if x % 2 != 0:
        x = Q - x
    return x


def _isoncurve(P):
    x = P[0]
    y = P[1]
    return (-x * x + y * y - 1 - d * x * x * y * y) % Q == 0


class NotOnCurve(Exception):
    """Raised when point fall off the curve."""


def _decodepoint(unclamped: int):
    clamp = (1 << 255) - 1
    y = unclamped & clamp  # clear MSB
    x = _xrecover(y)
    if bool(x & 1) != bool(unclamped & (1 << 255)):
        x = Q - x
    P = [x, y]
    if not _isoncurve(P):
        raise NotOnCurve("decoding point that is not on curve")
    return P


def is_on_curve(s: bytes) -> bool:
    """Verify the bytes s is a valid point on curve or not."""
    unclamped = int.from_bytes(s, byteorder="little")
    try:
        _ = _decodepoint(unclamped)
    except NotOnCurve:
        return False
    else:
        return True
