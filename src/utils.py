import logging
import time
import asyncio
from pathlib import Path

import dotenv
from hydra import compose, initialize_config_dir
import asyncpg as pg
from omegaconf import OmegaConf

def timed(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logging.info(f"Function {func.__name__} took {end_time - start_time:.2f} seconds")
        return result
    return wrapper

def set_logging():
    logging.basicConfig(
        level=logging.INFO, 
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("logs", mode='a'),
            logging.StreamHandler()
        ]
    )

def load_config(path: str = "config/main.yaml"):
    dotenv.load_dotenv()
    absolute_path = Path(path).resolve()
    absolute_parent_folder = absolute_path.parent
    with initialize_config_dir(version_base=None, config_dir=str(absolute_parent_folder)):
            cfg = compose(config_name=Path(path).stem)
            OmegaConf.resolve(cfg)  # apply interpolatations
    return cfg

def get_ingestion_config():
    cfg = load_config()
    username = cfg.db.auth.username
    password = cfg.db.auth.password
    host = cfg.db.auth.host
    port = cfg.db.params.ingestion_port
    protocol = cfg.db.params.ingestion_protocol
    return f"{protocol}::addr={host}:{port};username={username};password={password};"


async def query_db(query: str):
    cfg = load_config()
    conn = await pg.connect(
        host=cfg.db.auth.host,
        port=cfg.db.params.query_port,
        user=cfg.db.auth.username,
        password=cfg.db.auth.password,
        database=cfg.db.auth.db
    )
    results = await conn.fetch(query)
    await conn.close()
    return results

def create_table() -> None:
    cfg = load_config()
    to_index = cfg.db.params.indexes
    with open("db/schema.sql", "r") as f:
        schema_sql = f.read()

    # idempotent table creation
    _ = asyncio.run(query_db(schema_sql))

    # create indexes if not exist
    query = f"""
    SELECT "column"
    FROM table_columns('{cfg.db.params.table_name}')
    WHERE indexed = true;
    """
    indexed = asyncio.run(query_db(query))
    not_yet_indexed = set(to_index) - {row["column"] for row in indexed}
    for col in not_yet_indexed:
        index_sql = f"ALTER TABLE {cfg.db.params.table_name} ALTER COLUMN {col} ADD INDEX;"
        _ = asyncio.run(query_db(index_sql))
        logging.info(f"Created index on column {col}.")

class Pipe:
    def __init__(self, value):
        self.value = value

    def then(self, fn, *args, **kwargs):
        self.value = fn(self.value, *args, **kwargs)
        return self

    def get(self):
        return self.value
