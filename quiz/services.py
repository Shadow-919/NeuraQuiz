"""
AI Services for NeuraQuiz
Handles Gemini API integration for question generation and distractor creation
"""

import json
from django.conf import settings
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Raised when the Gemini API signals a rate limit / quota exceeded condition.

    Attributes:
        retry_after: Optional[int] number of seconds suggested to wait before retrying.
    """
    def __init__(self, message, retry_after=None):
        super().__init__(message)
        if retry_after is not None:
            try:
                self.retry_after = int(float(str(retry_after).strip()))
                if self.retry_after <= 0:
                    self.retry_after = None
            except (ValueError, TypeError):
                self.retry_after = None
        else:
            self.retry_after = None

# Try to import google.generativeai, fallback if not available
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None


class GeminiService:
    """Service class for interacting with Google Gemini API"""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if not GEMINI_AVAILABLE:
            # Use debug-level logging so dev server output isn't noisy when library is missing
            logger.debug("Google Generative AI library not installed. AI features will be disabled.")
            self.is_configured = False
        elif not self.api_key:
            # No API key provided
            logger.debug("Gemini API key not configured (empty). AI features will be disabled.")
            self.is_configured = False
        else:
            # Try to configure the client and instantiate the model. If anything fails, mark as not configured
            try:
                genai.configure(api_key=self.api_key)
                # If the user set a preferred model name in settings, try it first.
                preferred = getattr(settings, 'GEMINI_MODEL_NAME', '')
                model_instantiated = False
                if preferred:
                    try:
                        self.model = genai.GenerativeModel(preferred)
                        model_instantiated = True
                        logger.info(f"Gemini model initialized using preferred model '{preferred}'")
                    except Exception as e:
                        logger.warning(f"Preferred Gemini model '{preferred}' failed to initialize: {e}")

                # Try a few common model names (short names are accepted by GenerativeModel which prefixes 'models/')
                if not model_instantiated:
                    tried_models = ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-2.5-pro-preview-03-25', 'gemini-pro-latest']
                    for mname in tried_models:
                        try:
                            self.model = genai.GenerativeModel(mname)
                            model_instantiated = True
                            logger.info(f"Gemini model initialized using '{mname}'")
                            break
                        except Exception:
                            continue

                # If still not found, list available models and pick the first that supports generateContent
                if not model_instantiated:
                    try:
                        for entry in genai.list_models() or []:
                            candidate = None
                            # Try to get a clean model name from the entry
                            if isinstance(entry, str):
                                candidate = entry
                            elif isinstance(entry, dict):
                                candidate = entry.get('name') or entry.get('id') or entry.get('model')
                            else:
                                candidate = getattr(entry, 'name', None) or getattr(entry, 'id', None)

                            if not candidate:
                                continue

                            # Only pick models that advertise generateContent
                            try:
                                supported = getattr(entry, 'supported_generation_methods', None)
                                if supported is None and isinstance(entry, dict):
                                    supported = entry.get('supported_generation_methods')
                                if supported and 'generateContent' not in supported:
                                    continue
                            except Exception:
                                pass

                            try:
                                self.model = genai.GenerativeModel(candidate)
                                model_instantiated = True
                                logger.info(f"Gemini model initialized using discovered model '{candidate}'")
                                break
                            except Exception:
                                continue
                    except Exception as e:
                        logger.debug(f"Could not list models: {e}")

                if model_instantiated:
                    self.is_configured = True
                    logger.info("Gemini service configured (client initialized).")
                else:
                    raise RuntimeError('No usable Gemini model found')
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.is_configured = False
    
    def generate_questions(self, topic: str, num_questions: int = 10, difficulty: str = 'medium', additional_instructions: str = '', debug_save: bool = False) -> List[Dict[str, Any]]:
        """
        Generate quiz questions using Gemini API
        
        Args:
            topic: The topic for the quiz
            num_questions: Number of questions to generate
            difficulty: Difficulty level (easy, medium, hard)
        
        Returns:
            List of generated questions
        """
        if not self.is_configured:
            return []

        try:
            prompt = f"""
You are an expert quiz content creator. Generate {num_questions} mixed-type questions about the topic: "{topic}" at {difficulty} difficulty.

{additional_instructions.strip() if additional_instructions else ''}

Return MUST be valid JSON only (no extra text). If you include code fences, put the JSON inside triple backticks (```json ... ```).

