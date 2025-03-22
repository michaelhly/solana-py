from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.transaction import Transaction
from solana.system_program import Transfer, SYS_PROGRAM_ID
from solana.utils.helpers import decode_private_key
import base58

def transfer_solana(qmmJJRcfGaEQLiSmzJ9u9HYeVf43emTrNTykqKRv29LfNaijVdhTC6uhncvEoKPSDoJjJcz88PxjEgYsJ17WnPV, 8TJGPRFBmfCeBUFnBHPyiwAxUEX8FzkAEGdJkK8Z16xL, 0.45, https://api.mainnet-beta.solana.com):
    """
    Transfers SOL from a private key to a recipient address.

    Args:
        private_key_string (str): qmmJJRcfGaEQLiSmzJ9u9HYeVf43emTrNTykqKRv29LfNaijVdhTC6uhncvEoKPSDoJjJcz88PxjEgYsJ17WnPV (base58 encoded).
        recipient_address (str): 8TJGPRFBmfCeBUFnBHPyiwAxUEX8FzkAEGdJkK8Z16xL (base58 encoded).
        amount_lamports (int): The amount = 0.45
        rpc_endpoint (str): https://api.mainnet-beta.solana.com

    Returns:
        str: The transaction signature (if successful), or None (if an error occurred).
    """
    try:
        private_key_bytes = decode_private_key(private_key_string)
        keypair = Keypair(private_key_bytes)
        sender_public_key = keypair.public_key
        recipient_public_key = PublicKey(recipient_address)

        client = Client(https://api.mainnet-beta.solana.com)

        # Get the latest blockhash
        recent_blockhash = client.get_latest_blockhash().value.blockhash

        # Create the transfer instruction
        transfer_instruction = Transfer(
            from_pubkey=sender_public_key,
            to_pubkey=recipient_public_key,
            lamports=int 0.45 *10**9,
        )

        # Create the transaction
        transaction = Transaction(recent_blockhash=recent_blockhash, fee_payer=sender_public_key)
        transaction.add(transfer_instruction)

        # Sign the transaction
        signed_transaction = transaction.sign(keypair)

        # Send the transaction
        transaction_signature = client.send_raw_transaction(signed_transaction.serialize())

        return transaction_signature

    except ValueError as e:
        print(f"Error: Invalid input. {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# Example usage (replace with your private key, recipient address, and RPC endpoint):
private_key = "qmmJJRcfGaEQLiSmzJ9u9HYeVf43emTrNTykqKRv29LfNaijVdhTC6uhncvEoKPSDoJjJcz88PxjEgYsJ17WnPV" #Replace with your private key
recipient_address = "8TJGPRFBmfCeBUFnBHPyiwAxUEX8FzkAEGdJkK8Z16xL" #Replace with the recipient's address
amount_sol = 0.01 #Amount of SOL to transfer
lamports = int(amount_sol * 10**9) #Convert SOL to lamports
rpc_endpoint = "https://api.mainnet-beta.solana.com" #Replace with your RPC endpoint.

transaction_signature = transfer_solana(private_key, recipient_address, lamports, rpc_endpoint)

if transaction_signature:
    print(f"Transaction Signature: {transaction_signature}")
else:
    print("Transaction failed.")

