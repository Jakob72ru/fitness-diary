(function() {
  // Массив input-элементов, которые соответствуют твоему полю
  var inputs = document.querySelectorAll('.weight-input-no-spin');

  inputs.forEach(function(input) {
    // Запоминаем исходное значение при первом фокусе (не при загрузке страницы!)
    var initialValueSet = false;
    var initialValue = '';

    // Установка обработчика фокуса: запоминаем текущее значение, если ещё не запомнено
    input.addEventListener('focus', function() {
      if (!initialValueSet) {
        initialValue = input.value;
        input.dataset.originalValue = initialValue;
        initialValueSet = true;
      }
    });

    // Обработка отправки формы: если пустое, вернуть исходное значение
    var form = input.closest('form');
    if (form) {
      form.addEventListener('submit', function() {
        if (input.value.trim() === '') {
          // Вернуть то, что было до клика/фокусa
          var toSend = input.dataset.originalValue;
          input.value = (toSend != null && toSend !== '') ? toSend : '';
        } else {
          // Если ввёл поменялось значение, обновляем исходное для последующих отправок
          input.dataset.originalValue = input.value;
        }
      });
    }

    // Дополнительно: если кто-то стирает всё в поле, перед фокусом можно сохранить текущий state
    input.addEventListener('input', function() {
      // Ничего не делаем здесь по умолчанию, оставляем поведение браузера
      // Этот блок можно оставить пустым, чтобы не мешать
    });
  });
})();