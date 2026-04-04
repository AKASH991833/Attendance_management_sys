"""
Delete all students from database
Usage: python manage.py delete_all_students
"""
from django.core.management.base import BaseCommand
from apps.students.models import Student, Batch
from apps.attendance.models import AttendanceRecord


class Command(BaseCommand):
    help = 'Delete all students, batches and attendance records from database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion (required)',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This will DELETE ALL students, batches and attendance records!\n'
                    'Run with --confirm to proceed.'
                )
            )
            return

        # Count records before deletion
        student_count = Student.objects.count()
        batch_count = Batch.objects.count()
        attendance_count = AttendanceRecord.objects.count()

        self.stdout.write(f'Deleting {student_count} students...')
        self.stdout.write(f'Deleting {batch_count} batches...')
        self.stdout.write(f'Deleting {attendance_count} attendance records...')

        # Delete all records
        AttendanceRecord.objects.all().delete()
        Student.objects.all().delete()
        Batch.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Successfully deleted:\n'
                f'  - {student_count} students\n'
                f'  - {batch_count} batches\n'
                f'  - {attendance_count} attendance records'
            )
        )
