"""Unit tests for the compute budget program."""
import unittest

from solana.compute_budget_program import (
    RequestHeapFrameParams,
    RequestUnitsDeprecatedParams,
    SetComputeUnitLimitParams,
    SetComputeUnitPriceParams,
    SetLoadedAccountsDataSizeLimitParams,
    request_heap_frame,
    request_units_deprecated,
    set_compute_unit_limit,
    set_compute_unit_price,
    set_loaded_accounts_data_size_limit,
)
from solders.instruction import Instruction
from solders.pubkey import Pubkey

COMPUTE_BUDGET_PROGRAM_ID = Pubkey.from_string("ComputeBudget111111111111111111111111111111")


class TestComputeBudgetProgram(unittest.TestCase):
    """Unit tests for the compute budget program."""

    def test_request_units_deprecated_payload(self):
        """Test the payload of the request_units_deprecated instruction."""
        # Create the instruction using the function
        params = RequestUnitsDeprecatedParams(units=10, additional_fee=100, payer=Pubkey([1] * 32))
        instruction = request_units_deprecated(params)
        expected_instruction_index = (0).to_bytes(4, byteorder="little")
        expected_units = (10).to_bytes(4, byteorder="little")
        expected_additional_fee = (100).to_bytes(4, byteorder="little")
        expected_payer = Pubkey([1] * 32)
        expected_data = expected_instruction_index + expected_units + expected_additional_fee

        # Verify that the payload of the instruction matches the expected payload
        self.assertIsInstance(instruction, Instruction)
        self.assertEqual(instruction.program_id, COMPUTE_BUDGET_PROGRAM_ID)
        self.assertEqual(instruction.data, expected_data)
        self.assertEqual(len(instruction.accounts), 1)
        self.assertEqual(instruction.accounts[0].pubkey, expected_payer)
        self.assertEqual(instruction.accounts[0].is_signer, True)
        self.assertEqual(instruction.accounts[0].is_writable, True)

    def test_request_heap_frame_payload(self):
        """Test the payload of the request_heap_frame instruction."""
        # Create the instruction using the function
        params = RequestHeapFrameParams(value=10, payer=Pubkey([1] * 32))
        instruction = request_heap_frame(params)
        expected_instruction_index = (1).to_bytes(4, byteorder="little")
        expected_value = (10).to_bytes(4, byteorder="little")
        expected_payer = Pubkey([1] * 32)
        expected_data = expected_instruction_index + expected_value

        # Verify that the payload of the instruction matches the expected payload
        self.assertIsInstance(instruction, Instruction)
        self.assertEqual(instruction.program_id, COMPUTE_BUDGET_PROGRAM_ID)
        self.assertEqual(instruction.data, expected_data)
        self.assertEqual(len(instruction.accounts), 1)
        self.assertEqual(instruction.accounts[0].pubkey, expected_payer)
        self.assertEqual(instruction.accounts[0].is_signer, True)
        self.assertEqual(instruction.accounts[0].is_writable, True)

    def test_set_compute_unit_limit_payload(self):
        """Test the payload of the set_compute_unit_limit instruction."""
        # Create the instruction using the function
        params = SetComputeUnitLimitParams(value=10, payer=Pubkey([1] * 32))
        instruction = set_compute_unit_limit(params)
        expected_instruction_index = (2).to_bytes(4, byteorder="little")
        expected_value = (10).to_bytes(4, byteorder="little")
        expected_payer = Pubkey([1] * 32)
        expected_data = expected_instruction_index + expected_value

        # Verify that the payload of the instruction matches the expected payload
        self.assertIsInstance(instruction, Instruction)
        self.assertEqual(instruction.program_id, COMPUTE_BUDGET_PROGRAM_ID)
        self.assertEqual(instruction.data, expected_data)
        self.assertEqual(len(instruction.accounts), 1)
        self.assertEqual(instruction.accounts[0].pubkey, expected_payer)
        self.assertEqual(instruction.accounts[0].is_signer, True)
        self.assertEqual(instruction.accounts[0].is_writable, True)

    def test_set_compute_unit_price_payload(self):
        """Test the payload of the set_compute_unit_price instruction."""
        # Create the instruction using the function
        params = SetComputeUnitPriceParams(value=10, payer=Pubkey([1] * 32))
        instruction = set_compute_unit_price(params)
        expected_instruction_index = (3).to_bytes(4, byteorder="little")
        expected_value = (10).to_bytes(8, byteorder="little")
        expected_payer = Pubkey([1] * 32)
        expected_data = expected_instruction_index + expected_value

        # Verify that the payload of the instruction matches the expected payload
        self.assertIsInstance(instruction, Instruction)
        self.assertEqual(instruction.program_id, COMPUTE_BUDGET_PROGRAM_ID)
        self.assertEqual(instruction.data, expected_data)
        self.assertEqual(len(instruction.accounts), 1)
        self.assertEqual(instruction.accounts[0].pubkey, expected_payer)
        self.assertEqual(instruction.accounts[0].is_signer, True)
        self.assertEqual(instruction.accounts[0].is_writable, True)

    def test_set_loaded_accounts_data_size_limit(self):
        """Test the payload of the set_loaded_accounts_data_size_limit instruction."""
        # Create the instruction using the function
        params = SetLoadedAccountsDataSizeLimitParams(value=10, payer=Pubkey([1] * 32))
        instruction = set_loaded_accounts_data_size_limit(params)
        expected_instruction_index = (4).to_bytes(4, byteorder="little")
        expected_value = (10).to_bytes(4, byteorder="little")
        expected_payer = Pubkey([1] * 32)
        expected_data = expected_instruction_index + expected_value

        # Verify that the payload of the instruction matches the expected payload
        self.assertIsInstance(instruction, Instruction)
        self.assertEqual(instruction.program_id, COMPUTE_BUDGET_PROGRAM_ID)
        self.assertEqual(instruction.data, expected_data)
        self.assertEqual(len(instruction.accounts), 1)
        self.assertEqual(instruction.accounts[0].pubkey, expected_payer)
        self.assertEqual(instruction.accounts[0].is_signer, True)
        self.assertEqual(instruction.accounts[0].is_writable, True)
