import os

class Config:
    """Configuration settings for the application."""
    
    # Database configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")
    
    # Other configurations
    DEBUG = os.getenv("DEBUG", "False") == "True"
    SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
    
    # API settings
    API_VERSION = "v1"
    API_PREFIX = f"/api/{API_VERSION}"

    # Supabase Auth — JWT secret for verifying user tokens on the backend
    # Found in: Supabase Dashboard → Project Settings → API → JWT Secret
    SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")

    # Supabase project URL and anon key (public — used by frontend build)
    SUPABASE_URL      = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")