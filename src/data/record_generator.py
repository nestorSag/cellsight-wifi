import random
import numpy as np
import pandas as pd

from datetime import datetime, timedelta

from src.data import parameters

def generate_records(
    n_aps: int,
    base_time: datetime,
    n_sessions_per_ap: int=2,
    n_records_per_session: int=1,
    batch_size: int=1_000_000,
):
    """
    Generator that yields batches of records as DataFrames.
    
    Args:
        n_aps: Number of access points
        base_time: Base timestamp for record generation
        n_sessions_per_ap: Number of sessions per access point
        n_records_per_session: Number of records per session
        batch_size: Maximum number of records per batch (default: 1,000,000)
        
    Yields:
        pd.DataFrame: Batches of records with size <= batch_size
    """
    records = []
    columns = [
        "session_id", "user_mac", "timestamp", "rssi", "noise_floor", "snr",
        "bytes_in", "bytes_out", "packets_in", "packets_out", "throughput_mbps",
        "retries", "errors", "tx_power", "rx_power", "tx_rate", "rx_rate",
        "mcs_tx", "mcs_rx", "assoc_clients", "roam_events", "ap_temperature",
        "uptime_sec", "fw_version",  "channel", "channel_width", "ap_id",
    ]
    
    for i in range(n_aps):
        for j in range(n_sessions_per_ap):
            ap_id = i
            session_id = f"AP:{i}:{j}:S{random.randint(100000, 999999)}"
            user_mac = f"00:{random.randint(10,99):02x}:{random.randint(10,99):02x}:{random.randint(10,99):02x}:{random.randint(10,99):02x}:{random.randint(10,99):02x}" # 
            start_time = base_time + timedelta(minutes=random.randint(0, 60))
            
            # Initialize cumulative counters
            bytes_in = 0
            bytes_out = 0
            packets_in = 0
            packets_out = 0
            for k in range(n_records_per_session):

                timestamp = start_time + timedelta(minutes=k * random.randint(1, 3))
                # Signal & performance metrics
                rssi = random.randint(-85, -45)
                noise_floor = random.randint(-95, -75)
                snr = rssi - noise_floor
                delta_bytes_in = random.randint(20_000, 100_000)
                delta_bytes_out = random.randint(20_000, 100_000)
                bytes_in += delta_bytes_in
                bytes_out += delta_bytes_out
                delta_pkts_in = delta_bytes_in // random.randint(500, 1500)
                delta_pkts_out = delta_bytes_out // random.randint(500, 1500)
                packets_in += delta_pkts_in
                packets_out += delta_pkts_out
                throughput_mbps = round((delta_bytes_in + delta_bytes_out) * 8 / (60 * 1e6), 2)
                retries = random.randint(0, 50)
                errors = random.randint(0, 10)

                # Additional AP / band metrics
                tx_power = random.randint(15, 30)  # dBm
                rx_power = rssi
                tx_rate = random.randint(6, 1200)  # Mbps
                rx_rate = random.randint(6, 1200)  # Mbps
                mcs_tx = random.randint(0, 11)
                mcs_rx = random.randint(0, 11)
                assoc_clients = random.randint(1, 50)
                roam_events = random.randint(0, 5)
                ap_temperature = round(random.uniform(25.0, 45.0), 1)
                uptime_sec = random.randint(10_000, 500_000)
                fw_version = f"{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,99)}"
                channel = random.choice(parameters.channels)
                channel_width = random.choice(parameters.channel_widths)
                records.append(np.array(
                    [
                        session_id,
                        user_mac,
                        timestamp.isoformat(),
                        rssi,
                        noise_floor,
                        snr,
                        bytes_in,
                        bytes_out,
                        packets_in,
                        packets_out,
                        throughput_mbps,
                        retries,
                        errors,
                        tx_power,
                        rx_power,
                        tx_rate,
                        rx_rate,
                        mcs_tx,
                        mcs_rx,
                        assoc_clients,
                        roam_events,
                        ap_temperature,
                        uptime_sec,
                        fw_version,
                        channel,
                        channel_width,
                        ap_id,
                    ]
                ))
                
                # Yield batch when it reaches the specified size
                if len(records) >= batch_size:
                    yield pd.DataFrame(np.stack(records), columns=columns)
                    records = []
    
    # Yield remaining records if any
    if records:
        yield pd.DataFrame(np.stack(records), columns=columns)
