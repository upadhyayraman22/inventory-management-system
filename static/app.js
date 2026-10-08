const $ = (id) => document.getElementById(id);

const state = {
  editProductId: null,
  products: [],
  threshold: 5,
  sort: { key: "name", direction: "asc" },
};

function showToast(text, isError = false) {
  const toast = document.createElement("div");
  toast.className = `toast${isError ? " error" : ""}`;
  toast.textContent = text;
  $("toastRegion").append(toast);
  window.setTimeout(() => toast.remove(), 3600);
}

function clearFieldErrors() {
  for (const field of ["productId", "name", "category", "quantity", "price"]) {
    $(`${field}Error`).textContent = "";
    $(field).classList.remove("invalid");
  }
}

function setFieldError(field, message) {
  $(`${field}Error`).textContent = message;
  $(field).classList.add("invalid");
}

function visibleProducts() {
  const category = $("categoryFilter").value;
  const lowStockOnly = $("lowStockFilter").checked;
  const products = state.products.filter((product) =>
    (!category || product.category === category) &&
    (!lowStockOnly || product.quantity <= state.threshold)
  );
  const { key, direction } = state.sort;
  return products.sort((left, right) => {
    const comparison = key === "name"
      ? left.name.localeCompare(right.name, undefined, { sensitivity: "base" })
      : Number(left[key]) - Number(right[key]);
    return direction === "asc" ? comparison : -comparison;
  });
}

function addCell(row, value) {
  const cell = document.createElement("td");
  cell.textContent = value;
  row.append(cell);
  return cell;
}

function renderProducts() {
  const table = $("productTable");
  const products = visibleProducts();
  table.replaceChildren();

  if (!products.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 7;
    cell.className = "empty";
    cell.textContent = "No products found.";
    row.append(cell);
    table.append(row);
    return;
  }

  for (const product of products) {
    const row = document.createElement("tr");
    addCell(row, product.product_id);
    addCell(row, product.name);
    addCell(row, product.category);
    addCell(row, product.quantity);
    addCell(row, `₹${Number(product.price).toFixed(2)}`);

    const statusCell = document.createElement("td");
    const badge = document.createElement("span");
    const isLow = product.quantity <= state.threshold;
    badge.className = `badge ${isLow ? "low" : "ok"}`;
    badge.textContent = isLow ? "Low stock" : "Available";
    statusCell.append(badge);
    row.append(statusCell);

    const actionsCell = document.createElement("td");
    const actions = document.createElement("div");
    actions.className = "row-actions";
    for (const [action, label] of [["edit", "Edit"], ["delete", "Delete"]]) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `row-action${action === "delete" ? " delete" : ""}`;
      button.dataset.action = action;
      button.dataset.productId = product.product_id;
      button.textContent = label;
      actions.append(button);
    }
    actionsCell.append(actions);
    row.append(actionsCell);
    table.append(row);
  }
}

function updateSortIndicators() {
  document.querySelectorAll("[data-sort]").forEach((button) => {
    const active = button.dataset.sort === state.sort.key;
    button.classList.toggle("active", active);
    button.classList.toggle("desc", active && state.sort.direction === "desc");
  });
}

function populateCategoryFilter() {
  const select = $("categoryFilter");
  const selected = select.value;
  const categories = [...new Set(state.products.map((product) => product.category))]
    .sort((left, right) => left.localeCompare(right, undefined, { sensitivity: "base" }));
  select.replaceChildren(new Option("All categories", ""));
  for (const category of categories) select.add(new Option(category, category));
  select.value = categories.includes(selected) ? selected : "";
}

function renderStats(stats) {
  state.threshold = stats.low_stock_threshold;
  $("totalProducts").textContent = stats.total_products;
  $("totalQuantity").textContent = stats.total_quantity;
  $("lowStock").textContent = stats.low_stock;
  $("totalValue").textContent = `₹${Number(stats.total_value).toFixed(2)}`;
  $("thresholdLabel").textContent = `At or below ${state.threshold} unit${state.threshold === 1 ? "" : "s"}`;
}

async function loadProducts() {
  const search = $("searchInput").value.trim();
  try {
    const [productsResponse, statsResponse] = await Promise.all([
      fetch(`/api/products?search=${encodeURIComponent(search)}`),
      fetch("/api/stats"),
    ]);
    if (!productsResponse.ok || !statsResponse.ok) throw new Error("Unable to load inventory.");
    state.products = await productsResponse.json();
    renderStats(await statsResponse.json());
    populateCategoryFilter();
    updateSortIndicators();
    renderProducts();
  } catch (error) {
    showToast(error.message, true);
  }
}

function openAddModal() {
  state.editProductId = null;
  $("modalTitle").textContent = "Add product";
  $("productForm").reset();
  clearFieldErrors();
  $("productId").disabled = false;
  $("productModal").classList.remove("hidden");
  $("productId").focus();
}

