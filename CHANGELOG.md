# Changelog


## [0.18.3] - 2021-11-20

### Fixed

- Always return the tx signature when sending transaction (the async method was returning signature status if we were confirming the tx)

### Changed
- Raise OnCurveException instead of generic Exception in `create_program_address` https://github.com/michaelhly/solana-py/pull/128

## Added
- Add `until` parameter to `get_signatures_for_address` https://github.com/michaelhly/solana-py/pull/133
- This changelog.