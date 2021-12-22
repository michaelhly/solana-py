# Changelog

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
- Raise OnCurveException instead of generic Exception in `create_program_address` https://github.com/michaelhly/solana-py/pull/128

## Added
- Add `until` parameter to `get_signatures_for_address` https://github.com/michaelhly/solana-py/pull/133
- This changelog.
