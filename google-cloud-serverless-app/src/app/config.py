from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(populate_by_name=True)

    gcp_project: str = Field(default="dev-project", alias="GCP_PROJECT")
    bq_dataset_id: str = Field(default="document_processing", alias="BQ_DATASET_ID")
    bq_table_id: str = Field(default="document_metadata", alias="BQ_TABLE_ID")
    dlq_bucket_name: str = Field(default="dev-dlq-bucket", alias="DLQ_BUCKET_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")


settings = Settings()
