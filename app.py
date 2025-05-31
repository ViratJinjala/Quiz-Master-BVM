from flask import Flask, request, redirect, url_for, render_template, flash, session, jsonify, Response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from Models.models import *
from datetime import datetime
import csv
from io import StringIO
from google import genai
import os
import tempfile

app = Flask(__name__)
# Required for flashing messages and using flask 
app.secret_key = 'your_secret_key'  

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, email, name, is_admin=False):
        self.id = id
        self.email = email
        self.name = name
        self.is_admin = is_admin

@login_manager.user_loader
def load_user(user_id):
    if user_id == 'admin':
        return User('admin', 'admin@gmail.com', 'Admin', True)
    
    user_data = get_user_by_id(user_id)
    if user_data:
        return User(
            id=user_data['id'],
            email=user_data['email'],
            name=user_data['name']
        )
    return None

## FOR SECURITY WHEN SCALING THE APPLICATION
# @app.before_request
# def check_auth():
#     if not current_user.is_authenticated and \
#        request.endpoint not in PUBLIC_ROUTES:
#         return redirect(url_for('login'))



# Initialize DB
create_tables()

# These must be BEFORE any routes
ALLOWED_EXTENSIONS = {'csv'}  # Remove 'pdf', 'txt', 'doc', 'docx' if not needed

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')  # Default route
def home():
    return redirect(url_for('login'))  # Redirect to the login page

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['register-email']
        password = request.form['register-password']
        name = request.form['name']
        qualification = request.form['qualification']
        dob = request.form['dob']

        # Check if the user already exists
        existing_user = get_user_by_username(email)
        if existing_user:
            flash('User already exists. Please log in.')
            return redirect(url_for('login'))  # Redirect to login if user exists

        # Insert new user into the database
        insert_user(email, password, name, qualification, dob)
        flash('Registration successful! You can now log in.')
        return redirect(url_for('login'))  # Redirect to login after successful registration

    return render_template('login.html')  # Render registration form if GET request

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['login-email']
        password = request.form['login-password']
        
        # Check for admin credentials
        if email == 'admin@gmail.com' and password == 'admin':
            admin_user = User('admin', email, 'Admin', True)
            login_user(admin_user)
            return redirect(url_for('admin_dashboard'))

        user = get_user_by_email(email)
        if user and user['password'] == password:
            user_obj = User(
                id=user['id'],
                email=user['email'],
                name=user['name']
            )
            login_user(user_obj)
            return redirect(url_for('dashboard'))
        
        flash('Invalid credentials. Please try again.', 'error')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    subjects = get_subjects_with_chapters()
    return render_template('admin_dashboard.html', subjects=subjects)

# main page for quiz management
@app.route('/admin_quiz_management')
def admin_quiz_management():
    subjects = get_all_subjects()
    quizzes = get_quizzes()
    today_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('admin_quiz_management.html', 
                         subjects=subjects, 
                         quizzes=quizzes, 
                         today_date=today_date)

@app.route('/search_quiz')
def search_quiz():
    query = request.args.get('q')
    quizzes = search_quizzes(query)
    return render_template('admin_quiz_management.html', quizzes=quizzes)


@app.route('/add_question/<int:quiz_id>', methods=['POST'])
def add_question(quiz_id):
    try:
        question_data = {
            'quiz_id': quiz_id,
            'question_statement': request.form['question_statement'],
            'option1': request.form['option1'],
            'option2': request.form['option2'],
            'option3': request.form['option3'],
            'option4': request.form['option4'],
            'correct_option': int(request.form['correct_option']),
            'weightage': int(request.form['weightage'])  # New weightage field
        }
        
        add_question_in_db(**question_data)
        return jsonify({'success': True, 'message': 'Question added successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error adding question: {str(e)}'})

