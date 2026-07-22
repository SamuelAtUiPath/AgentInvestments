"""
This function creates a chart from given data.
"""

import json
import sys
import pandas as pd

from dataclasses import asdict, dataclass

from uipath.tracing import traced


@dataclass
class Inputs:
    category: str = ""
    portifolio: str = ""


@dataclass
class Outputs:
    out: str

# -----------------------
# Functions

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


@traced(name="Main")
def main(input: Inputs) -> Outputs:

    df = convert_dataframe(input.portifolio)
    total = (df["Value"]).sum()

    return Outputs(
        out=str(total)
    )


if __name__ == "__main__":
    # python.exe .\main.py '{\"category\":\"Stocks\",\"portifolio\":\"[{\\\"Name\\\":\\\"PETR4\\\",\\\"Quantity\\\":10,\\\"Value\\\":38.5},{\\\"Name\\\":\\\"VALE3\\\",\\\"Quantity\\\":5,\\\"Value\\\":62.1}]\"}'
    payload = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}

    result = main(
        Inputs(
            category=payload.get("category", ""),
            portifolio=payload.get("portifolio", ""),
        )
    )

    print(json.dumps(asdict(result), indent=2))
