document.addEventListener("DOMContentLoaded", () => {
    loadInAppNotifications();
    loadNotificationLogs();
    loadSettings();
    loadRules();
    loadEmailDashboard();
    
    document.getElementById('provider-settings-form')?.addEventListener('submit', saveSettings);
    document.getElementById('routing-rules-form')?.addEventListener('submit', addRule);
});

// Alias for WebSocket reload
function loadNotifications() {
    loadInAppNotifications();
}

async function loadInAppNotifications() {
    const list = document.getElementById('inapp-list');
    if (!list) return;
    
    list.innerHTML = '<li class="px-md py-md text-center text-slate-500">Loading notifications...</li>';
    
    try {
        const res = await fetch('/api/v1/notifications/in-app?limit=50');
        if (!res.ok) throw new Error('Failed to load in-app notifications');
        const notifs = await res.json();
        
        if (notifs.length === 0) {
            list.innerHTML = '<li class="px-md py-md text-center text-slate-500">You have no notifications</li>';
            return;
        }
        
        list.innerHTML = '';
        notifs.forEach(notif => {
            const date = new Date(notif.created_at).toLocaleString();
            const bgClass = notif.is_read ? 'bg-white' : 'bg-indigo-50/50';
            const icon = notif.is_read ? 'notifications' : 'notifications_active';
            const iconColor = notif.is_read ? 'text-slate-400' : 'text-indigo-600';
            
            const li = document.createElement('li');
            li.className = `px-md py-md ${bgClass} hover:bg-slate-50 transition-colors flex gap-4 items-start`;
            
            li.innerHTML = `
                <div class="mt-1">
                    <span class="material-symbols-outlined ${iconColor}">${icon}</span>
                </div>
                <div class="flex-1">
                    <div class="flex justify-between items-start">
                        <h4 class="font-medium text-slate-900">${notif.title}</h4>
                        <span class="text-xs text-slate-500">${date}</span>
                    </div>
                    <p class="text-sm text-slate-600 mt-1">${notif.content}</p>
                    <div class="mt-3 flex items-center gap-4">
                        ${notif.action_url ? `<a href="${notif.action_url}" class="text-xs font-medium text-indigo-600 hover:text-indigo-800">View Details</a>` : ''}
                        ${!notif.is_read ? `<button onclick="markAsRead(${notif.id})" class="text-xs font-medium text-slate-500 hover:text-slate-700">Mark Read</button>` : ''}
                        <button onclick="archiveNotification(${notif.id})" class="text-xs font-medium text-red-500 hover:text-red-700 ml-auto flex items-center gap-1">
                            <span class="material-symbols-outlined text-[14px]">archive</span> Archive
                        </button>
                    </div>
                </div>
            `;
            list.appendChild(li);
        });
    } catch (e) {
        list.innerHTML = '<li class="px-md py-md text-center text-red-500">Error loading notifications</li>';
        console.error(e);
    }
}

async function markAsRead(id) {
    try {
        await fetch(`/api/v1/notifications/in-app/${id}`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ is_read: 1 })
        });
        loadInAppNotifications();
        if(typeof fetchUnreadNotificationCount === 'function') fetchUnreadNotificationCount();
    } catch(e) {
        console.error(e);
    }
}

async function archiveNotification(id) {
    try {
        await fetch(`/api/v1/notifications/in-app/${id}`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ is_archived: 1 })
        });
        loadInAppNotifications();
    } catch(e) {
        console.error(e);
    }
}

async function markAllRead() {
    try {
        await fetch('/api/v1/notifications/in-app/mark-all-read', { method: 'POST' });
        loadInAppNotifications();
        if(typeof fetchUnreadNotificationCount === 'function') fetchUnreadNotificationCount();
    } catch(e) {
        console.error(e);
    }
}

