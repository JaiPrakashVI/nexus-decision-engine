"""
NEXUS Centralized Configuration
Loaded from environment variables or .env file with rigorous type checking.
"""

from pathlib import Path
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General Environment
    nexus_env: str = Field(default="development", alias="NEXUS_ENV")
    nexus_log_level: str = Field(default="INFO", alias="NEXUS_LOG_LEVEL")
    nexus_secret_key: str = Field(
        default="nexus-insecure-secret-key-change-in-prod",
        alias="NEXUS_SECRET_KEY"
    )

    # Secure Gateway
    gateway_host: str = Field(default="0.0.0.0", alias="GATEWAY_HOST")
    gateway_port: int = Field(default=8443, alias="GATEWAY_PORT")
    gateway_tls_enabled: bool = Field(default=False, alias="GATEWAY_TLS_ENABLED")
    gateway_mtls_enabled: bool = Field(default=False, alias="GATEWAY_MTLS_ENABLED")
    gateway_cert_file: str = Field(default="certs/gateway.crt", alias="GATEWAY_CERT_FILE")
    gateway_key_file: str = Field(default="certs/gateway.key", alias="GATEWAY_KEY_FILE")
    gateway_ca_file: str = Field(default="certs/ca.crt", alias="GATEWAY_CA_FILE")
    gateway_rate_limit_per_sec: int = Field(default=5000, alias="GATEWAY_RATE_LIMIT_PER_SEC")

    # Redis & Streaming
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: str | None = Field(default=None, alias="REDIS_PASSWORD")
    redis_stream_name: str = Field(default="nexus:telemetry:stream", alias="REDIS_STREAM_NAME")
    redis_consumer_group: str = Field(default="nexus:consumers:telemetry", alias="REDIS_CONSUMER_GROUP")
    redis_dlq_stream: str = Field(default="nexus:telemetry:dlq", alias="REDIS_DLQ_STREAM")

    # Database
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="nexus_db", alias="POSTGRES_DB")
    postgres_user: str = Field(default="nexus_user", alias="POSTGRES_USER")
    postgres_password: str = Field(default="nexus_secure_password", alias="POSTGRES_PASSWORD")
    database_url: str = Field(
        default="postgresql+asyncpg://nexus_user:nexus_secure_password@localhost:5432/nexus_db",
        alias="DATABASE_URL"
    )
    sqlite_fallback_url: str = Field(
        default="sqlite+aiosqlite:///nexus_local.db",
        alias="SQLITE_FALLBACK_URL"
    )

    # Digital Twin API
    twin_api_host: str = Field(default="0.0.0.0", alias="TWIN_API_HOST")
    twin_api_port: int = Field(default=8000, alias="TWIN_API_PORT")

    # Local AI / LLM (Ollama)
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.2", alias="OLLAMA_MODEL")
    llm_timeout_seconds: int = Field(default=15, alias="LLM_TIMEOUT_SECONDS")
    llm_mock_fallback: bool = Field(default=True, alias="LLM_MOCK_FALLBACK")

    # Sensor Simulator
    simulator_num_devices: int = Field(default=50, alias="SIMULATOR_NUM_DEVICES")
    simulator_frequency_hz: float = Field(default=1.0, alias="SIMULATOR_FREQUENCY_HZ")
    simulator_random_seed: int = Field(default=42, alias="SIMULATOR_RANDOM_SEED")
    simulator_fault_loss_rate: float = Field(default=0.0, alias="SIMULATOR_FAULT_LOSS_RATE")
    simulator_fault_delay_ms: int = Field(default=0, alias="SIMULATOR_FAULT_DELAY_MS")
    simulator_fault_noise_level: Literal["none", "low", "medium", "high"] = Field(
        default="low", alias="SIMULATOR_FAULT_NOISE_LEVEL"
    )
    simulator_out_of_order: bool = Field(default=False, alias="SIMULATOR_OUT_OF_ORDER")
    simulator_duplicates: bool = Field(default=False, alias="SIMULATOR_DUPLICATES")


settings = Settings()
