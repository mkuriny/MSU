from pydantic import BaseModel, Field
from typing import Optional, Literal

class SSHCredentialCreate(BaseModel):
    access_type: Literal["ssh", "api"]
    host: str
    port: int = 22
    username: str
    password: Optional[str] = None
    private_key: Optional[str] = None
    comment: Optional[str] = None