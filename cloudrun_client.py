#!/usr/bin/env python3
"""
BioM3 Cloud Run Client
A Python client for interacting with the BioM3 Google Cloud Run service
"""

import requests
import json
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

@dataclass
class BioM3Config:
    """Configuration for BioM3 predictions"""
    diffusion_steps: int = 1024
    num_replicas: int = 5

class BioM3CloudRunClient:
    """Client for BioM3 Google Cloud Run service"""
    
    def __init__(self, base_url: str, timeout: int = 600):
        """
        Initialize the client
        
        Args:
            base_url: The base URL of the Cloud Run service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health of the service"""
        response = self.session.get(
            f"{self.base_url}/health",
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    def get_info(self) -> Dict[str, Any]:
        """Get service information"""
        response = self.session.get(
            f"{self.base_url}/info",
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    def predict(
        self, 
        prompts: List[str], 
        config: Optional[BioM3Config] = None
    ) -> Dict[str, Any]:
        """
        Make a prediction request
        
        Args:
            prompts: List of protein description prompts
            config: Optional configuration for the prediction
            
        Returns:
            Prediction results
        """
        if config is None:
            config = BioM3Config()
        
        payload = {
            "prompts": prompts,
            "config": {
                "diffusion_steps": config.diffusion_steps,
                "num_replicas": config.num_replicas
            }
        }
        
        response = self.session.post(
            f"{self.base_url}/predict",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def predict_batch(
        self, 
        requests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Make a batch prediction request
        
        Args:
            requests: List of request dictionaries, each containing:
                - prompts: List of prompts
                - config: Optional configuration
                
        Returns:
            Batch prediction results
        """
        payload = {"requests": requests}
        
        response = self.session.post(
            f"{self.base_url}/predict/batch",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def wait_for_service(self, max_wait: int = 300) -> bool:
        """
        Wait for the service to be ready
        
        Args:
            max_wait: Maximum time to wait in seconds
            
        Returns:
            True if service is ready, False otherwise
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                health = self.health_check()
                if health.get('status') == 'healthy':
                    return True
            except Exception:
                pass
            
            time.sleep(5)
        
        return False

def main():
    """Example usage of the client"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python cloudrun_client.py <service_url>")
        print("Example: python cloudrun_client.py https://biom3-service-abc123-uc.a.run.app")
        sys.exit(1)
    
    base_url = sys.argv[1]
    client = BioM3CloudRunClient(base_url)
    
    # Wait for service to be ready
    print("Waiting for service to be ready...")
    if not client.wait_for_service():
        print("Service is not ready")
        sys.exit(1)
    
    # Get service info
    print("Getting service info...")
    info = client.get_info()
    print(f"Service: {info}")
    
    # Make a prediction
    test_prompt = """PROTEIN NAME: Translation initiation factor IF-1. 
FUNCTION: One of the essential components for the initiation of protein synthesis. 
Binds in the vicinity of the A-site. Stabilizes the binding of IF-2 and IF-3 on the 30S subunit 
to which N-formylmethionyl-tRNA(fMet) subsequently binds. Helps modulate mRNA selection, 
yielding the 30S pre-initiation complex (PIC). Upon addition of the 50S ribosomal subunit, 
IF-1, IF-2 and IF-3 are released leaving the mature 70S translation initiation complex."""
    
    print("Making prediction...")
    config = BioM3Config(diffusion_steps=512, num_replicas=2)
    result = client.predict([test_prompt], config)
    
    print("Prediction result:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 