import json
import re
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.core.config import settings
from app.db.models import User, Document, DocumentChunk, Quiz, Question, Progress
from app.services.ai_service import generate_embedding, get_gemini_client
from app.services.recommendation_service import generate_recommendations_for_user


def retrieve_semantic_chunks_for_quiz(
    user_id: str,
    topic: str,
    document_id: Optional[str],
    db: Session,
    top_k: int = 6,
) -> List[DocumentChunk]:
    """
    Perform semantic vector search using pgvector cosine distance to find top chunks
    relevant to the quiz topic, strictly scoped to the authenticated user and document.
    """
    query_text = topic if topic and topic.strip() else "Core principles and key concepts"
    query_vector = generate_embedding(query_text)

    # Base query joined with Document for strict user ownership
    stmt = (
        select(DocumentChunk)
        .join(Document, DocumentChunk.document_id == Document.id)
        .filter(Document.user_id == user_id, Document.status == "Ready")
    )

    if document_id:
        stmt = stmt.filter(Document.id == document_id)

    # Order by cosine distance (<-> operator in pgvector)
    stmt = stmt.order_by(DocumentChunk.embedding.cosine_distance(query_vector)).limit(top_k)

    results = db.execute(stmt).scalars().all()
    return list(results)


def parse_and_validate_quiz_json(raw_text: str, expected_count: int, default_topic: str) -> List[Dict[str, Any]]:
    """
    Validate that Gemini's output matches all strict quiz specifications:
    - Valid JSON list or object with 'questions' key
    - Exactly expected_count items
    - Each item has question, exactly 4 unique options, correct_answer matching one option, non-empty explanation, non-empty topic
    """
    cleaned = raw_text.strip()
    # Strip markdown fences if present
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
    except Exception as e:
        raise ValueError(f"AI response is not valid JSON: {str(e)}")

    if isinstance(data, dict):
        if "questions" in data and isinstance(data["questions"], list):
            questions_list = data["questions"]
        elif "quiz" in data and isinstance(data["quiz"], list):
            questions_list = data["quiz"]
        else:
            questions_list = [data]
    elif isinstance(data, list):
        questions_list = data
    else:
        raise ValueError("AI JSON root must be a list or an object with 'questions'")

    if len(questions_list) != expected_count:
        raise ValueError(f"Question count mismatch: expected {expected_count}, got {len(questions_list)}")

    validated = []
    for idx, q in enumerate(questions_list):
        if not isinstance(q, dict):
            raise ValueError(f"Question #{idx+1} must be an object")

        q_text = str(q.get("question") or q.get("question_text") or "").strip()
        if not q_text or len(q_text) < 5:
            raise ValueError(f"Question #{idx+1} text is empty or too short")

        raw_options = q.get("options")
        if not isinstance(raw_options, list) or len(raw_options) != 4:
            raise ValueError(f"Question #{idx+1} must contain exactly 4 options, got {len(raw_options) if isinstance(raw_options, list) else 'none'}")

        clean_options = [str(opt).strip() for opt in raw_options]
        if any(not opt for opt in clean_options):
            raise ValueError(f"Question #{idx+1} contains empty option strings")

        if len(set(clean_options)) != 4:
            raise ValueError(f"Question #{idx+1} options contain duplicates")

        correct = str(q.get("correct_answer") or "").strip()
        if not correct:
            raise ValueError(f"Question #{idx+1} missing correct_answer")

        # Verify correct answer matches one option verbatim or case-insensitively
        matching_opt = next((opt for opt in clean_options if opt.lower() == correct.lower()), None)
        if not matching_opt:
            raise ValueError(f"Question #{idx+1} correct_answer '{correct}' does not match any of the options: {clean_options}")

        explanation = str(q.get("explanation") or "").strip()
        if not explanation:
            explanation = f"The correct answer is '{matching_opt}' based on the retrieved study materials."

        topic = str(q.get("topic") or default_topic).strip() or default_topic

        validated.append({
            "question_text": q_text,
            "options": clean_options,
            "correct_answer": matching_opt,
            "explanation": explanation,
            "topic": topic,
        })

    return validated


