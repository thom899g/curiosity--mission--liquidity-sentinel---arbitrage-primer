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