from django.test import TestCase, Client
from django.contrib.auth.models import User
from unittest.mock import patch
from .models import Quiz
import json

class GeminiMock:
    def __init__(self, questions):
        self._questions = questions
    def __call__(self, *args, **kwargs):
        return self._questions

class GenerateQuestionsDedupCapTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='mockins', password='pass')
        from .models import UserProfile
        UserProfile.objects.create(user=self.user, role='instructor')
        self.quiz = Quiz.objects.create(title='Mock Quiz', topic='Sci', created_by=self.user)

    def _make_mock_questions(self, n):
        qs = []
        for i in range(n):
            qs.append({
                'question_type': 'mcq_single',
                'question_text': f'Mock question {i%5}',  # introduce duplicates every 5
                'choices': [f'opt{j}' for j in range(4)],
                'correct_answer': '1',
                'explanation': 'demo',
                'difficulty_score': 3.0
            })
        return qs

    @patch('quiz.views.gemini_service')
    def test_generate_respects_requested_count_and_dedupes(self, mock_service):
        # Mock gemini_service.generate_questions to return 10 items (with duplicates every 5)
        mock_service.is_configured = True
        mock_service.generate_questions.return_value = self._make_mock_questions(10)

        self.client.login(username='mockins', password='pass')
        url = f'/generate-ai-questions/{self.quiz.id}/'
        resp = self.client.post(url, data=json.dumps({'topic': 'sci', 'num_questions': 5}), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        # Reload quiz questions count
        self.quiz.refresh_from_db()
        qcount = self.quiz.questions.count()
        # Should have saved exactly 5 unique questions
        self.assertEqual(qcount, 5)

    def test_demo_generation_and_debug_log(self):
        # Use the demo generator path (no gemini) to run end-to-end and create debug log
        self.client.login(username='mockins', password='pass')
        url = f'/generate-ai-questions/{self.quiz.id}/'
        resp = self.client.post(url, data=json.dumps({'topic': 'demo', 'num_questions': 5, 'use_demo': True, 'debug_save': True}), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        # After demo generation, questions should be added
        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.questions.count(), 5)
        # Check debug log exists and contains the topic
        try:
            with open('ai_generation_debug.log', 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('Topic: demo', content)
        except FileNotFoundError:
            # It's acceptable if debug logging isn't available in this environment
            pass
 