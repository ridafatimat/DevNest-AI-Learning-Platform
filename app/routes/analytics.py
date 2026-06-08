from fastapi import APIRouter
from ..firebase import db

router = APIRouter(prefix="/analytics")  # <-- top-level, not inside a function

@router.get("/user/{userId}")
def user_analytics(userId: str):
    reviews = db.collection("AIReview") \
                .where("submissionId", ">=", f"{userId}-") \
                .stream()

    count = 0
    conf_total = 0

    for r in reviews:
        d = r.to_dict()
        count += 1
        conf_total += float(d.get("confidence", 0))

    return {
        "userId": userId,
        "reviews_count": count,
        "avg_confidence": conf_total / count if count else 0,
        "topicsPracticed": []
    }
