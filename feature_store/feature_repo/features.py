import os
from datetime import timedelta
from feast import Entity, Field, FeatureView, FileSource
from feast.value_type import ValueType
from feast.types import Float32, Int64

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARQUET_FILE = os.path.join(CURRENT_DIR, "data", "card_features.parquet")

# Define primary entity: card1
card_entity = Entity(
    name="card1",
    value_type=ValueType.INT64,
    join_keys=["card1"],
    description="Anonymized card / account relationship proxy identifier"
)

# Define file data source
card_stats_source = FileSource(
    path=PARQUET_FILE,
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp"
)

# Define feature view
card_features_view = FeatureView(
    name="card_features",
    entities=[card_entity],
    ttl=timedelta(days=90),
    schema=[
        Field(name="card1_avg_amount", dtype=Float32),
        Field(name="card1_trans_count_24h", dtype=Int64),
        Field(name="card1_total_count", dtype=Int64),
        Field(name="card1_max_amount", dtype=Float32),
    ],
    online=True,
    source=card_stats_source
)
