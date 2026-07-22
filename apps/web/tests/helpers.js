const fs = require("fs");
const http = require("http");
const path = require("path");

async function startStaticServer() {
  const root = path.resolve(__dirname, "..");
  const server = http.createServer((request, response) => {
    const pathname = new URL(request.url, "http://127.0.0.1").pathname;
    const filePath = pathname === "/styles.css" ? path.join(root, "styles.css") : path.join(root, "index.html");
    const contentType = pathname === "/styles.css" ? "text/css" : "text/html";
    response.writeHead(200, { "Content-Type": contentType });
    response.end(fs.readFileSync(filePath));
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  return { server, pageUrl: `http://127.0.0.1:${server.address().port}/` };
}

async function stopStaticServer(server) {
  await new Promise((resolve) => server.close(resolve));
}

async function stubApi(page, { routeAuthRequired = true, user = null, askHandler = null, ticketDetailHandler = null } = {}) {
  await page.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    const pathname = url.pathname;
    if (pathname === "/" || pathname.endsWith("/index.html") || pathname.endsWith("/styles.css")) {
      return route.fallback();
    }
    if (pathname === "/ready") {
      return route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          status: "ready",
          database: "available",
          autotask: "configured",
          app_route_auth_required: routeAuthRequired
        })
      });
    }
    if (pathname === "/auth/me") {
      if (!user) {
        return route.fulfill({ status: 401, contentType: "application/json", body: JSON.stringify({ detail: "unauthorized" }) });
      }
      return route.fulfill({ contentType: "application/json", body: JSON.stringify({ user }) });
    }
    if (pathname === "/api/sync/status" || pathname === "/sync/status") {
      return route.fulfill({ contentType: "application/json", body: JSON.stringify({ api_call_count: 0 }) });
    }
    if (pathname === "/api/sync/runs") {
      return route.fulfill({ contentType: "application/json", body: JSON.stringify({ runs: [] }) });
    }
    if (pathname === "/api/knowledge/noise-report") {
      return route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({ active_noise_chunks: 0, active_useful_chunks: 0, unknown_chunks: 0, eligible_missing_embeddings: 0 })
      });
    }
    if (pathname === "/api/analytics/recurring-issues") {
      return route.fulfill({ contentType: "application/json", body: JSON.stringify({ groups: [], excluded_count: 0, warnings: [] }) });
    }
    if (pathname === "/api/analytics/ticket-class-report") {
      return route.fulfill({ contentType: "application/json", body: JSON.stringify({ classified_tickets: 0 }) });
    }
    if (pathname === "/api/reference-data/status") {
      return route.fulfill({ contentType: "application/json", body: JSON.stringify({ total_reference_values: 0 }) });
    }
    if (pathname === "/api/operations/status") {
      return route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          api_status: "ok",
          db_status: "ok",
          ollama_status: "unknown",
          autotask_threshold_remaining: 100,
          disk_free_gb: 10,
          global_pause: false,
          scheduler: {
            state: "healthy",
            heartbeat_age_seconds: 12,
            heartbeat: { status: "running" },
            next_due_job: { job_name: "open_ticket_history_gaps", due_at: "2026-07-22T00:29:03Z" }
          },
          counts: {
            tickets: 67726,
            ticket_notes: 675531,
            time_entries: 49054,
            ticket_history: 29340,
            eligible_missing_embeddings: 0
          }
        })
      });
    }
    if (pathname === "/api/operations/jobs") {
      return route.fulfill({ contentType: "application/json", body: JSON.stringify({ jobs: [], running: [] }) });
    }
    if (pathname === "/api/operations/jobs/runs") {
      return route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          runs: [
            {
              id: 10,
              job_name: "open_ticket_history_gaps",
              status: "completed",
              started_at: "2026-07-22T00:13:11Z",
              finished_at: "2026-07-22T00:14:03Z",
              duration_ms: 52053,
              pulled_count: 685,
              inserted_count: 2,
              updated_count: 683,
              failed_count: 0,
              last_error: null
            },
            {
              id: 9,
              job_name: "ticket_time_entry_gaps",
              status: "completed",
              started_at: "2026-07-22T00:11:41Z",
              finished_at: "2026-07-22T00:12:10Z",
              duration_ms: 28598,
              pulled_count: 40,
              inserted_count: 40,
              updated_count: 0,
              failed_count: 0,
              last_error: null
            }
          ]
        })
      });
    }
    if (pathname === "/api/admin/curated-memory") {
      return route.fulfill({ contentType: "application/json", body: JSON.stringify({ items: [] }) });
    }
    if (pathname === "/audit-log") {
      return route.fulfill({ contentType: "application/json", body: JSON.stringify({ entries: [] }) });
    }
    if (pathname === "/api/assistant/ask" && askHandler) {
      return askHandler(route);
    }
    if (pathname.startsWith("/api/ticket-health/ticket-number/") && ticketDetailHandler) {
      return ticketDetailHandler(route);
    }
    return route.fulfill({ contentType: "application/json", body: JSON.stringify({ ok: true }) });
  });
}

module.exports = { startStaticServer, stopStaticServer, stubApi };
