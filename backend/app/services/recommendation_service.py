from typing import List
from sqlalchemy.orm import Session
from app.db.models import Recommendation, Progress, Quiz


def generate_recommendations_for_user(user_id: str, db: Session) -> List[Recommendation]:
    """
    Generate authentic personalized study recommendations based on student performance signals:
    - Low mastery score (< 70%) -> High Priority Revision
    - Low recent score (< 70%) -> Practice Quiz
    - High mastery (>= 85%) -> Continue Learning / Next Concept
    - Single attempt / early stage -> Practice reinforcement
    Deduplicates active recommendations per user.
    """
    progress_records = db.query(Progress).filter(Progress.user_id == user_id).all()
    if not progress_records:
        return []

    created_or_updated = []

    for prog in progress_records:
        topic = prog.topic
        mastery = prog.mastery_score
        recent_score = prog.latest_score if prog.latest_score is not None else mastery
        attempts = prog.quiz_attempts or 1

        rec_type = "Practice"
        priority = "medium"
        reason = ""
        action_label = "Practice Now"
        title = f"Study {topic}"
        description = ""

        if mastery < 60 or recent_score < 60:
            rec_type = "Revision"
            priority = "high"
            reason = f"Your latest score on {topic} was {recent_score}%, indicating key concepts require reinforcement."
            title = f"Revision Needed: {topic}"
            description = f"Review the foundational definitions and examples for {topic} before your next assessment."
            action_label = "Review Flashcards & Notes"
        elif mastery < 75 or recent_score < 75:
            rec_type = "Practice"
            priority = "medium"
            reason = f"Mastery on {topic} is currently {mastery}%. A short practice quiz will solidify memory retention."
            title = f"Practice Quiz: {topic}"
            description = f"Take a 5-question adaptive quiz on {topic} to raise your topic mastery above 80%."
            action_label = "Take Practice Quiz"
        elif mastery >= 85:
            rec_type = "Continue Learning"
            priority = "low"
            reason = f"Excellent mastery of {mastery}% on {topic}. You are prepared to advance to higher-level topics."
            title = f"Mastery Achieved: {topic}"
            description = f"Congratulations on mastering {topic}! Continue exploring advanced questions or adjacent course concepts."
            action_label = "Explore Advanced Topics"
        else:
            rec_type = "Quiz"
            priority = "medium"
            reason = f"Consistent progress on {topic} with {attempts} quiz session(s) recorded."
            title = f"Solidify Knowledge: {topic}"
            description = f"Test yourself on edge-cases and deeper applications of {topic}."
            action_label = "Take Quiz"

        # Check if an existing recommendation with same topic and type exists
        existing = (
            db.query(Recommendation)
            .filter(
                Recommendation.user_id == user_id,
                Recommendation.topic == topic,
                Recommendation.recommendation_type == rec_type,
            )
            .first()
        )

        if existing:
            existing.title = title
            existing.description = description
            existing.priority = priority
            existing.reason = reason
            existing.action_label = action_label
            created_or_updated.append(existing)
        else:
            rec = Recommendation(
                user_id=user_id,
                title=title,
                description=description,
                topic=topic,
                priority=priority,
                recommendation_type=rec_type,
                reason=reason,
                action_label=action_label,
            )
            db.add(rec)
            created_or_updated.append(rec)

    db.commit()
    return created_or_updated
