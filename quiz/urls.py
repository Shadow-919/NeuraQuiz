from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Access code management
    path('verify-access-code/', views.verify_access_code, name='verify_access_code'),
    path('clear-access-code/', views.clear_access_code, name='clear_access_code'),
    
    # Quiz management (instructor)
    path('create-quiz/', views.create_quiz, name='create_quiz'),
    path('edit-quiz/<uuid:quiz_id>/', views.edit_quiz, name='edit_quiz'),
    path('quiz-stats/<uuid:quiz_id>/', views.quiz_stats, name='quiz_stats'),
    path('generate-ai-questions/<uuid:quiz_id>/', views.generate_ai_questions, name='generate_ai_questions'),
    path('cancel-ai-generation/<uuid:quiz_id>/', views.cancel_ai_generation, name='cancel_ai_generation'),
    path('generate-ai-status/<uuid:quiz_id>/', views.generate_ai_status, name='generate_ai_status'),
    path('add-question/<uuid:quiz_id>/', views.add_question, name='add_question'),
    path('delete-question/<uuid:question_id>/', views.delete_question, name='delete_question'),
    path('publish-quiz/<uuid:quiz_id>/', views.publish_quiz, name='publish_quiz'),
    path('delete-quiz/<uuid:quiz_id>/', views.delete_quiz, name='delete_quiz'),
    path('edit-question/<uuid:question_id>/', views.edit_question, name='edit_question'),
    
    # Quiz taking (student)
    path('take-quiz/<uuid:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('submit-answer/<uuid:attempt_id>/', views.submit_answer, name='submit_answer'),
    path('finish-quiz/<uuid:attempt_id>/', views.finish_quiz, name='finish_quiz'),
    path('quiz-results/<uuid:attempt_id>/', views.quiz_results, name='quiz_results'),
    path('delete-attempts/<uuid:quiz_id>/', views.delete_attempts, name='delete_attempts'),
    path('delete-attempt/<uuid:attempt_id>/', views.delete_attempt, name='delete_attempt'),
]