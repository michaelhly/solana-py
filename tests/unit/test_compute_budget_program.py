from spl.compute_budget.instructions import (
    RequestUnitsParams,
    RequestHeapFrameParams,
    SetComputeUnitLimitParams,
    SetComputeUnitPriceParams,
    decode_request_units,
    decode_request_heap_frame,
    decode_set_compute_unit_limit,
    decode_set_compute_unit_price,
    request_units,
    request_heap_frame,
    set_compute_unit_limit,
    set_compute_unit_price,
)


def test_request_units():
    """Test creating a request_units instruction."""
    params = RequestUnitsParams(units=150_000, additional_fee=0)
    assert decode_request_units(request_units(params)) == params


def test_request_heap_frame():
    """Test creating a request_heap_frame instruction."""
    params = RequestHeapFrameParams(bytes=32_000 * 1024)
    assert decode_request_heap_frame(request_heap_frame(params)) == params


def test_set_compute_unit_limit():
    """Test creating a set_compute_unit_limit instruction."""
    params = SetComputeUnitLimitParams(units=150_000)
    assert decode_set_compute_unit_limit(set_compute_unit_limit(params)) == params


def test_set_compute_unit_price():
    """Test creating a set_compute_unit_price instruction."""
    params = SetComputeUnitPriceParams(micro_lamports=1500)
    assert decode_set_compute_unit_price(set_compute_unit_price(params)) == params
