from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, StringField, PasswordField, TextAreaField, SelectField, DateTimeField, FloatField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    role = SelectField('Role', choices=[('student', 'Student'), ('professor', 'Professor'), ('admin', 'Admin')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')


class NoteForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Save Note')

class TaskForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    start_time = DateTimeField('Start Time', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    end_time = DateTimeField('End Time', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    submit = SubmitField('Create Task')

    def validate_end_time(self, field):
        if field.data < self.start_time.data:
            raise ValidationError('End time must be after start time')
        

class AnnouncementForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post Announcement')

class AssignmentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    due_date = DateTimeField('Due Date', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')  # Changed format
    course = SelectField('Course', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Create Assignment')

class AssignmentSubmissionForm(FlaskForm):
    content = TextAreaField('Submission Content', validators=[DataRequired()])
    submit = SubmitField('Submit Assignment')

class GradeForm(FlaskForm):
    grade = FloatField('Grade (0-100)', validators=[
        DataRequired(),
        NumberRange(min=0, max=100, message="Grade must be between 0 and 100")
    ])
    feedback = TextAreaField('Feedback')
    submit = SubmitField('Submit Grade')

class CourseForm(FlaskForm):
    title = StringField('Course Title', validators=[DataRequired()])
    code = StringField('Course Code', validators=[DataRequired()])
    description = TextAreaField('Description')
    professor = SelectField('Professor', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Create Course')

class StudentEnrollmentForm(FlaskForm):
    courses = SelectMultipleField('Select Courses', coerce=int)
    submit = SubmitField('Update Enrollment')


from wtforms.fields import SelectField, TimeField
from datetime import time

class ClassScheduleForm(FlaskForm):
    course = SelectField('Course', coerce=int, validators=[DataRequired()])
    day_of_week = SelectField('Day', choices=[
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday')
    ], coerce=int, validators=[DataRequired()])
    start_time = TimeField('Start Time', validators=[DataRequired()], default=time(8, 0))
    end_time = TimeField('End Time', validators=[DataRequired()], default=time(9, 30))
    location = StringField('Location', validators=[DataRequired()])
    submit = SubmitField('Add Class Schedule')

    def validate_end_time(self, field):
        if self.start_time.data >= field.data:
            raise ValidationError('End time must be after start time')
        
        # Check if class is within 8 AM - 10 PM
        if field.data > time(22, 0) or self.start_time.data < time(8, 0):
            raise ValidationError('Classes must be scheduled between 8:00 AM and 10:00 PM')