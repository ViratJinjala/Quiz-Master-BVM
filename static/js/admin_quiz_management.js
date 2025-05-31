document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Confirm delete
    const deleteButtons = document.querySelectorAll('.btn-outline-danger');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('Are you sure you want to delete this item?')) {
                this.closest('form').submit();
            }
        });
    });

    // Clear form on modal close
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('hidden.bs.modal', function() {
            const forms = this.querySelectorAll('form');
            forms.forEach(form => form.reset());
        });
    });

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Search functionality enhancement
    const searchInput = document.querySelector('input[type="search"]');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            this.classList.toggle('is-valid', this.value.length > 2);
        });
    }

    // Dynamic Subject-Chapter Selection
    const subjectSelect = document.getElementById('subject-select');
    const chapterSelect = document.getElementById('chapter-select');

    if (subjectSelect && chapterSelect) {
        subjectSelect.addEventListener('change', function() {
            const subjectId = this.value;
            chapterSelect.disabled = true; // Disable while loading
            
            if (subjectId) {
                fetch(`/get_chapters/${subjectId}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(chapters => {
                        chapterSelect.innerHTML = '<option value="">Select Chapter</option>';
                        if (chapters && chapters.length > 0) {
                            chapters.forEach(chapter => {
                                chapterSelect.innerHTML += `
                                    <option value="${chapter.id}">${chapter.name}</option>
                                `;
                            });
                            chapterSelect.disabled = false;
                        } else {
                            chapterSelect.innerHTML = '<option value="">No chapters available</option>';
                            chapterSelect.disabled = true;
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching chapters:', error);
                        chapterSelect.innerHTML = '<option value="">Error loading chapters</option>';
                        chapterSelect.disabled = true;
                    });
            } else {
                chapterSelect.innerHTML = '<option value="">Select Chapter</option>';
                chapterSelect.disabled = true;
            }
        });
    }

    // Handle collapse button text
    const collapseButtons = document.querySelectorAll('[data-bs-toggle="collapse"]');
    collapseButtons.forEach(button => {
        button.addEventListener('click', function() {
            const isExpanded = this.getAttribute('aria-expanded') === 'true';
            this.innerHTML = isExpanded ? 
                '<i class="fas fa-chevron-down"></i> Show Questions' : 
                '<i class="fas fa-chevron-up"></i> Hide Questions';
        });
    });

    // Initialize all Bootstrap modals
    const modalElements = document.querySelectorAll('.modal');
    modalElements.forEach(modalElement => {
        new bootstrap.Modal(modalElement);
    });

    // Handle form submissions in modals
    document.querySelectorAll('.modal form').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                return;
            }
            // Let the form submit normally for file uploads
            // The page will reload after submission
        });
    });

    // Manual modal handling
    document.querySelectorAll('[data-bs-toggle="modal"]').forEach(button => {
        button.onclick = function(e) {
            e.preventDefault();
            const modalId = this.getAttribute('data-bs-target');
            const modal = document.querySelector(modalId);
            if (modal) {
                const bootstrapModal = bootstrap.Modal.getOrCreateInstance(modal);
                bootstrapModal.show();
            }
        };
    });
});

function submitQuestionForm(event, form) {
    event.preventDefault();
    fetch(form.action, {
        method: 'POST',
        body: new FormData(form)
    })
    .then(response => {
        // If response is not JSON, just reload the page
        if (!response.headers.get('content-type')?.includes('application/json')) {
            window.location.reload();
            return;
        }
        return response.json();
    })
    .then(data => {
        if (data && data.success) {
            const modal = bootstrap.Modal.getInstance(form.closest('.modal'));
            if (modal) modal.hide();
            form.reset();
        }
        window.location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
        window.location.reload(); // Fallback: just reload the page
    });
}

// Close modal on successful submission
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        if (message.classList.contains('alert-success')) {
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            });
        }
    });
}); 