async function loadNotificationLogs() {
    const tbody = document.getElementById('logs-tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="6" class="px-md py-md text-center text-slate-500">Loading logs...</td></tr>';
    
    try {
        const res = await fetch('/api/v1/notifications/logs');
        if (!res.ok) throw new Error('Failed to load logs');
        const logs = await res.json();
        
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="px-md py-md text-center text-slate-500">No notifications found</td></tr>';
            return;
        }
        
        tbody.innerHTML = '';
        logs.forEach(log => {
            const date = new Date(log.sent_at).toLocaleString();
            let statusBadge = '';
            if (log.status === 'sent') statusBadge = '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">Sent</span>';
            else if (log.status === 'failed') statusBadge = '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">Failed</span>';
            else statusBadge = `<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">${log.status}</span>`;
            
            let tracking = '<span class="text-xs text-slate-400">Not tracked</span>';
            if (log.opened_at) tracking = `<span class="text-xs text-emerald-600">Opened: ${new Date(log.opened_at).toLocaleTimeString()}</span>`;
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="px-md py-sm text-slate-500">${date}</td>
                <td class="px-md py-sm">
                    <div class="flex items-center gap-2">
                        <span class="material-symbols-outlined text-sm text-slate-400">${log.channel.toLowerCase() === 'email' ? 'mail' : 'chat'}</span>
                        ${log.channel}
                    </div>
                </td>
                <td class="px-md py-sm font-medium text-slate-700">${log.recipient}</td>
                <td class="px-md py-sm text-slate-600 truncate max-w-xs" title="${log.subject}">${log.subject}</td>
                <td class="px-md py-sm">${statusBadge}</td>
                <td class="px-md py-sm">${tracking}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="6" class="px-md py-md text-center text-red-500">Error loading logs</td></tr>';
        console.error(e);
    }
}

function switchTab(tabId) {
    // Hide all tabs
    document.querySelectorAll('[id^="tab-"]').forEach(el => {
        if (!el.id.startsWith("tab-btn-")) el.classList.add("hidden");
    });
    
    // Reset buttons
    document.querySelectorAll('[id^="tab-btn-"]').forEach(btn => {
        btn.classList.remove("border-indigo-500", "text-indigo-600");
        btn.classList.add("border-transparent", "text-slate-500");
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(`tab-${tabId}`);
    if (selectedTab) selectedTab.classList.remove("hidden");
    
    // Highlight button
    const btn = document.getElementById(`tab-btn-${tabId}`);
    if (btn) {
        btn.classList.remove("border-transparent", "text-slate-500");
        btn.classList.add("border-indigo-500", "text-indigo-600");
    }
}

async function loadSettings() {
    try {
        const res = await fetch('/api/v1/settings');
        if (!res.ok) return; // Might be 403 if not admin
        const data = await res.json();
        
        const providerEl = document.getElementById('email_provider');
        if (providerEl && data.email_provider) {
            providerEl.value = data.email_provider;
        }
        
        const senderEl = document.getElementById('sender_email');
        if (senderEl && data.sender_email) {
            senderEl.value = data.sender_email;
        }
    } catch (e) {
        console.error('Failed to load settings', e);
    }
}

async function saveSettings(e) {
    e.preventDefault();
    const statusEl = document.getElementById('settings-status');
    statusEl.textContent = 'Saving...';
    statusEl.className = 'text-sm mt-2 text-slate-500';
    
    const payload = {
        email_provider: document.getElementById('email_provider').value,
        sender_email: document.getElementById('sender_email').value
    };
    
    try {
        const res = await fetch('/api/v1/settings', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            statusEl.textContent = 'Settings saved successfully.';
            statusEl.className = 'text-sm mt-2 text-green-600';
            setTimeout(() => { statusEl.textContent = ''; }, 3000);
        } else {
            throw new Error(await res.text());
        }
    } catch (err) {
        statusEl.textContent = 'Error saving settings (Requires Administrator role).';
        statusEl.className = 'text-sm mt-2 text-red-600';
        console.error(err);
    }
}

async function loadRules() {
    const tbody = document.getElementById('rules-tbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="3" class="px-md py-md text-center text-slate-500">Loading rules...</td></tr>';
    
    try {
        const res = await fetch('/api/v1/notifications/rules');
        if (!res.ok) throw new Error('Failed to load rules');
        const rules = await res.json();
        
        if (rules.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="px-md py-md text-center text-slate-500">No routing rules found</td></tr>';
            return;
        }
        
        tbody.innerHTML = '';
        rules.forEach(rule => {
            const statusBadge = rule.is_active ? 
                '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">Active</span>' : 
                '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-800">Inactive</span>';
                
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="px-md py-sm font-medium text-slate-700">${rule.name}</td>
                <td class="px-md py-sm text-slate-600">${rule.recipients.join(', ')}</td>
                <td class="px-md py-sm">${statusBadge}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="3" class="px-md py-md text-center text-red-500">Error loading rules</td></tr>';
        console.error(e);
    }
}

async function addRule(e) {
    e.preventDefault();
    const name = document.getElementById('rule_name').value;
    const recipientsRaw = document.getElementById('rule_recipients').value;
    const recipients = recipientsRaw.split(',').map(s => s.trim()).filter(Boolean);
    
    const payload = {
        name: name,
        recipients: recipients,
        channels: ['Email', 'In-App'],
        event_types: ['TenderMatchedEvent', 'TenderDiscoveredEvent', 'HighPriority']
    };
    
    try {
        const res = await fetch('/api/v1/notifications/rules', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            document.getElementById('rule_name').value = '';
            document.getElementById('rule_recipients').value = '';
            document.getElementById('add-rule-form-container').classList.add('hidden');
            loadRules();
        } else {
            alert('Failed to create rule (Requires Administrator role).');
        }
    } catch (err) {
        console.error(err);
        alert('An error occurred.');
    }
}

// ─── Email Delivery Dashboard ────────────────────────────────────────────

async function loadEmailDashboard() {
    try {
        // Load stats
        const dashRes = await fetch('/api/v1/email/dashboard');
        if (dashRes.ok) {
            const data = await dashRes.json();
            const s = data.statistics;
            document.getElementById('stat-total') && (document.getElementById('stat-total').textContent = s.total_emails);
            document.getElementById('stat-success') && (document.getElementById('stat-success').textContent = s.successful);
            document.getElementById('stat-failed') && (document.getElementById('stat-failed').textContent = s.failed);
            document.getElementById('stat-pending') && (document.getElementById('stat-pending').textContent = s.pending);

            // Provider status inline
            const statusEl = document.getElementById('email-provider-status');
            if (statusEl) {
                const p = data.provider;
                const last = data.last_successful_send;
                statusEl.innerHTML = `
                    <div class="flex items-center gap-3">
                        <span class="w-3 h-3 rounded-full ${p.enabled ? 'bg-green-500' : 'bg-red-500'}"></span>
                        <div>
                            <p class="font-medium text-slate-700">Provider: <span class="text-indigo-600">${p.name}</span></p>
                            <p class="text-xs text-slate-500">${p.enabled ? 'Email sending enabled' : 'Email sending disabled — configure API key'}</p>
                            ${last.sent_at ? `<p class="text-xs text-slate-500 mt-1">Last sent: ${new Date(last.sent_at).toLocaleString()} to ${last.recipient || 'N/A'}</p>` : ''}
                        </div>
                    </div>
                `;
            }
        }
    } catch (e) {
        console.error('Failed to load email dashboard', e);
    }

    // Load email logs
    loadEmailLogs();
}

async function loadEmailLogs() {
    const tbody = document.getElementById('email-logs-tbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="8" class="px-3 py-4 text-center text-slate-400">Loading...</td></tr>';

    try {
        const res = await fetch('/api/v1/email/logs?limit=30');
        if (!res.ok) throw new Error('Failed to load email logs');
        const logs = await res.json();

        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="px-3 py-4 text-center text-slate-400">No email logs yet. Send a test email to get started.</td></tr>';
            return;
        }

        tbody.innerHTML = '';
        logs.forEach(log => {
            const statusBadge = log.status === 'sent'
                ? '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">Sent</span>'
                : log.status === 'failed'
                ? '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">Failed</span>'
                : `<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">${log.status}</span>`;

            const retryBtn = log.status === 'failed'
                ? `<button onclick="retryEmail(${log.id})" class="text-xs text-indigo-600 hover:text-indigo-800 font-medium">Retry</button>`
                : '<span class="text-xs text-slate-300">—</span>';

            const msgId = log.message_id
                ? `<span class="text-xs font-mono text-slate-500" title="${log.message_id}">${log.message_id.substring(0, 12)}...</span>`
                : '<span class="text-xs text-slate-300">—</span>';

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="px-3 py-2 text-slate-600">${log.recipient}</td>
                <td class="px-3 py-2 text-slate-700 truncate max-w-[200px]" title="${log.subject || ''}">${log.subject || '—'}</td>
                <td class="px-3 py-2 text-slate-500">${log.provider || '—'}</td>
                <td class="px-3 py-2">${statusBadge}</td>
                <td class="px-3 py-2">${msgId}</td>
                <td class="px-3 py-2 text-slate-500">${log.retry_count || 0}</td>
                <td class="px-3 py-2 text-slate-500 text-xs">${log.sent_at ? new Date(log.sent_at).toLocaleString() : '—'}</td>
                <td class="px-3 py-2">${retryBtn}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="8" class="px-3 py-4 text-center text-red-500">Error loading email logs</td></tr>';
        console.error(e);
    }
}

function showEmailResult(html, isError = false) {
    const el = document.getElementById('email-action-result');
    if (!el) return;
    el.classList.remove('hidden', 'bg-green-50', 'border-green-200', 'bg-red-50', 'border-red-200');
    if (isError) {
        el.classList.add('bg-red-50', 'border-red-200');
    } else {
        el.classList.add('bg-green-50', 'border-green-200');
    }
    el.innerHTML = html;
}

async function sendTestEmail() {
    const btn = document.getElementById('btn-send-test');
    if (btn) { btn.disabled = true; btn.textContent = 'Sending...'; }

    try {
        const res = await fetch('/api/v1/email/test', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ recipient: 'ordinary01012024@gmail.com' })
        });
        const data = await res.json();

        if (data.success) {
            showEmailResult(`
                <p class="font-medium text-green-800">✅ Test email sent successfully!</p>
                <div class="mt-2 text-sm text-green-700 space-y-1">
                    <p><strong>Recipient:</strong> ${data.recipient}</p>
                    <p><strong>Provider:</strong> ${data.provider}</p>
                    <p><strong>Message ID:</strong> <code class="bg-green-100 px-1 rounded">${data.message_id || 'N/A'}</code></p>
                    <p><strong>HTTP Status:</strong> ${data.http_status || 'N/A'}</p>
                    <p><strong>Sent At:</strong> ${data.sent_at ? new Date(data.sent_at).toLocaleString() : 'N/A'}</p>
                </div>
            `);
        } else {
            showEmailResult(`
                <p class="font-medium text-red-800">❌ Test email failed</p>
                <div class="mt-2 text-sm text-red-700 space-y-1">
                    <p><strong>Error:</strong> ${data.error || 'Unknown error'}</p>
                    <p><strong>Provider:</strong> ${data.provider || 'N/A'}</p>
                    <p><strong>HTTP Status:</strong> ${data.http_status || 'N/A'}</p>
                    <p><strong>Retries:</strong> ${data.retry_count || 0}</p>
                </div>
            `, true);
        }
        loadEmailDashboard();
    } catch (err) {
        showEmailResult(`<p class="font-medium text-red-800">❌ Request failed: ${err.message}</p>`, true);
        console.error(err);
    } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = '<span class="material-symbols-outlined text-sm">send</span> Send Test Email'; }
    }
}

async function runTestSeries() {
    const btn = document.getElementById('btn-run-series');
    if (btn) { btn.disabled = true; btn.textContent = 'Sending 6 emails...'; }

    try {
        const res = await fetch('/api/v1/email/test-series', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ recipient: 'ordinary01012024@gmail.com' })
        });
        const data = await res.json();

        let details = data.results.map(r =>
            `<li class="${r.success ? 'text-green-700' : 'text-red-700'}">
                ${r.success ? '✅' : '❌'} ${r.template} ${r.message_id ? `— ID: <code class="bg-slate-100 px-1 rounded text-xs">${r.message_id.substring(0, 16)}...</code>` : (r.error ? `— ${r.error}` : '')}
            </li>`
        ).join('');

        const isError = data.failed > 0;
        showEmailResult(`
            <p class="font-medium ${isError ? 'text-yellow-800' : 'text-green-800'}">
                ${isError ? '⚠️' : '✅'} Test Series: ${data.successful}/${data.total} successful
            </p>
            <ul class="mt-2 text-sm space-y-1">${details}</ul>
        `, isError);
        loadEmailDashboard();
    } catch (err) {
        showEmailResult(`<p class="font-medium text-red-800">❌ Test series failed: ${err.message}</p>`, true);
        console.error(err);
    } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = '<span class="material-symbols-outlined text-sm">playlist_play</span> Run Test Series (6 Emails)'; }
    }
}

