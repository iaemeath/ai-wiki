"""Application configuration via environment variables.

AI Gateway 默认指向 localhost:19090（WSL SSH 隧道端口）。
内网环境如需直连 192.168.6.100，设置 AI_GATEWAY_URL 环境变量覆盖。
"""

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    ai_gateway_url: str = field(
        default_factory=lambda: os.getenv(
            "AI_GATEWAY_URL",
            "http://localhost:19090/api/anthropic/v1/messages",
        )
    )
    api_key: str = field(
        default_factory=lambda: os.getenv(
            "AI_API_KEY",
            "caf4bb9dfcec493fa61e7efb2ac37bb3",
        )
    )
    model: str = field(
        default_factory=lambda: os.getenv(
            "AI_MODEL",
            "glm-5.2",
        )
    )
    max_tokens: int = 4096
    temperature: float = 0.7
    request_timeout: int = 120
    max_retries: int = 2
    upload_dir: str = field(
        default_factory=lambda: os.getenv("UPLOAD_DIR", "./uploads")
    )


settings = Settings()
