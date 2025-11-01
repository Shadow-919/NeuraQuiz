from django.db import migrations, models
import random
import string


def generate_unique_access_code(apps):
    """Generate a unique 6-digit access code"""
    UserProfile = apps.get_model('quiz', 'UserProfile')
    while True:
        code = ''.join(random.choices(string.digits, k=6))
        if not UserProfile.objects.filter(quiz_access_code=code).exists():
            return code


def assign_access_codes_to_existing_instructors(apps, schema_editor):
    """Assign unique access codes to existing instructors"""
    UserProfile = apps.get_model('quiz', 'UserProfile')
    instructors = UserProfile.objects.filter(role='instructor')
    
    for instructor in instructors:
        if not instructor.quiz_access_code:
            instructor.quiz_access_code = generate_unique_access_code(apps)
            instructor.save()


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='quiz_access_code',
            field=models.CharField(max_length=6, unique=True, null=True, blank=True, help_text='6-digit access code for instructor quizzes'),
        ),
        migrations.RunPython(assign_access_codes_to_existing_instructors, reverse_code=migrations.RunPython.noop),
    ]