# Changelog

## [0.23.1] - 2022-03-31

## Fixed

Fix str seed input for sp.create_account_with_seed ([#206](https://github.com/michaelhly/solana-py/pull/206))

## Changed

Update `jsonrpcserver` dependency ([#205](https://github.com/michaelhly/solana-py/pull/205))

## [0.23.0] - 2022-03-06

## Added

- Implement `__hash__` for PublicKey ([#202](https://github.com/michaelhly/solana-py/pull/202))

## [0.22.0] - 2022-03-03

## Added

- Add default RPC client commitment to token client [#187]
- Add cluster_api_url function [#193]
- Add getBlockHeight RPC method [#200]

### Changed

- Replace base58 library with based58 [#192]

## [0.21.0] - 2022-01-13

### Fixed

- Make `program_ids` list deterministic in `compile_message` ([#164](https://github.com/michaelhly/solana-py/pull/164))

### Changed

- Throw more specific Exception in API client on failure to retrieve RPC result ([#166](https://github.com/michaelhly/solana-py/pull/166/files))

## Added

- Add max_retries option to sendTransaction and commitment option to get_transaction ([#165](https://github.com/michaelhly/solana-py/pull/165))
- Add a partial support for vote program ([#167](https://github.com/michaelhly/solana-py/pull/167))

## [0.20.0] - 2021-12-30

### Changed

- Make keypair hashable and move setters out of property functions ([#158](https://github.com/michaelhly/solana-py/pull/158))

## Added

- Optional Commitment parameter to `get_signatures_for_address` ([#157](https://github.com/michaelhly/solana-py/pull/157))
- More SYSVAR constants ([#159](https://github.com/michaelhly/solana-py/pull/159))

## [0.19.1] - 2021-12-21

## Added

- Custom solana-py RPC error handling ([#152](https://github.com/michaelhly/solana-py/pull/152))

## [0.19.0] - 2021-12-02

## Added

- Websockets support ([#144](https://github.com/michaelhly/solana-py/pull/144))
- New client functions ([#139](https://github.com/michaelhly/solana-py/pull/139))
- A timeout param for `Client` and `AsyncClient` ([#146](https://github.com/michaelhly/solana-py/pull/146))

## [0.18.3] - 2021-11-20

### Fixed

- Always return the tx signature when sending transaction (the async method was returning signature status if we were confirming the tx)

### Changed

- Raise OnCurveException instead of generic Exception in `create_program_address`
  ([#128](https://github.com/michaelhly/solana-py/pull/128))

## Added

- Add `until` parameter to `get_signatures_for_address` ([#133](https://github.com/michaelhly/solana-py/pull/133))
- This changelog.

## [0.15.0] - 2021-9-26

### Changed

- To reduce RPC calls from fetching recent blockhashes - allow user-supplied blockhash to `.send_transaction` and dependent fns, and introduce an opt-in blockhash cache ([#102](https://github.com/michaelhly/solana-py/pull/102))
- ReadTheDocs theme and doc changes ([#103](https://github.com/michaelhly/solana-py/pull/103))
- Deprecate `Account` and replace with `Keypair` ([#105](https://github.com/michaelhly/solana-py/pull/105))

### Added

- Implement methods for `solana.system_program` similar to [solana-web3](https://github.com/solana-labs/solana-web3.js/blob/44f32d9857e765dd26647ffd33b0ea0927f73b7a/src/system-program.ts#L743-L771): `create_account_with_seed`, `decode_create_account_with_seed` ([#101](https://github.com/michaelhly/solana-py/pull/101))
- Support for [getMultipleAccounts RPC method](https://docs.solana.com/developing/clients/jsonrpc-api#getmultipleaccounts) ([#103](https://github.com/michaelhly/solana-py/pull/103))
- Support for `solana.rpc.api` methods `get_token_largest_accounts`, `get_token_supply` ([#104](https://github.com/michaelhly/solana-py/pull/104))

## [0.12.1] - 2021-8-28

### Fixed

- Issue with importing `Token` from spl.token.client` ([#91](https://github.com/michaelhly/solana-py/pull/91))
- Packaging fixes ([#85](https://github.com/michaelhly/solana-py/pull/85))

### Added

- Missing `spl.token.async_client` methods - `create_multisig`, `get_mint_info`, `get_account_info`, `approve`, `revoke`, `burn`, `close_account`, `freeze_account`, `thaw_account`, `transfer_checked`, `approve_checked`, `mint_to_checked`, `burn_checked`. Missing `spl.token.client` methods - `create_multisig`, `get_mint_info`, `get_account_info`, `approve`, `revoke`, set_authority`, close_account`, `freeze_account`, `thaw_account`, `transfer_checked`, `approve_checked`, `mint_to_checked`, `burn_checked` ([#89](https://github.com/michaelhly/solana-py/pull/89))

## [0.11.1] - 2021-8-4

### Fixed

- Valid instruction can contain no keys ([#70](https://github.com/michaelhly/solana-py/pull/70))

### Changed

- Commitment levels - deprecated `max`, `root`, `singleGossip`, `recent` and added `processed`, `confirmed`, `finalized` ([#82](https://github.com/michaelhly/solana-py/pull/82))

### Added

- Allocate instruction for system program - `solana.system_program.decode_allocate`, `solana.system_program.decode_allocate_with_seed`, `solana.system_program.allocate` ([#79](https://github.com/michaelhly/solana-py/pull/79))
- Async support - `AsyncClient` and `AsyncToken` classes, refactors sync code, httpx dependency ([#83](https://github.com/michaelhly/solana-py/pull/83))

## [0.10.0] - 2021-7-6

### Fixed

- Valid instruction can contain no keys ([#70](https://github.com/michaelhly/solana-py/pull/70))

### Changed

- Pipenv update
- Use new devnet api endpoint, deprecate `solana.rpc.api.getConfirmedSignaturesForAddress2` and use `solana.rpc.api.getSignaturesForAddress` instead ([#77](https://github.com/michaelhly/solana-py/pull/77))

### Added

- `spl.client.token.set_authority` ([#73](https://github.com/michaelhly/solana-py/pull/73/files))
- `spl.client.token.create_wrapped_native_account` ([#74](https://github.com/michaelhly/solana-py/pull/74))

## [0.9.1] - 2021-5-31

### Fixed

- Integration tests

## Added

- `solana.publickey.create_with_seed` ([#69](https://github.com/michaelhly/solana-py/pull/69))

## [0.9.0] - 2021-5-26

### Fixed

- Mismatch in annotation ([#63](https://github.com/michaelhly/solana-py/pull/63))
- unused imports

### Changed

- Use python-pure25519 curve check util instead of crypto_core_ed25519_is_valid_point

## Added ([#66](https://github.com/michaelhly/solana-py/pull/66))

- python-pure25519 curve check util
- `spl.token.client.create_associated_token_account`
- `spl.token.instructions.get_associated_token_address`
- `spl.token.instructions.create_associated_token_account`
- ATA constant `ASSOCIATED_TOKEN_PROGRAM_ID`
