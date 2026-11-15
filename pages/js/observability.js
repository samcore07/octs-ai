/**
 * Octs AI - Observability & Production Monitoring Client
 * Fetches real persisted operational telemetry and health probes.
 * Never fabricates simulated or fake metrics.
 */

document.addEventListener('DOMContentLoaded', () => {
    initObservabilityDashboard();
});

function initObservabilityDashboard() {
    loadHealthStatus();
    loadAnalyticsData();

    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            loadHealthStatus();
            loadAnalyticsData();
        });
    }

    const disciplineFilter = document.getElementById('disciplineFilter');
    if (disciplineFilter) {
        disciplineFilter.addEventListener('change', () => {
            loadAnalyticsData();
        });
    }

    const eventNameFilter = document.getElementById('eventNameFilter');
    if (eventNameFilter) {
        eventNameFilter.addEventListener('change', () => {
            loadEventsData();
        });
    }

    const eventRequestIdFilter = document.getElementById('eventRequestIdFilter');
    if (eventRequestIdFilter) {
        eventRequestIdFilter.addEventListener('input', debounce(() => {
            loadEventsData();
        }, 300));
    }
}

async function loadHealthStatus() {
    const healthDot = document.getElementById('systemHealthDot');
    const healthText = document.getElementById('systemHealthText');
    const statusBadge = document.getElementById('healthStatusBadge');
    const uptimeText = document.getElementById('uptimeText');

    try {
        const resp = await fetch('/api/health');
        if (!resp.ok) throw new Error('Health check failed: ' + resp.status);
        const data = await resp.json();

        const isHealthy = data.status === 'ok';
        if (healthDot) healthDot.className = 'status-dot ' + (isHealthy ? 'healthy' : 'unhealthy');
        if (healthText) healthText.textContent = isHealthy ? 'All Systems Operational' : 'Degraded';

        if (statusBadge) {
            statusBadge.className = 'health-badge ' + (isHealthy ? 'healthy' : 'unhealthy');
            statusBadge.textContent = isHealthy ? 'System Healthy' : 'Degraded';
        }

        if (uptimeText && data.uptime_seconds !== undefined) {
            uptimeText.textContent = `Uptime: ${formatUptime(data.uptime_seconds)}`;
        }

        // Dependencies
        if (data.dependencies) {
            data.dependencies.forEach(dep => {
                if (dep.name === 'memory_database') {
                    const el = document.getElementById('depMemoryDb');
                    if (el) el.textContent = `${dep.status} (${dep.latency_ms || 0}ms)`;
                } else if (dep.name === 'telemetry_database') {
                    const el = document.getElementById('depTelemetryDb');
                    if (el) el.textContent = `${dep.status} (${dep.latency_ms || 0}ms)`;
                } else if (dep.name === 'model_provider') {
                    const el = document.getElementById('depModel');
                    if (el) el.textContent = `${dep.status}`;
                }
            });
        }
    } catch (err) {
        console.error('Error loading health:', err);
        if (healthDot) healthDot.className = 'status-dot unhealthy';
        if (healthText) healthText.textContent = 'Health Probes Unreachable';
        if (statusBadge) {
            statusBadge.className = 'health-badge unhealthy';
            statusBadge.textContent = 'Offline';
        }
    }
}

async function loadAnalyticsData() {
    const discFilter = document.getElementById('disciplineFilter')?.value || '';
    let queryParam = discFilter ? `?discipline=${encodeURIComponent(discFilter)}` : '';

    try {
        // 1. Overview
        const overviewResp = await fetch(`/api/analytics/overview${queryParam}`);
        if (overviewResp.ok) {
            const ov = await overviewResp.json();
            renderKPIs(ov);
        }

        // 2. Discipline Breakdown
        const discResp = await fetch('/api/analytics/disciplines');
        if (discResp.ok) {
            const disciplines = await discResp.json();
            renderDisciplineTable(disciplines);
        }

        // 3. Refinement Summary
        const refResp = await fetch('/api/analytics/refinement');
        if (refResp.ok) {
            const ref = await refResp.json();
            renderRefinementStats(ref);
        }

        // 4. Memory Summary
        const memResp = await fetch('/api/analytics/memory');
        if (memResp.ok) {
            const mem = await memResp.json();
            renderMemoryStats(mem);
        }

        // 5. Events Feed
        loadEventsData();
    } catch (err) {
        console.error('Error fetching analytics:', err);
    }
}

