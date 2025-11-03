# backend/flagged_review_service/dal.py
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from typing import List, Optional
from ..review_data_models import FlaggedReviewModel, ReviewStatus, Review # Import Review
from motor.motor_asyncio import AsyncIOMotorClient

class FlaggedReviewDAL:
    def __init__(self, connection_string: str, db_name: str):
        self.client = AsyncIOMotorClient(connection_string) # Use AsyncIOMotorClient
        self.db = self.client[db_name]
        self.collection = self.db["flagged_reviews"]
        self._create_indexes()

    def _create_indexes(self):
        self.collection.create_index("review_id", unique=True)
        self.collection.create_index("reviewer_id")
        self.collection.create_index("product_asin")
        self.collection.create_index("status")
        self.collection.create_index("flagging_timestamp")
        self.collection.create_index([("text", "text")]) # Text index for keyword search

    async def create_flagged_review(self, review: FlaggedReviewModel) -> FlaggedReviewModel:
        try:
            # Convert Pydantic model to dict for MongoDB insertion
            # MongoDB uses _id, so map flagged_id to _id
            review_dict = review.dict(by_alias=True)
            review_dict["_id"] = review_dict.pop("flagged_id")

            await self.collection.insert_one(review_dict)
            # Re-map _id back to flagged_id for the returned model
            review_dict["flagged_id"] = review_dict.pop("_id")
            return FlaggedReviewModel(**review_dict)
        except PyMongoError as e:
            raise Exception(f"Error creating flagged review: {e}")

    async def get_flagged_reviews(
        self, 
        status: Optional[ReviewStatus] = None, 
        reviewer_id: Optional[str] = None,
        product_asin: Optional[str] = None,
        keywords: Optional[str] = None,
        skip: int = 0, 
        limit: int = 10
    ) -> List[FlaggedReviewModel]:
        query = {}
        if status:
            query["status"] = status.value
        if reviewer_id:
            query["reviewer_id"] = reviewer_id
        if product_asin:
            query["product_asin"] = product_asin
        if keywords:
            query["$text"] = {"$search": keywords}

        try:
            cursor = self.collection.find(query).skip(skip).limit(limit).sort("flagging_timestamp", -1)
            # Convert _id to flagged_id when fetching from DB
            results = []
            async for doc in cursor:
                doc["flagged_id"] = doc.pop("_id")
                results.append(FlaggedReviewModel(**doc))
            return results
        except PyMongoError as e:
            raise Exception(f"Error fetching flagged reviews: {e}")

    async def get_flagged_review_by_id(self, flagged_id: str) -> Optional[FlaggedReviewModel]:
        try:
            doc = await self.collection.find_one({"_id": flagged_id})
            if doc:
                doc["flagged_id"] = doc.pop("_id")
                return FlaggedReviewModel(**doc)
            return None
        except PyMongoError as e:
            raise Exception(f"Error fetching flagged review by ID: {e}")

    async def update_flagged_review_status(
        self, flagged_id: str, new_status: ReviewStatus, notes: Optional[str] = None
    ) -> Optional[FlaggedReviewModel]:
        try:
            update_fields = {"status": new_status.value}
            if notes is not None:
                update_fields["investigation_notes"] = notes

            result = await self.collection.find_one_and_update(
                {"_id": flagged_id},
                {"$set": update_fields},
                return_document=True # Return the updated document
            )
            if result:
                result["flagged_id"] = result.pop("_id")
                return FlaggedReviewModel(**result)
            return None
        except PyMongoError as e:
            raise Exception(f"Error updating flagged review status: {e}")