async function checkProviderStatus() {
    try {
        const res = await fetch('/api/v1/email/status');
        const data = await res.json();
        const c = data.connectivity;

        if (c.reachable) {
            showEmailResult(`
                <p class="font-medium text-green-800">✅ Provider connected: ${data.provider}</p>
                <div class="mt-2 text-sm text-green-700">
                    <p>HTTP Status: ${c.http_status}</p>
                    <p>API Key Configured: ${data.configuration.api_key_configured ? 'Yes' : 'No'}</p>
                </div>
            `);
        } else {
            showEmailResult(`
                <p class="font-medium text-red-800">❌ Provider unreachable: ${data.provider}</p>
                <div class="mt-2 text-sm text-red-700">
                    <p>Error: ${c.error || 'Unknown'}</p>
                    <p>API Key Configured: ${data.configuration.api_key_configured ? 'Yes' : 'No'}</p>
                </div>
            `, true);
        }
    } catch (err) {
        showEmailResult(`<p class="font-medium text-red-800">❌ Status check failed: ${err.message}</p>`, true);
    }
}

async function retryEmail(logId) {
    try {
        const res = await fetch(`/api/v1/email/retry/${logId}`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showEmailResult(`<p class="font-medium text-green-800">✅ Retry successful! Message ID: ${data.message_id || 'N/A'}</p>`);
        } else {
            showEmailResult(`<p class="font-medium text-red-800">❌ Retry failed: ${data.error}</p>`, true);
        }
        loadEmailDashboard();
    } catch (err) {
        showEmailResult(`<p class="font-medium text-red-800">❌ Retry request failed</p>`, true);
    }
}

