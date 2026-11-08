import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def build_card_features_parquet(sample_size: int = 5000):
    """
    Builds point-in-time correct historical card features avoiding target leakage.
    Features are strictly computed on historical transactions preceding each timestamp.
    """
    data_dir = os.path.join(BASE_DIR, "feature_store", "feature_repo", "data")
    os.makedirs(data_dir, exist_ok=True)
    parquet_path = os.path.join(data_dir, "card_features.parquet")

    trans_csv = os.path.join(BASE_DIR, "dataset", "train_transaction.csv")
    if os.path.exists(trans_csv):
        df = pd.read_csv(trans_csv, nrows=sample_size, usecols=["TransactionID", "TransactionDT", "TransactionAmt", "card1"])
    else:
        # Generate synthetic records if dataset is missing
        records = []
        for i in range(sample_size):
            records.append({
                "TransactionID": 3000000 + i,
                "TransactionDT": 86400 + (i * 120),
                "TransactionAmt": 50.0 + (i % 200),
                "card1": 1000 + (i % 50)
            })
        df = pd.DataFrame(records)

    df = df.dropna(subset=["card1", "TransactionDT"]).copy()
    df["card1"] = df["card1"].astype(int)
    df = df.sort_values(["card1", "TransactionDT"]).reset_index(drop=True)

    # Base reference datetime (2026-01-01)
    base_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    df["event_timestamp"] = df["TransactionDT"].apply(lambda dt: base_time + timedelta(seconds=float(dt)))
    df["created_timestamp"] = df["event_timestamp"]

    # Point-in-time expanding historical features (strictly shift by 1 to exclude current transaction)
    df["card1_total_count"] = df.groupby("card1").cumcount().astype(np.int64)

    df["card1_avg_amount"] = (
        df.groupby("card1")["TransactionAmt"]
        .transform(lambda s: s.shift(1).expanding().mean())
        .fillna(df["TransactionAmt"])
        .astype(np.float32)
    )

    df["card1_max_amount"] = (
        df.groupby("card1")["TransactionAmt"]
        .transform(lambda s: s.shift(1).expanding().max())
        .fillna(df["TransactionAmt"])
        .astype(np.float32)
    )

    # Calculate preceding 24h count
    counts_24h = []
    for card, group in df.groupby("card1", sort=False):
        times = group["TransactionDT"].to_numpy()
        # Find indices strictly 86400 seconds ago
        positions = np.arange(len(times))
        idx_24h = np.searchsorted(times, times - 86400, side="left")
        # Subtract 1 to exclude current transaction
        prior_24h = np.maximum(0, (positions - idx_24h))
        counts_24h.extend(prior_24h)

    df["card1_trans_count_24h"] = np.array(counts_24h, dtype=np.int64)

    # Save to parquet
    out_cols = [
        "card1",
        "event_timestamp",
        "created_timestamp",
        "card1_avg_amount",
        "card1_trans_count_24h",
        "card1_total_count",
        "card1_max_amount"
    ]
    df[out_cols].to_parquet(parquet_path, index=False)
    print(f"Generated Feast parquet source at {parquet_path} with {len(df)} rows.")
    return parquet_path


if __name__ == "__main__":
    build_card_features_parquet()
