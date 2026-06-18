/* ── Budget Bloom App ── */
const API = window.location.origin;
const tokenKey = "budget_bloom_token";
let currentUser = null;

const $ = (sel) => document.querySelector(sel);
const money = (v) => `₹${Number(v || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
const today = () => new Date().toISOString().slice(0, 10);
const currentMonth = () => new Date().toISOString().slice(0, 7);
const esc = (str) => String(str ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");

/* ── Toast ── */
function toast(text, type = "success") {
  const icons = { success: "✓", error: "✕", warning: "⚠" };
  const container = $("#toastContainer");
  const el = document.createElement("div");
  el.className = `toast ${type === "success" ? "" : type}`;
  el.innerHTML = `<span class="toast-icon">${icons[type] || "✓"}</span><span class="toast-text">${esc(text)}</span>`;
  container.appendChild(el);
  setTimeout(() => {
    el.classList.add("hide");
    setTimeout(() => el.remove(), 280);
  }, 3200);
}

/* ── Auth ── */
function getToken()        { return localStorage.getItem(tokenKey); }
function saveToken(t)      { localStorage.setItem(tokenKey, t); }
function clearToken()      { localStorage.removeItem(tokenKey); }

/* ── API ── */
async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${API}${path}`, { ...options, headers });
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "Something went wrong");
  return data;
}

function formToJson(form) {
  const data = Object.fromEntries(new FormData(form).entries());
  Object.keys(data).forEach((k) => { if (data[k] === "") delete data[k]; });
  return data;
}

function setDefaultDates() {
  document.querySelectorAll('input[type="date"]').forEach((i) => i.value = today());
  const m = document.querySelector('input[type="month"]');
  if (m) m.value = currentMonth();
}

/* ── UI State ── */
function showApp(isLoggedIn) {
  $("#authSection").classList.toggle("hidden", isLoggedIn);
  $("#dashboardSection").classList.toggle("hidden", !isLoggedIn);
  $("#logoutBtn").classList.toggle("hidden", !isLoggedIn);
  $("#userBadge").classList.toggle("hidden", !isLoggedIn);
}

async function loadMe() {
  currentUser = await request("/auth/me");
  const first = currentUser.full_name.split(" ")[0];
  $("#welcomeText").textContent = `Welcome back, ${first} 👋`;
  $("#userName").textContent = currentUser.full_name;
  $("#userEmail").textContent = currentUser.email;
  $("#userAvatar").textContent = first.charAt(0).toUpperCase();
}

/* ── Dashboard ── */
async function refreshDashboard() {
  const [summary, expenses, categories, monthly] = await Promise.all([
    request("/finance/summary"),
    request("/finance/expenses"),
    request("/finance/charts/categories"),
    request("/finance/charts/monthly"),
  ]);

  animateValue("#totalIncome",     summary.total_income);
  animateValue("#totalExpense",    summary.total_expense);
  animateValue("#totalSavings",    summary.total_savings);
  animateValue("#availableBalance",summary.available_balance);

  const topEl = $("#topCategory");
  if (topEl) {
    topEl.textContent = summary.highest_category
      ? `Top: ${summary.highest_category} (${money(summary.highest_category_amount)})`
      : "Top: —";
  }
  const badge = $("#topCategoryBadge");
  if (badge) {
    badge.textContent = summary.highest_category
      ? `🏆 ${summary.highest_category}`
      : "No data";
  }

  renderExpenseTable(expenses);
  renderCategoryChart(categories);
  renderMonthlyChart(monthly);
}

function animateValue(selector, newVal) {
  const el = $(selector);
  if (!el) return;
  el.textContent = money(newVal);
  el.style.animation = "none";
  el.offsetHeight; // reflow
  el.style.animation = "countUp 0.5s ease";
}