function renderKPIs(ov) {
    document.getElementById('kpiTotalRequests').textContent = ov.total_requests;
    document.getElementById('kpiSuccessRate').textContent = `${ov.success_rate_pct}% Success`;
    document.getElementById('kpiFailedRequests').textContent = `${ov.failed_requests} Failed`;

    document.getElementById('kpiAvgLatency').textContent = `${Math.round(ov.avg_latency_ms)} ms`;
    document.getElementById('kpiP50').textContent = `${Math.round(ov.p50_latency_ms)}ms`;
    document.getElementById('kpiP95').textContent = `${Math.round(ov.p95_latency_ms)}ms`;
    document.getElementById('kpiP99').textContent = `${Math.round(ov.p99_latency_ms)}ms`;

    document.getElementById('kpiTrustScore').textContent = ov.avg_trust_score !== null ? ov.avg_trust_score : '--';
    document.getElementById('kpiQualityScore').textContent = ov.avg_quality_score !== null ? ov.avg_quality_score : '--';

    document.getElementById('kpiTotalTokens').textContent = ov.total_tokens_used !== null ? ov.total_tokens_used.toLocaleString() : 'N/A';
    document.getElementById('kpiModelCalls').textContent = `${ov.total_model_calls} Calls`;
}

function renderDisciplineTable(disciplines) {
    const tbody = document.getElementById('disciplineTableBody');
    if (!tbody) return;

    if (!disciplines || disciplines.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No telemetry recorded yet.</td></tr>';
        return;
    }

    tbody.innerHTML = disciplines.map(d => `
        <tr>
            <td><strong>${capitalize(d.discipline)}</strong></td>
            <td>${d.request_count}</td>
            <td><span class="badge-success">${d.success_rate_pct}%</span></td>
            <td>${Math.round(d.avg_latency_ms)} ms</td>
            <td>${d.avg_trust_score !== null ? d.avg_trust_score : '--'}</td>
            <td>${d.refinement_rate_pct}%</td>
        </tr>
    `).join('');
}

function renderRefinementStats(ref) {
    document.getElementById('statRefAttempts').textContent = ref.total_refinements_attempted;
    document.getElementById('statRefAccepted').textContent = ref.refinement_acceptance_count;
    document.getElementById('statRefRejected').textContent = ref.refinement_rejection_count;
    document.getElementById('statRefReverted').textContent = ref.reversion_count;
    document.getElementById('statRefRate').textContent = `${ref.acceptance_rate_pct}%`;
}

function renderMemoryStats(mem) {
    document.getElementById('statMemRetrievals').textContent = mem.retrieval_requests;
    document.getElementById('statMemAvg').textContent = mem.avg_memories_retrieved.toFixed(1);
    document.getElementById('statMemExtracted').textContent = mem.total_memories_extracted;
    document.getElementById('statMemSuccess').textContent = `${mem.persistence_success_rate_pct}%`;
}

async function loadEventsData() {
    const tbody = document.getElementById('eventsTableBody');
    if (!tbody) return;

    const reqId = document.getElementById('eventRequestIdFilter')?.value?.trim() || '';
    const eventName = document.getElementById('eventNameFilter')?.value || '';

    const params = new URLSearchParams({ limit: '25' });
    if (reqId) params.append('request_id', reqId);
    if (eventName) params.append('event_name', eventName);

    try {
        const resp = await fetch(`/api/analytics/events?${params.toString()}`);
        if (!resp.ok) throw new Error('Events fetch error');
        const events = await resp.json();

        if (!events || events.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No matching lifecycle events found.</td></tr>';
            return;
        }

        tbody.innerHTML = events.map(ev => {
            const ts = ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : '--';
            const reqShort = ev.request_id ? `${ev.request_id.slice(0, 8)}...` : '--';
            const discPersona = [ev.discipline, ev.persona].filter(Boolean).join(' / ') || '--';
            const dur = ev.duration_ms !== null && ev.duration_ms !== undefined ? `${ev.duration_ms}ms` : '--';

            return `
                <tr>
                    <td class="text-muted">${ts}</td>
                    <td><strong>${ev.event_name}</strong></td>
                    <td class="text-secondary">${ev.component}</td>
                    <td title="${ev.request_id}">${reqShort}</td>
                    <td>${discPersona}</td>
                    <td>${dur}</td>
                </tr>
            `;
        }).join('');
    } catch (err) {
        console.error('Error fetching events:', err);
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Error loading lifecycle events.</td></tr>';
    }
}

function formatUptime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    if (m === 0) return `${s}s`;
    const h = Math.floor(m / 60);
    if (h === 0) return `${m}m ${s}s`;
    return `${h}h ${m % 60}m`;
}

function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function debounce(func, delay) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => func(...args), delay);
    };
}
