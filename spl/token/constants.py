"""SPL token constants."""

from solana.publickey import PublicKey

TOKEN_PROGRAM_ID: PublicKey = PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
"""Public key that identifies the SPL token program."""

WRAPPED_SOL_MINT: PublicKey = PublicKey("So11111111111111111111111111111111111111112")
"""Public key of the "Native Mint" for wrapping SOL to SPL token.

The Token Program can be used to wrap native SOL. Doing so allows native SOL to be treated like any
other Token program token type and can be useful when being called from other programs that interact
with the Token Program's interface.
"""
