"""Offline regressions for transaction confirmation and block-height expiry."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx2
import pytest
from solders.signature import Signature
from solders.transaction_status import TransactionConfirmationStatus

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed, Finalized, Processed
from solana.rpc.core import TransactionExpiredBlockheightExceededError, UnconfirmedTxError
from solana.rpc.models import TxOpts


class _Clock:
    """Advance confirmation time without sleeping or changing asyncio globally."""

    def __init__(self):
        self.now = 0.0

    def time(self):
        """Return the simulated wall-clock time."""
        return self.now

    async def sleep(self, seconds):
        """Advance only this test's clock."""
        self.now += seconds


@pytest.fixture(autouse=True)
def clock(monkeypatch):
    simulated = _Clock()
    monkeypatch.setattr("solana.rpc.async_api.time", simulated.time)
    monkeypatch.setattr("solana.rpc.async_api.asyncio", SimpleNamespace(sleep=simulated.sleep))
    return simulated


def _status_result(confirmation_status):
    status = None
    if confirmation_status is not None:
        status = {
            "slot": 123,
            "confirmations": {"processed": 0, "confirmed": 1, "finalized": None}[confirmation_status],
            "err": None,
            "status": {"Ok": None},
            "confirmationStatus": confirmation_status,
        }
    return {"context": {"slot": 123}, "value": [status]}


def _mock_rpc(monkeypatch, replies):
    """Replace HTTP only; retain SDK request building and response parsing."""
    scripted = iter(replies)

    async def post(endpoint, *, content, headers):
        request = json.loads(content)
        expected = next(scripted, None)
        if expected is None:
            pytest.fail(f"Unexpected extra RPC request: {request['method']}")
        method, result = expected
        assert request["method"] == method
        return httpx2.Response(
            200,
            json={"jsonrpc": "2.0", "id": request["id"], "result": result},
            request=httpx2.Request("POST", endpoint),
        )

    mocked = AsyncMock(side_effect=post)
    monkeypatch.setattr("httpx2.AsyncClient.post", mocked)
    return mocked


@pytest.mark.parametrize(
    ("client_commitment", "statuses", "expected_commitment"),
    [
        (Confirmed, [None, "processed", "confirmed"], "confirmed"),
        (Processed, [None, "processed"], "processed"),
    ],
)
async def test_send_raw_transaction_inherits_client_commitment(
    monkeypatch, client_commitment, statuses, expected_commitment
):
    signature = Signature.default()
    replies = [("sendTransaction", str(signature))]
    replies.extend(("getSignatureStatuses", _status_result(status)) for status in statuses)
    post = _mock_rpc(monkeypatch, replies)

    async with AsyncClient("http://rpc.invalid", commitment=client_commitment) as client:
        result = await client.send_raw_transaction(b"synthetic payload", opts=TxOpts(skip_confirmation=False))

    assert result.value == signature
    request = json.loads(post.await_args_list[0].kwargs["content"])
    assert request["params"][1]["preflightCommitment"] == expected_commitment
    assert post.await_count == len(replies)


@pytest.mark.parametrize(
    ("client_commitment", "override", "statuses", "expected_commitment"),
    [
        (Finalized, Confirmed, [None, "processed", "confirmed"], "confirmed"),
        (Confirmed, Finalized, ["confirmed", "finalized"], "finalized"),
    ],
)
async def test_send_raw_transaction_uses_explicit_commitment(
    monkeypatch, client_commitment, override, statuses, expected_commitment
):
    signature = Signature.default()
    replies = [("sendTransaction", str(signature))]
    replies.extend(("getSignatureStatuses", _status_result(status)) for status in statuses)
    post = _mock_rpc(monkeypatch, replies)
    opts = TxOpts(skip_confirmation=False, preflight_commitment=override)

    async with AsyncClient("http://rpc.invalid", commitment=client_commitment) as client:
        result = await client.send_raw_transaction(b"synthetic payload", opts=opts)

    assert result.value == signature
    request = json.loads(post.await_args_list[0].kwargs["content"])
    assert request["params"][1]["preflightCommitment"] == expected_commitment
    assert post.await_count == len(replies)


async def test_confirm_transaction_reaches_target_before_expiry(monkeypatch):
    post = _mock_rpc(
        monkeypatch,
        [
            ("getBlockHeight", 99),
            ("getSignatureStatuses", _status_result(None)),
            ("getBlockHeight", 100),
            ("getSignatureStatuses", _status_result("confirmed")),
        ],
    )

    async with AsyncClient("http://rpc.invalid", commitment=Confirmed) as client:
        result = await client.confirm_transaction(Signature.default(), last_valid_block_height=100)

    status = result.value[0]
    assert status is not None
    assert status.confirmation_status == TransactionConfirmationStatus.Confirmed
    assert post.await_count == 4


async def test_confirm_transaction_keeps_polling_at_last_valid_height(monkeypatch):
    post = _mock_rpc(
        monkeypatch,
        [
            ("getBlockHeight", 100),
            ("getSignatureStatuses", _status_result(None)),
            ("getBlockHeight", 100),
            ("getSignatureStatuses", _status_result("confirmed")),
        ],
    )

    async with AsyncClient("http://rpc.invalid", commitment=Confirmed) as client:
        result = await client.confirm_transaction(Signature.default(), last_valid_block_height=100)

    status = result.value[0]
    assert status is not None
    assert status.confirmation_status == TransactionConfirmationStatus.Confirmed
    assert post.await_count == 4


@pytest.mark.parametrize("initial_height", [100, 101])
async def test_confirm_transaction_checks_status_after_expiry(monkeypatch, initial_height):
    replies = [("getBlockHeight", initial_height)]
    if initial_height == 100:
        replies.extend(
            [
                ("getSignatureStatuses", _status_result("processed")),
                ("getBlockHeight", 101),
            ]
        )
    replies.append(("getSignatureStatuses", _status_result("confirmed")))
    post = _mock_rpc(monkeypatch, replies)

    async with AsyncClient("http://rpc.invalid", commitment=Confirmed) as client:
        result = await client.confirm_transaction(Signature.default(), last_valid_block_height=100)

    status = result.value[0]
    assert status is not None
    assert status.confirmation_status == TransactionConfirmationStatus.Confirmed
    assert post.await_count == len(replies)


@pytest.mark.parametrize("last_status", [None, "processed"])
async def test_confirm_transaction_raises_when_expired(monkeypatch, last_status):
    post = _mock_rpc(
        monkeypatch,
        [
            ("getBlockHeight", 100),
            ("getSignatureStatuses", _status_result(None)),
            ("getBlockHeight", 101),
            ("getSignatureStatuses", _status_result(last_status)),
        ],
    )

    async with AsyncClient("http://rpc.invalid", commitment=Confirmed) as client:
        with pytest.raises(TransactionExpiredBlockheightExceededError):
            await client.confirm_transaction(Signature.default(), last_valid_block_height=100)

    assert post.await_count == 4


@pytest.mark.parametrize("last_status", [None, "processed"])
async def test_confirm_transaction_times_out_without_reaching_target(monkeypatch, clock, last_status):
    post = _mock_rpc(
        monkeypatch,
        [
            ("getSignatureStatuses", _status_result(None)),
            ("getSignatureStatuses", _status_result(last_status)),
        ],
    )

    async with AsyncClient("http://rpc.invalid", commitment=Confirmed) as client:
        with pytest.raises(UnconfirmedTxError):
            await client.confirm_transaction(Signature.default(), sleep_seconds=45)

    assert post.await_count == 2
    assert clock.now == 90
