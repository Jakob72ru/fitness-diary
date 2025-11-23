document.addEventListener("DOMContentLoaded", function () {
  const input = document.getElementById("search-input");
  const resultsBox = document.getElementById("search-results");
  let debounceTimer;

  // Рендеринг результатов в выпадающий список
  function renderResults(items) {
    resultsBox.innerHTML = "";
    if (!items || items.length === 0) {
      resultsBox.style.display = "none";
      return;
    }
    items.forEach((it) => {
      const a = document.createElement("a");
      a.href = it.url;
      a.className = "list-group-item list-group-item-action";
      a.textContent = it.title;
      resultsBox.appendChild(a);
    });
    resultsBox.style.display = "block";
  }

  // AJAX-запрос через fetch
  function fetchResults(query) {
    fetch(`/search/?q=${encodeURIComponent(query)}`)
      .then((response) => {
        if (!response.ok) throw new Error("Network response was not ok");
        return response.json();
      })
      .then((data) => {
        renderResults(data.results || []);
      })
      .catch(() => {
        renderResults([]);
      });
  }

  // Обработчик ввода
  input.addEventListener("input", function () {
    const q = this.value.trim();
    clearTimeout(debounceTimer);
    if (q.length === 0) {
      renderResults([]);
      return;
    }
    // задержка (debounce) чтобы уменьшить частоту запросов
    debounceTimer = setTimeout(() => fetchResults(q), 250);
  });

  // По клику за пределами блока — скрыть список
  document.addEventListener("click", function (e) {
    if (!document.getElementById("search-container").contains(e.target)) {
      resultsBox.style.display = "none";
    }
  });

  // По клику внутри списка браузер сам перейдет по href
  // (нет необходимости в отдельном обработчике, если используете обычные <a>)
});