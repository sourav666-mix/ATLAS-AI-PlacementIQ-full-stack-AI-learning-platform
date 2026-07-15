# backend/app/config.py
"""
Application configuration.

Loads every secret and setting from the environment (backend/.env) using
pydantic-settings. Import the singleton `settings` anywhere in the app:

    from app.config import settings
    settings.DATABASE_URL

Nothing else in the codebase should read os.environ directly.
"""
from functools import lru_cache
from typing import Annotated, List

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    # --- Core ---------------------------------------------------------------
    APP_NAME: str = "ATLAS AI 2.0"
    ENVIRONMENT: str = "development"          # development | production
    DEBUG: bool = True

    # --- Database (MySQL, async aiomysql driver) ----------------------------
    # Format: mysql+aiomysql://USER:PASSWORD@HOST:PORT/DBNAME
    DATABASE_URL: str = "mysql+aiomysql://atlas:6772souravjana@localhost:3306/atlasai"

    # --- Redis (optional cache / rate-limit) --------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Auth / JWT ---------------------------------------------------------
    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7   # 7 days

    # --- Google Sign-In (OAuth client ID from Google Cloud Console) ---------
    # The frontend uses the same ID as VITE_GOOGLE_CLIENT_ID; blank disables
    # the /auth/google endpoint.
    GOOGLE_CLIENT_ID: str = ""

    # --- Free AI providers (rotation happens in ai_provider_router) ---------
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    CEREBRAS_API_KEY: str = ""
    SAMBANOVA_API_KEY: str = ""

    # --- AI provider models + routing ---------------------------------------
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GEMINI_MODEL: str = "gemini-flash-lite-latest"
    CEREBRAS_MODEL: str = "llama-3.3-70b"
    SAMBANOVA_MODEL: str = "Meta-Llama-3.3-70B-Instruct"
    CEREBRAS_BASE_URL: str = "https://api.cerebras.ai/v1"
    SAMBANOVA_BASE_URL: str = "https://api.sambanova.ai/v1"
    # Order the gateway tries providers in (first configured one wins).
    AI_PROVIDER_ORDER: List[str] = ["groq", "gemini", "cerebras", "sambanova"]
    AI_REQUEST_TIMEOUT: int = 30

    # --- Voice (Type-B surfaces only) ---------------------------------------
    CHATTERBOX_TTS_URL: str = ""             # self-hosted primary TTS
    ELEVENLABS_API_KEY: str = ""             # fallback voice only

    # --- v12 SkillPath Engine 3.0 -------------------------------------------
    SKILLPATH_TOTAL_QUESTIONS: int = 25
    PRACTICE_AUTOGEN_ENABLED: bool = True      # generate-once-cache-forever for the practice bank
    SKILLPATH_V3_ENABLED: bool = True          # feature flag for the domain-first flow

    # --- v12 Live Lab Pro ---------------------------------------------
    COPILOT_DAILY_CAP: int = 40        # cache-MISS copilot calls per day
    LABPRO_MAX_CELLS: int = 200
    LABPRO_MAX_WS_FILES: int = 200

    # --- v12 seeding pipeline ------------------------------------------
    SEED_CONCURRENCY: int = 3       # parallel subtopics (sequential within)

    # --- CORS (student app + admin panel) -----------------------------------
    CORS_ORIGINS: Annotated[List[str], NoDecode] = [
        "http://localhost:5173",             # student frontend (Vite)
        "http://localhost:5174",             # admin panel (Vite)
    ]

    @field_validator("CORS_ORIGINS", "AI_PROVIDER_ORDER", mode="before")
    @classmethod
    def _split_csv(cls, v):
        # Allow these list settings in .env as a comma-separated string too.
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    # --- Local storage (generated résumé PDFs, etc.) ------------------------
    STORAGE_DIR: str = "storage"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so the .env file is parsed exactly once."""
    return Settings()


# Import-and-use singleton.
settings = get_settings()



# --- AI Interview Studio: voice (v10 additions) --------------------------
CHATTERBOX_TTS_URL: str = ""          # e.g. http://tts.internal:8020/speak
TTS_FALLBACK: str = ""                # "elevenlabs" to enable the fallback
ELEVENLABS_API_KEY: str = ""
ELEVENLABS_VOICE_ID: str = ""         # optional; blank = default voice


PYODIDE_CDN: str = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/"
COLAB_TEMPLATE_URL: str = ""
COPILOT_DAILY_CAP: int = 30
BYO_KEY_ENABLED: bool = False

# --- v12 SkillPath Reforged ---------------------------------------
V12_QUESTIONS_PER_SUBTOPIC: int = 25      # locked (10 basic/10 med/5 adv)
V12_MASTERY_CORRECT_THRESHOLD: int = 20   # >=20/25 correct = mastered
V12_CORRECT_SCORE_THRESHOLD: int = 60     # attempt correct at score>=60
V12_ANALYZE_MAX_ANSWER_CHARS: int = 20000