@app.route('/add_quiz', methods=['POST'])
def add_quiz():
    try:
        # Print form data for debugging
        print("Form data:", request.form)
        
        quiz_data = {
            'chapter_id': int(request.form['chapter_id']),
            'quiz_date': request.form['quiz_date'],
            'quiz_duration': int(request.form['quiz_duration']),
            'passing_score': int(request.form['passing_score']),
            'max_attempts': int(request.form['max_attempts']),
            'instructions': request.form.get('instructions', ''),
            'status': request.form['status']
        }
        
        # Print quiz data for debugging
        print("Quiz data:", quiz_data)
        
        add_quiz_in_db(**quiz_data)
        flash('Quiz added successfully!', 'success')
        return redirect(url_for('admin_quiz_management'))
    except Exception as e:
        print(f"Error in add_quiz: {str(e)}")  # Debug print
        flash(f'Error adding quiz: {str(e)}', 'error')
        return redirect(url_for('admin_quiz_management'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    quizzes = get_available_quizzes()
    return render_template('dashboard.html', quizzes=quizzes)

@app.route('/add_chapter', methods=['POST'])
def add_chapter():
    try:
        subject_id = request.form['subject_id']
        name = request.form['name']  # Simplified to just 'name'
        description = request.form.get('description', '')  # Made description optional
        
        add_chapter_in_db(subject_id, name, description)
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        print(f"Error: {e}")  # For debugging
        return redirect(url_for('admin_dashboard'))

@app.route('/delete_chapter/<int:chapter_id>', methods=['POST'])
def delete_chapter(chapter_id):
    delete_chapter_in_db(chapter_id)
    return redirect(url_for('admin_dashboard'))

@app.route('/edit_chapter/<int:chapter_id>', methods=['POST'])
def edit_chapter(chapter_id):
    chapter_name = request.form['chapter_name']
    description = request.form.get('description', '')
    
    edit_chapter_in_db(chapter_id, chapter_name, description)
    return redirect(url_for('admin_dashboard'))

@app.route('/add_subject', methods=['POST'])
def add_subject():
    name = request.form.get('name')
    description = request.form.get('description')
    add_subject_in_db(name, description)
    return redirect(url_for('admin_dashboard'))

@app.route('/scores')
@login_required
def scores():
    user_scores = get_user_scores(current_user.id)
    return render_template('scores.html', scores=user_scores)

@app.route('/get_chapters/<int:subject_id>')
def get_chapters(subject_id):
    try:
        chapters = get_chapters_by_subject(subject_id)
        # Convert chapters to JSON format
        chapters_list = [{'id': chapter['id'], 'name': chapter['name']} for chapter in chapters]
        return jsonify(chapters_list)
    except Exception as e:
        return jsonify([]), 500  # Return empty list with error status

@app.route('/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    try:
        delete_question_in_db(question_id)
        flash('Question deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting question: {str(e)}', 'error')
    return redirect(url_for('admin_quiz_management'))

@app.route('/start_quiz/<int:quiz_id>')
@login_required
def start_quiz(quiz_id):
    try:
        # Get quiz details
        quiz = get_quiz_by_id(quiz_id)
        if not quiz:
            flash('Quiz not found.', 'error')
            return redirect(url_for('dashboard'))

        # Get questions
        questions = get_quiz_questions(quiz_id)
        if not questions:
            flash('No questions found for this quiz.', 'error')
            return redirect(url_for('dashboard'))

        # Store quiz data in session
        session['current_quiz'] = {
            'quiz_id': quiz_id,
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Redirect to first question
        return redirect(url_for('quiz', quiz_id=quiz_id, q=0))

    except Exception as e:
        flash(f'Error starting quiz: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/quiz/<int:quiz_id>')
def quiz(quiz_id):
    try:
        # Get current question number from query params
        current_q = request.args.get('q', 0, type=int)
        
        # Get quiz details
        quiz = get_quiz_by_id(quiz_id)
        if not quiz:
            flash('Quiz not found.', 'error')
            return redirect(url_for('dashboard'))

        # Get all questions
        questions = get_quiz_questions(quiz_id)
        if not questions:
            flash('No questions found for this quiz.', 'error')
            return redirect(url_for('dashboard'))

        total_questions = len(questions)
        
        # Validate question number
        if current_q >= total_questions:
            flash('Invalid question number.', 'error')
            return redirect(url_for('dashboard'))

        # Initialize quiz session if not already started
        if 'current_quiz' not in session:
            session['current_quiz'] = {
                'quiz_id': quiz_id,
                'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        return render_template('quiz.html', 
                             quiz=quiz,
                             questions=questions,
                             current_q=current_q,
                             total_questions=total_questions)

    except Exception as e:
        flash(f'Error loading quiz: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    try:
        questions = get_quiz_questions(quiz_id)
        total_marks = 0
        your_marks = 0

        for question in questions:
            user_answer = request.form.get(f'answer_{question["id"]}')
            if user_answer and int(user_answer) == question['correct_option']:
                your_marks += question['weightage']
            total_marks+= question['weightage']

        score_percentage = (your_marks / total_marks) * 100 if total_marks > 0 else 0
        
        save_quiz_score(
            quiz_id=quiz_id,
            user_id=current_user.id,
            score=score_percentage
        )

        flash({
            'type': 'quiz_result',
            'score': round(score_percentage, 1),
            'correct': your_marks,
            'total': total_marks
        }) 

        return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash('Error submitting quiz. Please try again.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/upload_questions/<int:quiz_id>', methods=['GET', 'POST'])
def upload_questions(quiz_id):
    if request.method == 'POST':
        # Check if file was uploaded
        if 'questions_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('admin_quiz_management'))
        
        file = request.files['questions_file']
        # If user submits without selecting a file
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('admin_quiz_management'))
        if not file.filename.endswith('.csv'):
            if file.filename.endswith('.pdf'):
                client = genai.Client(api_key="")
                
                # Save the uploaded PDF file to a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    file.save(temp_file.name)
                    temp_file_path = temp_file.name
                
                # Upload the temporary file
                sample_pdf = client.files.upload(file=temp_file_path)
                
                # Provide context to Gemini about what to do with the PDF
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[
                        """ read the given 'sample_pdf' content and extract data from it. return only response such that 
                            it will be like .csv format.
                            it will be having values in comma separated with the default header:
                            'question_statement','option1', 'option2', 'option3', 'option4', 'correct_option','weightage'
                            and the values are below them with the same format as csv files should be.
                            add question under 'question_statement' position, while add options appropriately into it's section. the 
                            'correct_option' will be numeric value between 1 to 4. here the weightage is optional, so if it's not 
                            given then keep it 1 by default.""",
                    sample_pdf
                    ]
                )
                L=response.text.split('\n')
                T=[]
                for x in L:
                    T.append(x.split(','))
                T=T[1:-1]

                success_count = 0
                for X in T:
                    try:
                        question_data = {
                            'quiz_id': quiz_id,
                            'question_statement': X[0].strip(),
                            'option1': X[1].strip(),
                            'option2': X[2].strip(),
                            'option3': X[3].strip(),
                            'option4': X[4].strip(),
                            'correct_option': X[5].strip(),
                            'weightage': X[6].strip()
                        }
                        add_question_in_db(**question_data)
                        success_count += 1
                    except Exception as e:
                        print(f"Error processing row: {e}")
                        continue
                
                if success_count > 0:
                    flash(f'Successfully uploaded {success_count} questions!', 'success')
                else:
                    flash('No questions were uploaded. Please check your PDF file.', 'error')                
                return redirect(url_for('admin_quiz_management'))
                
        try:
            stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_data = csv.DictReader(stream)
            
            # Validate headers
            required_columns = ['question_statement', 'option1', 'option2', 'option3', 'option4', 'correct_option','weightage']
            headers = csv_data.fieldnames
            if not headers or not all(col in headers for col in required_columns):
                flash('Invalid CSV format. Please use the correct template.', 'error')
                return redirect(url_for('admin_quiz_management'))
            
            # Process each row
            success_count = 0
            for row in csv_data:
                try:
                    question_data = {
                            'quiz_id': quiz_id,
                            'question_statement': row['question_statement'].strip(),
                            'option1': row['option1'].strip(),
                            'option2': row['option2'].strip(),
                            'option3': row['option3'].strip(),
                            'option4': row['option4'].strip(),
                            'correct_option': int(row['correct_option'].strip()),
                            'weightage': row['weightage'].strip()
                        }
                    add_question_in_db(**question_data)
                    success_count += 1
                except Exception as e:
                    print(f"Error processing row: {e}")
                    continue
                
                if success_count > 0:
                    flash(f'Successfully uploaded {success_count} questions!', 'success')
                else:
                    flash('No questions were uploaded. Please check your CSV file.', 'error')
                
                return redirect(url_for('admin_quiz_management'))
                
        except Exception as e:
            print(f"Error processing file: {e}")
            flash('Error processing file. Please check the format.', 'error')
            return redirect(url_for('admin_quiz_management'))
    
    return redirect(url_for('admin_quiz_management'))

@app.route('/download_template')
def download_template():
    # Create a sample CSV in memory
    output = StringIO()
    writer = csv.writer(output)
    # Write headers
    writer.writerow(['question_statement', 'option1', 'option2', 'option3', 'option4', 'correct_option','weightage'])
    # Write sample row
    writer.writerow(['What is 2+2?', '2', '3', '4', '5', '3','1'])
    
    # Create the response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=question_template.csv'}
    )

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8000, debug=True)