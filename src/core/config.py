"""
Configuration Manager - Single Responsibility Principle
Handles all environment configuration loading and validation
"""
import os
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class RivaConfig:
    """Configuration for NVIDIA Riva connection"""
    api_key: str
    server: str
    function_id: str
    
    def __post_init__(self):
        if not self.api_key:
            raise ValueError("API_KEY is required")
        if not self.function_id:
            raise ValueError("RIVA_FUNCTION_ID_WHISPER is required")


class ConfigManager:
    """
    Manages application configuration from .env files
    SRP: Only responsible for loading and validating configuration
    """
    
    def __init__(self, env_path: Optional[Path] = None):
        """
        Initialize config manager
        
        Args:
            env_path: Path to .env file, defaults to project root
        """
        self.env_path = env_path or self._find_env_file()
        self._load_env()
    
    @staticmethod
    def _find_env_file() -> Path:
        """Find .env file in project root"""
        current = Path(__file__).parent
        # Go up to project root (2 levels: core -> src -> root)
        return current.parent.parent / ".env"
    
    def _load_env(self) -> None:
        """Load environment variables from .env file"""
        if not self.env_path.exists():
            raise FileNotFoundError(f".env file not found at {self.env_path}")
        
        with open(self.env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ[key] = value
    
    def get_riva_config(self) -> RivaConfig:
        """
        Get validated Riva configuration
        
        Returns:
            RivaConfig object with validated settings
            
        Raises:
            ValueError: If required config is missing
        """
        return RivaConfig(
            api_key=os.getenv("API_KEY", ""),
            server=os.getenv("RIVA_SERVER", "grpc.nvcf.nvidia.com:443"),
            function_id=os.getenv("RIVA_FUNCTION_ID_WHISPER", "")
        )
    
    def get(self, key: str, default: str = "") -> str:
        """Get environment variable value"""
        return os.getenv(key, default)
