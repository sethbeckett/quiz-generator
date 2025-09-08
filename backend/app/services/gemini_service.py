"""
Service for interacting with Google Gemini API to generate quizzes.
"""

import json
import logging

import google.generativeai as genai

from ..config import settings
from ..schemas.quiz import (
    FeedbackItem,
    FeedbackRequest,
    FeedbackResponse,
    GeminiQuizResponse,
)

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for generating quizzes using Google Gemini API."""

    def __init__(self):
        """Initialize the Gemini service with API client."""
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    def _create_quiz_prompt(self, topic: str, num_questions: int = 5) -> str:
        """
        Create a structured prompt for quiz generation.

        Args:
            topic: The topic for the quiz
            num_questions: Number of questions to generate

        Returns:
            Formatted prompt string
        """
        return f"""Generate a multiple-choice quiz about "{topic}".

Requirements:
- Create exactly {num_questions} questions
- Each question should have exactly 4 options (A, B, C, D)
- Only one option should be correct
- Questions should be factual and educational
- Include a brief explanation for each correct answer
- Vary the difficulty from basic to intermediate
- Use current, accurate information

Use the search tool to find up-to-date and accurate information about {topic} to ensure factual correctness.

Return the response as a JSON object with this exact structure:
{{
    "topic": "{topic}",
    "difficulty_level": "medium",
    "questions": [
        {{
            "question": "Question text here?",
            "options": {{
                "A": "First option",
                "B": "Second option",
                "C": "Third option",
                "D": "Fourth option"
            }},
            "correct_answer": "A",
            "explanation": "Brief explanation of why this answer is correct"
        }}
    ]
}}