function openEditModal(product) {
  state.editProductId = product.product_id;
  $("modalTitle").textContent = "Update product";
  $("productId").value = product.product_id;
  $("productId").disabled = true;
  $("name").value = product.name;
  $("category").value = product.category;
  $("quantity").value = product.quantity;
  $("price").value = product.price;
  clearFieldErrors();
  $("productModal").classList.remove("hidden");
  $("name").focus();
}

function closeModal() {
  $("productModal").classList.add("hidden");
}

function validateForm() {
  clearFieldErrors();
  const productId = $("productId").value.trim();
  const name = $("name").value.trim();
  const category = $("category").value.trim();
  const quantityText = $("quantity").value;
  const priceText = $("price").value;
  let valid = true;
  const requiredTextFields = [["productId", productId, 50, "Product ID"], ["name", name, 120, "Product name"], ["category", category, 80, "Category"]];
  for (const [field, value, limit, label] of requiredTextFields) {
    if (!value) { setFieldError(field, `${label} is required.`); valid = false; }
    else if (value.length > limit) { setFieldError(field, `${label} must be at most ${limit} characters.`); valid = false; }
  }
  const quantity = Number(quantityText);
  if (!quantityText) { setFieldError("quantity", "Quantity is required."); valid = false; }
  else if (!Number.isInteger(quantity) || quantity < 0 || quantity > 1000000000) { setFieldError("quantity", "Enter a whole number from 0 to 1000000000."); valid = false; }
  const price = Number(priceText);
  if (!priceText) { setFieldError("price", "Price is required."); valid = false; }
  else if (!Number.isFinite(price) || price < 0 || price > 1000000000) { setFieldError("price", "Enter a price from 0 to 1000000000."); valid = false; }
  return valid ? { product_id: productId, name, category, quantity, price } : null;
}

function showServerError(message) {
  const field = message.startsWith("Product ID") ? "productId"
    : message.startsWith("Product name") ? "name"
      : message.startsWith("Category") ? "category"
        : message.startsWith("Quantity") ? "quantity"
          : message.startsWith("Price") ? "price" : null;
  if (field) setFieldError(field, message);
  showToast(message, true);
}

async function saveProduct(event) {
  event.preventDefault();
  const product = validateForm();
  if (!product) return;
  const isEditing = Boolean(state.editProductId);
  const response = await fetch(isEditing ? `/api/products/${encodeURIComponent(state.editProductId)}` : "/api/products", {
    method: isEditing ? "PUT" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(product),
  });
  const result = await response.json();
  if (!response.ok) { showServerError(result.error || "Operation failed."); return; }
  closeModal();
  showToast(result.message);
  await loadProducts();
}

async function handleTableAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const product = state.products.find((item) => item.product_id === button.dataset.productId);
  if (!product) return;
  if (button.dataset.action === "edit") { openEditModal(product); return; }
  if (!window.confirm(`Delete product ${product.product_id}?`)) return;
  const response = await fetch(`/api/products/${encodeURIComponent(product.product_id)}`, { method: "DELETE" });
  const result = await response.json();
  if (!response.ok) { showToast(result.error || "Delete failed.", true); return; }
  showToast(result.message);
  await loadProducts();
}

function csvCell(value) {
  let safeValue = String(value);
  if (/^[=+\-@]/.test(safeValue)) safeValue = `'${safeValue}`;
  return `"${safeValue.replaceAll('"', '""')}"`;
}

function exportCsv() {
  const rows = [["Product ID", "Name", "Category", "Quantity", "Price", "Status"]];
  for (const product of visibleProducts()) rows.push([
    product.product_id, product.name, product.category, product.quantity, product.price,
    product.quantity <= state.threshold ? "Low stock" : "Available",
  ]);
  const content = rows.map((row) => row.map(csvCell).join(",")).join("\n");
  const url = URL.createObjectURL(new Blob([content], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "inventory-export.csv";
  link.click();
  URL.revokeObjectURL(url);
  showToast("CSV export downloaded.");
}

$("addProductButton").addEventListener("click", openAddModal);
$("closeModalButton").addEventListener("click", closeModal);
$("cancelButton").addEventListener("click", closeModal);
$("productForm").addEventListener("submit", saveProduct);
$("searchInput").addEventListener("input", loadProducts);
$("categoryFilter").addEventListener("change", renderProducts);
$("lowStockFilter").addEventListener("change", renderProducts);
$("productTable").addEventListener("click", handleTableAction);
$("exportButton").addEventListener("click", exportCsv);
document.querySelectorAll("[data-sort]").forEach((button) => button.addEventListener("click", () => {
  const key = button.dataset.sort;
  state.sort.direction = state.sort.key === key && state.sort.direction === "asc" ? "desc" : "asc";
  state.sort.key = key;
  updateSortIndicators();
  renderProducts();
}));

loadProducts();
