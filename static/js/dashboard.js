let currentQuizId = null;
let quizDetailsModal; // Store modal instance

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    quizDetailsModal = new bootstrap.Modal(document.getElementById('quizDetailsModal'));
    
    // Initialize quiz result modal if needed
    const flashMessages = JSON.parse(document.getElementById('flashMessages')?.value || '[]');
    flashMessages.forEach(message => {
        if (message && typeof message === 'object' && message.type === 'quiz_result') {
            const resultModal = new bootstrap.Modal(document.getElementById('quizResultModal'));
            document.getElementById('resultScore').textContent = `${message.score}%`;
            document.getElementById('resultTotal').textContent = `Total Marks: ${message.total}`;
            document.getElementById('resultCorrect').textContent = `Your Marks: ${message.correct}`;
            resultModal.show();
        }
    });
});

// Function for View button
function viewQuizDetails(quizId) {
    const numericId = parseInt(quizId);
    const quiz = QUIZZES_DATA.find(q => q.id === numericId);
    
    if (quiz) {
        currentQuizId = numericId;
        document.getElementById('quizDetailsModalLabel').textContent = quiz.name || 'Quiz Details';
        document.querySelector('.quiz-subject').textContent = quiz.subject_name || 'N/A';
        document.querySelector('.quiz-chapter').textContent = quiz.chapter_name || 'N/A';
        document.querySelector('.quiz-questions').textContent = quiz.question_count || '0';
        document.querySelector('.quiz-duration').textContent = quiz.time_duration ? `${quiz.time_duration}` : 'N/A';
        quizDetailsModal.show();
    }
}

// For the modal's Start Quiz button
window.startQuizFromModal = function() {
    if (currentQuizId) {
        quizDetailsModal.hide();
        window.location.href = `/start_quiz/${currentQuizId}`;
    }
};

// Function for sorting quizzes
function sortQuizzes(by) {
    const tbody = document.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aValue = by === 'date' ? 
            a.cells[3].textContent : 
            a.cells[1].textContent;
        const bValue = by === 'date' ? 
            b.cells[3].textContent : 
            b.cells[1].textContent;
        return aValue.localeCompare(bValue);
    });
    
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
}