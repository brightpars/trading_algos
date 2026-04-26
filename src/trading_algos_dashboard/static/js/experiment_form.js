document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form[action$='/experiments']");
  const symbolInput = form?.querySelector("input[name='symbol']");
  const startDateInput = form?.querySelector("input[name='start_date']");
  const startTimeInput = form?.querySelector("input[name='start_time']");
  const endDateInput = form?.querySelector("input[name='end_date']");
  const endTimeInput = form?.querySelector("input[name='end_time']");
  const notesTextarea = form?.querySelector("textarea[name='notes']");
  const configurationTextarea = form?.querySelector(
    "textarea[name='configuration_json']",
  );

  const textareas = document.querySelectorAll(
    "textarea[name='configuration_json']",
  );
  textareas.forEach((textarea) => {
    textarea.addEventListener("blur", () => {
      try {
        JSON.parse(textarea.value || "{}");
        textarea.classList.remove("is-invalid");
      } catch (_error) {
        textarea.classList.add("is-invalid");
      }
    });
  });

  const recentExperimentButtons = document.querySelectorAll(
    ".recent-experiment-preset",
  );
  recentExperimentButtons.forEach((button) => {
    button.addEventListener("click", () => {
      if (symbolInput) {
        symbolInput.value = button.dataset.symbol || "";
      }
      if (startDateInput) {
        startDateInput.value = button.dataset.startDate || "";
      }
      if (startTimeInput) {
        startTimeInput.value = button.dataset.startTime || "";
      }
      if (endDateInput) {
        endDateInput.value = button.dataset.endDate || "";
      }
      if (endTimeInput) {
        endTimeInput.value = button.dataset.endTime || "";
      }
      if (notesTextarea) {
        notesTextarea.value = button.dataset.notes || "";
      }
      if (configurationTextarea) {
        configurationTextarea.value = button.dataset.configurationJson || "{}";
        configurationTextarea.classList.remove("is-invalid");
      }
    });
  });
});