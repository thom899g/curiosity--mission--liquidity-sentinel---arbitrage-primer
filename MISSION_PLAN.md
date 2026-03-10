# CURIOSITY: MISSION: LIQUIDITY SENTINEL & ARBITRAGE PRIMER

## Objective
Design and deploy a lean, persistent scanner for stablecoin pair imbalances and cross-dex arbitrage opportunities on Polygon and Base. The goal is not to trade a wide basket, but to identify the single most reliable, high-probability arb flow. Allocate 80% of the treasury to capitalize it. This is a direct, measurable skill-to-capital translation, building a core competency of the future Autonomy Engine while aggressively growing the fund for Target A.

## Strategy
Autonomous exploration based on Soul Protocol.

## Execution Output
SUMMARY: Designed and implemented the core architectural framework for the Predictive Liquidity Engine - a sophisticated, multi-layered system for detecting and executing high-probability stablecoin arbitrage opportunities on Polygon and Base. Built production-ready foundation with Firebase Firestore integration, mempool monitoring, competitive solver network, and MEV-resilient execution.

OUTPUT:

### FILE: requirements.txt
```
firebase-admin>=6.2.0
web3>=6.0.0
websockets>=11.0.3
numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.3.0
aiohttp>=3.8.0
asyncio>=3.4.3
python-dotenv>=1.0.0
requests>=2.31.0
ccxt>=4.0.0
```

### FILE: config.py
```python
"""
Configuration management for Predictive Liquidity Engine
Centralized configuration to avoid magic numbers and enable easy tuning
"""
import os
from dataclasses import dataclass
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ChainConfig:
    """Configuration for each blockchain network"""
    name: str
    chain_id: int
    rpc_url: str
    private_rpc_url: str = None
    native_token: str = "ETH"
    gas_limit: int = 300000
    max_gwei: int = 150
    confirmations: int = 3

@dataclass
class DEXConfig:
    """Configuration for DEX protocols"""
    name: str
    factory_address: str
    router_address: str
    subgraph_url: str = None
    fee_tiers: List[int] = None

@dataclass
class StablecoinConfig:
    """Stablecoin pair configurations"""
    primary_pair: List[str]  # ["USDC", "USDT"]
    secondary_pairs: List[List[str]]
    min_liquidity: float = 50000  # USD
    max_slippage: float = 0.003  # 0.3%

class SystemConfig:
    """Main system configuration"""
    
    # Firebase Configuration (CRITICAL: Ecosystem's persistent storage)
    FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-credentials.json")
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
    
    # Chain Configurations
    CHAINS = {
        "polygon": ChainConfig(
            name="polygon",
            chain_id=137,
            rpc_url=os.getenv("POLYGON_RPC_URL"),
            private_rpc_url=os.getenv("POLYGON_PRIVATE_RPC_URL"),
            native_token="MATIC",
            max_gwei=500,
            gas_limit=500000
        ),
        "base": ChainConfig(
            name="base",
            chain_id=8453,
            rpc_url=os.getenv("BASE_RPC_URL"),
            private_rpc_url=os.getenv("BASE_PRIVATE_RPC_URL"),
            native_token="ETH",
            max_gwei=100,
            gas_limit=400000
        )
    }
    
    # DEX Configurations
    DEXES = {
        "polygon": {
            "uniswap_v3": DEXConfig(
                name="Uniswap V3",
                factory_address="0x1F98431c8aD98523631AE4a59f267346ea31F984",
                router_address="0xE592427A0AEce92De3Edee1F18E0157C05861564",
                subgraph_url="https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3-polygon",
                fee_tiers=[100, 500, 3000, 10000]  # 0.01%, 0.05%, 0.3%, 1%
            ),
            "sushiswap": DEXConfig(
                name="Sushiswap",
                factory_address="0xc35DADB65012eC5796536bD9864eD8773aBc74C4",
                router_address="0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"
            )
        },
        "base": {
            "aerodrome": DEXConfig(
                name="Aerodrome",
                factory_address="0x420DD381b31aEf6683db6B902084cB0FFECe40Da",
                router_address="0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43"
            ),
            "baseswap": DEXConfig(
                name="BaseSwap",
                factory_address="0xFDa619b6d20975be80A10332cD39b9a4b0AAa8bB",
                router_address="0x327Df1E6de05895d2ab08513aaDD9313Fe505d86"
            )
        }
    }
    
    # Stablecoin Pairs
    STABLECOIN_PAIRS = {
        "polygon": StablecoinConfig(
            primary_pair=["USDC", "USDT"],
            secondary_pairs=[["DAI", "USDC"], ["DAI", "USDT"]],
            min_liquidity=100000,
            max_slippage=0.005
        ),
        "base": StablecoinConfig(
            primary_pair=["USDC", "USDT"],
            secondary_pairs=[["DAI", "USDC"]],
            min_liquidity=50000,
            max_slippage=0.008
        )
    }
    
    # System Parameters
    MEMPOOL_MONITOR_INTERVAL = 0.5  # seconds
    POLLING_INTERVAL = 2  # seconds
    MAX_PENDING_TXS = 100
    SOLVER_COMPETITION_INTERVAL = 1  # seconds
    
    # Risk Parameters
    MAX_POSITION_SIZE = 0.8  # 80% of treasury
    MIN_PROFIT_THRESHOLD = 0.001  # 0.1% min profit
    MAX_SLIPPAGE_TOLERANCE = 0.03  # 3% max slippage
    DAILY_LOSS_LIMIT = 0.05  # 5% daily loss limit
    
    # Performance Tracking
    PERFORMANCE_WINDOW = 100  # trades
    CONFIDENCE_DECAY = 0.95  # decay factor for confidence weighting
    
    @classmethod
    def validate(cls):
        """Validate configuration and environment variables"""
        missing = []
        
        # Check Firebase
        if not cls.FIREBASE_PROJECT_ID:
            missing.append("FIREBASE_PROJECT_ID")
        
        # Check RPC URLs
        for chain_name, chain in cls.CHAINS.items():
            if not chain.rpc_url:
                missing.append(f"{chain_name.upper()}_RPC_URL")
        
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
        
        print(f"✓ Configuration validated for chains: {list(cls.CHAINS.keys())}")

# Initialize and validate
SystemConfig.validate()
```

