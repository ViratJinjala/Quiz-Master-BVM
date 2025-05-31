// Add click handlers for the add chapter buttons
document.querySelectorAll('.btn-add-chapter').forEach(button => {
    button.addEventListener('click', () => {
        const modal = new bootstrap.Modal(document.getElementById('addChapterModal'));
        modal.show();
    });
});

const script = document.createElement('script');
script.src = "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha3/dist/js/bootstrap.bundle.min.js";
document.head.appendChild(script);

