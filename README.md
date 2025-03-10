# UniTasker: Academic Management System 🎓

UniTasker is a comprehensive web-based academic management system built with Flask. It's designed to streamline interactions between students, professors, and administrative personnel in an educational environment.

## Features ✨

- **Multiple User Roles**
  - 👨‍🎓 **Student**: Access to grades, assignments, courses, and personal schedule
  - 👨‍🏫 **Professor**: Course management, assignment creation, and grading
  - 👨‍💼 **Admin**: System management, course creation, and student enrollment

- **Core Functionality**
  - 📚 Course management and enrollment
  - ✍️ Assignment creation and submission
  - 🎯 Task tracking with completion status
  - 📝 Personal notes system
  - 📊 Grading system with course averages
  - 📅 Weekly academic schedule
  - 🗓️ Personal calendar with task and assignment integration

## Technologies Used 🛠️

- **Backend**: Flask, SQLAlchemy, Flask-Login, Flask-WTF
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript
- **Additional Libraries**: FullCalendar.js

## Setup Instructions 🚀

### Prerequisites

- Python 3.9+
- PostgreSQL
- Git

### Installation Steps

1. ✅ Clone the repository
   ```bash
   git clone https://github.com/yourusername/UniTasker.git
   cd UniTasker
   ```

2. ✅ Create a virtual environment
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Unix/MacOS
   source venv/bin/activate
   ```

3. ✅ Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. ✅ Create a PostgreSQL database
   ```sql
   CREATE DATABASE unitasker_db1;
   ```

5. ✅ Create a `.env` file with the following content:
   ```
   SECRET_KEY=your-super-secret-key-change-this
   DATABASE_URL=postgresql://postgres:your_password@localhost:5432/unitasker_db1
   FLASK_APP=app.py
   FLASK_ENV=development
   ```

6. ✅ Initialize and apply database migrations
   ```bash
   flask db init
   flask db migrate -m "initial migration"
   flask db upgrade
   ```

7. ✅ Create an admin user (run in Python shell)
   ```python
   from app import app, db
   from models import User
   
   with app.app_context():
       admin = User(
           username='admin',
           email='admin@example.com',
           first_name='Admin',
           last_name='User',
           role='admin'
       )
       admin.set_password('your_password')
       db.session.add(admin)
       db.session.commit()
   ```

8. ✅ Run the application
   ```bash
   flask run
   ```

9. ✅ Access the application at http://127.0.0.1:5000

## Using the Application 🖥️

### First Steps

1. Log in as the admin user you created
2. Create courses and assign professors
3. Enroll students in courses
4. Set up the academic schedule

### Key Workflows

- **For Administrators**:
  - Manage courses, professors, and student enrollments
  - Set up the academic schedule with classrooms and time slots

- **For Professors**:
  - Create assignments for your courses
  - Grade student submissions
  - View your teaching schedule

- **For Students**:
  - View enrolled courses and academic schedule
  - Submit assignments
  - Track grades
  - Manage personal tasks and notes

## Database Schema 📊

The application uses a relational database with the following main entities:
- Users (with role-based permissions)
- Courses
- Assignments and Submissions
- Grades
- Tasks
- Notes
- Schedule slots
- Notifications

## Acknowledgements 🙏

- Flask and its extensions for the powerful yet flexible web framework
- Bootstrap for the responsive frontend components
- FullCalendar.js for the calendar functionality

---