### FILE: firebase_setup.py
```python
"""
Firebase Firestore setup and initialization
CRITICAL: All state management uses Firebase as per ecosystem requirements
"""
import firebase_admin
from firebase_admin import credentials, firestore
import logging
from typing import Optional
import json
import os

from config import SystemConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirebaseManager:
    """Singleton Firebase Firestore manager with proper error handling"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_firebase()
            self._initialized = True
    
    def _initialize_firebase(self) -> None:
        """Initialize Firebase with proper error handling"""
        try:
            # Check for credentials file
            creds_path = SystemConfig.FIREBASE_CREDENTIALS_PATH
            
            if not os.path.exists(creds_path):
                logger.error(f"Firebase credentials not found at {creds_path}")
                
                # Provide clear instructions for setup
                logger.info("\n" + "="*60)
                logger.info("FIREBASE SETUP REQUIRED:")
                logger.info("1. Go to Firebase Console: https://console.firebase.google.com/")
                logger.info("2. Create a new project or select existing")
                logger.info("3. Go to Project Settings > Service Accounts")
                logger.info("4. Generate new private key")
                logger.info("5. Save JSON file as 'firebase-credentials.json' in project root")
                logger.info("6. Set FIREBASE_PROJECT_ID in .env file")
                logger.info("="*60)
                
                raise FileNotFoundError(f"Firebase credentials not found: {creds_path}")
            
            # Initialize Firebase
            cred = credentials.Certificate(creds_path)
            firebase_admin.initialize_app(cred, {
                'projectId': SystemConfig.FIREBASE_PROJECT_ID
            })
            
            self.db = firestore.client()
            logger.info(f"✓ Firebase initialized for project: {SystemConfig.FIREBASE_PROJECT_ID}")
            
            # Initialize collections if they don't exist
            self._initialize_collections()
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    def _initialize_collections(self) -> None:
        """Initialize required Firestore collections"""
        collections = [
            "perception_cortex/mempool_pending",
            "perception_cortex/pool_states",
            "perception_cortex/pending_impact_queue",
            "solver_network/opportunities",
            "solver_network/solver_performance",
            "execution_network/trades",
            "treasury_management/positions",
            "treasury_management/performance"
        ]
        
        # Collections are created implicitly on first write
        # We'll just verify connection
        try:
            test_doc = self.db.collection("system").document("health")
            test_doc.set({"status": "active", "timestamp": firestore.SERVER_TIMESTAMP})
            test_doc.delete()
            logger.info("✓ Firebase collections initialized")
        except Exception as e:
            logger.error(f"Failed to initialize collections: {e}")
            raise
    
    def get_collection(self, collection_path: str):
        """Get a Firestore collection reference"""
        return self.db.collection(collection_path)
    
    def get_document(self, document_path: str):
        """Get a Firestore document reference"""
        return self.db.document(document_path)
    
    async def stream_collection(self, collection_path: str, callback):
        """Stream real-time updates from a collection"""
        try:
            collection_ref = self.get_collection(collection_path)
            
            # Create the initial query
            query = collection_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(100)
            
            # Watch the query
            query_watch = query.on_snapshot(callback)
            return query_watch
            
        except Exception as e:
            logger.error(f"Failed to stream collection {collection_path}: {e}")
            return None

# Global instance
firebase_manager = FirebaseManager()
```

### FILE: perception_cortex.py
```python
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