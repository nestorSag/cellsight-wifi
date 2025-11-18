import shutil
import polars as pl
from pathlib import Path
import logging

import pandas as pd
import pandas as pd
from questdb.ingress import Sender
import omegaconf

import src.utils as utils


@utils.timed
def csv_to_parquet(input_path: str, output_path: str, delete_csv: bool = False) -> None:
    """
    Stream-convert a large CSV file to Parquet using Polars lazy API.
    """
    pl.scan_csv(input_path).sink_parquet(
        output_path,
        compression="zstd",  # options: 'snappy', 'gzip', 'zstd', 'lz4', 'brotli', etc.
        compression_level=9, # optional, higher = more compression
    )
    # delete csv
    if delete_csv:
        shutil.rmtree(input_path)

@utils.timed
def aggregate_parquet(
        input_path: str, 
        output_path: str, 
        cfg: omegaconf.dictconfig.DictConfig,
    ) -> None:
    """
    Aggregate Parquet data by access point ID using Polars lazy API.
    """
    (pl.scan_parquet(input_path)
        .group_by(cfg.colnames.ap_id)
        .agg(
            [
                pl.col("rssi").mean().alias("avg_rssi"),
                pl.col("session_id").n_unique().alias("unique_sessions"),
                pl.col("noise_floor").max().alias("max_noise_floor"),
                pl.col("noise_floor").mean().alias("avg_noise_floor"),
                pl.col("snr").mean().alias("avg_snr"),
                pl.col("bytes_in").sum().alias("total_bytes_in"),
                pl.col("bytes_out").sum().alias("total_bytes_out"),
                pl.col("packets_in").sum().alias("total_packets_in"),
                pl.col("packets_out").sum().alias("total_packets_out"),
                pl.col("throughput_mbps").mean().alias("avg_throughput_mbps"),
                pl.col("retries").sum().alias("total_retries"),
                pl.col("errors").sum().alias("total_errors"),
                pl.col("tx_power").mean().alias("avg_tx_power"),
                pl.col("rx_power").mean().alias("avg_rx_power"),
                pl.col("tx_rate").mean().alias("avg_tx_rate"),
                pl.col("rx_rate").mean().alias("avg_rx_rate"),
                pl.col("mcs_tx").mean().alias("avg_mcs_tx"),
                pl.col("mcs_rx").mean().alias("avg_mcs_rx"),
                pl.col("assoc_clients").max().alias("max_assoc_clients"),
                pl.col("roam_events").sum().alias("total_roam_events"),
                pl.col("ap_temperature").mean().alias("avg_ap_temperature"),
                pl.col("uptime_sec").max().alias("max_uptime_sec"),
                pl.col("fw_version").first().alias("fw_version"),
                pl.col(cfg.colnames.channel).first().alias("channel"),
                pl.col("channel_width").first().alias("channel_width"),
                pl.col(cfg.colnames.lon).first().alias("longitude"),
                pl.col(cfg.colnames.lat).first().alias("latitude"),
                pl.col(cfg.colnames.state).first().alias("state"),
                pl.col(cfg.colnames.region).first().alias("region"),
                pl.col(cfg.colnames.band).first().alias("band"),
                pl.col("vendor_source").first().alias("vendor_source"),
                pl.col("vendor_name").first().alias("vendor_name"),
                pl.col("model").first().alias("model"),
                pl.col("ssid").first().alias("ssid"),
            ]
        )
        .sink_parquet(output_path, compression="zstd", compression_level=9)
    )

@utils.timed
def parquet_to_db(
    input_path: str, 
    table_name: str,
    timestamp: str,
) -> None:
    """
    Load Parquet data into a questDB table.
    """

    # Read Parquet file into Pandas DataFrame
    df = pd.read_parquet(input_path)
    
    # add timestamp column
    df = df.with_column(pl.lit(timestamp).alias("timestamp"))

    # Create database engine
    addr = utils.get_connection_config()

    with Sender.from_config(addr) as sender:
        sender.dataframe(
            df,
            table_name=table_name,
            at="timestamp",
        )


if __name__ == "__main__":
    # log to stdout and append to log file
    utils.set_logging()
    cfg = utils.load_config()
    # find all csv files in data/csv/
    files = list(Path("data/csv/").glob("*.csv"))
    if not files:
        logging.info("No CSV files found in data/csv/. Exiting.")
    for file in files:
        filename = file.stem
        parquet_path = f"data/parquet/{filename}.parquet"
        csv_to_parquet(
            input_path=str(file), 
            output_path=parquet_path,
        )
        aggregated_path = f"data/parquet/aggregated/{filename}.parquet"
        aggregate_parquet(
            input_path=str(parquet_path), 
            output_path=str(aggregated_path), 
            cfg=cfg,
        )
        parquet_to_db(
            input_path=str(aggregated_path),
            table_name=cfg.db.metrics_table,
            timestamp=file.stem,
        )