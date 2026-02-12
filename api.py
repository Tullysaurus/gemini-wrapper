import os
from fastapi import FastAPI, HTTPException, Query, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import get_db, Question
from ai import process_gemini_request


load_dotenv()

# 2. Your Custom API Key (Front-end)
# Matches the `apiKey` variable in your JS
VALID_API_KEY = os.getenv("VALID_API_KEY")

app = FastAPI(title="Gemini API Mirror")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models (Matching your JS Payload) ---

class InlineData(BaseModel):
    mime_type: str
    data: str # This is the base64 string

class Part(BaseModel):
    text: Optional[str] = None
    inline_data: Optional[InlineData] = None

class Content(BaseModel):
    parts: List[Part]

# We define these even if we don't use them, so the API accepts the request
class ThinkingConfig(BaseModel):
    thinkingBudget: Optional[int] = None

class GenerationConfig(BaseModel):
    temperature: Optional[float] = None
    topP: Optional[float] = None
    topK: Optional[float] = None
    maxOutputTokens: Optional[int] = None
    thinkingConfig: Optional[ThinkingConfig] = None

class SafetySetting(BaseModel):
    category: str
    threshold: str

class GenerateContentRequest(BaseModel):
    contents: List[Content]
    generationConfig: Optional[GenerationConfig] = None
    safetySettings: Optional[List[SafetySetting]] = None

class QuestionQuery(BaseModel):
    questionId: str
    questionType: Optional[str] = None
    answerIds: Optional[List[str]] = None

class AnswerSubmission(BaseModel):
    questionId: str
    correctAnswers: Any
    answerType: Optional[str] = None

# --- Endpoints ---

@app.post("/ai")
async def generate_content(
    model: str, 
    request: GenerateContentRequest, 
    key: str = Query(..., description="The API Key") # catches ?key=... from JS
):
    # 1. Validate API Key
    if key != VALID_API_KEY:
        raise HTTPException(status_code=400, detail="Invalid API Key")

    try:
        prompt_text = ""
        image_data = None
        
        # 2. Parse the complex JS payload
        for content in request.contents:
            for part in content.parts:
                # Handle Text
                if part.text:
                    prompt_text += part.text + "\n"
                
                # Handle Image (Base64)
                if part.inline_data:
                    try:
                        image_data = base64.b64decode(part.inline_data.data)
                    except Exception:
                        print("Failed to decode base64 image")

        # 3. Call the Unofficial WebAPI
        response_text = await generate_response(prompt_text, image_data)

        # 4. Format Response to EXACTLY match what your JS expects
        # JS expects: result.candidates[0].content.parts[0].text
        formatted_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": response_text
                            }
                        ],
                        "role": "model"
                    },
                    "finishReason": "STOP",
                    "index": 0,
                    "safetyRatings": [] # Empty to satisfy schema if needed
                }
            ]
        }

        return formatted_response

    except Exception as e:
        print(f"Error: {e}")
        # Return a structure that your JS error handler catches (result.error.message)
        return {
            "error": {
                "code": 500,
                "message": str(e),
                "status": "INTERNAL_ERROR"
            }
        }

# --- UETS Endpoints ---

@app.post("/api/question")
async def query_question(query: QuestionQuery, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.question_id == query.questionId).first()
    if question:
        return {
            "hasAnswer": True,
            "correctAnswers": question.correct_answers,
            "questionType": question.answer_type or query.questionType
        }
    return {"hasAnswer": False}

@app.post("/api/answer")
async def submit_answer(submission: AnswerSubmission, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.question_id == submission.questionId).first()
    if question:
        question.correct_answers = submission.correctAnswers
        question.answer_type = submission.answerType
    else:
        question = Question(question_id=submission.questionId, correct_answers=submission.correctAnswers, answer_type=submission.answerType)
        db.add(question)
    db.commit()
    return {"status": "success"}