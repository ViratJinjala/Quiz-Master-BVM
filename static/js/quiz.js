// Get quiz data from hidden input
const quizDataElement = document.getElementById('quizData');
const quizDuration = parseInt(quizDataElement.dataset.duration) * 60; // in seconds

// Initialize quiz when page loads
window.onload = function() {
    // Check if timer is already running
    if (!localStorage.getItem('quizStarted')) {
        initializeQuiz();
    } else {
        startTimer();
        loadSavedAnswers();
    }
};

function initializeQuiz() {
    // Clear any existing quiz data
    localStorage.clear();
    localStorage.setItem('quizStarted', 'true');
    localStorage.setItem('quizStartTime', Date.now().toString());
    startTimer();
}

function startTimer() {
    let timerInterval;
    
    function updateTimer() {
        const startTime = parseInt(localStorage.getItem('quizStartTime'));
        const now = Date.now();
        const elapsedSeconds = Math.floor((now - startTime) / 1000);
        const remainingSeconds = quizDuration - elapsedSeconds;

        if (remainingSeconds <= 0) {
            clearInterval(timerInterval);
            alert('Time is up! Submitting quiz...');
            document.getElementById('quizForm').submit();
            return;
        }

        const hours = Math.floor(remainingSeconds / 3600);
        const minutes = Math.floor((remainingSeconds % 3600) / 60);
        const seconds = remainingSeconds % 60;

        const timeString = `Time Left: ${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        document.getElementById('timer').textContent = timeString;
    }

    updateTimer();
    timerInterval = setInterval(updateTimer, 1000);
}

function saveAnswer() {
    const form = document.getElementById('quizForm');
    const formData = new FormData(form);
    const answers = {};
    
    for (let pair of formData.entries()) {
        answers[pair[0]] = pair[1];
    }
    
    localStorage.setItem('quizAnswers', JSON.stringify(answers));
}

function loadSavedAnswers() {
    const savedAnswers = localStorage.getItem('quizAnswers');
    if (savedAnswers) {
        const answers = JSON.parse(savedAnswers);
        for (let name in answers) {
            const input = document.querySelector(`input[name="${name}"][value="${answers[name]}"]`);
            if (input) input.checked = true;
        }
    }
}

function submitQuiz() {
    localStorage.clear(); // Clear all stored quiz data
}

// Save answers before page unloads
window.onbeforeunload = function() {
    if (localStorage.getItem('quizStarted')) {
        saveAnswer();
    }
};

document.addEventListener('DOMContentLoaded', function() {
    const answers = {};

    // Load existing answers from local storage if available
    const storedAnswers = localStorage.getItem('quizAnswers');
    if (storedAnswers) {
        Object.assign(answers, JSON.parse(storedAnswers));
    }

    // Pre-select the saved answer if available
    const currentQuestionId = document.querySelector('input[type="radio"]').name.split('_')[1];
    if (answers[currentQuestionId]) {
        document.querySelector(`input[name="answer_${currentQuestionId}"][value="${answers[currentQuestionId]}"]`).checked = true;
    }

    // Function to save the current answer
    function saveAnswer() {
        const selectedOption = document.querySelector('input[type="radio"]:checked');
        if (selectedOption) {
            const questionId = selectedOption.name.split('_')[1];
            answers[questionId] = selectedOption.value;
            localStorage.setItem('quizAnswers', JSON.stringify(answers));
        }
    }

    // Attach saveAnswer to navigation buttons
    document.querySelectorAll('.nav-arrow').forEach(button => {
        button.addEventListener('click', saveAnswer);
    });

    // Submit all answers when the quiz is submitted
    document.getElementById('quizForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveAnswer(); // Save the current answer
        const formData = new FormData();
        for (const [questionId, answer] of Object.entries(answers)) {
            formData.append(`answer_${questionId}`, answer);
        }
        fetch(this.action, {
            method: 'POST',
            body: formData
        }).then(response => {
            if (response.ok) {
                localStorage.removeItem('quizAnswers'); // Clear stored answers
                window.location.href = response.url; // Redirect to the response URL
            }
        }).catch(error => {
            console.error('Error submitting quiz:', error);
        });
    });

    // Save answers before page unloads
    window.onbeforeunload = function() {
        if (localStorage.getItem('quizStarted')) {
            saveAnswer();
        }
    };
});