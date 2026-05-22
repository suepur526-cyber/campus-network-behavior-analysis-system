const chartPalette = ["#0f766e", "#c97817", "#2563eb", "#7c3aed", "#b42318", "#475569", "#16a34a"];
let currentLogPage = 1;
let totalLogPages = 1;
let currentAlertPage = 1;
let totalAlertPages = 1;

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`请求失败: ${url}`);
  return response.json();
}

function makeChart(id, option) {
  const element = document.getElementById(id);
  if (!element || !window.echarts) return;
  const chart = echarts.init(element);
  chart.setOption(option);
  window.addEventListener("resize", () => chart.resize());
}

function pieOption(data) {
  return {
    color: chartPalette,
    tooltip: { trigger: "item" },
    series: [{ type: "pie", radius: ["42%", "72%"], avoidLabelOverlap: true, data }]
  };
}

function renderMetrics(totals) {
  const el = document.getElementById("metrics");
  if (!el) return;
  const cards = [
    ["日志总量", totals.logs],
    ["用户数量", totals.users],
    ["总流量 GB", totals.traffic_gb],
    ["异常日志", totals.anomalies],
  ];
  el.innerHTML = cards.map(([label, value]) => `<div class="metric"><span>${label}</span><strong>${value}</strong></div>`).join("");
}

function renderTraffic(id, rows) {
  makeChart(id, {
    color: ["#0f766e"],
    tooltip: { trigger: "axis" },
    grid: { left: 42, right: 18, top: 28, bottom: 52 },
    xAxis: { type: "category", data: rows.map(r => r.time), axisLabel: { rotate: 35 } },
    yAxis: { type: "value", name: "GB" },
    series: [{ type: "line", smooth: true, areaStyle: { opacity: 0.12 }, data: rows.map(r => r.gb) }]
  });
}

function renderRanks(id, users) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = users.map((u, index) => `
    <div class="rank-item">
      <div><strong>${index + 1}. ${u.user_id}</strong><br><small>${u.visits} 次访问</small></div>
      <strong>${u.traffic_mb} MB</strong>
    </div>
  `).join("") || "<p>暂无数据</p>";
}

function renderAlerts(alerts) {
  const el = document.getElementById("alertList");
  if (!el) return;
  el.innerHTML = alerts.map(a => `
    <div class="alert-item">
      <div><strong>${a.category}</strong><br><small>${a.message}</small></div>
      <span class="badge ${a.severity}">${a.severity}</span>
    </div>
  `).join("") || "<p>暂无告警，导入数据后可在异常检测页运行检测。</p>";
}

async function loadDashboard() {
  const data = await fetchJson("/api/dashboard");
  renderMetrics(data.totals);
  renderTraffic("trafficChart", data.traffic_by_hour);
  makeChart("protocolChart", pieOption(data.protocol_distribution));
  makeChart("categoryChart", pieOption(data.category_distribution));
  renderAlerts(data.recent_alerts);
  renderRanks("topUsers", data.top_users);
  renderTraffic("analysisTraffic", data.traffic_by_hour);
  makeChart("userTypeChart", pieOption(data.user_type_distribution));
  makeChart("appChart", pieOption(data.application_distribution));
  renderRanks("analysisTopUsers", data.top_users);
  makeChart("anomalyTypeChart", pieOption(data.anomaly_types));
}

function currentLogParams() {
  return new URLSearchParams({
    keyword: document.getElementById("keyword")?.value || "",
    user_type: document.getElementById("userType")?.value || "",
    protocol: document.getElementById("protocol")?.value || "",
    is_anomaly: document.getElementById("isAnomaly")?.value || "",
    per_page: "50",
    page: String(currentLogPage),
  });
}

async function loadLogs() {
  const table = document.getElementById("logsTable");
  if (!table) return;
  const params = currentLogParams();
  const data = await fetchJson(`/api/logs?${params.toString()}`);
  totalLogPages = data.total_pages || 1;
  const pageInfo = document.getElementById("pageInfo");
  if (pageInfo) pageInfo.textContent = `第 ${data.page} / ${totalLogPages} 页，共 ${data.total} 条`;
  const exportLink = document.getElementById("exportLogs");
  if (exportLink) exportLink.href = `/api/logs/export?${params.toString()}`;

  table.innerHTML = data.items.map(row => `
    <tr>
      <td>${row.timestamp}</td><td>${row.user_id}</td><td>${row.user_type}</td><td>${row.ip_address}</td>
      <td>${row.target}</td><td>${row.protocol}</td><td>${row.port}</td>
      <td>${(row.total_bytes / 1024 / 1024).toFixed(2)} MB</td>
      <td><span class="badge ${row.is_anomaly ? "bad" : "ok"}">${row.is_anomaly ? "异常" : "正常"}</span></td>
    </tr>
  `).join("") || "<tr><td colspan='9'>暂无日志，请先导入测试数据。</td></tr>";
}

