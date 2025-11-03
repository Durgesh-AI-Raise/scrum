from src.flagging_service import FlaggedReviewRepository
from src.review_ingestion import ReviewIngestionService
from src.review_details_service import ReviewDetailsService

def main():
    review_ingestion_service = ReviewIngestionService()
    flagged_review_repository = FlaggedReviewRepository()
    review_details_service = ReviewDetailsService(review_ingestion_service, flagged_review_repository)

    while True:
        print("\n--- Trust & Safety Review Dashboard ---")
        print("1. List all flagged reviews")
        print("2. View details of a specific flagged review")
        print("3. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            flagged_reviews = flagged_review_repository.get_all_flagged_reviews()
            if not flagged_reviews:
                print("No reviews currently flagged.")
            else:
                print("\n--- Flagged Reviews ---")
                for fr in flagged_reviews:
                    print(f"ID: {fr.review_id}, Type: {fr.flag_type}, Confidence: {fr.confidence_score:.2f}")
        elif choice == '2':
            review_id = input("Enter the ID of the flagged review to view: ")
            full_review_details = review_details_service.get_full_flagged_review_details(review_id)
            if full_review_details:
                print("\n--- Review Details ---")
                print(f"Review ID: {full_review_details['review_id']}")
                print(f"Flag Type: {full_review_details['flag_type']}")
                print(f"Confidence: {full_review_details['confidence_score']:.2f}")
                print(f"Original Text: {full_review_details['original_text']}")
                print(f"Reviewer ID (Anonymized): {full_review_details['reviewer_id']}")
            else:
                print(f"Review with ID '{review_id}' not found or not flagged.")
        elif choice == '3':
            print("Exiting dashboard.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()