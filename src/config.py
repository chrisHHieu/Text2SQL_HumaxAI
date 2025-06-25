from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DB_DRIVER = os.getenv("DB_DRIVER")
    DB_SERVER = os.getenv("DB_SERVER")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    @staticmethod
    def get_db_connection_string():
        conn_str = (
            f"Driver={{{Config.DB_DRIVER}}};"
            f"Server={Config.DB_SERVER};"
            f"Database={Config.DB_NAME};"
            f"Uid={Config.DB_USER};"
            f"Pwd={Config.DB_PASSWORD};"
        )
        return conn_str