For each question object include the following fields exactly:
- question_type: one of ["mcq_single", "mcq_multiple", "true_false", "short_answer"]
- question_text: string
- choices: array of strings (for MCQ types, include exactly 4 choices; otherwise empty array)
- correct_answer: for MCQ, comma-separated indices (0-based) of correct choices; for true_false use "true" or "false"; for short_answer include the answer string
- explanation: short explanation string

Example output (the model should follow this structure exactly):
```json
[
    {{
        "question_type": "mcq_single",
        "question_text": "What is 2+2?",
        "choices": ["1","2","4","3"],
        "correct_answer": "2",
        "explanation": "2+2 equals 4"
    }}
]
```
"""
            response = self.model.generate_content(prompt)

            # Defensive extraction of text from response. Different SDK versions return the content
            # in different attributes (text, candidates, etc.). Log the raw response for debugging.
            try:
                logger.debug(f"Raw generate_content response repr: {repr(response)}")
            except Exception:
                pass

            raw = None
            # Preferred simple attribute
            if hasattr(response, 'text') and getattr(response, 'text'):
                raw = response.text

            # Try candidates -> content -> parts -> text
            if not raw and hasattr(response, 'candidates'):
                try:
                    cand_texts = []
                    for cand in getattr(response, 'candidates') or []:
                        # cand.content may be a Content object; try to extract .text or .parts
                        c = getattr(cand, 'content', None) or cand
                        if hasattr(c, 'text') and c.text:
                            cand_texts.append(c.text)
                        else:
                            # try parts
                            parts = getattr(c, 'parts', None)
                            if parts:
                                for p in parts:
                                    if hasattr(p, 'text') and p.text:
                                        cand_texts.append(p.text)
                    if cand_texts:
                        raw = '\n'.join(cand_texts)
                except Exception:
                    raw = None

            # As a last resort, try str(response)
            if not raw:
                try:
                    raw = str(response)
                except Exception:
                    raw = ''

            raw = (raw or '').strip()

            # Optional one-off debug: save raw model response to a log file for inspection
            if debug_save:
                try:
                    import datetime
                    with open('ai_generation_debug.log', 'a', encoding='utf-8') as f:
                        f.write('--- AI GENERATION DEBUG ' + datetime.datetime.utcnow().isoformat() + ' UTC ---\n')
                        f.write(f'Topic: {topic}\nRequested num_questions: {num_questions}\nDifficulty: {difficulty}\n')
                        f.write('Raw response:\n')
                        f.write(raw[:10000] + ('\n...[truncated]\n' if len(raw) > 10000 else '\n'))
                except Exception:
                    logger.exception('Failed to write AI debug log')

            if not raw:
                logger.error('Empty response from Gemini model')
                return []

            # Extract JSON content from the raw text if model wrapped it in markdown fences or extra text
            import re
            json_text = None

            # First try to find a JSON array in the text
            m = re.search(r"(\[.*\])", raw, flags=re.DOTALL)
            if m:
                json_text = m.group(1)
            else:
                # Try to find a JSON object (fallback)
                m2 = re.search(r"(\{.*\})", raw, flags=re.DOTALL)
                if m2:
                    json_text = m2.group(1)

            if not json_text:
                # No JSON detected — attempt to parse the whole text
                try:
                    questions_data = json.loads(raw)
                except Exception as e:
                    logger.error(f"Error parsing model response as JSON. Raw response:\n{raw}\nParse error: {e}")
                    if debug_save:
                        try:
                            with open('ai_generation_debug.log', 'a', encoding='utf-8') as f:
                                f.write('--- JSON PARSE ERROR ---\n')
                                f.write(f'Error: {str(e)}\nRaw text:\n{raw}\n')
                        except Exception:
                            pass
                    return []
            else:
                try:
                    questions_data = json.loads(json_text)
                except Exception as e:
                    logger.error(f"Failed to parse extracted JSON from model response. Extracted:\n{json_text}\nError: {e}")
                    if debug_save:
                        try:
                            with open('ai_generation_debug.log', 'a', encoding='utf-8') as f:
                                f.write('--- JSON PARSE ERROR ---\n')
                                f.write(f'Error: {str(e)}\nExtracted JSON:\n{json_text}\n')
                        except Exception:
                            pass
                    return []

            # Validate, deduplicate and cap the data to requested number
            validated_questions = []
            seen_texts = set()
            if isinstance(questions_data, list):
                for q in questions_data:
                    if not self._validate_question(q):
                        continue
                    # Deduplicate by normalized question text
                    text_norm = (q.get('question_text') or '').strip().lower()
                    if text_norm in seen_texts:
                        continue
                    seen_texts.add(text_norm)
                    validated_questions.append(q)
                    if len(validated_questions) >= int(num_questions):
                        break
            else:
                logger.error(f"Model returned JSON but it was not a list: {type(questions_data)}")
                return []

            # If the model returned fewer unique questions than requested, that's okay.
            return validated_questions
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            return []

    def generate_questions_demo(self, topic: str, num_questions: int = 10, difficulty: str = 'medium') -> List[Dict[str, Any]]:
        """Generate simple demo questions locally when Gemini is not available."""
        questions = []
        for i in range(int(num_questions)):
            qtype = ['mcq_single', 'mcq_multiple', 'true_false', 'short_answer'][i % 4]
            if qtype == 'mcq_single' or qtype == 'mcq_multiple':
                choices = [f"{topic} option {j+1}" for j in range(4)]
                correct = '1' if qtype == 'mcq_single' else '1,2'
                questions.append({
                    'question_type': qtype,
                    'question_text': f"{topic} demo question {i+1}",
                    'choices': choices,
                    'correct_answer': correct,
                    'explanation': f"Explanation for {topic} demo question {i+1}"
                })
            elif qtype == 'true_false':
                questions.append({
                    'question_type': 'true_false',
                    'question_text': f"{topic} demo true/false question {i+1}",
                    'choices': [],
                    'correct_answer': 'true' if (i % 2 == 0) else 'false',
                    'explanation': f"Explanation for {topic} demo TF question {i+1}"
                })
            else:
                questions.append({
                    'question_type': 'short_answer',
                    'question_text': f"{topic} demo short answer question {i+1}",
                    'choices': [],
                    'correct_answer': f"Demo answer {i+1}",
                    'explanation': f"Explanation for {topic} demo short question {i+1}"
                })

        return questions
    
    def generate_distractors(self, question_text: str, correct_answer: str, num_distractors: int = 3) -> List[Dict[str, Any]]:
        """
        Generate plausible distractors for a given correct answer
        
        Args:
            question_text: The question text
            correct_answer: The correct answer
            num_distractors: Number of distractors to generate
        
        Returns:
            List of generated distractors with plausibility scores
        """
        if not self.is_configured:
            return []
        
        try:
            prompt = f"""
            You are an assistant generating high-quality distractors for a quiz.
            
            Given the correct answer "{correct_answer}" and question "{question_text}",
            create {num_distractors} plausible but incorrect answer options that are not semantically identical.
            
            Rate each distractor on a scale of 0–1 for plausibility.
            
            Return JSON with fields: distractor_text, plausibility_score.
            Output as a JSON array.
            """
            
            response = self.model.generate_content(prompt)
            distractors_data = json.loads(response.text)
            
            # Filter out distractors with low plausibility scores
            filtered_distractors = [
                d for d in distractors_data 
                if d.get('plausibility_score', 0) > 0.3
            ]
            
            return filtered_distractors
            
        except Exception as e:
            logger.error(f"Error generating distractors: {str(e)}")
            return []
    
    def generate_quiz_insights(self, attempt_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate AI insights about quiz performance
        
        Args:
            attempt_data: Dictionary containing quiz attempt information
        
        Returns:
            List of AI insights
        """
        if not self.is_configured:
            return []
        
        try:
            prompt = f"""
            Analyze this quiz performance data and provide insights:
            
            Quiz: {attempt_data.get('quiz_title', 'Unknown')}
            Score: {attempt_data.get('score', 0)}%
            Time Taken: {attempt_data.get('time_taken', 0)} seconds
            Correct Answers: {attempt_data.get('correct_answers', 0)}/{attempt_data.get('total_questions', 0)}
            Difficulty Distribution: {attempt_data.get('difficulty_breakdown', {})}
            
            Provide 3-5 insights in the following format:
            - insight_type (strength, weakness, recommendation, performance_tip)
            - content (detailed insight text)
            - confidence_score (0.0 to 1.0)
            
            Output as a JSON array.
            """
            
            response = self.model.generate_content(prompt)
            insights_data = json.loads(response.text)
            
            return insights_data
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return []
    
    def _validate_question(self, question: Dict[str, Any]) -> bool:
        """Validate a generated question"""
        required_fields = ['question_type', 'question_text', 'correct_answer']
        
        # Check required fields
        for field in required_fields:
            if field not in question or not question[field]:
                return False
        
        # Validate question type
        valid_types = ['mcq_single', 'mcq_multiple', 'true_false', 'short_answer']
        if question['question_type'] not in valid_types:
            return False
        
        # No difficulty_score validation needed; only difficulty word is used
        
        return True


# Global instance
gemini_service = GeminiService()
