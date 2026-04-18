(() => {
  const button = document.getElementById("check-data-source-btn");
  const form = document.getElementById("data-source-settings-form");
  const result = document.getElementById("data-source-check-result");
  if (!button || !form || !result) {
    return;
  }

  button.addEventListener("click", async () => {
    const formData = new FormData(form);
    result.innerHTML = '<div class="alert alert-info mb-0" role="alert">Checking connection...</div>';
    try {
      const response = await fetch(button.dataset.checkUrl, {
        method: "POST",
        body: formData,
      });
      const payload = await response.json();
      if (!response.ok || payload.status !== "ok") {
        const message = payload.message || "The data server is not responding.";
        result.innerHTML = `<div class="alert alert-danger mb-0" role="alert">${message}</div>`;
        return;
      }
      result.innerHTML = `<div class="alert alert-success mb-0" role="alert">Connected to ${payload.endpoint}.</div>`;
    } catch (_error) {
      result.innerHTML = '<div class="alert alert-danger mb-0" role="alert">Connection check failed.</div>';
    }
  });
})();