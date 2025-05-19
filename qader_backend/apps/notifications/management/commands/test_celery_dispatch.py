from django.core.management.base import BaseCommand
from django.conf import settings

# If you have another simple task, import that one.
# from apps.notifications.tasks import dispatch_notification_email_task # Or a simpler task
from qader_project.celery import debug_task


class Command(BaseCommand):
    help = "Tests dispatching a simple task to Celery"

    def handle(self, *args, **options):
        self.stdout.write(f"Using Celery Broker: {settings.CELERY_BROKER_URL}")
        self.stdout.write("Attempting to dispatch a simple Celery task...")
        try:
            # Using a very simple task like debug_task is best for this test
            result = debug_task.delay()
            # If using your actual email task for testing this part:
            # result = dispatch_notification_email_task.delay(
            #     notification_id=0, # Dummy data
            #     recipient_email="test@example.com",
            #     subject="Test Email",
            #     body_template_name="emails/generic_notification_email", # Ensure this template exists
            #     context={"message": "This is a test"}
            # )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Task dispatched successfully. Task ID: {result.id}"
                )
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to dispatch task: {e}"))
            import traceback

            traceback.print_exc()
