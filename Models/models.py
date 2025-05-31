from Models.database import get_db_connection
from datetime import datetime
import pytz

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            qualification TEXT,
            dob TEXT
        );

        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter_id INTEGER NOT NULL,
            date_of_quiz TEXT,
            time_duration TEXT,
            remarks TEXT,
            FOREIGN KEY (chapter_id) REFERENCES chapters (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            question_statement TEXT NOT NULL,
            option1 TEXT NOT NULL,
            option2 TEXT NOT NULL,
            option3 TEXT NOT NULL,
            option4 TEXT NOT NULL,
            correct_option INTEGER NOT NULL,
            weightage INTEGER,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            quiz_id INTEGER NOT NULL,
            time_stamp TEXT,
            total_score INTEGER,
            correct_answers INTEGER,
            total_questions INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    conn.close()

def insert_user(email, password, name, qualification, dob):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (email, password, name, qualification, dob) VALUES (?, ?, ?, ?, ?)",
                   (email, password, name, qualification, dob))
    conn.commit()
    conn.close()

def get_user_by_username(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()  # Fetch one user
    conn.close()
    return user

# all this for admin dashboard
def get_subjects_with_chapters():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Modified query to correctly count questions
    query = """
    SELECT 
        s.id as subject_id,
        s.name as subject_name,
        c.id as chapter_id,
        c.name as chapter_name,
        (
            SELECT COUNT(*)
            FROM questions q2
            JOIN quizzes qz ON q2.quiz_id = qz.id
            WHERE qz.chapter_id = c.id
        ) as question_count
    FROM subjects s
    LEFT JOIN chapters c ON s.id = c.subject_id
    ORDER BY s.id, c.id
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    # Organize the data into a nested structure
    subjects = {}
    for row in rows:
        if row['subject_id'] not in subjects:
            subjects[row['subject_id']] = {
                'id': row['subject_id'],
                'name': row['subject_name'],
                'chapters': []
            }
        
        if row['chapter_id']:  # Only add chapter if it exists
            subjects[row['subject_id']]['chapters'].append({
                'id': row['chapter_id'],
                'name': row['chapter_name'],
                'questions': row['question_count'] or 0
            })
    
    conn.close()
    return list(subjects.values())

def add_chapter_in_db(subject_id, name, description):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chapters (subject_id, name, description)
        VALUES (?, ?, ?)
    """, (subject_id, name, description))
    conn.commit()
    conn.close()

def delete_chapter_in_db(chapter_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chapters WHERE id = ?", (chapter_id,))
    conn.commit()
    conn.close()

def edit_chapter_in_db(chapter_id, name, description):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE chapters 
        SET name = ?, description = ?
        WHERE id = ?
    """, (name, description, chapter_id))
    conn.commit()
    conn.close()

def get_chapter_by_id(chapter_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM chapters WHERE id = ?
    """, (chapter_id,))
    chapter = cursor.fetchone()
    conn.close()
    return chapter

