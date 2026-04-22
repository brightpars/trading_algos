(() => {
  const root = document.querySelector("[data-admin-algorithm-catalog]");
  if (!root) {
    return;
  }

  const queueTable = root.querySelector("[data-admin-queue-table] tbody");
  const searchInput = document.getElementById("catalog-admin-search");
  const statusSelect = document.getElementById("catalog-admin-status");
  const reviewStateSelect = document.getElementById("catalog-admin-review-state");
  const categorySelect = document.getElementById("catalog-admin-category");
  const catalogTypeSelect = document.getElementById("catalog-admin-catalog-type");
  const advancedLabelSelect = document.getElementById("catalog-admin-advanced-label");
  const linkedSelect = document.getElementById("catalog-admin-linked");
  const brokenOnlyCheckbox = document.getElementById("catalog-admin-only-broken");
  const unresolvedOnlyCheckbox = document.getElementById("catalog-admin-only-unresolved");

  const refreshQueueSnapshot = async () => {
    if (!queueTable) {
      return;
    }
    const params = new URLSearchParams();
    if (searchInput?.value.trim()) {
      params.set("search", searchInput.value.trim());
    }
    if (statusSelect?.value) {
      params.set("status", statusSelect.value);
    }
    if (reviewStateSelect?.value) {
      params.set("review_state", reviewStateSelect.value);
    }
    if (categorySelect?.value) {
      params.set("category", categorySelect.value);
    }
    if (catalogTypeSelect?.value) {
      params.set("catalog_type", catalogTypeSelect.value);
    }
    if (advancedLabelSelect?.value) {
      params.set("advanced_label", advancedLabelSelect.value);
    }
    if (linkedSelect?.value) {
      params.set("linked", linkedSelect.value);
    }
    if (brokenOnlyCheckbox?.checked) {
      params.set("only_broken", "true");
    }
    if (unresolvedOnlyCheckbox?.checked) {
      params.set("only_unresolved", "true");
    }
    try {
      const response = await fetch(`/api/algorithms/catalog/admin?${params.toString()}`, {
        headers: { Accept: "application/json" },
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Unable to load queue snapshot.");
      }
      queueTable.innerHTML = payload.items.map((entry) => `
        <tr>
          <td>${entry.catalog_number}</td>
          <td>${entry.name}</td>
          <td>${entry.implementation_label}</td>
          <td>${entry.alg_impl_id ? `<code>${entry.alg_impl_id}</code>` : '<span class="text-muted">None</span>'}</td>
          <td>${entry.review_state_label}</td>
        </tr>
      `).join("");
      if (!payload.items.length) {
        queueTable.innerHTML = '<tr><td colspan="5" class="text-muted">No matching items.</td></tr>';
      }
    } catch (error) {
      queueTable.innerHTML = `<tr><td colspan="5" class="text-danger">${error.message}</td></tr>`;
    }
  };

  [
    searchInput,
    statusSelect,
    reviewStateSelect,
    categorySelect,
    catalogTypeSelect,
    advancedLabelSelect,
    linkedSelect,
    brokenOnlyCheckbox,
    unresolvedOnlyCheckbox,
  ].forEach((element) => {
    element?.addEventListener(element === searchInput ? "input" : "change", () => {
      void refreshQueueSnapshot();
    });
  });

  void refreshQueueSnapshot();
})();