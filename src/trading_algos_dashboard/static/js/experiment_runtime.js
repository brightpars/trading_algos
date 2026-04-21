document.addEventListener("DOMContentLoaded", () => {
  const runtimePanel = document.querySelector("[data-experiment-runtime]");
  if (!runtimePanel) {
    return;
  }

  const timerElement = runtimePanel.querySelector("[data-elapsed-timer]");
  const statusHeading = runtimePanel.querySelector(".experiment-runtime-status");
  const statusMessage = runtimePanel.querySelector(".experiment-runtime-message");
  const runtimeCard = runtimePanel.querySelector(".experiment-runtime-card");
  const cancelButton = runtimePanel.querySelector("button[type='submit']");
  const statusApiUrl = runtimePanel.dataset.statusApiUrl;

  let runtime = JSON.parse(runtimePanel.dataset.experimentRuntime || "{}");

  const formatDuration = (totalSeconds) => {
    const seconds = Math.max(0, Math.floor(totalSeconds));
    const hours = String(Math.floor(seconds / 3600)).padStart(2, "0");
    const minutes = String(Math.floor((seconds % 3600) / 60)).padStart(2, "0");
    const secs = String(seconds % 60).padStart(2, "0");
    return `${hours}:${minutes}:${secs}`;
  };

  const formatTimestamp = (value) => {
    if (!value) {
      return "—";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return String(value);
    }
    return date.toLocaleString();
  };

  const updateField = (fieldName, value) => {
    const field = runtimePanel.querySelector(`[data-runtime-field='${fieldName}']`);
    if (field) {
      field.textContent = value;
    }
  };

  const render = () => {
    const startedAt = runtime.started_at ? new Date(runtime.started_at) : null;
    const finishedAt = runtime.finished_at ? new Date(runtime.finished_at) : null;

    if (timerElement) {
      if (runtime.duration_seconds != null) {
        timerElement.textContent = formatDuration(runtime.duration_seconds);
      } else if (startedAt && !Number.isNaN(startedAt.getTime())) {
        timerElement.textContent = formatDuration((Date.now() - startedAt.getTime()) / 1000);
      } else {
        timerElement.textContent = "00:00:00";
      }
    }

    updateField("started_at", formatTimestamp(runtime.started_at || runtime.created_at));
    updateField("finished_at", formatTimestamp(runtime.finished_at));
    updateField("status", runtime.status || "unknown");
    updateField(
      "dataset_endpoint",
      runtime.dataset_source?.endpoint || "Loading…",
    );

    if (runtime.status === "running") {
      statusHeading.textContent = "Running experiment…";
      statusMessage.textContent = "Your algorithm run is in progress. This page updates automatically every second.";
      runtimeCard?.classList.remove("is-failed");
      if (cancelButton) {
        cancelButton.disabled = false;
        cancelButton.textContent = "Stop experiment";
      }
    } else if (runtime.status === "cancelling") {
      statusHeading.textContent = "Cancelling experiment…";
      statusMessage.textContent = "Stop requested. The run will finish its current safe checkpoint and then stop.";
      runtimeCard?.classList.remove("is-failed");
      if (cancelButton) {
        cancelButton.disabled = true;
        cancelButton.textContent = "Stopping…";
      }
    } else if (runtime.status === "cancelled") {
      statusHeading.textContent = "Experiment cancelled";
      statusMessage.textContent = "This experiment was stopped by the user before completion.";
      runtimeCard?.classList.add("is-failed");
      if (cancelButton) {
        cancelButton.closest("form")?.remove();
      }
    } else if (runtime.status === "failed") {
      statusHeading.textContent = "Experiment failed";
      statusMessage.textContent = runtime.error_message || "The experiment stopped before completion.";
      runtimeCard?.classList.add("is-failed");
      if (cancelButton) {
        cancelButton.closest("form")?.remove();
      }
    } else if (runtime.status === "completed") {
      window.location.reload();
    }
  };

  render();

  const timerId = window.setInterval(render, 1000);

  if (!statusApiUrl) {
    return;
  }

  const pollStatus = async () => {
    try {
      const response = await fetch(statusApiUrl, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) {
        return;
      }
      const payload = await response.json();
      runtime = payload.experiment || runtime;
      render();
      if (runtime.status !== "running") {
        window.clearInterval(timerId);
      }
    } catch (_error) {
      // Ignore transient polling errors and keep the local timer running.
    }
  };

  window.setInterval(pollStatus, 1000);
});