/* ── Expense Table ── */
function renderExpenseTable(expenses) {
  const tbody = $("#expenseTable");
  if (!expenses || !expenses.length) {
    const tr = document.createElement("tr");
    tr.className = "empty-row";
    const td = document.createElement("td");
    td.colSpan = 5;
    td.textContent = "No expenses yet — add one above to get started.";
    tr.appendChild(td);
    tbody.innerHTML = "";
    tbody.appendChild(tr);
    return;
  }

  tbody.innerHTML = "";
  expenses.slice(0, 12).forEach((exp, i) => {
    const tr = document.createElement("tr");
    tr.style.animationDelay = `${i * 0.04}s`;
    tr.style.animation = "fadeSlideIn 0.3s ease both";

    const cells = [exp.expense_date, exp.title, exp.category, exp.amount];
    cells.forEach((val, idx) => {
      const td = document.createElement("td");
      if (idx === 2) {
        const chip = document.createElement("span");
        chip.className = "category-chip";
        chip.textContent = val;
        td.appendChild(chip);
      } else if (idx === 3) {
        td.className = "amount-cell";
        td.textContent = money(val);
      } else {
        td.textContent = val;
      }
      tr.appendChild(td);
    });

    const tdAction = document.createElement("td");
    const btn = document.createElement("button");
    btn.className = "delete-btn";
    btn.textContent = "Delete";
    btn.dataset.id = exp.id;
    btn.addEventListener("click", async () => {
      btn.textContent = "…";
      btn.disabled = true;
      try {
        await request(`/finance/expenses/${exp.id}`, { method: "DELETE" });
        toast("Expense deleted.");
        await refreshDashboard();
      } catch (err) {
        toast(err.message, "error");
        btn.textContent = "Delete";
        btn.disabled = false;
      }
    });
    tdAction.appendChild(btn);
    tr.appendChild(tdAction);
    tbody.appendChild(tr);
  });
}

/* ── Category Chart ── */
function renderCategoryChart(items) {
  const chart = $("#categoryChart");
  if (!items || !items.length) {
    chart.innerHTML = `<div style="color:var(--muted);text-align:center;padding:40px;font-size:13px;">No expense data yet.</div>`;
    return;
  }
  const max = Math.max(...items.map((i) => Number(i.total)));
  chart.innerHTML = "";
  items.slice(0, 8).forEach((item, idx) => {
    const pct = max ? (Number(item.total) / max) * 100 : 0;
    const row = document.createElement("div");
    row.className = "bar-row";
    row.style.animationDelay = `${idx * 0.06}s`;

    const label = document.createElement("span");
    label.title = item.category;
    label.textContent = item.category;

    const track = document.createElement("div");
    track.className = "bar-track";
    const fill = document.createElement("div");
    fill.className = "bar-fill";
    fill.style.width = "0%";
    track.appendChild(fill);
    setTimeout(() => { fill.style.width = `${pct}%`; }, 50 + idx * 60);

    const amount = document.createElement("strong");
    amount.textContent = money(item.total);

    row.appendChild(label);
    row.appendChild(track);
    row.appendChild(amount);
    chart.appendChild(row);
  });
}

/* ── Monthly Chart ── */
function renderMonthlyChart(items) {
  const chart = $("#monthlyChart");
  const visible = (items || []).filter((i) => Number(i.income) || Number(i.expense) || Number(i.savings));
  if (!visible.length) {
    chart.innerHTML = `<div style="color:var(--muted);text-align:center;padding:40px;font-size:13px;">No monthly activity yet.</div>`;
    return;
  }
  const max = Math.max(...visible.flatMap((i) => [Number(i.income), Number(i.expense), Number(i.savings)]), 1);
  chart.innerHTML = "";
  visible.forEach((item, idx) => {
    const row = document.createElement("div");
    row.className = "month-row";
    row.style.animationDelay = `${idx * 0.05}s`;

    const label = document.createElement("strong");
    label.textContent = item.month.slice(5);

    const barsWrap = document.createElement("div");
    barsWrap.className = "month-bars";
    barsWrap.title = `Income ${money(item.income)} | Expense ${money(item.expense)} | Savings ${money(item.savings)}`;

    [item.income, item.expense, item.savings].forEach((val) => {
      const bar = document.createElement("span");
      bar.style.width = "0%";
      barsWrap.appendChild(bar);
      setTimeout(() => { bar.style.width = `${(Number(val) / max) * 100}%`; }, 80 + idx * 50);
    });

    row.appendChild(label);
    row.appendChild(barsWrap);
    chart.appendChild(row);
  });
}

