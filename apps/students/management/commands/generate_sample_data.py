"""
Generate sample data for testing
Usage: python manage.py generate_sample_data
"""
from django.core.management.base import BaseCommand
from apps.students.models import Student, Batch
from apps.accounts.models import Teacher
import random


class Command(BaseCommand):
    help = 'Generate sample batches and students for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--teacher-email',
            type=str,
            default='akashvishwakarma1262@gmail.com',
            help='Teacher email to assign batches to',
        )
        parser.add_argument(
            '--students-per-batch',
            type=int,
            default=25,
            help='Number of students per batch (default: 25)',
        )

    def handle(self, *args, **options):
        teacher_email = options['teacher_email']
        students_per_batch = options['students_per_batch']

        # Get teacher
        try:
            teacher = Teacher.objects.get(user__email=teacher_email)
        except Teacher.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Teacher with email {teacher_email} not found!')
            )
            return

        self.stdout.write(f'Creating batches for teacher: {teacher.full_name}')

        # Batch configurations (6 semesters, different timings)
        batch_configs = [
            # Semester 1
            {'name': 'Sem 1 - Batch A', 'semester': '1', 'subject': 'Programming Fundamentals', 'timing': '09:00 - 10:30'},
            {'name': 'Sem 1 - Batch B', 'semester': '1', 'subject': 'Programming Fundamentals', 'timing': '10:30 - 12:00'},
            {'name': 'Sem 1 - Batch C', 'semester': '1', 'subject': 'Programming Fundamentals', 'timing': '14:00 - 15:30'},
            
            # Semester 2
            {'name': 'Sem 2 - Batch A', 'semester': '2', 'subject': 'Data Structures', 'timing': '09:00 - 10:30'},
            {'name': 'Sem 2 - Batch B', 'semester': '2', 'subject': 'Data Structures', 'timing': '10:30 - 12:00'},
            {'name': 'Sem 2 - Batch C', 'semester': '2', 'subject': 'Data Structures', 'timing': '14:00 - 15:30'},
            
            # Semester 3
            {'name': 'Sem 3 - Batch A', 'semester': '3', 'subject': 'Database Management', 'timing': '09:00 - 10:30'},
            {'name': 'Sem 3 - Batch B', 'semester': '3', 'subject': 'Database Management', 'timing': '10:30 - 12:00'},
            {'name': 'Sem 3 - Batch C', 'semester': '3', 'subject': 'Database Management', 'timing': '14:00 - 15:30'},
            
            # Semester 4
            {'name': 'Sem 4 - Batch A', 'semester': '4', 'subject': 'Operating Systems', 'timing': '09:00 - 10:30'},
            {'name': 'Sem 4 - Batch B', 'semester': '4', 'subject': 'Operating Systems', 'timing': '10:30 - 12:00'},
            {'name': 'Sem 4 - Batch C', 'semester': '4', 'subject': 'Operating Systems', 'timing': '14:00 - 15:30'},
            
            # Semester 5
            {'name': 'Sem 5 - Batch A', 'semester': '5', 'subject': 'Computer Networks', 'timing': '09:00 - 10:30'},
            {'name': 'Sem 5 - Batch B', 'semester': '5', 'subject': 'Computer Networks', 'timing': '10:30 - 12:00'},
            {'name': 'Sem 5 - Batch C', 'semester': '5', 'subject': 'Computer Networks', 'timing': '14:00 - 15:30'},
            
            # Semester 6
            {'name': 'Sem 6 - Batch A', 'semester': '6', 'subject': 'Software Engineering', 'timing': '09:00 - 10:30'},
            {'name': 'Sem 6 - Batch B', 'semester': '6', 'subject': 'Software Engineering', 'timing': '10:30 - 12:00'},
            {'name': 'Sem 6 - Batch C', 'semester': '6', 'subject': 'Software Engineering', 'timing': '14:00 - 15:30'},
        ]

        # Sample Indian names for students (unique combinations)
        first_names = [
            'Aarav', 'Vivaan', 'Aditya', 'Vihaan', 'Arjun', 'Sai', 'Reyansh', 'Ayan',
            'Krishna', 'Ishaan', 'Shaurya', 'Atharva', 'Kabeer', 'Rohan', 'Aryan',
            'Aakash', 'Rahul', 'Priya', 'Anjali', 'Sneha', 'Pooja', 'Neha', 'Ritu',
            'Kavya', 'Divya', 'Meera', 'Sonia', 'Rajesh', 'Suresh', 'Amit', 'Vikram',
            'Sanjay', 'Deepak', 'Manoj', 'Pankaj', 'Ajay', 'Vijay', 'Rakesh',
            'Mukesh', 'Dinesh', 'Sachin', 'Ravi', 'Kiran', 'Nitin', 'Asha', 'Usha',
            'Preeti', 'Shanti', 'Lata', 'Geeta', 'Sita', 'Gita', 'Urmila', 'Tara'
        ]

        last_names = [
            'Kumar', 'Singh', 'Sharma', 'Verma', 'Patel', 'Gupta', 'Joshi', 'Mehta',
            'Desai', 'Shah', 'Jain', 'Kapoor', 'Malhotra', 'Khanna', 'Bhatt', 'Pandey',
            'Mishra', 'Srivastava', 'Trivedi', 'Dubey', 'Chaturvedi', 'Bhardwaj', 'Agarwal',
            'Bansal', 'Garg', 'Mittal', 'Arora', 'Chopra', 'Bedi', 'Sethi', 'Thakur',
            'Rathore', 'Chauhan', 'Rajput', 'Yadav', 'Maurya', 'Nair', 'Menon', 'Iyer',
            'Rao', 'Reddy', 'Naidu', 'Pillai', 'Das', 'Dutta', 'Banerjee', 'Mukherjee'
        ]

        total_batches = 0
        total_students = 0
        name_index = 0

        for config in batch_configs:
            # Create batch
            batch, created = Batch.objects.get_or_create(
                teacher=teacher,
                name=config['name'],
                defaults={
                    'semester': config['semester'],
                    'subject': config['subject'],
                }
            )
            
            if created:
                self.stdout.write(f'✓ Created batch: {batch.name} ({config["timing"]})')
            else:
                self.stdout.write(f'  Batch exists: {batch.name}')
            
            total_batches += 1

            # Generate students for this batch with UNIQUE names
            for i in range(students_per_batch):
                # Use diverse first names to generate unique roll numbers
                first_name = first_names[name_index % len(first_names)]
                last_name = last_names[name_index % len(last_names)]
                full_name = f'{first_name} {last_name}'
                
                # Generate unique contact number
                contact = f'9{100000000 + name_index}'
                
                # Generate unique email
                email = f'student{name_index}@example.com'
                
                # Create student (roll number will be auto-generated based on name)
                try:
                    student = Student.objects.create(
                        teacher=teacher,
                        batch=batch,
                        full_name=full_name,
                        semester=config['semester'],
                        contact_number=contact,
                        email=email,
                        is_active=True,
                    )
                    total_students += 1
                    name_index += 1
                except Exception as e:
                    # Skip duplicates
                    pass

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Successfully created:\n'
                f'  - {total_batches} batches\n'
                f'  - {total_students} students\n'
                f'\nEach batch has {students_per_batch} students with auto-generated roll numbers!'
            )
        )
