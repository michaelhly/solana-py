# Changelog

## [0.23.0] - 2022-03-03

## Added
- Implement `__hash__` for PublicKey  ([#187](https://github.com/michaelhly/solana-py/pull/202))

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
