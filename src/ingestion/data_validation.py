from datetime import datetime

def validate_review_data(data):
    errors = []

    # Validate Product Data
    product_data = data.get('product', {})
    if not product_data.get('product_id'):
        errors.append("Product ID is missing.")
    if not product_data.get('product_name'):
        errors.append("Product Name is missing.")

    # Validate Reviewer Data
    reviewer_data = data.get('reviewer', {})
    if not reviewer_data.get('reviewer_id'):
        errors.append("Reviewer ID is missing.")
    if not reviewer_data.get('reviewer_name'):
        errors.append("Reviewer Name is missing.")
    if reviewer_data.get('account_creation_date'):
        try:
            datetime.fromisoformat(reviewer_data['account_creation_date'].replace('Z', '+00:00'))
        except ValueError:
            errors.append("Invalid Account Creation Date format. Expected ISO 8601.")

    # Validate Order Data (optional for review, but good to validate if present)
    order_data = data.get('order', {})
    if order_data.get('order_id') and not order_data.get('reviewer_id'):
        errors.append("Order has an ID but missing associated Reviewer ID.")
    if order_data.get('order_date'):
        try:
            datetime.fromisoformat(order_data['order_date'].replace('Z', '+00:00'))
        except ValueError:
            errors.append("Invalid Order Date format. Expected ISO 8601.")

    # Validate Review Data
    review_data = data.get('review', {})
    if not review_data.get('review_id'):
        errors.append("Review ID is missing.")
    if not review_data.get('product_id'):
        errors.append("Review Product ID is missing.")
    if not review_data.get('reviewer_id'):
        errors.append("Review Reviewer ID is missing.")
    if not review_data.get('content'):
        errors.append("Review content is empty.")
    
    rating = review_data.get('rating')
    if rating is None:
        errors.append("Review rating is missing.")
    else:
        try:
            rating = int(rating)
            if not (1 <= rating <= 5):
                errors.append("Review rating must be an integer between 1 and 5.")
        except ValueError:
            errors.append("Review rating is not a valid integer.")

    if review_data.get('review_date'):
        try:
            datetime.fromisoformat(review_data['review_date'].replace('Z', '+00:00'))
        except ValueError:
            errors.append("Invalid Review Date format. Expected ISO 8601.")
    else:
        errors.append("Review date is missing.")

    return {'is_valid': len(errors) == 0, 'errors': errors}