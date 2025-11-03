
# src/backend/dashboard_api.py
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import date, timedelta
import random # For mock data

app = FastAPI(title="Abuse Pattern Dashboard API")

class MetricTrend(BaseModel):
    date: date
    value: int

class CategoryBreakdown(BaseModel):
    category: str
    count: int

class TopItem(BaseModel):
    id: str
    name: Optional[str] = None
    flagged_count: int

@app.get("/api/dashboard/flagged_reviews_trend")
async def get_flagged_reviews_trend(
    start_date: date = Query(default=(date.today() - timedelta(days=30))),
    end_date: date = Query(default=date.today()),
    abuse_category: Optional[str] = None
) -> List[MetricTrend]:
    """Retrieves the trend of flagged reviews over a specified date range."""
    # In a real app, query AggregatedMetrics table here
    mock_data = []
    current_date = start_date
    while current_date <= end_date:
        mock_data.append(MetricTrend(date=current_date, value=random.randint(50, 200)))
        current_date += timedelta(days=1)
    return mock_data

@app.get("/api/dashboard/abuse_category_breakdown")
async def get_abuse_category_breakdown(
    start_date: date = Query(default=(date.today() - timedelta(days=30))),
    end_date: date = Query(default=date.today())
) -> List[CategoryBreakdown]:
    """Retrieves the breakdown of flagged reviews by abuse category."""
    # In a real app, query AggregatedMetrics table here
    return [
        CategoryBreakdown(category="FAKE_POSITIVE", count=1500),
        CategoryBreakdown(category="COMPETITOR_SABOTAGE", count=800),
        CategoryBreakdown(category="UNRELATED_CONTENT", count=300),
        CategoryBreakdown(category="INCENTIVIZED_REVIEW", count=200),
    ]

@app.get("/api/dashboard/top_flagged_products")
async def get_top_flagged_products(
    limit: int = 10,
    start_date: date = Query(default=(date.today() - timedelta(days=30))),
    end_date: date = Query(default=date.today())
) -> List[TopItem]:
    """Retrieves the top N products with the most flagged reviews."""
    # In a real app, query AggregatedMetrics table or join FlaggedReview with ReviewData
    return [
        TopItem(id="P001", name="Product A", flagged_count=50),
        TopItem(id="P002", name="Product B", flagged_count=45),
        TopItem(id="P003", name="Product C", flagged_count=30),
    ]