def generate_fallback_quiz_from_chunks(
    chunks: List[DocumentChunk],
    topic: str,
    difficulty: str,
    num_questions: int,
) -> List[Dict[str, Any]]:
    """
    Offline/Test deterministic generator extracting facts directly from retrieved chunks.
    Guarantees strict format conformance when Gemini API is unavailable or rate-limited.
    """
    combined_sentences = []
    for ch in chunks:
        sentences = [s.strip() for s in re.split(r"[.!?]\s+", ch.content) if len(s.strip()) > 20]
        combined_sentences.extend(sentences)

    if not combined_sentences:
        combined_sentences = [f"Key fundamental concept regarding {topic} involves structured analytical reasoning."]

    questions = []
    for i in range(num_questions):
        sentence = combined_sentences[i % len(combined_sentences)]
        words = [w for w in sentence.split() if len(w) > 4]
        keyword = words[0] if words else "Principle"

        q_text = f"According to the study material on {topic}, which statement correctly describes {keyword}?"
        correct_option = f"Correct: {sentence}."
        distractor1 = f"Incorrect: {sentence.replace('is', 'is never').replace('can', 'cannot')}."
        distractor2 = f"Alternative: {keyword} is exclusively utilized in unrelated domain architectures."
        distractor3 = f"Constraint: The parameter has zero operational correlation with {topic}."

        options = [correct_option, distractor1, distractor2, distractor3]
        # Rotate options so correct answer isn't always at index 0
        rot = i % 4
        options = options[rot:] + options[:rot]

        questions.append({
            "question_text": q_text,
            "options": options,
            "correct_answer": correct_option,
            "explanation": f"As documented in your study material: '{sentence}'.",
            "topic": topic,
        })

    return questions


def create_quiz_pipeline(
    user_id: str,
    topic: str,
    difficulty: str,
    num_questions: int,
    document_id: Optional[str],
    db: Session,
) -> Quiz:
    """
    Complete end-to-end Quiz generation:
    1. Retrieve relevant chunks via pgvector cosine distance search.
    2. Prompt Gemini for strictly grounded multiple choice questions.
    3. Validate JSON output strictly.
    4. Save Quiz and Questions to PostgreSQL.
    """
    # 1. Retrieve chunks
    chunks = retrieve_semantic_chunks_for_quiz(user_id, topic, document_id, db, top_k=6)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No study material found for this topic. Please upload and process a document first.",
        )

    context_text = "\n\n".join(
        [f"[Chunk {idx+1} - Page {c.page_number}]:\n{c.content}" for idx, c in enumerate(chunks)]
    )

    # 2. Query Gemini
    prompt = (
        f"You are an expert university examiner. Generate a {difficulty}-difficulty multiple-choice quiz "
        f"with EXACTLY {num_questions} questions on the topic '{topic}'.\n\n"
        f"STRICT GROUNDING INSTRUCTIONS:\n"
        f"1. You MUST generate questions ONLY from the provided Retrieved Study Material.\n"
        f"2. Do NOT use outside facts. Do NOT invent details.\n"
        f"3. Return ONLY a valid JSON array of {num_questions} objects, with NO markdown fences and NO extra text.\n\n"
        f"JSON Schema per question:\n"
        f"[\n"
        f"  {{\n"
        f'    "question": "Question text here",\n'
        f'    "options": ["Option A", "Option B", "Option C", "Option D"],\n'
        f'    "correct_answer": "Exact string matching one of the options",\n'
        f'    "explanation": "Explanation grounded in the source text",\n'
        f'    "topic": "{topic}"\n'
        f"  }}\n"
        f"]\n\n"
        f"Retrieved Study Material:\n{context_text}"
    )

    validated_questions = None
    client = get_gemini_client()

    if client:
        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
            )
            if response and response.text:
                validated_questions = parse_and_validate_quiz_json(response.text, num_questions, topic)
        except Exception as e:
            print(f"[Quiz Generator] Gemini API call or validation failed: {e}. Utilizing fallback generator.")

    # Use grounded fallback if Gemini is offline, test environment, or validation failed
    if not validated_questions:
        validated_questions = generate_fallback_quiz_from_chunks(chunks, topic, difficulty, num_questions)

    # 3. Persist Quiz and Questions
    quiz = Quiz(
        user_id=user_id,
        document_id=document_id,
        title=f"{topic} Quiz",
        topic=topic,
        difficulty=difficulty,
        score=None,
    )
    db.add(quiz)
    db.flush()

    for q in validated_questions:
        question_row = Question(
            quiz_id=quiz.id,
            question_text=q["question_text"],
            options=json.dumps(q["options"]),
            correct_answer=q["correct_answer"],
            explanation=q["explanation"],
            topic=q["topic"],
        )
        db.add(question_row)

    db.commit()
    db.refresh(quiz)
    return quiz


