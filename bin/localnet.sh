#!/usr/bin/env bash
# Manage a local solana-test-validator instance for development.

set -e

VALIDATOR_ARGS=(
    --reset
    --rpc-pubsub-enable-vote-subscription
    #--rpc-pubsub-enable-block-subscription  # Removed: causes clap panic in Agave 4.0.0
    --quiet
)
LEDGER_DIR="test-ledger"

usage() {
  exitcode=0
  if [[ -n "$1" ]]; then
    exitcode=1
    echo "Error: $*"
  fi
  cat <<EOF
usage: $0 [update|up|down|logs]

Operate a local solana-test-validator

 update   - Update the Agave toolchain via agave-install update.
 up       - Start solana-test-validator in the background.
 down     - Stop a running solana-test-validator.
 logs     - Display the validator log (pass -f to follow).

EOF
  exit $exitcode
}

[[ -n $1 ]] || usage
cmd="$1"
shift

case $cmd in
update)
  (
    set -x
    agave-install update
  )
  ;;
up)
  (
    set -x
    solana-test-validator "${VALIDATOR_ARGS[@]}" &
  )
  # Poll until the validator is healthy (up to 60 s)
  echo -n "Waiting for validator"
  for i in $(seq 1 60); do
    if curl -sf \
        -X POST -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}' \
        http://127.0.0.1:8899 > /dev/null 2>&1; then
      echo " ready (${i}s)"
      break
    fi
    echo -n "."
    sleep 1
  done
  ;;
down)
  (
    set -x
    pkill -f "solana-test-validator" || true
  )
  ;;
logs)
  log_file="${LEDGER_DIR}/validator.log"
  if [[ -n "$1" && "$1" = "-f" ]]; then
    tail -f "$log_file"
  else
    cat "$log_file" 2>/dev/null || echo "No validator log found at ${log_file}"
  fi
  ;;
*)
  usage "Unknown command: $cmd"
esac

exit 0
