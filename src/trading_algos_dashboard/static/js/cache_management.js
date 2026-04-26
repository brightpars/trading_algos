document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".cache-chart-trigger").forEach((button) => {
    button.addEventListener("click", async () => {
      const chartUrl = button.dataset.chartUrl;
      const targetId = button.dataset.targetId;
      if (!chartUrl || !targetId) {
        return;
      }
      const target = document.getElementById(targetId);
      if (!target) {
        return;
      }
      const isLoaded = target.dataset.chart && target.dataset.chart !== "null";
      if (isLoaded) {
        target.innerHTML = "";
        target.dataset.chart = "null";
        button.textContent = "View chart";
        return;
      }
      button.disabled = true;
      try {
        const response = await fetch(chartUrl, { headers: { Accept: "application/json" } });
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.message || "Failed to load chart");
        }
        target.dataset.chart = JSON.stringify(payload.chart);
        Plotly.newPlot(target, payload.chart.data, payload.chart.layout || {}, payload.chart.config || {});
        button.textContent = "Hide chart";
      } catch (error) {
        target.innerHTML = `<div class="text-danger small">${error.message}</div>`;
      } finally {
        button.disabled = false;
      }
    });
  });
});