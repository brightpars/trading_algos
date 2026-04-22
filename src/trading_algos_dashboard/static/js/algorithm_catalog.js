(() => {
  const root = document.querySelector("[data-algorithm-catalog-root]");
  if (!root) {
    return;
  }

  const searchInput = document.getElementById("algorithm-catalog-search");
  const statusFilter = document.getElementById("algorithm-catalog-status-filter");
  const categoryFilter = document.getElementById("algorithm-catalog-category-filter");
  const cards = Array.from(document.querySelectorAll("[data-catalog-card]"));
  const offcanvasElement = document.getElementById("algorithmCatalogOffcanvas");
  const detailBody = document.getElementById("algorithm-catalog-detail-body");
  const detailTitle = document.getElementById("algorithm-catalog-detail-title");
  const detailsButtons = Array.from(document.querySelectorAll("[data-catalog-detail-url]"));
  const bootstrapRef = window.bootstrap;
  const offcanvas = offcanvasElement && bootstrapRef ? new bootstrapRef.Offcanvas(offcanvasElement) : null;

  const applyFilters = () => {
    const searchText = (searchInput?.value || "").trim().toLowerCase();
    const statusValue = statusFilter?.value || "";
    const categoryValue = categoryFilter?.value || "";
    cards.forEach((card) => {
      const haystack = (card.dataset.searchText || "").toLowerCase();
      const status = card.dataset.implementationStatus || "";
      const category = card.dataset.category || "";
      const visible = (!searchText || haystack.includes(searchText))
        && (!statusValue || status === statusValue)
        && (!categoryValue || category === categoryValue);
      card.classList.toggle("d-none", !visible);
    });
  };

  const renderDetailList = (items) => items.map((item) => `
      <dt class="col-sm-4">${item.label}</dt>
      <dd class="col-sm-8">${item.value}</dd>
    `).join("");

  const renderAlgImplSpec = (algImplSpec) => {
    if (!algImplSpec) {
      return '<div class="alert alert-secondary mb-0">No algorithm implementation is linked to this catalog entry.</div>';
    }
    return `
      <dl class="row mb-0">
        ${renderDetailList([
          { label: "Implementation ID", value: `<code>${algImplSpec.key}</code>` },
          { label: "Implementation status", value: algImplSpec.status },
          { label: "Category", value: algImplSpec.category },
          { label: "Asset scope", value: algImplSpec.asset_scope },
          { label: "Runtime kind", value: algImplSpec.runtime_kind },
          { label: "Warmup", value: String(algImplSpec.warmup_period) },
          { label: "Input domains", value: algImplSpec.input_domains.join(", ") || "—" },
          { label: "Output modes", value: algImplSpec.output_modes.join(", ") || "—" },
          { label: "Composition roles", value: algImplSpec.composition_roles.join(", ") || "—" },
        ])}
      </dl>
      <div class="mt-3">
        <h6>Default params</h6>
        <pre class="small mb-0">${JSON.stringify(algImplSpec.default_param, null, 2)}</pre>
      </div>
    `;
  };

  const loadDetail = async (button) => {
    if (!detailBody || !detailTitle) {
      return;
    }
    detailTitle.textContent = button.dataset.catalogName || "Algorithm details";
    detailBody.innerHTML = '<div class="text-muted">Loading details…</div>';
    if (offcanvas) {
      offcanvas.show();
    }
    try {
      const response = await fetch(button.dataset.catalogDetailUrl, { headers: { Accept: "application/json" } });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Unable to load details.");
      }
      detailBody.innerHTML = `
        <div class="mb-4">
          <div class="d-flex gap-2 flex-wrap mb-3">
            <span class="badge text-bg-primary">${payload.implementation_label}</span>
            <span class="badge text-bg-light">${payload.category}</span>
            <span class="badge text-bg-light">Home suitability ${payload.home_suitability_score}</span>
            <span class="badge text-bg-light">${payload.link_source_label}</span>
            <span class="badge text-bg-light">${payload.review_state_label}</span>
          </div>
          <p class="mb-2"><strong>Core idea:</strong> ${payload.core_idea}</p>
          <p class="mb-2"><strong>Best use / horizon:</strong> ${payload.best_use_horizon}</p>
          <p class="mb-2"><strong>Typical inputs:</strong> ${payload.typical_inputs}</p>
          <p class="mb-2"><strong>Signal style:</strong> ${payload.signal_style}</p>
          <p class="mb-2"><strong>Reference:</strong> ${payload.initial_reference}</p>
          <p class="mb-0"><strong>Source version:</strong> ${payload.source_version} · <strong>Last import:</strong> ${payload.last_import_timestamp || "—"}</p>
        </div>
        <div class="mb-4">
          <h6>Extended implementation details</h6>
          <p class="mb-0">${payload.extended_implementation_details}</p>
        </div>
        <div class="mb-4">
          <h6>Curation metadata</h6>
          <dl class="row mb-0">
            ${renderDetailList([
              { label: "Link source", value: payload.link_source_label || "Unlinked" },
              { label: "Review state", value: payload.review_state_label || "Not reviewed" },
              { label: "Match confidence", value: String(payload.alg_impl_link?.match_confidence ?? "—") },
              { label: "Match notes", value: payload.alg_impl_link?.notes || payload.alg_impl_link?.match_reason || "—" },
            ])}
          </dl>
        </div>
        <div>
          <h6>Implementation metadata</h6>
          ${renderAlgImplSpec(payload.alg_impl_spec)}
        </div>
      `;
    } catch (error) {
      detailBody.innerHTML = `<div class="alert alert-danger mb-0">${error.message}</div>`;
    }
  };

  searchInput?.addEventListener("input", applyFilters);
  statusFilter?.addEventListener("change", applyFilters);
  categoryFilter?.addEventListener("change", applyFilters);
  detailsButtons.forEach((button) => {
    button.addEventListener("click", () => {
      void loadDetail(button);
    });
  });
})();