async function loadAnomalies() {
  const table = document.getElementById("anomalyTable");
  if (!table) return;
  const data = await fetchJson(`/api/anomalies?page=${currentAlertPage}&per_page=30`);
  totalAlertPages = data.total_pages || 1;
  const pageInfo = document.getElementById("alertPageInfo");
  if (pageInfo) pageInfo.textContent = `第 ${data.page} / ${totalAlertPages} 页，共 ${data.total} 条`;
  table.innerHTML = data.items.map(row => `
    <tr><td>${row.created_at}</td><td><span class="badge ${row.severity}">${row.severity}</span></td><td>${row.category}</td><td>${row.detected_by}</td><td>${row.message}</td></tr>
  `).join("") || "<tr><td colspan='5'>暂无告警，请先运行异常检测。</td></tr>";
}

function renderStatusRows(id, rows) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = rows.map(([label, value]) => `
    <div class="status-row"><span>${label}</span><strong>${value}</strong></div>
  `).join("");
}

async function loadReport() {
  const metrics = document.getElementById("reportMetrics");
  if (!metrics) return;
  const data = await fetchJson("/api/report");
  const status = data.system_status;
  metrics.innerHTML = [
    ["日志总量", status.database.logs],
    ["告警数量", status.database.alerts],
    ["准确率", `${Math.round(data.quality.accuracy * 100)}%`],
    ["响应时间", `${data.performance.query_response_ms} ms`],
  ].map(([label, value]) => `<div class="metric"><span>${label}</span><strong>${value}</strong></div>`).join("");
  const ingestFolder = document.getElementById("ingestFolder");
  if (ingestFolder) ingestFolder.textContent = "data/ingest";
  renderStatusRows("systemStatus", [
    ["运行状态", status.runtime.status],
    ["Web 框架", status.runtime.framework],
    ["数据库", status.runtime.database],
    ["检测模型", status.runtime.model],
    ["用户数量", status.database.users],
    ["日志来源", status.database.sources.join("、") || "暂无"],
    ["最近导入", status.activity.last_import?.created_at || "暂无"],
    ["最近检测", status.activity.last_detection?.created_at || "暂无"],
  ]);
  renderStatusRows("qualityList", [
    ["准确率 Accuracy", data.quality.accuracy],
    ["精确率 Precision", data.quality.precision],
    ["召回率 Recall", data.quality.recall],
    ["F1 值", data.quality.f1],
    ["真实异常数", data.quality.actual_anomalies],
    ["预测异常数", data.quality.predicted_anomalies],
  ]);
  renderStatusRows("performanceList", [
    ["查询响应时间", `${data.performance.query_response_ms} ms`],
    ["目标响应时间", `${data.performance.target_response_ms} ms`],
    ["接入日志规模", `${data.performance.log_scale} 条`],
  ]);
  const testList = document.getElementById("testCaseList");
  if (testList) {
    testList.innerHTML = data.test_cases.map(item => `
      <div class="status-row"><span>${item.name}</span><strong>${item.status}</strong></div>
    `).join("");
  }
}

async function simulateCollect(event) {
  event.preventDefault();
  const response = await fetch("/api/collect/run", { method: "POST" });
  const data = await response.json();
  const result = document.getElementById("collectResult");
  if (result) result.textContent = `已接入 ${data.files.length} 个文件，新增 ${data.inserted} 条日志。`;
  await loadReport();
}

document.addEventListener("DOMContentLoaded", () => {
  loadDashboard().catch(console.error);
  loadLogs().catch(console.error);
  loadAnomalies().catch(console.error);
  loadReport().catch(console.error);
  document.getElementById("collectForm")?.addEventListener("submit", simulateCollect);
  document.getElementById("searchLogs")?.addEventListener("click", () => {
    currentLogPage = 1;
    loadLogs();
  });
  document.getElementById("prevPage")?.addEventListener("click", () => {
    currentLogPage = Math.max(1, currentLogPage - 1);
    loadLogs();
  });
  document.getElementById("nextPage")?.addEventListener("click", () => {
    currentLogPage = Math.min(totalLogPages, currentLogPage + 1);
    loadLogs();
  });
  document.getElementById("prevAlertPage")?.addEventListener("click", () => {
    currentAlertPage = Math.max(1, currentAlertPage - 1);
    loadAnomalies();
  });
  document.getElementById("nextAlertPage")?.addEventListener("click", () => {
    currentAlertPage = Math.min(totalAlertPages, currentAlertPage + 1);
    loadAnomalies();
  });
});
