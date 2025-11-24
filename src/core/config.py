"""
Configuration Manager - Singleton Pattern Implementation
Garantiza que la clase tenga una única instancia y proporciona un punto de acceso global.
Según diseño especificado en docs/design_patterns.md
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
    Singleton Pattern - Configuration Manager
    
    Propósito: Garantizar que una clase tenga una única instancia y proporcionar
    un punto de acceso global a ella.
    
    La configuración de la aplicación debe ser consistente y centralizada.
    Solo existe una instancia de ConfigManager en toda la aplicación.
    """
    
    _instance: Optional['ConfigManager'] = None
    _initialized: bool = False
    
    def __new__(cls, env_path: Optional[Path] = None):
        """
        Sobrescribe __new__ para controlar la creación de instancias.
        Solo crea una nueva instancia si no existe una.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, env_path: Optional[Path] = None):
        """
        Constructor que solo se ejecuta una vez.
        Las llamadas subsecuentes no reinicializan la instancia.
        
        Args:
            env_path: Path to .env file, defaults to project root
        """
        # Solo inicializar una vez
        if self._initialized:
            return
            
        self.env_path = env_path or self._find_env_file()
        self._load_env()
        self._initialized = True
    
    @classmethod
    def get_instance(cls, env_path: Optional[Path] = None) -> 'ConfigManager':
        """
        Método estático para obtener la única instancia de ConfigManager.
        Este es el punto de acceso global al Singleton.
        
        Args:
            env_path: Path to .env file (solo se usa en la primera llamada)
            
        Returns:
            La única instancia de ConfigManager
        """
        if cls._instance is None:
            cls._instance = cls(env_path)
        return cls._instance
    
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
    
    @classmethod
    def reset_instance(cls):
        """
        Resetear la instancia del Singleton (útil para testing).
        NO usar en código de producción.
        """
        cls._instance = None
        cls._initialized = False
