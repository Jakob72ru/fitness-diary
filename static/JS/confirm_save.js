document.addEventListener('DOMContentLoaded', function () {
    // Блок 1: модальное окно
    var confirmModal = document.getElementById('confirmModal');
    // Когда модальное окно открывается
    confirmModal.addEventListener('shown.bs.modal', function() {
        document.getElementById('confirmSave').focus();
    });

    // Обработчик для кнопки подтверждения
    document.getElementById('confirmSave').addEventListener('click', function() {
        document.getElementById('month-results').submit();
    });

    // Обработчик нажатия Enter в модальном окне
    confirmModal.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            document.getElementById('confirmSave').click();
        }
    });

    // Предотвращаем отправку формы по Enter в основной форме
    document.getElementById('month-results').addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            var modal = new bootstrap.Modal(document.getElementById('confirmModal'));
            modal.show();
        }
    });

    // Блок 2: Bootstrap Tooltip инициализация для кнопок в сетке grid-summary
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});