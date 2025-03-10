from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
import os
from datetime import datetime, time, timedelta 
from extensions import db, login_manager, migrate
from models import AssignmentSubmission, ClassSchedule, User, Course, Assignment, Grade, Note, Task, UserNotification
from forms import AssignmentForm, AssignmentSubmissionForm, ClassScheduleForm, CourseForm, GradeForm, LoginForm, NoteForm, RegistrationForm, StudentEnrollmentForm, TaskForm  
from models import (
    User, Course, Assignment, Grade, Note, Task, 
    UserNotification, course_students
)

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # App configuration using encironment variables
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = True

    # Initialize app and db
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                flash('Login successful!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page if next_page else url_for('dashboard'))
            flash('Invalid username or password', 'danger')
        return render_template('login.html', form=form)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(
                username=form.username.data,
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                role=form.role.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            try:
                db.session.commit()
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred. Please try again.', 'danger')
        return render_template('register.html', form=form)

    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Currently not used
        notifications = UserNotification.query.filter_by(user_id=current_user.id, read=False).all()
        
        if current_user.is_student:
            # Student-specific data
            enrolled_courses = current_user.courses
            pending_assignments = Assignment.query.join(Course).filter(
                Course.id.in_([c.id for c in enrolled_courses]),
                Assignment.due_date > datetime.utcnow()
            ).all()
            recent_activities = get_student_activities(current_user.id)
            upcoming_events = get_student_events(current_user.id)
            
            return render_template('dashboard.html',
                                notifications=notifications,
                                enrolled_courses=enrolled_courses,
                                pending_assignments=pending_assignments,
                                recent_activities=recent_activities,
                                upcoming_events=upcoming_events)
        
        elif current_user.is_professor:
            # Professor-specific data
            teaching_courses = Course.query.filter_by(professor_id=current_user.id).all()
            submissions_to_grade = AssignmentSubmission.query.join(Assignment).join(Course).filter(
                Course.professor_id == current_user.id,
                AssignmentSubmission.grade.is_(None)
            ).all()
            recent_activities = get_professor_activities(current_user.id)
            upcoming_events = get_professor_events(current_user.id)
            
            return render_template('dashboard.html',
                                notifications=notifications,
                                teaching_courses=teaching_courses,
                                submissions_to_grade=submissions_to_grade,
                                recent_activities=recent_activities,
                                upcoming_events=upcoming_events)
        
        # Admin dashboard 
        recent_activities = get_admin_activities(current_user.id)
        upcoming_events = get_admin_events(current_user.id)
        return render_template('dashboard.html',
                            notifications=notifications,
                            recent_activities=recent_activities,
                            upcoming_events=upcoming_events)

    # Helper functions for activities and events
    def get_student_activities(student_id):
        # Get last 5 activities for student
        activities = []
        # Add recent grade updates
        grades = Grade.query.filter_by(student_id=student_id).order_by(Grade.created_at.desc()).limit(5).all()
        for grade in grades:
            activities.append({
                'title': f'New Grade in {grade.course.title}',
                'description': f'You received a grade of {grade.value}',
                'timestamp': grade.created_at
            })
        return sorted(activities, key=lambda x: x['timestamp'], reverse=True)[:5]

    def get_professor_activities(professor_id):
        activities = []
        # Add recent submission activities
        submissions = AssignmentSubmission.query.join(Assignment).join(Course).filter(
            Course.professor_id == professor_id
        ).order_by(AssignmentSubmission.submission_date.desc()).limit(5).all()
        for sub in submissions:
            activities.append({
                'title': f'New Submission for {sub.assignment.title}',
                'description': f'Student {sub.student.username} submitted their work',
                'timestamp': sub.submission_date
            })
        return activities

    def get_admin_activities(admin_id):
        # Currently adimins don't have activities
        return []

    def get_student_events(student_id):
        events = []
        try:
            # Get the courses
            student = User.query.get(student_id)
            if not student:
                return events

            # Upcoming assignments for enrolled classes
            upcoming_assignments = Assignment.query\
                .join(Course)\
                .filter(
                    Course.students.any(id=student_id),
                    Assignment.due_date > datetime.utcnow()
                )\
                .order_by(Assignment.due_date)\
                .limit(5)\
                .all()

            # Create events from assignments
            for assignment in upcoming_assignments:
                events.append({
                    'title': f'Assignment Due: {assignment.title}',
                    'description': f'For course: {assignment.course.title}',
                    'date': assignment.due_date
                })
        except Exception as e:
            print(f"Error in get_student_events: {e}")
            return []
            
        return events

    def get_professor_events(professor_id):
        events = []
        # Upcoming due dates
        assignments = Assignment.query.join(Course).filter(
            Course.professor_id == professor_id,
            Assignment.due_date > datetime.utcnow()
        ).order_by(Assignment.due_date).limit(5).all()
        
        for assignment in assignments:
            events.append({
                'title': f'Assignment Due: {assignment.title}',
                'description': f'For course: {assignment.course.title}',
                'date': assignment.due_date
            })
        return events

    def get_admin_events(admin_id):
        return []

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))
    
    @app.route('/assignments')
    @login_required
    def view_assignments():
        if current_user.role == 'student':
            # Assignments from enrolled courses
            assignments = Assignment.query.join(Course).filter(
                Course.students.any(id=current_user.id)
            ).order_by(Assignment.due_date.desc()).all()
        else:
            # Assignments for courses the professor teaches
            assignments = Assignment.query.join(Course).filter(
                Course.professor_id == current_user.id
            ).order_by(Assignment.due_date.desc()).all()
        
        return render_template('assignments/list.html', assignments=assignments)

    @app.route('/assignments/create', methods=['GET', 'POST'])
    @login_required
    def create_assignment():
        if current_user.role != 'professor':
            flash('Only professors can create assignments.', 'danger')
            return redirect(url_for('view_assignments'))
        
        form = AssignmentForm()
        # Courses being tought for the dorpdown menu
        form.course.choices = [(c.id, c.title) for c in Course.query.filter_by(professor_id=current_user.id).all()]
        
        if form.validate_on_submit():
            try:
                # Debug info
                print(f"Form Data - Title: {form.title.data}")
                print(f"Form Data - Description: {form.description.data}")
                print(f"Form Data - Due Date: {form.due_date.data}")
                print(f"Form Data - Course ID: {form.course.data}")
                
                assignment = Assignment(
                    title=form.title.data,
                    description=form.description.data,
                    due_date=form.due_date.data,
                    course_id=form.course.data
                )
                db.session.add(assignment)
                db.session.commit()
                flash('Assignment created successfully!', 'success')
                return redirect(url_for('view_assignments'))
            except Exception as e:
                print(f"Error creating assignment: {str(e)}")
                db.session.rollback()
                flash('Error creating assignment. Please try again.', 'danger')
        else:
            print(f"Form validation errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'danger')
        
        return render_template('assignments/create.html', form=form)

    @app.route('/assignments/<int:assignment_id>/submit', methods=['GET', 'POST'])
    @login_required
    def submit_assignment(assignment_id):
        if current_user.role != 'student':
            flash('Only students can submit assignments.', 'danger')
            return redirect(url_for('view_assignments'))
        
        assignment = Assignment.query.get_or_404(assignment_id)
        
        if current_user not in assignment.course.students:
            flash('You are not enrolled in this course.', 'danger')
            return redirect(url_for('view_assignments'))
        
        existing_submission = AssignmentSubmission.query.filter_by(
            assignment_id=assignment_id,
            student_id=current_user.id
        ).first()
        
        if existing_submission:
            flash('You have already submitted this assignment.', 'warning')
            return redirect(url_for('view_assignments'))
        
        form = AssignmentSubmissionForm()
        
        if form.validate_on_submit():
            submission = AssignmentSubmission(
                content=form.content.data,
                assignment_id=assignment_id,
                student_id=current_user.id
            )
            db.session.add(submission)
            try:
                db.session.commit()
                flash('Assignment submitted successfully!', 'success')
                return redirect(url_for('view_assignments'))
            except Exception as e:
                db.session.rollback()
                flash('Error submitting assignment. Please try again.', 'danger')
        
        return render_template('assignments/submit.html', form=form, assignment=assignment)

    @app.route('/assignments/<int:assignment_id>/submissions')
    @login_required
    def view_submissions(assignment_id):
        if current_user.role != 'professor':
            flash('Only professors can view submissions.', 'danger')
            return redirect(url_for('view_assignments'))
        
        assignment = Assignment.query.get_or_404(assignment_id)
        
        if assignment.course.professor_id != current_user.id:
            flash('You do not teach this course.', 'danger')
            return redirect(url_for('view_assignments'))
        
        submissions = AssignmentSubmission.query.filter_by(assignment_id=assignment_id).all()
        return render_template('assignments/submissions.html', assignment=assignment, submissions=submissions)

    
    @app.route('/submissions/<int:submission_id>/grade', methods=['GET', 'POST'])
    @login_required
    def grade_submission(submission_id):
        if current_user.role != 'professor':
            flash('Only professors can grade submissions.', 'danger')
            return redirect(url_for('dashboard'))

        submission = AssignmentSubmission.query.get_or_404(submission_id)
        
        if submission.assignment.course.professor_id != current_user.id:
            flash('You do not teach this course.', 'danger')
            return redirect(url_for('dashboard'))

        form = GradeForm()
        
        if form.validate_on_submit():
            submission.grade = form.grade.data
            submission.feedback = form.feedback.data
            try:
                db.session.commit()
                flash('Grade submitted successfully!', 'success')
                return redirect(url_for('view_submissions', assignment_id=submission.assignment_id))
            except Exception as e:
                db.session.rollback()
                flash('Error submitting grade. Please try again.', 'danger')

        return render_template('assignments/grade.html', form=form, submission=submission)
    

    @app.route('/grades')
    @login_required
    def view_grades():
        if current_user.role == 'student':
            # Get all submissions with grades
            submissions = AssignmentSubmission.query.filter_by(
                student_id=current_user.id
            ).join(
                Assignment
            ).join(
                Course
            ).order_by(
                Course.title,
                Assignment.due_date
            ).all()

            # Calculate course averages
            course_grades = {}
            for submission in submissions:
                if submission.grade is not None:
                    course = submission.assignment.course
                    if course.id not in course_grades:
                        course_grades[course.id] = {
                            'course': course,
                            'grades': [],
                            'average': 0
                        }
                    course_grades[course.id]['grades'].append(submission.grade)
            
            for course_id in course_grades:
                grades = course_grades[course_id]['grades']
                course_grades[course_id]['average'] = sum(grades) / len(grades)

            return render_template('grades/student_grades.html', 
                                submissions=submissions,
                                course_grades=course_grades)
        else:
            # Professor view so show all grades for their courses
            courses = Course.query.filter_by(professor_id=current_user.id).all()
            return render_template('grades/professor_grades.html', courses=courses)
        

    @app.route('/admin/courses')
    @login_required
    def admin_courses():
        if current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        
        courses = Course.query.all()
        return render_template('admin/courses.html', courses=courses)

    @app.route('/admin/courses/create', methods=['GET', 'POST'])
    @login_required
    def create_course():
        if current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        
        form = CourseForm()
        # Get all professors for the dropdown menu
        professors = User.query.filter_by(role='professor').all()
        form.professor.choices = [(p.id, f"{p.first_name} {p.last_name}") for p in professors]
        
        if form.validate_on_submit():
            course = Course(
                title=form.title.data,
                code=form.code.data,
                description=form.description.data,
                professor_id=form.professor.data
            )
            try:
                db.session.add(course)
                db.session.commit()
                flash('Course created successfully!', 'success')
                return redirect(url_for('admin_courses'))
            except Exception as e:
                db.session.rollback()
                flash('Error creating course. Please try again.', 'danger')
        
        return render_template('admin/create_course.html', form=form)

    @app.route('/admin/students')
    @login_required
    def admin_students():
        if current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        
        students = User.query.filter_by(role='student').all()
        return render_template('admin/students.html', students=students)

    @app.route('/admin/students/<int:student_id>/enroll', methods=['GET', 'POST'])
    @login_required
    def manage_student_enrollment(student_id):
        if current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        
        student = User.query.get_or_404(student_id)
        if student.role != 'student':
            flash('Selected user is not a student.', 'danger')
            return redirect(url_for('admin_students'))
        
        form = StudentEnrollmentForm()
        all_courses = Course.query.all()
        form.courses.choices = [(c.id, f"{c.code} - {c.title}") for c in all_courses]
        
        if form.validate_on_submit():
            # Get the selected courses
            selected_courses = Course.query.filter(Course.id.in_(form.courses.data)).all()
            # Update the student's courses
            student.courses = selected_courses
            try:
                db.session.commit()
                flash('Enrollment updated successfully!', 'success')
                return redirect(url_for('admin_students'))
            except Exception as e:
                db.session.rollback()
                flash('Error updating enrollment. Please try again.', 'danger')
        else:
            # Courses the student is already enrolled in should be preselected
            form.courses.data = [c.id for c in student.courses]
        
        return render_template('admin/manage_enrollment.html', form=form, student=student)

    @app.route('/courses/teaching')
    @login_required
    def teaching_courses():
        if current_user.role != 'professor':
            flash('Access denied. Professor privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        
        courses = Course.query.filter_by(professor_id=current_user.id).all()
        return render_template('courses/teaching.html', courses=courses)

    @app.route('/courses/enrolled')
    @login_required
    def enrolled_courses():
        if current_user.role != 'student':
            flash('Access denied. Student privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        
        courses = current_user.courses
        return render_template('courses/enrolled.html', courses=courses)

    @app.route('/notes')
    @login_required
    def view_notes():
        notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.updated_at.desc()).all()
        return render_template('notes/list.html', notes=notes)

    @app.route('/notes/create', methods=['GET', 'POST'])
    @login_required
    def create_note():
        form = NoteForm()
        if form.validate_on_submit():
            note = Note(
                title=form.title.data,
                content=form.content.data,
                user_id=current_user.id
            )
            try:
                db.session.add(note)
                db.session.commit()
                flash('Note created successfully!', 'success')
                return redirect(url_for('view_notes'))
            except Exception as e:
                db.session.rollback()
                flash('Error creating note. Please try again.', 'danger')
        
        return render_template('notes/create.html', form=form)

    @app.route('/notes/<int:note_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_note(note_id):
        note = Note.query.get_or_404(note_id)
        if note.user_id != current_user.id:
            flash('You do not have permission to edit this note.', 'danger')
            return redirect(url_for('view_notes'))
        
        form = NoteForm(obj=note)
        if form.validate_on_submit():
            note.title = form.title.data
            note.content = form.content.data
            try:
                db.session.commit()
                flash('Note updated successfully!', 'success')
                return redirect(url_for('view_notes'))
            except Exception as e:
                db.session.rollback()
                flash('Error updating note. Please try again.', 'danger')
        
        return render_template('notes/edit.html', form=form, note=note)

    @app.route('/notes/<int:note_id>/delete', methods=['POST'])
    @login_required
    def delete_note(note_id):
        note = Note.query.get_or_404(note_id)
        if note.user_id != current_user.id:
            flash('You do not have permission to delete this note.', 'danger')
            return redirect(url_for('view_notes'))
        
        try:
            db.session.delete(note)
            db.session.commit()
            flash('Note deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error deleting note. Please try again.', 'danger')
        
        return redirect(url_for('view_notes'))


    @app.route('/tasks')
    @login_required
    def view_tasks():
        upcoming_tasks = Task.query.filter_by(
            user_id=current_user.id,
            is_completed=False
        ).order_by(Task.start_time.asc()).all()
        
        completed_tasks = Task.query.filter_by(
            user_id=current_user.id,
            is_completed=True
        ).order_by(Task.end_time.desc()).limit(10).all()
        
        return render_template('schedule/tasks.html', 
                            upcoming_tasks=upcoming_tasks,
                            completed_tasks=completed_tasks)

    @app.route('/tasks/create', methods=['GET', 'POST'])
    @login_required
    def create_task():
        form = TaskForm()
        if form.validate_on_submit():
            task = Task(
                title=form.title.data,
                description=form.description.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data,
                user_id=current_user.id
            )
            db.session.add(task)
            try:
                db.session.commit()
                flash('Task created successfully!', 'success')
                return redirect(url_for('view_tasks'))
            except Exception as e:
                db.session.rollback()
                flash('Error creating task. Please try again.', 'danger')
        
        return render_template('schedule/create_task.html', form=form)

    @app.route('/tasks/<int:task_id>/toggle', methods=['POST'])
    @login_required
    def toggle_task(task_id):
        task = Task.query.get_or_404(task_id)
        if task.user_id != current_user.id:
            flash('Access denied.', 'danger')
            return redirect(url_for('view_tasks'))
        
        task.is_completed = not task.is_completed
        try:
            db.session.commit()
            status = 'completed' if task.is_completed else 'uncompleted'
            flash(f'Task marked as {status}!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error updating task. Please try again.', 'danger')
        
        return redirect(url_for('view_tasks'))

    @app.route('/tasks/<int:task_id>/delete', methods=['POST'])
    @login_required
    def delete_task(task_id):
        task = Task.query.get_or_404(task_id)
        if task.user_id != current_user.id:
            flash('Access denied.', 'danger')
            return redirect(url_for('view_tasks'))
        
        try:
            db.session.delete(task)
            db.session.commit()
            flash('Task deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error deleting task. Please try again.', 'danger')
        
        return redirect(url_for('view_tasks'))

    @app.route('/schedule')
    @login_required
    def view_schedule():
        # Get the user schedule based on their role
        if current_user.role == 'student':
            # Get schedules for all enrolled courses
            schedules = ClassSchedule.query.join(Course).filter(
                Course.students.any(id=current_user.id)
            ).order_by(ClassSchedule.day_of_week, ClassSchedule.start_time).all()
        elif current_user.role == 'professor':
            # Get schedules for courses the teacher teaches
            schedules = ClassSchedule.query.join(Course).filter(
                Course.professor_id == current_user.id
            ).order_by(ClassSchedule.day_of_week, ClassSchedule.start_time).all()
        else:
            schedules = []

        # Group schedules by day
        schedule_by_day = {day: [] for day in range(5)}  # Monday to Friday
        for schedule in schedules:
            schedule_by_day[schedule.day_of_week].append(schedule)
        
        return render_template('schedule/view_schedule.html', 
                            schedule_by_day=schedule_by_day)

    @app.route('/calendar')
    @login_required
    def view_calendar():
        tasks = Task.query.filter_by(user_id=current_user.id).all()
        
        # Get assignments based on user role
        if current_user.role == 'student':
            assignments = Assignment.query.join(Course).filter(
                Course.students.any(id=current_user.id)
            ).all()
        elif current_user.role == 'professor':
            assignments = Assignment.query.join(Course).filter(
                Course.professor_id == current_user.id
            ).all()
        else:
            assignments = []
        
        events = []
        
        for task in tasks:
            events.append({
                'title': task.title,
                'start': task.start_time.isoformat(),
                'end': task.end_time.isoformat(),
                'color': 'green' if task.is_completed else 'blue',
                'type': 'task',
                'url': url_for('view_tasks')
            })
        
        for assignment in assignments:
            events.append({
                'title': f'Due: {assignment.title}',
                'start': assignment.due_date.isoformat(),
                'color': 'red',
                'type': 'assignment',
                'url': url_for('view_assignments')
            })
        
        return render_template('schedule/calendar.html', events=events)

    @app.route('/admin/schedule')
    @login_required
    def admin_schedule():
        if current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        
        # Get all schedules grouped by day
        schedules = ClassSchedule.query.order_by(
            ClassSchedule.day_of_week,
            ClassSchedule.start_time
        ).all()
        
        # Group schedules by day
        schedule_by_day = {day: [] for day in range(5)}  # Monday to Friday
        for schedule in schedules:
            schedule_by_day[schedule.day_of_week].append(schedule)
        
        return render_template('admin/schedule.html', schedule_by_day=schedule_by_day)

    @app.route('/admin/schedule/add', methods=['GET', 'POST'])
    @login_required
    def add_class_schedule():
        if current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        
        form = ClassScheduleForm()
        
        # Get all courses for the dropdown menu
        courses = Course.query.all()
        form.course.choices = [(c.id, f"{c.code} - {c.title}") for c in courses]
        
        if form.validate_on_submit():
            # Check for schedule conflicts
            conflicting_schedule = ClassSchedule.query.filter(
                ClassSchedule.day_of_week == form.day_of_week.data,
                ClassSchedule.location == form.location.data,
                db.or_(
                    db.and_(
                        ClassSchedule.start_time <= form.start_time.data,
                        ClassSchedule.end_time > form.start_time.data
                    ),
                    db.and_(
                        ClassSchedule.start_time < form.end_time.data,
                        ClassSchedule.end_time >= form.end_time.data
                    )
                )
            ).first()
            
            if conflicting_schedule:
                flash('There is a scheduling conflict with another class.', 'danger')
                return render_template('admin/add_schedule.html', form=form)
            
            schedule = ClassSchedule(
                course_id=form.course.data,
                day_of_week=form.day_of_week.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data,
                location=form.location.data
            )
            
            try:
                db.session.add(schedule)
                db.session.commit()
                flash('Class schedule added successfully!', 'success')
                return redirect(url_for('admin_schedule'))
            except Exception as e:
                db.session.rollback()
                flash('Error adding class schedule. Please try again.', 'danger')
        
        return render_template('admin/add_schedule.html', form=form)

    @app.route('/admin/schedule/<int:schedule_id>/delete', methods=['POST'])
    @login_required
    def delete_class_schedule(schedule_id):
        if current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        
        schedule = ClassSchedule.query.get_or_404(schedule_id)
        try:
            db.session.delete(schedule)
            db.session.commit()
            flash('Class schedule deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error deleting class schedule. Please try again.', 'danger')
        
        return redirect(url_for('admin_schedule'))

    

    @app.route('/api/calendar-events')
    @login_required
    def get_calendar_events():
        tasks = Task.query.filter_by(user_id=current_user.id).all()
        
        # Get assignments based on role
        if current_user.role == 'student':
            assignments = Assignment.query.join(Course).filter(
                Course.students.any(id=current_user.id)
            ).all()
        elif current_user.role == 'professor':
            assignments = Assignment.query.join(Course).filter(
                Course.professor_id == current_user.id
            ).all()
        else:
            assignments = []
        
        events = []
        
        for task in tasks:
            events.append({
                'id': f'task_{task.id}',
                'title': task.title,
                'start': task.start_time.isoformat(),
                'end': task.end_time.isoformat(),
                'color': '#28a745' if task.is_completed else '#0d6efd',
                'textColor': 'white',
                'extendedProps': {
                    'type': 'task',
                    'description': task.description or '',
                    'status': 'Completed' if task.is_completed else 'Pending'
                }
            })
        
        for assignment in assignments:
            events.append({
                'id': f'assignment_{assignment.id}',
                'title': f'Due: {assignment.title}',
                'start': assignment.due_date.isoformat(),
                'allDay': True,
                'color': '#dc3545',
                'textColor': 'white',
                'extendedProps': {
                    'type': 'assignment',
                    'description': assignment.description or '',
                    'course': assignment.course.title
                }
            })
        
        return jsonify(events)

    return app

# Instantiate the app
app = create_app()

# Only use this if you're running the file directly
if __name__ == '__main__':
    # Create an application context before running the app
    with app.app_context():
        # Create all database tables
        db.create_all()
    app.run(debug=True)