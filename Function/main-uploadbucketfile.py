"""
UiPath Function that uploads a local file to a storage bucket.
"""

from dataclasses import asdict, dataclass
import json
import mimetypes
import os
from pathlib import Path, PurePosixPath
import sys
from uipath.tracing import traced


@dataclass
class BucketUploadIn:
    source_file_path: str
    bucket_name: str = "investments"
    folder_path: str = "Brazil - My TAM Solutions"
    bucket_directory: str = ""
    bucket_file_path: str = ""


@dataclass
class BucketUploadOut:
    bucket_name: str
    bucket_file_path: str
    source_file_path: str
    file_name: str
    file_size_bytes: int
    content_type: str


def _load_local_env(env_path: Path = Path(".env")) -> None:
    if not env_path.is_file():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _normalize_bucket_path(path: str) -> str:
    cleaned = path.replace("\\", "/").strip().strip("/")
    normalized_path = PurePosixPath(cleaned)
    if ".." in normalized_path.parts:
        raise ValueError("Bucket file path cannot contain parent directory segments.")

    normalized = str(normalized_path)
    if normalized in ("", "."):
        return ""

    return normalized


def _build_bucket_file_path(
    source_file: Path,
    bucket_directory: str,
    bucket_file_path: str,
) -> str:
    explicit_path = _normalize_bucket_path(bucket_file_path)
    if explicit_path:
        return explicit_path

    directory = _normalize_bucket_path(bucket_directory)
    file_name = source_file.name
    return f"{directory}/{file_name}" if directory else file_name


def _upload_to_bucket(
    bucket_name: str,
    source_file_path: str,
    bucket_file_path: str,
    folder_path: str,
) -> None:
    from uipath.platform import UiPath

    _load_local_env()
    sdk = UiPath()
    sdk.buckets.upload(
        name=bucket_name,
        source_path=source_file_path,
        blob_file_path=bucket_file_path,
        folder_path=folder_path or None,
    )


@traced(name="main")
def main(input: BucketUploadIn) -> BucketUploadOut:
    source_file_path = input.source_file_path.strip()
    if not source_file_path:
        raise ValueError("Source file path is required.")

    source_file = Path(source_file_path).expanduser()
    if not source_file.is_file():
        raise FileNotFoundError(f"Source file does not exist: {source_file}")

    bucket_name = input.bucket_name.strip()
    if not bucket_name:
        raise ValueError("Bucket name is required.")

    bucket_file_path = _build_bucket_file_path(
        source_file=source_file,
        bucket_directory=input.bucket_directory,
        bucket_file_path=input.bucket_file_path,
    )
    if not bucket_file_path:
        raise ValueError("Bucket file path could not be resolved.")

    content_type = mimetypes.guess_type(source_file.name)[0] or "application/octet-stream"

    _upload_to_bucket(
        bucket_name=bucket_name,
        source_file_path=str(source_file),
        bucket_file_path=bucket_file_path,
        folder_path=input.folder_path.strip(),
    )

    return BucketUploadOut(
        bucket_name=bucket_name,
        bucket_file_path=bucket_file_path,
        source_file_path=str(source_file),
        file_name=source_file.name,
        file_size_bytes=source_file.stat().st_size,
        content_type=content_type,
    )


if __name__ == "__main__":
    source_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    bucket_arg = sys.argv[2] if len(sys.argv) > 2 else "investments"
    folder_arg = sys.argv[3] if len(sys.argv) > 3 else "Brazil - My TAM Solutions"
    directory_arg = sys.argv[4] if len(sys.argv) > 4 else ""
    bucket_file_arg = sys.argv[5] if len(sys.argv) > 5 else ""
    if not source_arg or not bucket_arg:
        raise SystemExit(
            "Usage: python main.py SOURCE_FILE_PATH BUCKET_NAME [FOLDER_PATH] "
            "[BUCKET_DIRECTORY] [BUCKET_FILE_PATH]"
        )

    result = main(
        BucketUploadIn(
            source_file_path=source_arg,
            bucket_name=bucket_arg,
            folder_path=folder_arg,
            bucket_directory=directory_arg,
            bucket_file_path=bucket_file_arg,
        )
    )
    print(json.dumps(asdict(result), indent=2))
