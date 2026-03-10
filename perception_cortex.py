"""
Perception Cortex: Real-time data ingestion layer with mempool monitoring
Core Innovation: Predictive execution through mempool analysis
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import aiohttp
from web3 import Web3
from web3.exceptions import TransactionNotFound
import websockets

from config import SystemConfig
from firebase_setup import firebase_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MempoolMonitor:
    """Monitor pending transactions with filtering for DEX interactions"""
    
    def __init__(self, chain_config):
        self.chain_config = chain_config
        self.web3_public = Web3(Web3.HTTPProvider(chain_config.rpc_url))
        self.web3_private = None
        
        if chain_config.private_rpc_url:
            self.web3_private = Web3(Web3.HTTPProvider(chain_config.private_rpc_url))
        
        self.pending_txs = {}
        self.dex_addresses = self._load_dex_addresses()
        
    def _load_dex_addresses(self) -> List[str]:
        """Load DEX contract addresses from config"""
        addresses = []
        chain_dexes = SystemConfig.DEXES.get(self.chain_config.name, {})
        
        for dex_name, dex_config in chain_dexes.items():
            addresses.append(dex_config.factory_address.lower())
            addresses.append(dex_config.router_address.lower())
        
        return addresses
    
    async def start_mempool_stream(self) -> None:
        """Start streaming pending transactions via WebSocket"""
        try:
            # Use private RPC if available for better mempool access
            ws_url = self.chain_config.private_rpc_url.replace("https", "wss") if self.chain_config.private_rpc_url else None
            
            if not ws_url:
                logger.warning(f"No WebSocket URL for {self.chain_config.name}, falling back to polling")
                asyncio.create_task(self._poll_mempool())
                return
            
            async with websockets.connect(ws_url) as websocket:
                # Subscribe to new pending transactions
                subscribe_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_subscribe",
                    "params": ["newPendingTransactions"]
                }
                
                await websocket.send(json.dumps(subscribe_request))
                response = await websocket.recv()
                logger.info(f"Subscribed to mempool on {self.chain_config.name}")
                
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    if 'params' in data and 'result' in data['params']:
                        tx_hash = data['params']['result']
                        await self._process_pending_tx(tx_hash)
                        
        except Exception as e:
            logger.error(f"Mempool stream error on {self.chain_config.name}: {e}")
            # Fallback to polling
            asyncio.create_task(self._poll_mempool())
    
    async def _poll_mempool(self) -> None:
        """Fallback polling method for mempool"""
        logger.info(f"Starting mempool polling for {self.chain_config.name}")
        
        while True:
            try:
                # Get pending transactions (limited to avoid overload)
                pending = self.web3_public.eth.get_block('pending', full_transactions=True)
                
                for tx in pending.transactions:
                    if tx.hash not in self.pending_txs:
                        await self._process_pending_tx(tx.hash.hex())
                
                await asyncio.sleep(SystemConfig.MEMPOOL_MONITOR_INTERVAL)
                
            except Exception as e:
                logger.error(f"Mempool polling error: {e}")
                await asyncio.sleep(5)
    
    async def _process_pending_tx(self, tx_hash: str) -> None:
        """Process a single pending transaction"""
        try:
            # Get transaction details
            web3_to_use = self.web3_private if self.web3_private else self.web3_public
            tx = web3_to_use.eth.get_transaction(tx_hash)
            
            # Check if it interacts with DEX addresses
            to_address = tx.get('to', '').lower() if tx.get('to') else ''
            
            if to_address in self.dex_addresses or self._is_dex_calldata(tx.get('input', '')):
                # Store in Firestore
                tx_data = {
                    'hash': tx_hash,
                    'from': tx['from'].lower(),
                    'to': to_address,
                    'value': str(tx['value']),
                    'gasPrice': str(tx.get('gasPrice', 0)),
                    'gas': str(tx.get('gas', 0)),
                    'input': tx.get('input', ''),
                    'nonce': tx['nonce'],
                    'chain': self.chain_config.name,
                    'timestamp': firestore.SERVER_TIMESTAMP
                }
                
                # Store in Firebase
                doc_ref = firebase_manager.get_collection("perception_cortex/mempool_pending").document(tx_hash)
                doc_ref.set(tx_data, merge=True)
                
                # Keep local cache
                self.pending_txs[tx_hash] = tx_data
                
                #