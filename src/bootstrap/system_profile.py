from pydantic import BaseModel
from typing import Dict, List, Optional

class HostingSystemProfile(BaseModel):
    tools: Dict[str, str] = {}
    project_type: Optional[str] = None
    build_settings: Dict = {}
    platforms: List[Dict] = []
    credentials: Dict = {}
    inference_config: Dict = {}
    
    class Config:
        # Allow extra fields for flexibility
        extra = "allow"
