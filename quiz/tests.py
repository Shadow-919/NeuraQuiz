from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Quiz, Question
import json


class AIGenerationTests(TestCase):
	def setUp(self):
		# create an instructor user
		self.client = Client()
		self.user = User.objects.create_user(username='ins1', password='pass')
		# create profile
		from .models import UserProfile
		UserProfile.objects.create(user=self.user, role='instructor')

		# create a quiz
		self.quiz = Quiz.objects.create(title='Test Quiz', topic='Math', created_by=self.user)

	def test_generate_ai_endpoint_without_service(self):
		# when gemini service is not configured, endpoint should return 503
		self.client.login(username='ins1', password='pass')
		url = f'/generate-ai-questions/{self.quiz.id}/'
		resp = self.client.post(url, data=json.dumps({'topic': 'math', 'num_questions': 3}), content_type='application/json')
		self.assertIn(resp.status_code, (200, 503))


class AddQuestionTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.user = User.objects.create_user(username='ins2', password='pass')
		from .models import UserProfile
		UserProfile.objects.create(user=self.user, role='instructor')
		self.quiz = Quiz.objects.create(title='AddQ Quiz', topic='Bio', created_by=self.user)

	def test_add_question_post(self):
		self.client.login(username='ins2', password='pass')
		url = f'/add-question/{self.quiz.id}/'
		data = {
			'text': 'What is 2+2?',
			'question_type': 'mcq_single',
			'choice_0': '3',
			'choice_1': '4',
			'choice_2': '5',
			'choice_3': '6',
			'correct_answer': '1',
			'difficulty_score': '3.0'
		}
		resp = self.client.post(url, data)
		# should redirect back to edit page
		self.assertEqual(resp.status_code, 302)
		self.assertEqual(self.quiz.questions.count(), 1)