def grade_quiz_submission(
    quiz_id: str,
    user_id: str,
    user_answers: Dict[str, str],
    db: Session,
) -> Dict[str, Any]:
    """
    Authoritative server-side grading and mastery update:
    1. Retrieve stored Quiz and Question entities.
    2. Check ownership and validate question count.
    3. Calculate score and question correctness.
    4. Update Progress topic record with exponential moving average mastery.
    5. Trigger recommendation signals.
    """
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.user_id == user_id).first()
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found.")

    questions = db.query(Question).filter(Question.quiz_id == quiz.id).all()
    if not questions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot grade an empty quiz with 0 questions.")

    correct_count = 0
    question_results = []

    for q in questions:
        options = json.loads(q.options) if isinstance(q.options, str) else q.options
        student_ans = user_answers.get(q.id)
        is_correct = False

        if student_ans:
            is_correct = (student_ans.strip().lower() == q.correct_answer.strip().lower())

        if is_correct:
            correct_count += 1

        question_results.append({
            "question_id": q.id,
            "question_text": q.question_text,
            "options": options,
            "student_answer": student_ans,
            "correct_answer": q.correct_answer,
            "is_correct": is_correct,
            "explanation": q.explanation,
            "topic": q.topic or quiz.topic,
        })

    total_questions = len(questions)
    percentage = round((correct_count / total_questions) * 100.0, 1)

    # Update Quiz score
    quiz.score = percentage
    db.commit()

    # Update Student Topic Progress
    topic_name = quiz.topic or "General Study"
    progress = (
        db.query(Progress)
        .filter(Progress.user_id == user_id, Progress.topic == topic_name)
        .first()
    )

    if not progress:
        progress = Progress(
            user_id=user_id,
            topic=topic_name,
            mastery_score=percentage,
            questions_attempted=total_questions,
            questions_correct=correct_count,
            quiz_attempts=1,
            latest_score=percentage,
            average_score=percentage,
            last_studied_at=func.now(),
        )
        db.add(progress)
    else:
        # Moving average mastery formula:
        # 70% weight on latest score, 30% weight on accumulated mastery
        progress.mastery_score = round((0.7 * percentage) + (0.3 * progress.mastery_score), 1)
        prev_attempts = progress.quiz_attempts or 0
        progress.quiz_attempts = prev_attempts + 1
        progress.questions_attempted += total_questions
        progress.questions_correct += correct_count
        progress.latest_score = percentage
        prev_avg = progress.average_score if progress.average_score is not None else progress.mastery_score
        progress.average_score = round(((prev_avg * prev_attempts) + percentage) / progress.quiz_attempts, 1)
        progress.last_studied_at = func.now()

    db.commit()

    # Update recommendations based on learning signals
    try:
        generate_recommendations_for_user(user_id, db)
    except Exception as e:
        print(f"[Quiz Service] Recommendation trigger error: {e}")

    return {
        "quiz_id": quiz.id,
        "title": quiz.title,
        "topic": quiz.topic,
        "difficulty": quiz.difficulty,
        "score": percentage,
        "percentage": percentage,
        "total_questions": total_questions,
        "correct_count": correct_count,
        "question_results": question_results,
        "created_at": quiz.created_at,
    }
