import json

import pandas as pd

from uipath.tracing import traced


@traced(name="converting input to data frame")
def convert_dataframe(portifolio_json: str) -> pd.DataFrame:
    portifolio_list = json.loads(portifolio_json) if portifolio_json else []
    df = pd.DataFrame(portifolio_list)

    expected_columns = ["Name", "Quantity", "Value"]
    df = df.reindex(columns=expected_columns)

    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df = df.dropna(subset=["Quantity", "Value"])

    return df
