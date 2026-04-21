document.addEventListener("DOMContentLoaded", () => {
  const root = document.getElementById("configuration-builder-app");
  if (!root) {
    return;
  }

  const hiddenPayloadInput = document.getElementById("configuration-payload-input");
  const validationRoot = document.getElementById("configuration-validation");
  const previewRoot = document.getElementById("configuration-structure-preview");
  const jsonPreviewRoot = document.getElementById("configuration-json-preview");
  const catalogSummaryRoot = document.getElementById("configuration-catalog-summary");
  const builderRoot = document.getElementById("configuration-builder-root");
  const metadataForm = document.getElementById("configuration-metadata-form");
  const templateButtons = root.querySelectorAll("[data-template]");
  const form = root.closest("form");
  const saveHelp = document.getElementById("configuration-save-help");
  const bootstrapRoot = document.getElementById("configuration-builder-bootstrap");

  const bootstrap = (() => {
    if (!bootstrapRoot?.textContent) {
      return null;
    }
    try {
      return JSON.parse(bootstrapRoot.textContent);
    } catch (_error) {
      return null;
    }
  })();

  const state = {
    metadata: {
      config_key: "",
      version: "1.0.0",
      name: "",
      description: "",
      tagsText: "",
      notes: "",
      status: "draft",
    },
    rootNodeId: null,
    nodesById: {},
    catalog: [],
    ui: {
      validationMessages: [],
      serverValidationMessages: [],
      validationByNodeId: {},
      validationByField: {},
      algorithmSearchByNodeId: {},
      catalogSearch: "",
      manualConfigKeyDirty: false,
      nodeCounter: 0,
    },
  };

  const slugify = (value) =>
    String(value || "")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");

  const nextNodeId = () => {
    state.ui.nodeCounter += 1;
    return `node-${state.ui.nodeCounter}`;
  };

  const getCatalogEntry = (algKey) =>
    state.catalog.find((entry) => entry.key === algKey) || null;

  const deepClone = (value) => JSON.parse(JSON.stringify(value));

  const defaultAlgorithmKey = () => state.catalog[0]?.key || "close_high_channel_breakout";

  const createAlgorithmNode = (algKey = defaultAlgorithmKey()) => {
    const entry = getCatalogEntry(algKey);
    return {
      node_id: nextNodeId(),
      node_type: "algorithm",
      name: entry?.name || "Algorithm",
      description: entry?.description || "",
      alg_key: algKey,
      alg_param: deepClone(entry?.default_param || {}),
      buy_enabled: entry?.supports_buy ?? true,
      sell_enabled: entry?.supports_sell ?? true,
      runtime_editable_param_keys: [],
    };
  };

  const createGroupNode = (groupType) => ({
    node_id: nextNodeId(),
    node_type: groupType,
    name: `${groupType.toUpperCase()} group`,
    description: "",
    children: [],
  });

  const resetState = () => {
    state.metadata = {
      config_key: "",
      version: "1.0.0",
      name: "",
      description: "",
      tagsText: "",
      notes: "",
      status: "draft",
    };
    state.rootNodeId = null;
    state.nodesById = {};
    state.ui.validationMessages = [];
    state.ui.serverValidationMessages = [];
    state.ui.validationByNodeId = {};
    state.ui.validationByField = {};
    state.ui.algorithmSearchByNodeId = {};
    state.ui.catalogSearch = "";
    state.ui.manualConfigKeyDirty = false;
  };

  const labelize = (value) =>
    String(value || "")
      .replace(/_/g, " ")
      .replace(/\b\w/g, (character) => character.toUpperCase());

  const syncNodeCounter = () => {
    const maxCounter = Object.keys(state.nodesById).reduce((currentMax, nodeId) => {
      const match = /^node-(\d+)$/.exec(nodeId);
      if (!match) {
        return currentMax;
      }
      return Math.max(currentMax, Number(match[1]));
    }, 0);
    state.ui.nodeCounter = maxCounter;
  };

  const loadPayloadIntoState = (payload) => {
    resetState();
    if (!payload || typeof payload !== "object") {
      return;
    }
    state.metadata = {
      config_key: String(payload.config_key || ""),
      version: String(payload.version || "1.0.0"),
      name: String(payload.name || ""),
      description: String(payload.description || ""),
      tagsText: Array.isArray(payload.tags) ? payload.tags.join(", ") : "",
      notes: String(payload.notes || ""),
      status: String(payload.status || "draft"),
    };
    state.rootNodeId =
      typeof payload.root_node_id === "string" ? payload.root_node_id : null;
    const nodes = Array.isArray(payload.nodes) ? payload.nodes : [];
    nodes.forEach((rawNode) => {
      if (!rawNode || typeof rawNode !== "object") {
        return;
      }
      const nodeType = String(rawNode.node_type || "");
      const common = {
        node_id: String(rawNode.node_id || nextNodeId()),
        node_type: nodeType,
        name: String(rawNode.name || ""),
        description: String(rawNode.description || ""),
      };
      if (nodeType === "algorithm") {
        state.nodesById[common.node_id] = {
          ...common,
          alg_key: String(rawNode.alg_key || defaultAlgorithmKey()),
          alg_param:
            rawNode.alg_param && typeof rawNode.alg_param === "object"
              ? deepClone(rawNode.alg_param)
              : {},
          buy_enabled: Boolean(rawNode.buy_enabled ?? true),
          sell_enabled: Boolean(rawNode.sell_enabled ?? true),
          runtime_editable_param_keys: Array.isArray(
            rawNode.runtime_editable_param_keys,
          )
            ? [...rawNode.runtime_editable_param_keys]
            : [],
        };
        return;
      }
      state.nodesById[common.node_id] = {
        ...common,
        children: Array.isArray(rawNode.children) ? [...rawNode.children] : [],
      };
    });
    syncNodeCounter();
    state.ui.manualConfigKeyDirty = Boolean(state.metadata.config_key);
  };

  const setTemplate = (templateName) => {
    resetState();
    if (templateName === "blank") {
      renderAll();
      return;
    }

    if (templateName === "single_algorithm") {
      const algorithm = createAlgorithmNode();
      state.nodesById[algorithm.node_id] = algorithm;
      state.rootNodeId = algorithm.node_id;
      state.metadata.name = algorithm.name;
      state.metadata.config_key = slugify(algorithm.name);
      renderAll();
      return;
    }

    const groupType = templateName === "or_strategy" ? "or" : "and";
    const rootGroup = createGroupNode(groupType);
    const algorithmA = createAlgorithmNode();
    const algorithmB = createAlgorithmNode(
      state.catalog[1]?.key || defaultAlgorithmKey(),
    );
    rootGroup.children = [algorithmA.node_id, algorithmB.node_id];
    state.nodesById[rootGroup.node_id] = rootGroup;
    state.nodesById[algorithmA.node_id] = algorithmA;
    state.nodesById[algorithmB.node_id] = algorithmB;
    state.rootNodeId = rootGroup.node_id;

    if (templateName === "breakout_example") {
      state.metadata.name = "Breakout Example";
      state.metadata.config_key = "breakout-example";
    } else {
      state.metadata.name = `${groupType.toUpperCase()} Strategy`;
      state.metadata.config_key = slugify(state.metadata.name);
    }
    renderAll();
  };

  const collectSubtreeIds = (nodeId) => {
    const node = state.nodesById[nodeId];
    if (!node) {
      return [];
    }
    if (node.node_type === "algorithm") {
      return [nodeId];
    }
    return [
      nodeId,
      ...node.children.flatMap((childId) => collectSubtreeIds(childId)),
    ];
  };

  const removeNode = (nodeId) => {
    if (!nodeId || !state.nodesById[nodeId]) {
      return;
    }
    Object.values(state.nodesById).forEach((node) => {
      if (node.node_type === "algorithm") {
        return;
      }
      node.children = node.children.filter((childId) => childId !== nodeId);
    });
    collectSubtreeIds(nodeId).forEach((subtreeNodeId) => {
      delete state.nodesById[subtreeNodeId];
    });
    if (state.rootNodeId === nodeId) {
      state.rootNodeId = null;
    }
    renderAll();
  };

  const attachNodeToParent = (node, parentId = null) => {
    state.nodesById[node.node_id] = node;
    if (!parentId) {
      state.rootNodeId = node.node_id;
      return;
    }
    const parent = state.nodesById[parentId];
    if (parent && parent.node_type !== "algorithm") {
      parent.children.push(node.node_id);
    }
  };

  const addAlgorithmNode = (parentId = null) => {
    const node = createAlgorithmNode();
    attachNodeToParent(node, parentId);
    renderAll();
  };

  const addGroupNode = (groupType, parentId = null) => {
    const node = createGroupNode(groupType);
    attachNodeToParent(node, parentId);
    renderAll();
  };

  const moveChild = (parentId, childId, direction) => {
    const parent = state.nodesById[parentId];
    if (!parent || parent.node_type === "algorithm") {
      return;
    }
    const index = parent.children.indexOf(childId);
    if (index < 0) {
      return;
    }
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= parent.children.length) {
      return;
    }
    const updatedChildren = [...parent.children];
    [updatedChildren[index], updatedChildren[targetIndex]] = [
      updatedChildren[targetIndex],
      updatedChildren[index],
    ];
    parent.children = updatedChildren;
    renderAll();
  };

  const parseParamValue = (rawValue, currentValue) => {
    if (typeof currentValue === "number") {
      return Number(rawValue);
    }
    if (typeof currentValue === "boolean") {
      return Boolean(rawValue);
    }
    return rawValue;
  };

  const filterCatalog = (searchTerm) => {
    const normalizedSearch = String(searchTerm || "").trim().toLowerCase();
    if (!normalizedSearch) {
      return state.catalog;
    }
    return state.catalog.filter((entry) => {
      const haystack = [
        entry.name,
        entry.key,
        entry.description,
        entry.category,
        ...(entry.tags || []),
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(normalizedSearch);
    });
  };

  const collectValidationMessages = () => {
    const globalMessages = [];
    const byNodeId = {};
    const byField = {};
    const addFieldError = (fieldName, message) => {
      byField[fieldName] = [...(byField[fieldName] || []), message];
      globalMessages.push(message);
    };
    const addNodeError = (nodeId, message) => {
      byNodeId[nodeId] = [...(byNodeId[nodeId] || []), message];
      globalMessages.push(message);
    };
    if (!state.metadata.name.trim()) {
      addFieldError("name", "Configuration name is required.");
    }
    if (!state.metadata.config_key.trim()) {
      addFieldError("config_key", "Config key is required.");
    }
    if (!state.metadata.version.trim()) {
      addFieldError("version", "Version is required.");
    }
    if (!state.rootNodeId) {
      globalMessages.push(
        "Add a root node using a starter template or the builder actions.",
      );
    }
    Object.values(state.nodesById).forEach((node) => {
      if (node.node_type === "algorithm") {
        if (!node.alg_key) {
          addNodeError(node.node_id, `Node ${node.node_id} must select an algorithm.`);
        }
        if (!node.buy_enabled && !node.sell_enabled) {
          addNodeError(node.node_id, `Node ${node.node_id} must enable buy or sell.`);
        }
        Object.entries(node.alg_param || {}).forEach(([key, value]) => {
          if (typeof value === "number" && (!Number.isFinite(value) || value <= 0)) {
            addNodeError(
              node.node_id,
              `Node ${node.node_id} field ${key} must be greater than zero.`,
            );
          }
          if (value === "") {
            addNodeError(node.node_id, `Node ${node.node_id} field ${key} is required.`);
          }
        });
      } else if ((node.children || []).length < 2) {
        addNodeError(node.node_id, `Group ${node.node_id} must contain at least 2 children.`);
      }
    });
    state.ui.validationByNodeId = byNodeId;
    state.ui.validationByField = byField;
    return [...globalMessages, ...state.ui.serverValidationMessages];
  };

  const paramSchemaByKey = (entry) => {
    const schema = entry?.param_schema;
    return Array.isArray(schema)
      ? Object.fromEntries(schema.map((item) => [item.key, item]))
      : {};
  };

  const runServerValidation = async () => {
    const payload = serializePayload();
    try {
      const response = await fetch("/api/configurations/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await response.json();
      if (!response.ok) {
        state.ui.serverValidationMessages = Array.isArray(result.errors)
          ? result.errors.map((item) => String(item.message || "Validation error"))
          : ["Server validation failed."];
      } else {
        state.ui.serverValidationMessages = [];
      }
    } catch (_error) {
      state.ui.serverValidationMessages = [
        "Server validation is currently unavailable.",
      ];
    }
    renderAll();
  };

  const renderMetadataErrors = () => {
    if (!metadataForm) {
      return;
    }
    metadataForm.querySelectorAll(".builder-field-error").forEach((element) => {
      element.remove();
    });
    metadataForm.querySelectorAll(".builder-invalid").forEach((element) => {
      element.classList.remove("builder-invalid");
    });
    Object.entries(state.ui.validationByField).forEach(([fieldName, messages]) => {
      const input = metadataForm.querySelector(`[name='${fieldName}']`);
      if (!input) {
        return;
      }
      input.classList.add("builder-invalid");
      const error = document.createElement("div");
      error.className = "builder-field-error";
      error.textContent = messages.join(" ");
      input.insertAdjacentElement("afterend", error);
    });
  };

  const serializePayload = () => ({
    config_key: state.metadata.config_key.trim(),
    version: state.metadata.version.trim(),
    name: state.metadata.name.trim(),
    description: state.metadata.description.trim(),
    tags: state.metadata.tagsText
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean),
    notes: state.metadata.notes,
    status: state.metadata.status,
    root_node_id: state.rootNodeId || "",
    nodes: Object.values(state.nodesById),
    runtime_overrides: {},
    algorithm_package_constraints: {},
    compatibility_metadata: {},
  });

  const buildPreviewLines = (nodeId, depth = 0) => {
    const node = state.nodesById[nodeId];
    if (!node) {
      return [];
    }
    const prefix = `${"  ".repeat(depth)}- `;
    if (node.node_type === "algorithm") {
      return [
        `${prefix}${node.name || node.alg_key} (${node.alg_key}) ${JSON.stringify(node.alg_param)}`,
      ];
    }
    return [
      `${prefix}${(node.name || node.node_type).toUpperCase()} [${node.node_type.toUpperCase()}]`,
      ...node.children.flatMap((childId) => buildPreviewLines(childId, depth + 1)),
    ];
  };

  const renderValidation = () => {
    state.ui.validationMessages = collectValidationMessages();
    const messages = state.ui.validationMessages;
    validationRoot.innerHTML = `
      <div class="builder-card">
        <h2 class="h5 mb-3">Validation</h2>
        ${
          messages.length === 0
            ? '<p class="text-success mb-0">Ready to save. Client and server validation checks are clear.</p>'
            : `<ul class="builder-validation-list mb-0">${messages
                .map((message) => `<li>${message}</li>`)
                .join("")}</ul>`
        }
        <button type="button" class="btn btn-sm btn-outline-primary mt-3" id="builder-server-validate">Validate with backend</button>
      </div>
    `;
    renderMetadataErrors();
    validationRoot
      .querySelector("#builder-server-validate")
      ?.addEventListener("click", () => {
        void runServerValidation();
      });
  };

  const renderPreview = () => {
    const lines = state.rootNodeId ? buildPreviewLines(state.rootNodeId) : ["No structure yet."];
    previewRoot.innerHTML = `
      <div class="builder-card builder-preview">
        <h2 class="h5 mb-3">Structure preview</h2>
        <pre class="mb-0">${lines.join("\n")}</pre>
      </div>
    `;
    const payload = serializePayload();
    hiddenPayloadInput.value = JSON.stringify(payload);
    jsonPreviewRoot.textContent = JSON.stringify(payload, null, 2);
  };

  const renderCatalogSummary = () => {
    if (!catalogSummaryRoot) {
      return;
    }
    const filteredCatalog = filterCatalog(state.ui.catalogSearch);
    catalogSummaryRoot.innerHTML = `
      <div class="builder-card">
        <h2 class="h5 mb-3">Algorithm reference</h2>
        <input class="form-control builder-catalog-search" type="text" placeholder="Search algorithms, tags, categories" value="${state.ui.catalogSearch}">
        <div class="builder-catalog-list">
          ${
            filteredCatalog.length
              ? filteredCatalog
                  .map(
                    (entry) => `
                      <div class="builder-catalog-item">
                        <h3>${entry.name}</h3>
                        <p class="small text-muted mb-2">${entry.description || "No description available."}</p>
                        <div class="builder-algorithm-meta">
                          <span class="builder-meta-pill">key: ${entry.key}</span>
                          <span class="builder-meta-pill">category: ${entry.category}</span>
                          <span class="builder-meta-pill">warmup: ${entry.warmup_period}</span>
                        </div>
                      </div>
                    `,
                  )
                  .join("")
              : '<p class="text-muted small mb-0">No algorithms match your search.</p>'
          }
        </div>
      </div>
    `;
    const searchInput = catalogSummaryRoot.querySelector(".builder-catalog-search");
    searchInput?.addEventListener("input", (event) => {
      state.ui.catalogSearch = event.target.value;
      renderCatalogSummary();
    });
  };

  const renderRuntimeEditableOptions = (node) => {
    const paramKeys = Object.keys(node.alg_param || {});
    if (paramKeys.length === 0) {
      return '<p class="builder-param-help mb-0">No editable parameters available for this algorithm.</p>';
    }
    return `
      <div class="builder-runtime-options">
        <div class="d-flex justify-content-between align-items-center mb-2">
          <strong class="small">Runtime editable parameters</strong>
          <button type="button" class="btn btn-sm btn-outline-secondary" data-action="reset-params" data-node-id="${node.node_id}">Reset to defaults</button>
        </div>
        <p class="builder-param-help">Choose which parameters may be safely changed later without rebuilding the full configuration.</p>
        <div class="d-flex flex-wrap gap-3">
          ${paramKeys
            .map(
              (key) => `
                <label class="form-check-label d-flex align-items-center gap-2">
                  <input class="form-check-input mt-0" type="checkbox" data-action="toggle-runtime-editable" data-node-id="${node.node_id}" data-param-key="${key}" ${node.runtime_editable_param_keys.includes(key) ? "checked" : ""}>
                  <span>${labelize(key)}</span>
                </label>
              `,
            )
            .join("")}
        </div>
      </div>
    `;
  };

  const renderAlgorithmCard = (node, parentId = null) => {
    const entry = getCatalogEntry(node.alg_key);
    const paramSchema = paramSchemaByKey(entry);
    const algorithmSearch = state.ui.algorithmSearchByNodeId[node.node_id] || "";
    const options = filterCatalog(algorithmSearch)
      .map(
        (catalogEntry) =>
          `<option value="${catalogEntry.key}" ${catalogEntry.key === node.alg_key ? "selected" : ""}>${catalogEntry.name}</option>`,
      )
      .join("");
    const paramFields = Object.entries(node.alg_param || {})
      .map(([key, value]) => {
        const inputType = typeof value === "number" ? "number" : "text";
        const schema = paramSchema[key] || {};
        return `
          <div class="col-md-6">
            <label class="form-label">${schema.label || key}</label>
            <input class="form-control" data-action="update-param" data-node-id="${node.node_id}" data-param-key="${key}" type="${inputType}" value="${value}" ${schema.minimum ? `min="${schema.minimum}"` : ""}>
            <div class="builder-param-help">${schema.description || `${labelize(key)} for ${entry?.name || node.alg_key}.`}</div>
          </div>
        `;
      })
      .join("");
    const parentButtons = parentId
      ? `
          <button type="button" class="btn btn-sm btn-outline-secondary" data-action="move-up" data-parent-id="${parentId}" data-child-id="${node.node_id}">↑</button>
          <button type="button" class="btn btn-sm btn-outline-secondary" data-action="move-down" data-parent-id="${parentId}" data-child-id="${node.node_id}">↓</button>
        `
      : "";
    const nodeErrors = state.ui.validationByNodeId[node.node_id] || [];
    return `
      <div class="builder-node builder-node--algorithm">
        <div class="d-flex justify-content-between align-items-start gap-2 mb-3">
          <div>
            <span class="builder-badge builder-badge--algorithm">Algorithm</span>
            <h3 class="h6 mt-2 mb-1">${node.name || entry?.name || node.alg_key}</h3>
            <p class="text-muted small mb-0">${entry?.description || "Choose an algorithm and adjust its parameters."}</p>
            <div class="builder-algorithm-meta">
              ${entry?.category ? `<span class="builder-meta-pill">category: ${entry.category}</span>` : ""}
              ${entry?.version ? `<span class="builder-meta-pill">version: ${entry.version}</span>` : ""}
              ${entry?.warmup_period ? `<span class="builder-meta-pill">warmup: ${entry.warmup_period}</span>` : ""}
              ${(entry?.tags || []).slice(0, 3).map((tag) => `<span class="builder-meta-pill">${tag}</span>`).join("")}
            </div>
          </div>
          <div class="d-flex gap-1">
            ${parentButtons}
            <button type="button" class="btn btn-sm btn-outline-danger" data-action="remove-node" data-node-id="${node.node_id}">Remove</button>
          </div>
        </div>
        <div class="mb-3">
          <label class="form-label">Find algorithm</label>
          <input class="form-control mb-2" data-action="algorithm-search" data-node-id="${node.node_id}" type="text" value="${algorithmSearch}" placeholder="Search by name, key, tag, category">
          <label class="form-label">Algorithm</label>
          <select class="form-select" data-action="update-algorithm" data-node-id="${node.node_id}">
            ${options}
          </select>
        </div>
        <div class="row g-3 mb-3">${paramFields}</div>
        <div class="form-check form-switch">
          <input class="form-check-input" data-action="toggle-buy" data-node-id="${node.node_id}" type="checkbox" ${node.buy_enabled ? "checked" : ""}>
          <label class="form-check-label">Buy enabled</label>
        </div>
        <div class="form-check form-switch">
          <input class="form-check-input" data-action="toggle-sell" data-node-id="${node.node_id}" type="checkbox" ${node.sell_enabled ? "checked" : ""}>
          <label class="form-check-label">Sell enabled</label>
        </div>
        ${renderRuntimeEditableOptions(node)}
        ${
          nodeErrors.length
            ? `<ul class="builder-node-errors">${nodeErrors.map((message) => `<li>${message}</li>`).join("")}</ul>`
            : ""
        }
      </div>
    `;
  };

  const renderGroupCard = (node, parentId = null) => {
    const childMarkup = node.children
      .map((childId) => renderNode(childId, node.node_id))
      .join("");
    const parentButtons = parentId
      ? `
          <button type="button" class="btn btn-sm btn-outline-secondary" data-action="move-up" data-parent-id="${parentId}" data-child-id="${node.node_id}">↑</button>
          <button type="button" class="btn btn-sm btn-outline-secondary" data-action="move-down" data-parent-id="${parentId}" data-child-id="${node.node_id}">↓</button>
        `
      : "";
    const nodeErrors = state.ui.validationByNodeId[node.node_id] || [];
    return `
      <div class="builder-node builder-node--group">
        <div class="d-flex justify-content-between align-items-start gap-2 mb-3">
          <div>
            <span class="builder-badge builder-badge--group">${node.node_type.toUpperCase()}</span>
            <h3 class="h6 mt-2 mb-1">${node.name || `${node.node_type.toUpperCase()} group`}</h3>
            <p class="text-muted small mb-0">Groups combine child algorithms or child groups.</p>
          </div>
          <div class="d-flex gap-1">
            ${parentButtons}
            <button type="button" class="btn btn-sm btn-outline-danger" data-action="remove-node" data-node-id="${node.node_id}">Remove</button>
          </div>
        </div>
        <div class="builder-group-actions mb-3">
          <button type="button" class="btn btn-sm btn-outline-primary" data-action="add-algorithm" data-parent-id="${node.node_id}">Add algorithm</button>
          <button type="button" class="btn btn-sm btn-outline-primary" data-action="add-and-group" data-parent-id="${node.node_id}">Add AND group</button>
          <button type="button" class="btn btn-sm btn-outline-primary" data-action="add-or-group" data-parent-id="${node.node_id}">Add OR group</button>
        </div>
        <div class="builder-children">${
          childMarkup || `
            <div class="builder-empty-hint">
              <strong>Add at least two children</strong>
              <p class="text-muted small mb-0 mt-1">Use child algorithms when you want the group to evaluate conditions. AND = all children agree, OR = any child can trigger.</p>
            </div>
          `
        }</div>
        ${
          nodeErrors.length
            ? `<ul class="builder-node-errors">${nodeErrors.map((message) => `<li>${message}</li>`).join("")}</ul>`
            : ""
        }
      </div>
    `;
  };

  const renderNode = (nodeId, parentId = null) => {
    const node = state.nodesById[nodeId];
    if (!node) {
      return "";
    }
    return node.node_type === "algorithm"
      ? renderAlgorithmCard(node, parentId)
      : renderGroupCard(node, parentId);
  };

  const renderBuilder = () => {
    const rootNodeMarkup = state.rootNodeId
      ? renderNode(state.rootNodeId)
      : `
          <div class="builder-card text-center">
            <p class="mb-3 text-muted">Start from a template or create a root node.</p>
            <div class="d-flex flex-wrap justify-content-center gap-2">
              <button type="button" class="btn btn-outline-primary" data-action="add-root-algorithm">Add root algorithm</button>
              <button type="button" class="btn btn-outline-primary" data-action="add-root-and">Add root AND group</button>
              <button type="button" class="btn btn-outline-primary" data-action="add-root-or">Add root OR group</button>
            </div>
          </div>
        `;
    builderRoot.innerHTML = rootNodeMarkup;
  };

  const renderAll = () => {
    renderBuilder();
    renderValidation();
    renderPreview();
    renderCatalogSummary();
    const saveButton = root.querySelector("button[type='submit']");
    if (saveButton) {
      saveButton.disabled = state.ui.validationMessages.length > 0;
    }
    if (saveHelp) {
      saveHelp.hidden = state.ui.validationMessages.length === 0;
    }
  };

  metadataForm?.addEventListener("input", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement)) {
      return;
    }
    const fieldName = target.name;
    if (fieldName === "config_key") {
      state.ui.manualConfigKeyDirty = true;
    }
    state.metadata[fieldName] = target.value;
    if (fieldName === "name" && !state.ui.manualConfigKeyDirty) {
      state.metadata.config_key = slugify(target.value);
      const configKeyInput = metadataForm.querySelector("input[name='config_key']");
      if (configKeyInput) {
        configKeyInput.value = state.metadata.config_key;
      }
    }
    renderAll();
  });

  root.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-action], [data-template]");
    if (!trigger) {
      return;
    }
    if (trigger.dataset.template) {
      setTemplate(trigger.dataset.template);
      return;
    }
    const { action, nodeId, parentId, childId } = trigger.dataset;
    if (action === "add-root-algorithm") {
      addAlgorithmNode();
    } else if (action === "add-root-and") {
      addGroupNode("and");
    } else if (action === "add-root-or") {
      addGroupNode("or");
    } else if (action === "add-algorithm") {
      addAlgorithmNode(parentId);
    } else if (action === "add-and-group") {
      addGroupNode("and", parentId);
    } else if (action === "add-or-group") {
      addGroupNode("or", parentId);
    } else if (action === "remove-node") {
      removeNode(nodeId);
    } else if (action === "move-up") {
      moveChild(parentId, childId, "up");
    } else if (action === "move-down") {
      moveChild(parentId, childId, "down");
    }
  });

  root.addEventListener("change", (event) => {
    const target = event.target;
    if (
      !(target instanceof HTMLInputElement || target instanceof HTMLSelectElement)
    ) {
      return;
    }
    const action = target.dataset.action;
    const nodeId = target.dataset.nodeId;
    if (action === "algorithm-search") {
      state.ui.algorithmSearchByNodeId[nodeId] = target.value;
      renderAll();
      return;
    }
    if (!action || !nodeId || !state.nodesById[nodeId]) {
      return;
    }
    const node = state.nodesById[nodeId];
    if (action === "update-algorithm") {
      const entry = getCatalogEntry(target.value);
      node.alg_key = target.value;
      node.name = entry?.name || node.name;
      node.description = entry?.description || "";
      node.alg_param = deepClone(entry?.default_param || {});
      node.buy_enabled = entry?.supports_buy ?? true;
      node.sell_enabled = entry?.supports_sell ?? true;
    } else if (action === "update-param") {
      const paramKey = target.dataset.paramKey;
      if (!paramKey) {
        return;
      }
      node.alg_param[paramKey] = parseParamValue(target.value, node.alg_param[paramKey]);
    } else if (action === "toggle-buy") {
      node.buy_enabled = target.checked;
    } else if (action === "toggle-sell") {
      node.sell_enabled = target.checked;
    } else if (action === "toggle-runtime-editable") {
      const paramKey = target.dataset.paramKey;
      if (!paramKey) {
        return;
      }
      if (target.checked) {
        node.runtime_editable_param_keys = [
          ...new Set([...node.runtime_editable_param_keys, paramKey]),
        ];
      } else {
        node.runtime_editable_param_keys = node.runtime_editable_param_keys.filter(
          (item) => item !== paramKey,
        );
      }
    } else if (action === "reset-params") {
      const entry = getCatalogEntry(node.alg_key);
      node.alg_param = deepClone(entry?.default_param || {});
      node.runtime_editable_param_keys = [];
    }
    renderAll();
  });

  form?.addEventListener("submit", () => {
    hiddenPayloadInput.value = JSON.stringify(serializePayload());
  });

  templateButtons.forEach((button) => {
    button.disabled = true;
  });
  fetch("/api/algorithms")
    .then((response) => response.json())
    .then((catalog) => {
      state.catalog = Array.isArray(catalog) ? catalog : [];
      templateButtons.forEach((button) => {
        button.disabled = false;
      });
      if (bootstrap?.initial_payload) {
        loadPayloadIntoState(bootstrap.initial_payload);
        renderAll();
      } else {
        setTemplate("single_algorithm");
      }
    })
    .catch(() => {
      templateButtons.forEach((button) => {
        button.disabled = false;
      });
      if (bootstrap?.initial_payload) {
        loadPayloadIntoState(bootstrap.initial_payload);
        renderAll();
      } else {
        setTemplate("blank");
      }
    });
});