Make sure the JSON is valid and properly formatted."""

    async def generate_quiz(
        self, topic: str, num_questions: int = 5
    ) -> GeminiQuizResponse | None:
        """
        Generate a quiz using Gemini API with search grounding.

        Args:
            topic: The topic for the quiz
            num_questions: Number of questions to generate (default: 5)

        Returns:
            GeminiQuizResponse object or None if generation fails
        """
        try:
            prompt = self._create_quiz_prompt(topic, num_questions)

            # Configure the generation with structured output
            model = genai.GenerativeModel(self.model)
            response = await model.generate_content_async(prompt)

            if not response.text:
                logger.error("Empty response from Gemini API")
                return None

            # Parse the JSON response (handle markdown-wrapped JSON)
            try:
                response_text = response.text.strip()

                # Check if response is wrapped in markdown code blocks
                if response_text.startswith("```json") and response_text.endswith(
                    "```"
                ):
                    # Extract JSON from markdown code block
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.rfind("```")
                    response_text = response_text[json_start:json_end].strip()
                elif response_text.startswith("```") and response_text.endswith("```"):
                    # Handle generic code blocks
                    json_start = response_text.find("```") + 3
                    json_end = response_text.rfind("```")
                    response_text = response_text[json_start:json_end].strip()

                quiz_data = json.loads(response_text)
                quiz_response = GeminiQuizResponse(**quiz_data)

                # Validate business rules
                if not self._validate_quiz_business_rules(quiz_response, num_questions):
                    logger.error("Generated quiz does not meet business rules")
                    return None

                return quiz_response
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw response: {response.text}")
                return None
            except Exception as e:
                logger.error(f"Failed to validate response schema: {e}")
                return None

        except Exception as e:
            logger.error(f"Error generating quiz with Gemini API: {e}")
            return None

    async def explain_incorrect_answers(
        self, payload: FeedbackRequest
    ) -> FeedbackResponse | None:
        """
        Ask the model for brief explanations for incorrect answers.

        The prompt enforces concise, factual, 2–3 sentence explanations.
        """
        try:
            # Build a compact prompt
            bullet_lines = []
            for item in payload.items:
                bullet_lines.append(
                    f"- QID {item.question_id}: Q='{item.question_text}' | you='{item.user_selected}. {item.user_selected_text}' | correct='{item.correct_option}. {item.correct_text}'"
                )

            prompt = (
                "You are an instructor. For each question below, explain in 2–3 short sentences why the user-selected answer is incorrect and why the correct answer is right. "
                'Use plain language, no hedging, and avoid repeating the full question text. Output strict JSON array with items of the form {"question_id": number, "explanation": string}.\n\n'
                f"Topic: {payload.topic}\nQuestions:\n" + "\n".join(bullet_lines)
            )

            model = genai.GenerativeModel(self.model)
            response = await model.generate_content_async(prompt)
            if not response.text:
                return None

            text = response.text.strip()
            if text.startswith("```json") and text.endswith("```"):
                text = text[text.find("```json") + 7 : text.rfind("```")].strip()
            elif text.startswith("```") and text.endswith("```"):
                text = text[text.find("```") + 3 : text.rfind("```")].strip()

            parsed = json.loads(text)
            items = [
                FeedbackItem(question_id=i["question_id"], explanation=i["explanation"])
                for i in parsed
            ]
            return FeedbackResponse(items=items)
        except Exception as e:
            logger.error(f"Failed to get feedback explanations: {e}")
            return None

    def _validate_quiz_business_rules(
        self, quiz_response: GeminiQuizResponse, expected_questions: int
    ) -> bool:
        """
        Validate that the generated quiz meets business rules.

        Args:
            quiz_response: The generated quiz response
            expected_questions: Expected number of questions

        Returns:
            True if all business rules are met, False otherwise
        """
        try:
            # Check number of questions
            if len(quiz_response.questions) != expected_questions:
                logger.warning(
                    f"Expected {expected_questions} questions, got {len(quiz_response.questions)}"
                )
                return False

            # Check each question
            for i, question in enumerate(quiz_response.questions):
                # Check that question has text
                if not question.question or len(question.question.strip()) == 0:
                    logger.warning(f"Question {i+1} has empty text")
                    return False

                # Check number of options (should be exactly 4: A, B, C, D)
                if len(question.options) != settings.default_options_per_question:
                    logger.warning(
                        f"Question {i+1} has {len(question.options)} options, expected {settings.default_options_per_question}"
                    )
                    return False

                # Check that we have exactly A, B, C, D options
                expected_letters = {"A", "B", "C", "D"}
                actual_letters = set(question.options.keys())
                if actual_letters != expected_letters:
                    logger.warning(
                        f"Question {i+1} has incorrect option letters: {actual_letters}"
                    )
                    return False

                # Check that correct_answer is one of the option letters
                if question.correct_answer not in question.options:
                    logger.warning(
                        f"Question {i+1} correct answer '{question.correct_answer}' not in options"
                    )
                    return False

                # Check that all options have non-empty text
                for letter, option_text in question.options.items():
                    if not option_text or len(option_text.strip()) == 0:
                        logger.warning(
                            f"Question {i+1}, option {letter} has empty text"
                        )
                        return False

            logger.info("Quiz validation passed all business rules")
            return True

        except Exception as e:
            logger.error(f"Error validating quiz business rules: {e}")
            return False

    def validate_topic(self, topic: str) -> bool:
        """
        Validate if a topic is appropriate for quiz generation.

        Args:
            topic: The topic to validate

        Returns:
            True if topic is valid, False otherwise
        """
        if not topic or len(topic.strip()) == 0:
            return False

        if len(topic) > settings.max_topic_length:
            return False

        # Basic content filtering - avoid inappropriate topics
        inappropriate_keywords = ["explicit", "nsfw", "adult", "violence"]
        topic_lower = topic.lower()

        return all(keyword not in topic_lower for keyword in inappropriate_keywords)

    async def test_api_connection(self) -> bool:
        """
        Test the connection to Gemini API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            model = genai.GenerativeModel(self.model)
            response = await model.generate_content_async(
                "Hello, can you respond with 'API connection successful'?"
            )
            return "API connection successful" in response.text
        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return False


# Global service instance (lazily available during tests without API key)
try:
    gemini_service = GeminiService()
except Exception:
    # In test environments without GEMINI_API_KEY, allow import and let tests patch this symbol
    gemini_service = None  # type: ignore
