from django.core.management.base import BaseCommand
import json

class Command(BaseCommand):
    help = 'List Gemini/Generative AI models available to configured client (development only)'

    def handle(self, *args, **options):
        try:
            import google.generativeai as genai
        except Exception as e:
            self.stderr.write('google.generativeai is not installed or failed to import: %s' % e)
            return

        try:
            models = genai.list_models()
            # list_models may return a generator — iterate and collect
            collected = []
            try:
                for m in models:
                    collected.append(m)
            except TypeError:
                # not iterable, just use as-is
                collected = models

            try:
                self.stdout.write(json.dumps(collected, indent=2, default=str))
            except Exception:
                self.stdout.write(str(collected))
        except Exception as e:
            self.stderr.write('Error calling list_models(): %s' % e)
