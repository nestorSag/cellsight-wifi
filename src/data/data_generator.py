
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import logging

import src.data.access_point_generator as ap_gen
import src.data.record_generator as rec_gen
import pandas as pd
import toml

from src.utils import timed, set_logging

@timed
def generate_data(
    n_aps: int,
    n_sessions_per_ap: int=2,
    n_records_per_session: int=1,
):
    
    ap_file_path = Path("data/.metadata/access_points/data.parquet")
    base_time = get_current_time()
    regenerate = False
    if ap_file_path.exists():
        _ = pd.read_parquet(
            ap_file_path,
            columns=["ap_id"],
        )
        if len(_) < n_aps:
            regenerate = True
    else:
        regenerate = True
    
    if regenerate:
        ap_data = ap_gen.sample_access_points(n_aps)
        ap_data.to_parquet(ap_file_path, index=False)
    else:
        logging.info("Reading existing access point data...")
        ap_data = pd.read_parquet(ap_file_path)

    logging.info("Generating record data...")
    rec_data = rec_gen.generate_records(
        n_aps=n_aps,
        base_time=base_time,
        n_sessions_per_ap=n_sessions_per_ap,
        n_records_per_session=n_records_per_session,
    )
    rec_data['ap_id'] = rec_data['ap_id'].astype(int)
    ap_data['ap_id'] = ap_data['ap_id'].astype(int)

    logging.info("Merging record and access point data...")
    full_data = rec_data.merge(
        ap_data,
        on="ap_id",
        how="left",
    )
    return full_data

def get_current_time():
    with open("data/.metadata/config.toml", "r") as f:
        config = toml.load(f)
    return datetime.fromisoformat(config["params"]["current_time"])

def bump_current_time(hours: int = 1):
    current_time = get_current_time()
    new_time = current_time + timedelta(hours=hours)
    with open("data/.metadata/config.toml", "r") as f:
        config = toml.load(f)
    config["params"]["current_time"] = new_time.isoformat()
    with open("data/.metadata/config.toml", "w") as f:
        toml.dump(config, f)


@timed
def persist_data(
    n_aps: int,
    n_sessions_per_ap: int=2,
    n_records_per_session: int=1,
):
    base_time = get_current_time()
    data = generate_data(
        n_aps=n_aps,
        n_sessions_per_ap=n_sessions_per_ap,
        n_records_per_session=n_records_per_session,
    )
    output_path = Path(f"data/csv/{base_time}.csv")
    logging.info(f"Persisting data to {output_path}...")
    data.to_csv(output_path, index=False)
    bump_current_time(hours=1)
    

if __name__ == "__main__":
    # log to stdout and append to log file
    set_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--n_aps",
        type=int,
        default=100,
        help="Number of access points to simulate.",
    )
    parser.add_argument(
        "--n_sessions_per_ap",
        type=int,
        default=2,
        help="Number of sessions per access point.",
    )
    parser.add_argument(
        "--n_records_per_session",
        type=int,
        default=1,
        help="Number of records per session.",
    )
    args = parser.parse_args()
    persist_data(
        n_aps=args.n_aps,
        n_sessions_per_ap=args.n_sessions_per_ap,
        n_records_per_session=args.n_records_per_session,
    )