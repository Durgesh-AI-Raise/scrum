from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# Import mock database functions and data models from our detection service
from detection_service import (
    Review, Reviewer,
    get_flagged_reviews_from_db,
    get_review_by_id_from_db,
    get_reviewer_by_id_from_db,
    update_review_in_db,
    log_for_learning,
    get_flagged_reviews_from_db_with_filters
)

app = FastAPI(
    title="Review Abuse Triage API",
    description="API for Trust & Safety Analysts to manage flagged reviews."
)

# Ensure Pydantic models are compatible with our dataclasses for API responses
class ReviewResponse(Review, BaseModel):
    # Pydantic will automatically map fields from the Review dataclass
    # It also handles serialization of datetime objects
    pass

class ReviewerResponse(Reviewer, BaseModel):
    pass

class ConfirmationRequest(BaseModel):
    is_abusive: bool
    abuse_category: Optional[str] = None

@app.get("/api/flagged-reviews", response_model=List[ReviewResponse], summary="Get all flagged reviews with pagination and sorting")
async def get_flagged_reviews_api(
    page: int = Query(1, ge=1, description="Page number for pagination"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    sort_by: str = Query("severity_score", description="Field to sort by (e.g., 'severity_score', 'review_date')"),
    sort_order: str = Query("desc", description="Sort order: 'asc' for ascending, 'desc' for descending")
):
    """
    Retrieves a list of reviews that have been flagged by the automated detection system.
    Supports pagination and sorting.
    """
    reviews = get_flagged_reviews_from_db(page, limit, sort_by, sort_order)
    return reviews

@app.get("/api/reviews/{review_id}", response_model=ReviewResponse, summary="Get detailed information for a specific review")
async def get_review_details_api(review_id: str):
    """
    Retrieves comprehensive details for a single review by its ID.
    """
    review = get_review_by_id_from_db(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review

@app.get("/api/reviewers/{reviewer_id}", response_model=ReviewerResponse, summary="Get detailed profile for a specific reviewer")
async def get_reviewer_profile_api(reviewer_id: str):
    """
    Retrieves comprehensive profile information for a single reviewer by their ID.
    """
    reviewer = get_reviewer_by_id_from_db(reviewer_id)
    if not reviewer:
        raise HTTPException(status_code=404, detail="Reviewer not found")
    return reviewer

@app.put("/api/reviews/{review_id}/confirm", response_model=ReviewResponse, summary="Manually confirm or reject review abuse")
async def confirm_review_abuse_api(review_id: str, request: ConfirmationRequest):
    """
    Allows a Trust & Safety Analyst to manually confirm a flagged review as abusive
    or mark it as not abusive, including categorizing the abuse type if confirmed.
    """
    review = get_review_by_id_from_db(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    review.is_confirmed_abusive = request.is_abusive
    review.confirmed_abuse_category = request.abuse_category if request.is_abusive else None
    review.confirmation_date = datetime.now()

    update_review_in_db(review)
    log_for_learning(review) # Simulate logging for future ML model training
    return review

@app.get("/api/flagged-reviews-filtered", response_model=List[ReviewResponse], summary="Get flagged reviews with extensive filtering, pagination, and sorting")
async def get_flagged_reviews_with_filters_api(
    page: int = Query(1, ge=1, description="Page number for pagination"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    sort_by: str = Query("severity_score", description="Field to sort by (e.g., 'severity_score', 'review_date')"),
    sort_order: str = Query("desc", description="Sort order: 'asc' for ascending, 'desc' for descending"),
    product_asin: Optional[str] = Query(None, description="Filter by product ASIN"),
    reviewer_id: Optional[str] = Query(None, description="Filter by reviewer ID"),
    abuse_type: Optional[str] = Query(None, description="Filter by predicted abuse type"),
    start_date: Optional[str] = Query(None, description="Filter by review date (start date YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by review date (end date YYYY-MM-DD)"),
    min_severity: Optional[int] = Query(None, ge=0, le=100, description="Filter by minimum severity score"),
    max_severity: Optional[int] = Query(None, ge=0, le=100, description="Filter by maximum severity score"),
    search_text: Optional[str] = Query(None, description="Full-text search within review content")
):
    """
    Retrieves a list of flagged reviews, allowing for advanced filtering, pagination, and sorting.
    """
    filters = {
        "product_asin": product_asin,
        "reviewer_id": reviewer_id,
        "abuse_type": abuse_type,
        "start_date": start_date,
        "end_date": end_date,
        "min_severity": min_severity,
        "max_severity": max_severity,
        "search_text": search_text
    }
    # Remove None or empty string values from filters before passing to DB function
    active_filters = {k: v for k, v in filters.items() if v is not None and v != ''}

    reviews = get_flagged_reviews_from_db_with_filters(page, limit, sort_by, sort_order, active_filters)
    return reviews
