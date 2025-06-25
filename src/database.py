import urllib.parse
from langchain_community.utilities import SQLDatabase
from src.config import Config
from src.logger import setup_logger

logger = setup_logger()

def init_database() -> SQLDatabase:
    logger.info("Initializing database connection")
    try:
        conn_str = Config.get_db_connection_string()
        encoded_conn_str = urllib.parse.quote_plus(conn_str)
        db_uri = f"mssql+pyodbc:///?odbc_connect={encoded_conn_str}"
        db = SQLDatabase.from_uri(db_uri)
        logger.info("Database connection established")
        return db
    except Exception as e:
        logger.error(f"Failed to connect to database | error={str(e)}", exc_info=True)
        raise