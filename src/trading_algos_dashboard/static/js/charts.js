document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".chart-container").forEach((element) => {
    const raw = element.dataset.chart;
    if (!raw || raw === "null") {
      return;
    }
    const payload = JSON.parse(raw);
    Plotly.newPlot(element, payload.data, payload.layout || {}, payload.config || {});
  });
});