// ─── Tab Switching ────────────────────────────────────────────────────────

function switchTab(tabName) {
    const tabs = ['inapp', 'logs', 'settings', 'rules', 'email', 'scheduler', 'ops', 'aicost'];
    tabs.forEach(t => {
        const btn = document.getElementById(`tab-btn-${t}`);
        const content = document.getElementById(`tab-${t}`);
        if (btn) {
            if (t === tabName) {
                btn.className = "border-indigo-500 text-indigo-600 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm";
            } else {
                btn.className = "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm";
            }
        }
        if (content) {
            if (t === tabName) content.classList.remove('hidden');
            else content.classList.add('hidden');
        }
    });

    if (tabName === 'scheduler') loadSchedulerDashboard();
    else if (tabName === 'ops') loadOperationsDashboard();
    else if (tabName === 'aicost') loadAICostMonitoring();
    else if (tabName === 'email') loadEmailDashboard();
}

// ─── Phase 1 & 10: Scheduler Dashboard & Trigger Controls ──────────────────

async function loadSchedulerDashboard() {
    const tbody = document.getElementById('scheduler-history-tbody');
    if (!tbody) return;

    try {
        const res = await fetch('/api/v1/scheduler/dashboard');
        if (!res.ok) throw new Error('Failed to load scheduler dashboard');
        const data = await res.json();

        if (!data.recent_executions || data.recent_executions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="px-3 py-4 text-center text-slate-400">No background jobs executed yet. Trigger a job above to test.</td></tr>';
            return;
        }

        tbody.innerHTML = '';
        data.recent_executions.forEach(j => {
            const badge = j.status === 'Success'
                ? '<span class="px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">Success</span>'
                : j.status === 'Failed'
                ? '<span class="px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">Failed</span>'
                : `<span class="px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">${j.status}</span>`;

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="px-3 py-2 font-medium text-slate-700">${j.job_name}</td>
                <td class="px-3 py-2">${badge}</td>
                <td class="px-3 py-2 text-xs text-slate-500">${j.last_run ? new Date(j.last_run).toLocaleString() : '—'}</td>
                <td class="px-3 py-2 text-slate-600">${j.duration_seconds}s</td>
                <td class="px-3 py-2 text-xs text-slate-600 truncate max-w-[250px]" title="${j.summary || j.error || ''}">${j.summary || j.error || '—'}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="5" class="px-3 py-4 text-center text-red-500">Error loading scheduler dashboard</td></tr>';
        console.error(e);
    }
}

async function triggerJob(jobName) {
    try {
        const res = await fetch('/api/v1/scheduler/trigger-job', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ job_name: jobName })
        });
        const data = await res.json();
        alert(`Job [${jobName}] triggered: ${data.execution_result?.summary || data.status}`);
        loadSchedulerDashboard();
    } catch (e) {
        alert(`Failed to trigger job: ${e.message}`);
    }
}

