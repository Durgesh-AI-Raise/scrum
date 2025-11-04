# data_lake/schemas/review_schema.py
REVIEW_SCHEMA_DEFINITION = {
    "type": "struct",
    "fields": [
        {"name": "review_id", "type": "string", "nullable": False},
        {"name": "product_id", "type": "string", "nullable": False},
        {"name": "reviewer_id", "type": "string", "nullable": False},
        {"name": "star_rating", "type": "integer", "nullable": False},
        {"name": "review_headline", "type": "string", "nullable": True},
        {"name": "review_body", "type": "string", "nullable": False},
        {"name": "review_date", "type": "string", "nullable": False}, # "YYYY-MM-DDTHH:MM:SSZ"
        {"name": "helpful_votes", "type": "integer", "nullable": False},
        {"name": "total_votes", "type": "integer", "nullable": False},
        {"name": "verified_purchase", "type": "boolean", "nullable": False},
        {"name": "product_title", "type": "string", "nullable": True},
        {"name": "product_category", "type": "string", "nullable": True},
        {"name": "reviewer_name", "type": "string", "nullable": True},
        {"name": "reviewer_profile_link", "type": "string", "nullable": True},
        {"name": "marketplace", "type": "string", "nullable": False},
        {"name": "review_url", "type": "string", "nullable": True},
        {"name": "image_urls", "type": {"type": "array", "elementType": "string", "containsNull": True}, "nullable": True}
    ]
}

# Example usage (for validation or documentation)
# from pyspark.sql.types import StructType, StructField, StringType, IntegerType, BooleanType, ArrayType
#
# pyspark_review_schema = StructType([
#     StructField("review_id", StringType(), False),
#     StructField("product_id", StringType(), False),
#     StructField("reviewer_id", StringType(), False),
#     StructField("star_rating", IntegerType(), False),
#     StructField("review_headline", StringType(), True),
#     StructField("review_body", StringType(), False),
#     StructField("review_date", StringType(), False),
#     StructField("helpful_votes", IntegerType(), False),
#     StructField("total_votes", IntegerType(), False),
#     StructField("verified_purchase", BooleanType(), False),
#     StructField("product_title", StringType(), True),
#     StructField("product_category", StringType(), True),
#     StructField("reviewer_name", StringType(), True),
#     StructField("reviewer_profile_link", StringType(), True),
#     StructField("marketplace", StringType(), False),
#     StructField("review_url", StringType(), True),
#     StructField("image_urls", ArrayType(StringType()), True)
# ])