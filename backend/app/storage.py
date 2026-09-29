import os, shutil
from fastapi.responses import FileResponse, RedirectResponse
from . import config as c

def put(key: str, path: str):
    if c.STORAGE == "s3":
        import boto3
        boto3.client("s3", region_name=c.S3_REGION).upload_file(
            path, c.S3_BUCKET, key, ExtraArgs={"ContentType": "audio/mpeg"})
    else:
        os.makedirs(c.LOCAL_DIR, exist_ok=True)
        shutil.copy(path, os.path.join(c.LOCAL_DIR, key))

def serve(key: str):
    if c.STORAGE == "s3":
        import boto3
        url = boto3.client("s3", region_name=c.S3_REGION).generate_presigned_url(
            "get_object", Params={"Bucket": c.S3_BUCKET, "Key": key}, ExpiresIn=3600)
        return RedirectResponse(url)
    return FileResponse(os.path.join(c.LOCAL_DIR, key), media_type="audio/mpeg")