// ─── Phase 25: Operations Dashboard & Phase 24: Backup ────────────────────

async function loadOperationsDashboard() {
    try {
        const res = await fetch('/api/v1/admin/operations-dashboard');
        if (!res.ok) return;
        const data = await res.json();
        const sys = data.system_resources;
        const srv = data.services;

        document.getElementById('ops-cpu') && (document.getElementById('ops-cpu').textContent = `${sys.cpu_usage_pct}%`);
        document.getElementById('ops-ram') && (document.getElementById('ops-ram').textContent = `${sys.ram_usage_pct}%`);
        document.getElementById('ops-disk') && (document.getElementById('ops-disk').textContent = `${sys.disk_usage_pct}%`);
        document.getElementById('ops-ws') && (document.getElementById('ops-ws').textContent = srv.websocket_active_clients);
    } catch (e) {
        console.error(e);
    }
}

async function createBackup() {
    try {
        const res = await fetch('/api/v1/admin/backup/create', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            alert(`Backup archive created successfully!\nFile: ${data.backup_filename}\nFiles: ${data.files_count}\nSize: ${Math.round(data.size_bytes / 1024)} KB`);
        } else {
            alert('Failed to create backup.');
        }
    } catch (e) {
        alert(`Backup error: ${e.message}`);
    }
}

// ─── Phase 16: AI Cost Monitoring ─────────────────────────────────────────

async function loadAICostMonitoring() {
    try {
        const res = await fetch('/api/v1/analytics/ai-cost');
        if (!res.ok) return;
        const data = await res.json();

        document.getElementById('cost-total-requests') && (document.getElementById('cost-total-requests').textContent = data.total_requests);
        document.getElementById('cost-total-tokens') && (document.getElementById('cost-total-tokens').textContent = data.total_tokens.toLocaleString());
        document.getElementById('cost-total-usd') && (document.getElementById('cost-total-usd').textContent = `$${data.total_cost_usd}`);
        document.getElementById('cost-avg-latency') && (document.getElementById('cost-avg-latency').textContent = `${data.average_latency_seconds}s`);
    } catch (e) {
        console.error(e);
    }
}

