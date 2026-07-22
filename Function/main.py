"""
This function creates a chart from given data.
"""

import json
import sys

from dataclasses import asdict, dataclass

from uipath.tracing import traced

from chart_utils import create_donut_chart_png
from dataframe_utils import convert_dataframe
from upload_utils import upload_file_to_bucket


@dataclass
class Inputs:
    category: str = ""
    portifolio: str = ""


@dataclass
class Outputs:
    bucket_file_path: str


@traced(name="Main")
def main(input: Inputs) -> Outputs:

    df = convert_dataframe(input.portifolio)
    image_path = create_donut_chart_png(df, category=input.category)
    bucket_file_path = upload_file_to_bucket(image_path, category=input.category)

    return Outputs(
        bucket_file_path=bucket_file_path
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
