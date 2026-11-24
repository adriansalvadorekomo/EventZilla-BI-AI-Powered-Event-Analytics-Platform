"""Landing: split the source workbook into one CSV per entity and put them in the landing bucket.

    python ingestion/land_workbook.py [--workbook data/eventzella_schema_general-DW.xlsx] [--out DIR] [--s3]

Airbyte reads the landing bucket (one stream per entity, ingestion/airbyte/setup_airbyte.py). Values are written as they
are in the workbook: no cleaning here, so the raw layer is the source and every fix is visible in dbt.
With --s3 the files go to S3_ENDPOINT / LANDING_BUCKET (SeaweedFS in compose.yaml) under eventzilla/<entity>/.
"""

import argparse
import io
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
# sheet in the workbook -> entity name in the landing bucket, in Airbyte and in dbt sources
ENTITIES = {
    "BENEFICIARY": "beneficiary", "PROVIDER": "provider", "CATEGORY": "category", "SUBCATEGORY": "subcategory",
    "CATEGORY_SERVICE": "category_service", "SERVICE": "service", "EVENT": "event", "RESERVATION": "reservation",
    "EVALUATION": "evaluation", "COMPLAINT": "complaint", "VISITORS": "site_traffic",
    "MARKETING_SPEND": "marketing_spend", "competitor": "competitor", "locations": "location", "saison": "season",
    "reviews": "platform_review",
}


def entity_frames(workbook: Path) -> dict[str, pd.DataFrame]:
    sheets = pd.read_excel(workbook, sheet_name=list(ENTITIES), dtype=str, keep_default_na=False)
    frames = {}
    for sheet, df in sheets.items():
        df.columns = [str(c).strip().lower() for c in df.columns]
        frames[ENTITIES[sheet]] = df
    return frames


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--workbook", default=str(ROOT / "data" / "eventzella_schema_general-DW.xlsx"))
    parser.add_argument("--out", help="also write the CSVs to this folder")
    parser.add_argument("--s3", action="store_true", help="upload to the landing bucket")
    args = parser.parse_args()

    frames = entity_frames(Path(args.workbook))
    if args.s3:
        import boto3  # only needed for the upload

        s3 = boto3.client("s3", endpoint_url=os.environ["S3_ENDPOINT"],
                          aws_access_key_id=os.environ["S3_ACCESS_KEY"],
                          aws_secret_access_key=os.environ["S3_SECRET_KEY"])
        bucket = os.environ.get("LANDING_BUCKET", "landing")
        if bucket not in [b["Name"] for b in s3.list_buckets()["Buckets"]]:
            s3.create_bucket(Bucket=bucket)
    for entity, df in frames.items():
        data = df.to_csv(index=False).encode()
        if args.out:
            Path(args.out).mkdir(parents=True, exist_ok=True)
            (Path(args.out) / f"{entity}.csv").write_bytes(data)
        if args.s3:
            s3.upload_fileobj(io.BytesIO(data), bucket, f"eventzilla/{entity}/{entity}.csv")
        print(f"{entity:18} {len(df):>6} rows")


if __name__ == "__main__":
    main()
