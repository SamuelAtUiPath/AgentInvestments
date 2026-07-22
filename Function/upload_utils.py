import os

from uipath.platform import UiPath
from uipath.tracing import traced


BUCKET_NAME = "investments"
FOLDER_PATH = "Brazil - My TAM Solutions"
DEFAULT_BUCKET_FILE_PATH = "reports/output.png"

_sdk: UiPath | None = None


def sdk() -> UiPath:
    global _sdk
    if _sdk is None:
        _sdk = UiPath()
    return _sdk


def get_bucket_file_path(category: str = "") -> str:
    file_stem = (category or "").strip()
    if not file_stem:
        return DEFAULT_BUCKET_FILE_PATH

    for invalid_char in ('\\', '/', ':', '*', '?', '"', '<', '>', '|'):
        file_stem = file_stem.replace(invalid_char, "_")

    return f"reports/{file_stem}.png"


@traced(name="uploading file to storage bucket")
def upload_file_to_bucket(local_file_path: str, category: str = "") -> str:
    if not os.path.isfile(local_file_path):
        raise FileNotFoundError(f"File to upload was not found: {local_file_path}")

    bucket_file_path = get_bucket_file_path(category)

    sdk().buckets.upload(
        name=BUCKET_NAME,
        blob_file_path=bucket_file_path,
        source_path=local_file_path,
        content_type="image/png",
        folder_path=FOLDER_PATH,
    )

    return bucket_file_path
