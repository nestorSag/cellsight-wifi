
import argparse
import os
import geopandas as gpd
import osmnx as ox
import logging

import numpy as np
import pandas as pd

import src.data.constants as constants


def sample_points_in_polygon(polygon, n_points, batch_size=50000):
    """Uniformly sample n_points inside a shapely Polygon."""
    minx, miny, maxx, maxy = polygon.bounds
    x_sample, y_sample = [], []
    current = 0
    while current < n_points:
        x = np.random.uniform(minx, maxx, size=batch_size)
        y = np.random.uniform(miny, maxy, size=batch_size)
        is_inside = gpd.points_from_xy(x, y).within(polygon)
        x_sample.append(x[is_inside])
        y_sample.append(y[is_inside])
        current += is_inside.sum()
    return np.stack(
        [np.concatenate(x_sample), np.concatenate(y_sample)],
        axis=1,
    )[:n_points]

def get_state_polygons():
    logging.info("Fetching state polygons from OSMnx...")
    state_names = [val for key, vals in constants.region_to_states_map.items() for val in vals]
    state_gdfs = []
    for state in state_names:
        state_gdf = ox.geocode_to_gdf(f"{state}, USA", which_result=1)
        state_gdfs.append(state_gdf)

    all_states_gdf = gpd.GeoDataFrame(pd.concat(state_gdfs, ignore_index=True))
    return all_states_gdf.assign(state=state_names)

def sample_locations(n_locations: int):
    logging.info("Sampling user locations...")
    all_states_gdf = get_state_polygons()
    state_to_region_map = {
        state: region
        for region, states in constants.region_to_states_map.items()
        for state in states
    }
    n_states = len(all_states_gdf)
    locations_per_state = n_locations // n_states + 1

    samples = []
    for _, row in all_states_gdf.iterrows():
        state_polygon = row.geometry
        points = sample_points_in_polygon(state_polygon, locations_per_state)
        points_df = (pd
            .DataFrame(points, columns=["longitude", "latitude"])
            .assign(
                state=row['state'],
                region=state_to_region_map[row['state']],
            )
        )
        samples.append(points_df)
    all_samples_df = pd.concat(samples, ignore_index=True)
    return all_samples_df

def sample_access_points(n_devices: int):
    logging.info("Sampling access point attributes...")
    bands = np.random.choice(constants.bands, size=n_devices)
    vendors = np.random.choice(constants.vendors, size=n_devices)
    ssids = np.random.choice(constants.ssid_types, size=n_devices)
    ap_id = [f"AP{str(_).zfill(9)}" for _ in range(n_devices)]
    return pd.DataFrame({
        "ap_id": ap_id,
        "band": bands,
        "vendor_source": vendors,
        "ssid": ssids,
    })


def generate_data(n_points: int):
    # Sample user locations
    user_locations = sample_locations(n_points)

    # Sample devices
    devices = sample_access_points(n_points)

    # Combine data
    data = pd.concat([user_locations, devices], axis=1)
    return data

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    parser = argparse.ArgumentParser(description="Generate userbase data.")
    parser.add_argument(
        "--n_points",
        type=int,
        default=10000,
        help="Number of user points to generate.",
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default="userbase.parquet",
        help="Path to save the generated userbase data.",
    )
    args = parser.parse_args()

    data = generate_data(args.n_points)
    # create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
    data.to_parquet(args.output_path, index=False)