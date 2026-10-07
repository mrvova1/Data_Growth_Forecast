import json
from pathlib import Path
from uuid import uuid4

from minio import Minio

from core.config import settings


client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_USE_SSL,
)


def ensure_bucket() -> None:
    if not client.bucket_exists(settings.MINIO_BUCKET):
        client.make_bucket(settings.MINIO_BUCKET)

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [
                    f"arn:aws:s3:::{settings.MINIO_BUCKET}/*"
                ],
            }
        ],
    }

    client.set_bucket_policy(
        settings.MINIO_BUCKET,
        json.dumps(policy)
    )


def _generated_key(
    original_name: str | None,
    prefix: str,
) -> str:
    extension = Path(
        original_name or ""
    ).suffix.lower()

    return f"{prefix}/{uuid4().hex}{extension}"


def put_upload(
    upload,
    prefix: str,
) -> str:
    ensure_bucket()

    key = _generated_key(
        upload.filename,
        prefix,
    )

    file_obj = upload.file

    file_obj.seek(0, 2)
    length = file_obj.tell()
    file_obj.seek(0)

    client.put_object(
        settings.MINIO_BUCKET,
        key,
        file_obj,
        length=length,
        content_type=(
            upload.content_type
            or "application/octet-stream"
        ),
    )

    return key


def delete_object(key: str | None) -> None:
    if not key:
        return

    try:
        client.remove_object(
            settings.MINIO_BUCKET,
            key
        )
    except Exception:
        pass


def public_url(key: str | None) -> str | None:
    if not key:
        return None

    return (
        f"{settings.MINIO_PUBLIC_BASE_URL.rstrip('/')}/"
        f"{settings.MINIO_BUCKET}/{key}"
    )