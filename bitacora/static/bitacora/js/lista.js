(function () {
  const form = document.getElementById("filtroForm");
  const status = document.getElementById("filterStatus");
  const tableContainer = document.getElementById("bitacoraTableContainer");
  const clearButton = document.getElementById("limpiarFiltros");
  const transitionDuration = 220;

  if (!form || !tableContainer) return;

  const controls = form.querySelectorAll("select, input[type=\"date\"]");
  let timeout = null;
  let controller = null;
  let requestId = 0;

  const setLoading = (isLoading) => {
    if (status) status.classList.toggle("is-visible", isLoading);
    tableContainer.classList.toggle("is-loading", isLoading);
  };

  const resetFormControls = () => {
    controls.forEach((control) => {
      control.value = "";
    });
  };

  const updateTable = async (url = null) => {
    if (controller) controller.abort();

    requestId += 1;
    const currentRequestId = requestId;
    controller = new AbortController();
    const params = new URLSearchParams(new FormData(form));
    const queryString = params.toString();
    const nextUrl =
      url || (queryString ? `${window.location.pathname}?${queryString}` : window.location.pathname);

    setLoading(true);

    try {
      const response = await fetch(nextUrl, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
        signal: controller.signal,
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const html = await response.text();
      const doc = new DOMParser().parseFromString(html, "text/html");
      const nextTable = doc.getElementById("bitacoraTableContainer");
      if (!nextTable) throw new Error("No se encontró la tabla filtrada.");

      if (currentRequestId !== requestId) return;

      await new Promise((resolve) => setTimeout(resolve, transitionDuration));
      if (currentRequestId !== requestId) return;

      tableContainer.innerHTML = nextTable.innerHTML;
      tableContainer.classList.remove("is-loading");
      tableContainer.classList.add("is-entering");
      tableContainer.addEventListener(
        "animationend",
        () => tableContainer.classList.remove("is-entering"),
        { once: true }
      );
      window.history.replaceState({}, "", nextUrl);
    } catch (error) {
      if (error.name !== "AbortError") form.submit();
    } finally {
      if (currentRequestId === requestId) {
        if (!tableContainer.classList.contains("is-entering")) {
          setLoading(false);
        } else if (status) {
          status.classList.remove("is-visible");
        }
      }
    }
  };

  const submitWithDelay = () => {
    window.clearTimeout(timeout);
    timeout = window.setTimeout(() => updateTable(), 180);
  };

  controls.forEach((control) => control.addEventListener("change", submitWithDelay));

  if (clearButton) {
    clearButton.addEventListener("click", (event) => {
      event.preventDefault();
      window.clearTimeout(timeout);
      resetFormControls();
      updateTable(clearButton.getAttribute("href") || window.location.pathname);
    });
  }
})();

