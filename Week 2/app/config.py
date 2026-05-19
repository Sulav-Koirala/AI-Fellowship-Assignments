from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_HOST : str
    POSTGRES_USER : str
    POSTGRES_PASSWORD : str 
    POSTGRES_DB : str
    POSTGRES_PORT : str

    class Config:
        env_file=".env"

settings=Settings()