def add_subject_in_db(name, description):
    print(f"Adding subject: {name}, {description}")  # Debug print
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO subjects (name, description)
            VALUES (?, ?)
        """, (name, description))
        conn.commit()
        print("Subject added successfully")  # Debug print
    except Exception as e:
        print(f"Error adding subject: {e}")
        conn.rollback()
    finally:
        conn.close()

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_quizzes():
    conn = get_db_connection()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    # Get quizzes with basic info
    cursor.execute("""
        SELECT q.id, q.chapter_id, q.remarks,
               q.date_of_quiz, q.time_duration,
               c.name as chapter_name, s.name as subject_name
        FROM quizzes q
        JOIN chapters c ON q.chapter_id = c.id
        JOIN subjects s ON c.subject_id = s.id
        ORDER BY q.date_of_quiz DESC
    """)
    quizzes = cursor.fetchall()
    
    # Get questions for each quiz, including weightage
    for quiz in quizzes:
        cursor.execute("""
            SELECT id, question_statement as title,
                   option1, option2, option3, option4, correct_option, weightage
            FROM questions
            WHERE quiz_id = ?
            ORDER BY id
        """, (quiz['id'],))
        quiz['questions'] = cursor.fetchall()
    
    conn.close()
    return quizzes

def search_quizzes(query):
    conn = get_db_connection()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    search_term = f"%{query}%"
    cursor.execute("""
        SELECT q.id, q.chapter_id, q.remarks,
               q.date_of_quiz, q.time_duration,
               c.name as chapter_name, s.name as subject_name
        FROM quizzes q
        JOIN chapters c ON q.chapter_id = c.id
        JOIN subjects s ON c.subject_id = s.id
        WHERE s.name LIKE ? 
           OR c.name LIKE ?
           OR q.remarks LIKE ?
        ORDER BY q.date_of_quiz DESC
    """, (search_term, search_term, search_term))
    quizzes = cursor.fetchall()
    
    # Get questions for each quiz
    for quiz in quizzes:
        cursor.execute("""
            SELECT id, question_statement as title
            FROM questions
            WHERE quiz_id = ?
        """, (quiz['id'],))
        quiz['questions'] = cursor.fetchall()
    
    conn.close()
    return quizzes

# all this for quiz management
def add_question_in_db(quiz_id, question_statement, option1, option2, option3, option4, correct_option, weightage):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO questions (quiz_id, question_statement, option1, option2, option3, option4, correct_option, weightage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (quiz_id, question_statement, option1, option2, option3, option4, correct_option, weightage))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Database error: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()
    

def add_quiz_in_db(chapter_id, quiz_date, quiz_duration, passing_score, max_attempts, instructions, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Convert quiz_date to IST if it's not already
        if quiz_date:
            try:
                ist = pytz.timezone('Asia/Kolkata')
                date_obj = datetime.strptime(quiz_date, '%Y-%m-%d')
                date_ist = ist.localize(date_obj)
                quiz_date = date_ist.strftime('%Y-%m-%d')
            except Exception as e:
                print(f"Error converting date to IST: {e}")
        
        cursor.execute("""
            INSERT INTO quizzes (
                chapter_id, date_of_quiz, time_duration, remarks
            ) VALUES (?, ?, ?, ?)
        """, (chapter_id, quiz_date, quiz_duration, instructions))
        conn.commit()
        
    except Exception as e:
        print(f"Error adding quiz: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_all_subjects():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name 
        FROM subjects 
        ORDER BY name
    """)
    subjects = cursor.fetchall()
    conn.close()
    return subjects

def get_chapters_by_subject(subject_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.name, s.name as subject_name
        FROM chapters c
        JOIN subjects s ON c.subject_id = s.id
        WHERE c.subject_id = ?
        ORDER BY c.name
    """, (subject_id,))
    chapters = cursor.fetchall()
    conn.close()
    return chapters

def delete_question_in_db(question_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
    conn.commit()
    conn.close()

def get_available_quizzes():
    conn = get_db_connection()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                q.id,
                q.remarks as name,
                q.date_of_quiz,
                q.time_duration,
                s.name as subject_name,
                c.name as chapter_name,
                (SELECT COUNT(*) FROM questions WHERE quiz_id = q.id) as question_count
            FROM quizzes q
            LEFT JOIN chapters c ON q.chapter_id = c.id
            LEFT JOIN subjects s ON c.subject_id = s.id
            ORDER BY q.date_of_quiz DESC
        """)
        
        quizzes = cursor.fetchall()
        
        for quiz in quizzes:
            if quiz['date_of_quiz']:
                
                for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d']:
                    try:
                        quiz['date_of_quiz'] = datetime.strptime(
                                quiz['date_of_quiz'], fmt
                            ).strftime('%d %b %Y')
                        break
                    except ValueError:
                        continue
            
            # Rest of the formatting...
            if quiz['time_duration']:
                quiz['time_duration'] = f"{quiz['time_duration']} mins"
            else:
                quiz['time_duration'] = 'Not set'
            
            if not quiz['name']:
                quiz['name'] = f"{quiz['subject_name']} Quiz"
                
            if quiz['question_count'] is None:
                quiz['question_count'] = 0
                
        return quizzes
        
    except Exception as e:
        print(f"Error retrieving quizzes: {e}")
        return []
        
    finally:
        conn.close()

