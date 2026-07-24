document.addEventListener("DOMContentLoaded", () => {
    loadInAppNotifications();
    loadNotificationLogs();
    loadSettings();
    loadRules();
    
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
