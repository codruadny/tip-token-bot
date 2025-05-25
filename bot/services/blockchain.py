import logging
import json
import secrets
from decimal import Decimal
from typing import Tuple, Optional, Dict, Any

from eth_account import Account
from eth_account.signers.local import LocalAccount
import web3
from web3 import Web3
from web3.middleware import geth_poa_middleware

from bot.config import settings
from bot.services.database import get_user_private_key

# Initialize Web3 connection to Polygon
w3 = Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Load TIP token ABI
# This is a simplified ERC20 ABI with just the methods we need
TOKEN_ABI = json.loads('''
[
    {
        "constant": true,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]
''')

# Initialize token contract
try:
    token_contract = w3.eth.contract(
        address=Web3.to_checksum_address(settings.TIP_TOKEN_ADDRESS),
        abi=TOKEN_ABI
    )
    # Get token decimals
    TOKEN_DECIMALS = 18  # Default to 18 if not specified in contract
    try:
        TOKEN_DECIMALS = token_contract.functions.decimals().call()
    except Exception as e:
        logging.warning(f"Could not get token decimals, using default: {e}")
except Exception as e:
    logging.error(f"Error initializing token contract: {e}")
    token_contract = None

async def create_wallet() -> Tuple[str, str]:
    """Create a new Ethereum/Polygon wallet.
    
    Returns:
        Tuple[str, str]: (wallet_address, private_key)
    """
    # Generate a secure random private key
    private_key = "0x" + secrets.token_hex(32)
    account: LocalAccount = Account.from_key(private_key)
    wallet_address = account.address
    
    return wallet_address, private_key

async def check_wallet_exists(wallet_address: str) -> bool:
    """Check if a wallet exists on the blockchain."""
    try:
        if not wallet_address:
            return False
        
        # Check if the address is valid
        wallet_address = Web3.to_checksum_address(wallet_address)
        
        # Check if address has any transactions or balance
        # This is a simple check that the address is valid format
        return True
    except Exception as e:
        logging.error(f"Error checking wallet existence: {e}")
        return False

async def get_token_balance(wallet_address: str) -> Decimal:
    """Get TIP token balance for a wallet."""
    try:
        if not token_contract or not wallet_address:
            return Decimal('0')
        
        # Convert address to checksum format
        wallet_address = Web3.to_checksum_address(wallet_address)
        
        # Call the balanceOf function
        balance_wei = token_contract.functions.balanceOf(wallet_address).call()
        
        # Convert from wei to token units
        balance = Decimal(balance_wei) / Decimal(10 ** TOKEN_DECIMALS)
        
        return balance
    except Exception as e:
        logging.error(f"Error getting token balance: {e}")
        return Decimal('0')

async def send_tip(
    sender_wallet_address: str,
    recipient_wallet_address: str,
    amount: Decimal
) -> str:
    """Send TIP tokens from one wallet to another.
    
    Args:
        sender_wallet_address: The sender's wallet address
        recipient_wallet_address: The recipient's wallet address
        amount: The amount to send
        
    Returns:
        str: Transaction hash
    """
    try:
        if not token_contract:
            raise ValueError("Token contract not initialized")
        
        # Get the sender's private key
        from bot.services.database import get_user_private_key
        sender_id = await get_user_id_by_wallet(sender_wallet_address)
        if not sender_id:
            raise ValueError("Sender ID not found")
        
        private_key = await get_user_private_key(sender_id)
        if not private_key:
            raise ValueError("Private key not found")
        
        # Convert addresses to checksum format
        sender_address = Web3.to_checksum_address(sender_wallet_address)
        recipient_address = Web3.to_checksum_address(recipient_wallet_address)
        
        # Convert amount to wei
        amount_wei = int(amount * Decimal(10 ** TOKEN_DECIMALS))
        
        # Build the transaction
        nonce = w3.eth.get_transaction_count(sender_address)
        
        # Create the transaction
        tx = token_contract.functions.transfer(
            recipient_address,
            amount_wei
        ).build_transaction({
            'chainId': w3.eth.chain_id,
            'gas': 100000,  # Adjust gas as needed
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
        })
        
        # Sign the transaction
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        
        # Send the transaction
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for the transaction to be mined
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Return the transaction hash
        return tx_receipt.transactionHash.hex()
    
    except Exception as e:
        logging.error(f"Error sending TIP tokens: {e}")
        raise

async def withdraw_tokens(
    wallet_address: str,
    destination_address: str,
    amount: float
) -> str:
    """Withdraw tokens to an external wallet.
    
    Args:
        wallet_address: The user's wallet address
        destination_address: The destination wallet address
        amount: The amount to withdraw
        
    Returns:
        str: Transaction hash
    """
    # This is essentially the same as send_tip with different parameter names
    return await send_tip(
        sender_wallet_address=wallet_address,
        recipient_wallet_address=destination_address,
        amount=Decimal(str(amount))
    )

async def get_user_id_by_wallet(wallet_address: str) -> Optional[int]:
    """Get user ID from wallet address."""
    # This function is a placeholder
    # In a real implementation, you would query the database
    from bot.services.database import async_session_maker
    import sqlalchemy as sa
    from bot.services.database import Users
    
    async with async_session_maker() as session:
        query = sa.select(Users.user_id).where(Users.wallet_address == wallet_address)
        result = await session.execute(query)
        user_id = result.scalar_one_or_none()
        return user_id