def get_user_by_id(user_id):
    if user_id == 'admin':
        return None
        
    conn = get_db_connection()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        return user
    except Exception as e:
        print(f"Error getting user by ID: {e}")
        return None
    finally:
        conn.close()

def get_user_by_email(email):
    conn = get_db_connection()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        return user
    except Exception as e:
        print(f"Error getting user by email: {e}")
        return None
    finally:
        conn.close()

def get_quiz_by_id(quiz_id):
    conn = get_db_connection()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                q.id,
                q.remarks as name,
                q.date_of_quiz,
                q.time_duration,
                s.name as subject_name,
                c.name as chapter_name,
                (SELECT COUNT(*) FROM questions WHERE quiz_id = q.id) as question_count
            FROM quizzes q
            LEFT JOIN chapters c ON q.chapter_id = c.id
            LEFT JOIN subjects s ON c.subject_id = s.id
            WHERE q.id = ?
        """, (quiz_id,))
        
        quiz = cursor.fetchone()
        
        if quiz:
            # Format date if it exists
            if quiz['date_of_quiz']:
                try:
                    quiz['date_of_quiz'] = datetime.strptime(
                        quiz['date_of_quiz'], '%Y-%m-%d'
                    ).strftime('%d %b %Y')
                except:
                    quiz['date_of_quiz'] = 'Not set'
            
            # Add duration unit if exists
            if quiz['time_duration']:
                quiz['time_duration'] = int(quiz['time_duration'])
            else:
                quiz['time_duration'] = 0
                
            # Set default name if not provided
            if not quiz['name']:
                quiz['name'] = f"{quiz['subject_name']} Quiz"
        
        return quiz
        
    except Exception as e:
        print(f"Error retrieving quiz: {e}")
        return None
        
    finally:
        conn.close()

def get_quiz_questions(quiz_id):
    conn = get_db_connection()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                id,
                question_statement,
                option1,
                option2,
                option3,
                option4,
                correct_option,
                weightage
            FROM questions 
            WHERE quiz_id = ?
            ORDER BY id
        """, (quiz_id,))
        
        questions = cursor.fetchall()
        return questions
        
    except Exception as e:
        print(f"Error retrieving questions: {e}")
        return []
        
    finally:
        conn.close()

def save_quiz_score(quiz_id, user_id, score):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get current time in IST
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("""
            INSERT INTO scores (
                user_id, 
                quiz_id, 
                time_stamp, 
                total_score
            ) VALUES (?, ?, ?, ?)
        """, (user_id, quiz_id, current_time, score))
        
        score_id = cursor.lastrowid
        conn.commit()
        return score_id
        
    except Exception as e:
        print(f"Error saving score: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_user_scores(user_id):
    conn = get_db_connection()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                s.id,
                s.total_score,
                s.time_stamp,
                CASE 
                    WHEN q.remarks IS NOT NULL AND q.remarks != '' 
                    THEN q.remarks 
                    ELSE sub.name || ' ' || ch.name
                END as quiz_name,
                (SELECT COUNT(*) FROM questions WHERE quiz_id = s.quiz_id) as total_questions
            FROM scores s
            JOIN quizzes q ON s.quiz_id = q.id
            JOIN chapters ch ON q.chapter_id = ch.id
            JOIN subjects sub ON ch.subject_id = sub.id
            WHERE s.user_id = ?
            ORDER BY s.time_stamp DESC
        """, (user_id,))
        
        scores = cursor.fetchall()
        return scores
        
    except Exception as e:
        print(f"Error retrieving scores: {e}")
        return []
    finally:
        conn.close()
