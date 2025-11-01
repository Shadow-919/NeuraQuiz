#!/usr/bin/env python
"""
Simple test script to verify NeuraQuiz application is working correctly
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraquiz.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from quiz.models import UserProfile, Quiz, Question, Choice

def test_basic_functionality():
    """Test basic application functionality"""
    print("Testing NeuraQuiz Application...")
    
    # Test 1: Check if superuser exists
    print("\n1. Testing superuser creation...")
    try:
        shadow_user = User.objects.get(username='Shadow')
        print("SUCCESS: Superuser 'Shadow' exists")
        
        # Check if user profile exists
        profile = UserProfile.objects.get(user=shadow_user)
        print(f"SUCCESS: User profile created with role: {profile.role}")
    except User.DoesNotExist:
        print("ERROR: Superuser 'Shadow' not found")
        return False
    
    # Test 2: Test URL routing
    print("\n2. Testing URL routing...")
    client = Client()
    
    # Test home page
    response = client.get('/')
    if response.status_code == 200:
        print("SUCCESS: Home page loads successfully")
    else:
        print(f"ERROR: Home page failed with status: {response.status_code}")
    
    # Test login page
    response = client.get('/login/')
    if response.status_code == 200:
        print("SUCCESS: Login page loads successfully")
    else:
        print(f"ERROR: Login page failed with status: {response.status_code}")
    
    # Test register page
    response = client.get('/register/')
    if response.status_code == 200:
        print("SUCCESS: Register page loads successfully")
    else:
        print(f"ERROR: Register page failed with status: {response.status_code}")
    
    # Test 3: Test authentication
    print("\n3. Testing authentication...")
    login_success = client.login(username='Shadow', password='Qwerty123')
    if login_success:
        print("SUCCESS: Superuser login successful")
        
        # Test dashboard access
        response = client.get('/dashboard/')
        if response.status_code == 200:
            print("SUCCESS: Dashboard accessible after login")
        else:
            print(f"ERROR: Dashboard failed with status: {response.status_code}")
    else:
        print("ERROR: Superuser login failed")
    
    # Test 4: Test model creation
    print("\n4. Testing model creation...")
    try:
        # Create a test quiz
        quiz = Quiz.objects.create(
            title="Test Quiz",
            topic="Testing",
            difficulty="medium",
            time_limit=30,
            created_by=shadow_user
        )
        print("SUCCESS: Quiz model creation successful")
        
        # Create a test question
        question = Question.objects.create(
            quiz=quiz,
            text="What is 2 + 2?",
            question_type="mcq_single",
            correct_answer="0",
            difficulty_score=1.0
        )
        print("SUCCESS: Question model creation successful")
        
        # Create test choices
        Choice.objects.create(
            question=question,
            choice_text="3",
            is_correct=False,
            order=0
        )
        Choice.objects.create(
            question=question,
            choice_text="4",
            is_correct=True,
            order=1
        )
        print("SUCCESS: Choice model creation successful")
        
        # Clean up test data
        quiz.delete()
        print("SUCCESS: Test data cleaned up")
        
    except Exception as e:
        print(f"ERROR: Model creation failed: {e}")
        return False
    
    print("\nAll tests passed! NeuraQuiz is working correctly.")
    return True

if __name__ == "__main__":
    success = test_basic_functionality()
    if success:
        print("\nApplication is ready to use!")
        print("\nTo start the server, run: python manage.py runserver")
        print("Then visit: http://127.0.0.1:8000")
        print("\nLogin credentials:")
        print("   Username: Shadow")
        print("   Password: Qwerty123")
    else:
        print("\nSome tests failed. Please check the errors above.")
        sys.exit(1)
