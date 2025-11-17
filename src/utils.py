import logging
import time
from pathlib import Path

import dotenv
from hydra import compose, initialize_config_dir
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

def get_db_connection_string():
    cfg = load_config()
    user = cfg.db.user
    password = cfg.db.password
    host = cfg.db.host
    port = cfg.db.port
    database = cfg.db.database
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"


class Pipe:
    def __init__(self, value):
        self.value = value

    def then(self, fn, *args, **kwargs):
        self.value = fn(self.value, *args, **kwargs)
        return self

    def get(self):
        return self.value
