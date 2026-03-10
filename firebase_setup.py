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