/* ── Bootstrap ── */
async function bootstrap() {
  setDefaultDates();
  if (!getToken()) { showApp(false); return; }
  try {
    showApp(true);
    await loadMe();
    await refreshDashboard();
  } catch {
    clearToken();
    showApp(false);
  }
}

/* ── Nav highlight ── */
document.querySelectorAll(".nav-link").forEach((link) => {
  link.addEventListener("click", () => {
    document.querySelectorAll(".nav-link").forEach((l) => l.classList.remove("active"));
    link.classList.add("active");
  });
});

/* ── Auth Tabs ── */
document.querySelectorAll(".auth-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".auth-tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    const isLogin = tab.dataset.tab === "login";
    $("#loginForm").classList.toggle("hidden", !isLogin);
    $("#registerForm").classList.toggle("hidden", isLogin);
    $("#authMessage").textContent = "";
    $("#authMessage").className = "auth-message";
  });
});

/* ── Login ── */
$("#loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = e.target.querySelector("button[type=submit]");
  btn.textContent = "Signing in…";
  btn.disabled = true;
  try {
    const data = await request("/auth/login", { method: "POST", body: JSON.stringify(formToJson(e.target)) });
    saveToken(data.access_token);
    toast(`Welcome back, ${data.user.full_name.split(" ")[0]}!`);
    showApp(true);
    await loadMe();
    await refreshDashboard();
  } catch (err) {
    const msg = $("#authMessage");
    msg.textContent = err.message;
    msg.className = "auth-message error";
  } finally {
    btn.innerHTML = "Sign In <span class='btn-arrow'>→</span>";
    btn.disabled = false;
  }
});

/* ── Register ── */
$("#registerForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = e.target.querySelector("button[type=submit]");
  btn.textContent = "Creating account…";
  btn.disabled = true;
  try {
    const data = await request("/auth/register", { method: "POST", body: JSON.stringify(formToJson(e.target)) });
    saveToken(data.access_token);
    toast(`Account created! Welcome, ${data.user.full_name.split(" ")[0]}!`);
    showApp(true);
    await loadMe();
    await refreshDashboard();
  } catch (err) {
    const msg = $("#authMessage");
    msg.textContent = err.message;
    msg.className = "auth-message error";
  } finally {
    btn.innerHTML = "Create Account <span class='btn-arrow'>→</span>";
    btn.disabled = false;
  }
});

/* ── Logout ── */
$("#logoutBtn").addEventListener("click", () => {
  clearToken();
  currentUser = null;
  showApp(false);
  toast("Logged out successfully.");
});

/* ── Data Forms ── */
function handleDataForm(formId, endpoint, successText) {
  const form = $(formId);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = form.querySelector("button[type=submit]");
    const originalText = btn.textContent;
    btn.textContent = "Saving…";
    btn.disabled = true;
    try {
      await request(endpoint, { method: "POST", body: JSON.stringify(formToJson(form)) });
      form.reset();
      setDefaultDates();
      toast(successText);
      await refreshDashboard();
    } catch (err) {
      toast(err.message, "error");
    } finally {
      btn.textContent = originalText;
      btn.disabled = false;
    }
  });
}

handleDataForm("#salaryForm",  "/finance/salary",  "Income added! Balance updated.");
handleDataForm("#expenseForm", "/finance/expenses", "Expense recorded. Wallet felt that.");
handleDataForm("#savingForm",  "/finance/savings",  "Saving added. Future you is smiling.");
handleDataForm("#budgetForm",  "/finance/budgets",  "Budget saved successfully.");

bootstrap();
