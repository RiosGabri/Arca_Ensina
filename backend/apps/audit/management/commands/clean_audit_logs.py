from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.audit.models import AuditLog


class Command(BaseCommand):
    help = "Remove audit logs older than AUDIT_LOG_RETENTION_DAYS (default 90)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=None,
            help="Number of days to retain (overrides setting)",
        )

    def handle(self, *args, **options):
        days = options["days"] or getattr(settings, "AUDIT_LOG_RETENTION_DAYS", 90)
        cutoff = timezone.now() - timedelta(days=days)
        deleted, _ = AuditLog.objects.filter(timestamp__lt=cutoff).delete()
        msg = f"Deleted {deleted} audit log(s) older than {days} days."
        self.stdout.write(self.style.SUCCESS(msg))
