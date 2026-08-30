'use strict';

const App = {

    // ─── State ─────────────────────────────────────────────────────────────────
    state: {
        authenticated: false,
        config: {},
        selectedDuration: 24,
        countdownTimer: null,
        loginPollInterval: null,
        folderStack: [{ id: 'root', name: 'My Drive' }],
        queue: [],
        // Clone-specific
        cloneDestId: 'root',
        cloneDestName: 'My Drive (root)',
        cloneFolderBrowserMode: false,  // true when folder browser was opened from Clone tab
        // Multi-link queue
        cloneLinks: [],          // parsed array of link strings
        cloneCurrentIndex: 0,   // index of current link being cloned
        cloneSuccessCount: 0,
        cloneErrorCount: 0,
        cloneRunning: false,     // true while any clone job is in progress
    },



    // ─── Init ──────────────────────────────────────────────────────────────────
    async init() {
        this._bindNav();
        this._bindBeforeUnload();
        await Promise.all([this._loadConfig(), this._checkStatus()]);
        this._initCreateTab();
        // Check credentials on first load — show alert if missing
        await this._checkCredsOnStartup();
    },

    /** Warn the user before closing tab/browser while a clone is running */
    _bindBeforeUnload() {
        window.addEventListener('beforeunload', (e) => {
            if (!this.state.cloneRunning) return;
            // Standard way to trigger browser's native confirmation dialog
            e.preventDefault();
            e.returnValue = 'Clone đang chạy! Nếu tắt bây giờ, quá trình sẽ bị hủy giữa chừng. Bạn chắc chắn muốn thoát?';
            return e.returnValue;
        });
    },

    _initCreateTab() {
        const nameInput = document.getElementById('folder-name');
        if (nameInput) nameInput.value = this._defaultFolderName();
        this.selectDuration(this.state.config.default_duration_hours || 24);
    },

    // ─── Navigation ────────────────────────────────────────────────────────────
    _bindNav() {
        document.querySelectorAll('.nav-item').forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });
    },

    switchTab(tab) {
        document.querySelectorAll('.nav-item').forEach(b =>
            b.classList.toggle('active', b.dataset.tab === tab)
        );
        document.querySelectorAll('.tab-panel').forEach(p =>
            p.classList.toggle('hidden', p.dataset.tab !== tab)
        );
        if (tab === 'list')     this.loadQueue();
        if (tab === 'settings') this._checkCredsFile();
    },

    // ─── Auth ──────────────────────────────────────────────────────────────────
    async _checkStatus() {
        try {
            const res  = await fetch('/api/status');
            const data = await res.json();
            this.state.authenticated = data.authenticated;
            this._updateAuthBadge();
            this._updateSettingsAuth(data.authenticated);
            if (data.authenticated) this._loadUserInfo();
        } catch (e) { console.error('Status check failed:', e); }
    },

    async _loadUserInfo() {
        try {
            const res  = await fetch('/api/userinfo');
            const data = await res.json();
            const el   = document.getElementById('user-display');
            if (el && (data.name || data.email)) {
                el.textContent = [data.name, data.email].filter(Boolean).join('  •  ');
            }
        } catch (_) {}
    },

    _updateAuthBadge() {
        const dot  = document.getElementById('status-dot');
        const text = document.getElementById('status-text');
        if (!dot || !text) return;
        if (this.state.authenticated) {
            dot.className  = 'status-dot connected';
            text.textContent = 'Đã kết nối';
        } else {
            dot.className  = 'status-dot disconnected';
            text.textContent = 'Chưa đăng nhập';
        }
    },

    _updateSettingsAuth(ok) {
        const statusEl  = document.getElementById('auth-status');
        const loginBtn  = document.getElementById('login-btn');
        const logoutBtn = document.getElementById('logout-btn');
        if (!statusEl) return;
        if (ok) {
            statusEl.innerHTML    = '<span style="color:var(--success)">✅ Đã đăng nhập</span>';
            if (loginBtn)  loginBtn.disabled  = true;
            if (logoutBtn) logoutBtn.disabled = false;
        } else {
            statusEl.innerHTML    = '<span style="color:var(--error)">❌ Chưa đăng nhập</span>';
            if (loginBtn)  loginBtn.disabled  = false;
            if (logoutBtn) logoutBtn.disabled = true;
        }
    },

    async login() {
        const btn      = document.getElementById('login-btn');
        const statusEl = document.getElementById('auth-status');

        btn.disabled     = true;
        btn.textContent  = '⏳ Đang chuẩn bị...';
        statusEl.innerHTML = '<span style="color:var(--subtext)">⏳ Đang kết nối Google...</span>';

        let authUrl = null;
        try {
            const res  = await fetch('/api/auth/login', { method: 'POST' });
            const data = await res.json();
            if (!data.ok) {
                statusEl.innerHTML = `<span style="color:var(--error)">❌ ${data.error || 'Lỗi không xác định'}</span>`;
                btn.disabled = false;
                btn.textContent = '🔑 Đăng nhập Google';
                return;
            }
            authUrl = data.auth_url;
        } catch (e) {
            statusEl.innerHTML = '<span style="color:var(--error)">❌ Không thể kết nối server</span>';
            btn.disabled = false;
            btn.textContent = '🔑 Đăng nhập Google';
            return;
        }

        // Open Google OAuth in a new tab — browser always has permission to do this
        if (authUrl) {
            window.open(authUrl, '_blank');
            btn.textContent = '⏳ Đang chờ đăng nhập...';
            statusEl.innerHTML = '<span style="color:var(--subtext)">⏳ Đã mở tab Google — đăng nhập rồi quay lại đây...</span>';
        }

        let attempts = 0;
        this.state.loginPollInterval = setInterval(async () => {
            attempts++;
            try {
                const res  = await fetch('/api/status');
                const data = await res.json();

                if (data.authenticated) {
                    clearInterval(this.state.loginPollInterval);
                    this.state.authenticated = true;
                    this._updateAuthBadge();
                    this._updateSettingsAuth(true);
                    statusEl.innerHTML = '<span style="color:var(--success)">✅ Đã đăng nhập thành công!</span>';
                    btn.textContent    = '🔑 Đăng nhập Google';
                    this._loadUserInfo();
                    this.showToast('✅ Đăng nhập thành công!', 'success');

                } else if (data.login_state === 'error') {
                    clearInterval(this.state.loginPollInterval);
                    statusEl.innerHTML = `<span style="color:var(--error)">❌ ${data.login_error || 'Đăng nhập thất bại'}</span>`;
                    btn.disabled   = false;
                    btn.textContent = '🔑 Đăng nhập Google';

                } else if (attempts > 60) {   // 2-minute timeout
                    clearInterval(this.state.loginPollInterval);
                    statusEl.innerHTML = '<span style="color:var(--error)">❌ Hết thời gian. Thử lại.</span>';
                    btn.disabled   = false;
                    btn.textContent = '🔑 Đăng nhập Google';
                }
            } catch (_) {}
        }, 2000);
    },

    async logout() {
        await fetch('/api/auth/logout', { method: 'POST' });
        this.state.authenticated = false;
        this._updateAuthBadge();
        this._updateSettingsAuth(false);
        const ud = document.getElementById('user-display');
        if (ud) ud.textContent = '';
        this.showToast('Đã đăng xuất', 'info');
    },

    // ─── Config ────────────────────────────────────────────────────────────────
    async _loadConfig() {
        try {
            const res = await fetch('/api/config');
            this.state.config = await res.json();

            const src = document.getElementById('src-folder-name');
            if (src) src.textContent = this.state.config.source_folder_name || 'My Drive';

            const dur = document.getElementById('default-duration');
            if (dur) dur.value = this.state.config.default_duration_hours || 24;

            const pfx = document.getElementById('folder-prefix');
            if (pfx) pfx.value = this.state.config.temp_folder_prefix || '';

            this.state.selectedDuration = this.state.config.default_duration_hours || 24;
        } catch (_) {}
    },

    async saveSettings() {
        const dur = parseInt(document.getElementById('default-duration').value) || 24;
        const pfx = document.getElementById('folder-prefix').value;

        await fetch('/api/config', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ default_duration_hours: dur, temp_folder_prefix: pfx }),
        });

        this.state.config.default_duration_hours = dur;
        this.state.config.temp_folder_prefix     = pfx;

        const msg = document.getElementById('save-msg');
        if (msg) {
            msg.textContent = '✅ Đã lưu!';
            setTimeout(() => { msg.textContent = ''; }, 2500);
        }
        this.showToast('✅ Đã lưu cài đặt!', 'success');
    },

    async _checkCredsFile() {
        try {
            const res  = await fetch('/api/creds-status');
            const data = await res.json();
            const el   = document.getElementById('creds-status');
            const btn  = document.getElementById('creds-browse-btn');
            if (!el) return;
            if (data.exists) {
                el.innerHTML = '<span style="color:var(--success)">✅ Đã có file credentials.json</span>';
                if (btn) btn.textContent = '🔄 Thay thế file';
            } else {
                el.innerHTML = '<span style="color:var(--error)">❌ Chưa có file credentials.json</span>';
                if (btn) btn.textContent = '📂 Chọn file credentials.json';
            }
        } catch (_) {}
    },

    async _checkCredsOnStartup() {
        try {
            const res  = await fetch('/api/creds-status');
            const data = await res.json();
            if (!data.exists) {
                this._showCredsModal();
            }
        } catch (_) {}
    },

    _showCredsModal() {
        const modal = document.getElementById('no-creds-modal');
        if (modal) modal.style.display = 'flex';
    },

    dismissCredsModal() {
        const modal = document.getElementById('no-creds-modal');
        if (modal) modal.style.display = 'none';
    },

    openCredsFromModal() {
        // Close modal, switch to settings tab, then trigger file picker
        this.dismissCredsModal();
        this.switchTab('settings');
        // Small delay to let tab render
        setTimeout(() => {
            const input = document.getElementById('creds-file-input');
            if (input) input.click();
        }, 150);
    },

    async uploadCredentials(inputEl) {
        const file = inputEl.files[0];
        if (!file) return;

        const hintEl = document.getElementById('creds-upload-hint');
        const btn    = document.getElementById('creds-browse-btn');

        if (hintEl) { hintEl.textContent = '⏳ Đang tải lên...'; hintEl.style.color = 'var(--subtext)'; }
        if (btn)    btn.disabled = true;

        try {
            const formData = new FormData();
            formData.append('file', file);

            const res  = await fetch('/api/upload-credentials', { method: 'POST', body: formData });
            const data = await res.json();

            if (data.ok) {
                if (hintEl) { hintEl.textContent = '✅ Đã lưu thành công!'; hintEl.style.color = 'var(--success)'; }
                this.showToast('✅ Credentials đã được cập nhật!', 'success');
                await this._checkCredsFile();
                // Also dismiss the no-creds modal if open
                this.dismissCredsModal();
            } else {
                if (hintEl) { hintEl.textContent = '❌ ' + (data.error || 'Lỗi không xác định'); hintEl.style.color = 'var(--error)'; }
                this.showToast('❌ ' + (data.error || 'Upload thất bại'), 'error');
            }
        } catch (e) {
            if (hintEl) { hintEl.textContent = '❌ ' + e.message; hintEl.style.color = 'var(--error)'; }
            this.showToast('❌ ' + e.message, 'error');
        } finally {
            if (btn) btn.disabled = false;
            // Reset input so same file can be re-selected
            inputEl.value = '';
        }
    },

    _defaultFolderName() {
        const now = new Date();
        const dd  = String(now.getDate()).padStart(2, '0');
        const mm  = String(now.getMonth() + 1).padStart(2, '0');
        const yy  = now.getFullYear();
        const hh  = String(now.getHours()).padStart(2, '0');
        const min = String(now.getMinutes()).padStart(2, '0');
        const pfx = this.state.config.temp_folder_prefix || 'Tài liệu Share Tạm - ';
        return `${pfx}${dd}/${mm}/${yy} ${hh}:${min}`;
    },

    // ─── Duration ──────────────────────────────────────────────────────────────
    selectDuration(hours) {
        this.state.selectedDuration = hours;
        document.querySelectorAll('.dur-btn').forEach(btn =>
            btn.classList.toggle('active', parseInt(btn.dataset.hours) === hours)
        );
    },

    _getDuration() {
        const custom = (document.getElementById('custom-hours').value || '').trim();
        if (custom) { const h = parseInt(custom); return h > 0 ? h : null; }
        return this.state.selectedDuration || 24;
    },

    // ─── Create Share ──────────────────────────────────────────────────────────
    async createShare() {
        if (!this.state.authenticated) {
            this.showToast('❌ Chưa đăng nhập. Vào tab Cài đặt để đăng nhập.', 'error');
            this.switchTab('settings');
            return;
        }
        const hours = this._getDuration();
        if (!hours) { this.showToast('❌ Vui lòng chọn thời hạn hợp lệ', 'error'); return; }

        const folderName = (document.getElementById('folder-name').value || '').trim();
        if (!folderName) { this.showToast('❌ Vui lòng nhập tên thư mục', 'error'); return; }

        const sourceId = this.state.config.source_folder_id || 'root';

        // ── UI: loading state ──
        const btn         = document.getElementById('create-btn');
        const progressArea = document.getElementById('progress-area');
        btn.disabled      = true;
        btn.textContent   = '⏳ Đang xử lý...';
        progressArea.style.display = 'block';

        // Reset
        document.getElementById('progress-bar-fill').style.width = '0%';
        document.getElementById('progress-msg').textContent = '';
        document.getElementById('progress-msg').style.color = 'var(--subtext)';
        document.getElementById('result-area').style.display = 'none';
        document.querySelectorAll('.step-item').forEach(s => s.classList.remove('done', 'active'));

        try {
            const response = await fetch('/api/share/create', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ folder_name: folderName, hours, source_folder_id: sourceId }),
            });

            const reader  = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try { this._handleProgress(JSON.parse(line.slice(6)), hours); } catch (_) {}
                    }
                }
            }
        } catch (e) {
            document.getElementById('progress-msg').textContent = `❌ ${e.message}`;
            document.getElementById('progress-msg').style.color = 'var(--error)';
            btn.disabled    = false;
            btn.textContent = '🚀 Tạo & Share ngay';
        }
    },

    _handleProgress(data, hours) {
        if (data.type === 'ping') return;

        const bar = document.getElementById('progress-bar-fill');
        const msg = document.getElementById('progress-msg');
        const btn = document.getElementById('create-btn');

        if (data.type === 'progress') {
            bar.style.width    = `${Math.round(data.pct * 100)}%`;
            msg.textContent    = data.msg;
            msg.style.color    = 'var(--subtext)';

            const step = typeof data.step === 'number' ? data.step : -1;
            document.querySelectorAll('.step-item').forEach((s, i) => {
                if      (i < step)  { s.classList.add('done');   s.classList.remove('active'); }
                else if (i === step){ s.classList.add('active'); s.classList.remove('done');   }
                else                { s.classList.remove('done', 'active'); }
            });

        } else if (data.type === 'done') {
            bar.style.width = '100%';
            msg.textContent = `✅ Hoàn tất! Sẽ tự xóa sau ${hours} giờ.`;
            msg.style.color = 'var(--success)';
            document.querySelectorAll('.step-item').forEach(s => {
                s.classList.add('done'); s.classList.remove('active');
            });
            document.getElementById('share-link').value = data.link;
            document.getElementById('result-area').style.display = 'flex';
            btn.disabled    = false;
            btn.textContent = '🚀 Tạo & Share ngay';
            document.getElementById('folder-name').value = this._defaultFolderName();
            this.showToast('🎉 Share đã sẵn sàng!', 'success');

        } else if (data.type === 'error') {
            msg.textContent = `❌ ${data.msg}`;
            msg.style.color = 'var(--error)';
            btn.disabled    = false;
            btn.textContent = '🚀 Tạo & Share ngay';
            this.showToast(`❌ ${data.msg}`, 'error');
        }
    },

    copyLink() {
        const link = document.getElementById('share-link').value;
        const btn  = document.getElementById('copy-btn');
        navigator.clipboard.writeText(link).then(() => {
            btn.textContent      = '✔ Đã copy!';
            btn.style.background = '#3A8C60';
            setTimeout(() => {
                btn.textContent      = '📋 Copy Link';
                btn.style.background = '';
            }, 2000);
        }).catch(() => this.showToast('Không thể copy link', 'error'));
    },

    // ─── Queue / List ──────────────────────────────────────────────────────────
    async loadQueue() {
        const container = document.getElementById('queue-list');
        const status    = document.getElementById('list-status');
        const btn       = document.getElementById('refresh-btn');

        status.textContent = '⏳ Đang tải...';
        btn.disabled       = true;

        if (!this.state.authenticated) {
            status.textContent    = '';
            container.innerHTML   = '<div class="empty-state">🔐 Vui lòng đăng nhập để xem danh sách</div>';
            btn.disabled          = false;
            return;
        }

        try {
            const res = await fetch('/api/queue');
            if (!res.ok) { const e = await res.json(); throw new Error(e.error || 'Lỗi tải dữ liệu'); }
            this.state.queue = await res.json();
            this._renderQueue();
            const now = new Date();
            status.textContent = `Cập nhật lúc ${now.toLocaleTimeString('vi-VN')} — ${this.state.queue.length} mục`;
        } catch (e) {
            status.textContent = `❌ ${e.message}`;
        } finally {
            btn.disabled = false;
        }
    },

    _renderQueue() {
        const container = document.getElementById('queue-list');

        if (this.state.countdownTimer) {
            clearInterval(this.state.countdownTimer);
            this.state.countdownTimer = null;
        }

        if (!this.state.queue.length) {
            container.innerHTML = '<div class="empty-state">🎉 Chưa có thư mục nào đang chia sẻ</div>';
            return;
        }

        container.innerHTML = this.state.queue.map(e => this._queueCardHtml(e)).join('');

        container.querySelectorAll('[data-action="delete"]').forEach(btn =>
            btn.addEventListener('click', () => this.deleteShare(btn.dataset.id, btn.dataset.name))
        );
        container.querySelectorAll('[data-action="open"]').forEach(btn =>
            btn.addEventListener('click', () => window.open(btn.dataset.url, '_blank'))
        );
        container.querySelectorAll('[data-action="copy"]').forEach(btn =>
            btn.addEventListener('click', () => {
                navigator.clipboard.writeText(btn.dataset.url);
                this.showToast('📋 Đã copy link!', 'success');
            })
        );

        this._startCountdown();
    },

    _queueCardHtml(entry) {
        const link    = `https://drive.google.com/drive/folders/${entry.folder_id}`;
        const created = new Date(entry.created_at);
        const local   = created.toLocaleString('vi-VN', {
            day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
        });
        return `
        <div class="queue-card"
             data-id="${entry.folder_id}"
             data-expires="${entry.expires_at}"
             data-created="${entry.created_at}">
            <div class="queue-card-header">
                <span class="queue-name">📁 ${this._esc(entry.folder_name)}</span>
                <span class="countdown" id="cd-${entry.folder_id}">--:--:--</span>
            </div>
            <div class="queue-progress">
                <div class="queue-progress-bar" id="bar-${entry.folder_id}" style="width:100%;background:var(--warn)"></div>
            </div>
            <div class="queue-card-footer">
                <span class="queue-created">Tạo lúc ${local}</span>
                <div class="queue-actions">
                    <button class="btn btn-sm btn-ghost"
                            data-action="copy" data-url="${link}">📋 Copy</button>
                    <button class="btn btn-sm btn-outline"
                            data-action="open" data-url="${link}">🔗 Mở link</button>
                    <button class="btn btn-sm btn-danger"
                            data-action="delete"
                            data-id="${entry.folder_id}"
                            data-name="${this._esc(entry.folder_name)}">🗑 Xóa</button>
                </div>
            </div>
        </div>`;
    },

    _startCountdown() {
        this.state.countdownTimer = setInterval(() => {
            const now = new Date();
            document.querySelectorAll('.queue-card').forEach(card => {
                const id      = card.dataset.id;
                const expires = new Date(card.dataset.expires);
                const created = new Date(card.dataset.created);
                const rem     = (expires - now) / 1000;
                const total   = Math.max((expires - created) / 1000, 1);
                const cdEl    = document.getElementById(`cd-${id}`);
                const barEl   = document.getElementById(`bar-${id}`);

                if (rem <= 0) {
                    if (cdEl) { cdEl.textContent = 'Hết hạn'; cdEl.style.color = 'var(--error)'; }
                    if (barEl){ barEl.style.width = '0%'; barEl.style.background = 'var(--error)'; }
                    return;
                }

                const h   = Math.floor(rem / 3600);
                const m   = Math.floor((rem % 3600) / 60);
                const s   = Math.floor(rem % 60);
                const pct = Math.min(100, Math.max(0, (rem / total) * 100));
                const col = rem < 3600 ? 'var(--error)' : rem < 21600 ? 'var(--warn)' : 'var(--success)';

                if (cdEl) {
                    cdEl.textContent = `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
                    cdEl.style.color = col;
                }
                if (barEl) {
                    barEl.style.width      = `${pct}%`;
                    barEl.style.background = col;
                }
            });
        }, 1000);
    },

    async deleteShare(folderId, folderName) {
        const card = document.querySelector(`.queue-card[data-id="${folderId}"]`);
        if (card) { card.style.opacity = '0.5'; card.style.pointerEvents = 'none'; }

        try {
            const res = await fetch(`/api/share/${folderId}`, { method: 'DELETE' });
            if (!res.ok) { const e = await res.json(); throw new Error(e.error || 'Lỗi khi xóa'); }

            if (card) {
                card.style.transition = 'all 0.3s ease';
                card.style.transform  = 'translateX(24px)';
                card.style.opacity    = '0';
                setTimeout(() => card.remove(), 320);
            }

            this.state.queue = this.state.queue.filter(e => e.folder_id !== folderId);

            if (!this.state.queue.length) {
                setTimeout(() => {
                    const c = document.getElementById('queue-list');
                    if (c && !c.querySelector('.queue-card'))
                        c.innerHTML = '<div class="empty-state">🎉 Chưa có thư mục nào đang chia sẻ</div>';
                }, 360);
            }
            this.showToast('🗑 Đã xóa thư mục!', 'success');

        } catch (e) {
            if (card) { card.style.opacity = '1'; card.style.pointerEvents = ''; }
            this.showToast(`❌ ${e.message}`, 'error');
        }
    },

    // ─── Folder Browser ────────────────────────────────────────────────────────
    openFolderBrowser() {
        if (!this.state.authenticated) { this.showToast('❌ Chưa đăng nhập', 'error'); this.switchTab('settings'); return; }
        this.state.cloneFolderBrowserMode = false;
        document.getElementById('folder-modal').style.display = 'flex';
        this.state.folderStack = [{ id: 'root', name: 'My Drive' }];
        this._loadFolderChildren('root');
    },

    closeFolderBrowser() {
        document.getElementById('folder-modal').style.display = 'none';
    },

    closeFolderBrowserOutside(e) {
        if (e.target === document.getElementById('folder-modal')) this.closeFolderBrowser();
    },

    async _loadFolderChildren(parentId) {
        const list = document.getElementById('folder-list');
        list.innerHTML = '<div class="folder-loading">⏳ Đang tải...</div>';
        this._updateBreadcrumb();

        try {
            const res     = await fetch(`/api/folders?parent=${encodeURIComponent(parentId)}`);
            const folders = await res.json();

            if (!Array.isArray(folders) || !folders.length) {
                list.innerHTML = '<div class="folder-empty">📂 Thư mục này không có subfolder</div>';
                return;
            }

            list.innerHTML = folders.map(f => `
                <div class="folder-item" data-id="${f.id}" data-name="${this._esc(f.name)}">
                    <span class="folder-icon">📁</span>
                    <span class="folder-name">${this._esc(f.name)}</span>
                    <span class="folder-chevron">›</span>
                </div>`).join('');

            list.querySelectorAll('.folder-item').forEach(item =>
                item.addEventListener('click', () => {
                    this.state.folderStack.push({ id: item.dataset.id, name: item.dataset.name });
                    this._loadFolderChildren(item.dataset.id);
                })
            );
        } catch (e) {
            list.innerHTML = `<div class="folder-error">❌ ${e.message}</div>`;
        }
    },

    _updateBreadcrumb() {
        const crumb = document.getElementById('folder-breadcrumb');
        crumb.innerHTML = this.state.folderStack.map((item, i) => {
            const isLast = i === this.state.folderStack.length - 1;
            return isLast
                ? `<span class="crumb-current">${this._esc(item.name)}</span>`
                : `<span class="crumb-item" data-idx="${i}">${this._esc(item.name)}</span><span class="crumb-sep">›</span>`;
        }).join('');

        crumb.querySelectorAll('.crumb-item').forEach(item =>
            item.addEventListener('click', () => {
                const idx = parseInt(item.dataset.idx);
                this.state.folderStack = this.state.folderStack.slice(0, idx + 1);
                this._loadFolderChildren(this.state.folderStack[idx].id);
            })
        );
    },

    selectCurrentFolder() {
        const current = this.state.folderStack[this.state.folderStack.length - 1];

        if (this.state.cloneFolderBrowserMode) {
            // Clone mode: save as destination, don't touch config
            this.state.cloneDestId   = current.id;
            this.state.cloneDestName = current.name;
            const label = document.getElementById('clone-dest-name');
            if (label) label.textContent = current.name;
            this.closeFolderBrowser();
            this.showToast(`📂 Đích: ${current.name}`, 'success');
            return;
        }

        fetch('/api/config', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ source_folder_id: current.id, source_folder_name: current.name }),
        });

        this.state.config.source_folder_id   = current.id;
        this.state.config.source_folder_name = current.name;

        const label = document.getElementById('src-folder-name');
        if (label) label.textContent = current.name;

        this.closeFolderBrowser();
        this.showToast(`📁 Đã chọn: ${current.name}`, 'success');
    },

    // ─── Clone ─────────────────────────────────────────────────────────────────
    async createCloneDest() {
        const nameInput = document.getElementById('clone-new-folder-name');
        const hint      = document.getElementById('clone-create-dest-hint');
        const btn       = document.getElementById('clone-create-dest-btn');
        const name      = (nameInput.value || '').trim();

        if (!name) {
            hint.textContent   = '⚠️ Vui lòng nhập tên thư mục';
            hint.style.color   = 'var(--warn)';
            hint.style.display = 'block';
            nameInput.focus();
            return;
        }
        if (!this.state.authenticated) {
            this.showToast('❌ Chưa đăng nhập', 'error');
            this.switchTab('settings');
            return;
        }

        btn.disabled    = true;
        btn.textContent = '⏳ Đang tạo...';
        hint.style.display = 'none';

        // Create under cloneDestId (current selected parent, defaults to root)
        try {
            const res  = await fetch('/api/folders', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({
                    name:      name,
                    parent_id: this.state.cloneDestId,
                }),
            });
            const data = await res.json();
            if (!res.ok || !data.ok) throw new Error(data.error || 'Lỗi tạo thư mục');

            const folder = data.folder;
            // Auto-select as destination
            this.state.cloneDestId   = folder.id;
            this.state.cloneDestName = folder.name;
            document.getElementById('clone-dest-name').textContent = '📁 ' + folder.name;

            nameInput.value    = '';
            btn.textContent    = '＋ Tạo & chọn';
            btn.disabled       = false;
            hint.textContent   = `✅ Đã tạo và chọn: ${folder.name}`;
            hint.style.color   = 'var(--success)';
            hint.style.display = 'block';
            setTimeout(() => { hint.style.display = 'none'; }, 3500);

            this.showToast(`📁 Đã tạo: ${folder.name}`, 'success');
        } catch (e) {
            btn.textContent    = '＋ Tạo & chọn';
            btn.disabled       = false;
            hint.textContent   = '❌ ' + e.message;
            hint.style.color   = 'var(--error)';
            hint.style.display = 'block';
            this.showToast('❌ ' + e.message, 'error');
        }
    },

    openCloneFolderBrowser() {
        if (!this.state.authenticated) { this.showToast('❌ Chưa đăng nhập', 'error'); this.switchTab('settings'); return; }
        this.state.cloneFolderBrowserMode = true;
        document.getElementById('folder-modal').style.display = 'flex';
        this.state.folderStack = [{ id: 'root', name: 'My Drive' }];
        this._loadFolderChildren('root');
    },

    // ─── Clone Link List Helpers ───────────────────────────────────────────────
    /** Parse textarea into valid, non-empty, non-comment lines */
    _parseCloneLinks() {
        const raw = (document.getElementById('clone-source-input').value || '');
        return raw.split('\n')
            .map(l => l.trim())
            .filter(l => l.length > 0 && !l.startsWith('#'));
    },

    /** Update the link-count badge next to the section label */
    _updateLinkCount() {
        const links = this._parseCloneLinks();
        const badge = document.getElementById('clone-link-count');
        if (!badge) return;
        badge.textContent = links.length + ' link';
        badge.classList.toggle('empty', links.length === 0);
    },

    /** Import links from a .txt file (appends to existing content) */
    importLinksFromFile(inputEl) {
        const file = inputEl.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            const text = e.target.result || '';
            const ta = document.getElementById('clone-source-input');
            if (!ta) return;
            const existing = ta.value.trimEnd();
            ta.value = existing ? existing + '\n' + text.trimEnd() : text.trimEnd();
            this._updateLinkCount();
            this.showToast('📂 Đã import ' + this._parseCloneLinks().length + ' link', 'success');
        };
        reader.readAsText(file);
        // Reset so same file can be re-selected
        inputEl.value = '';
    },

    /** Export current links to a .txt file */
    exportLinksToFile() {
        const links = this._parseCloneLinks();
        if (!links.length) {
            this.showToast('⚠️ Chưa có link nào để xuất', 'error');
            return;
        }
        const blob = new Blob([links.join('\n')], { type: 'text/plain;charset=utf-8' });
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = 'clone_links.txt';
        a.click();
        URL.revokeObjectURL(url);
        this.showToast('💾 Đã xuất ' + links.length + ' link', 'success');
    },

    /** Clear the textarea */
    clearCloneLinks() {
        const ta = document.getElementById('clone-source-input');
        if (ta) ta.value = '';
        this._updateLinkCount();
    },

    /**
     * Read clipboard and append links to the textarea + running queue.
     * Works both before and during a clone session.
     */
    async pasteMoreLinks() {
        let text = '';
        try {
            text = await navigator.clipboard.readText();
        } catch (e) {
            this.showToast('❌ Không đọc được clipboard: ' + e.message, 'error');
            return;
        }

        const newLinks = text.split('\n')
            .map(l => l.trim())
            .filter(l => l.length > 0 && !l.startsWith('#'));

        if (!newLinks.length) {
            this.showToast('⚠️ Clipboard không có link hợp lệ', 'error');
            return;
        }

        // Append to textarea
        const ta = document.getElementById('clone-source-input');
        if (ta) {
            const existing = ta.value.trimEnd();
            ta.value = existing ? existing + '\n' + newLinks.join('\n') : newLinks.join('\n');
        }
        this._updateLinkCount();

        // If clone is running, also push into the live queue
        if (this.state.cloneRunning) {
            this.state.cloneLinks.push(...newLinks);
            const added = newLinks.length;
            const remaining = this.state.cloneLinks.length - this.state.cloneCurrentIndex - 1;
            this._appendCloneLog(
                `➕ Đã thêm ${added} link vào hàng đợi (còn ${remaining} link chờ)`,
                'info'
            );
            this.showToast(`➕ Đã thêm ${added} link vào hàng đợi!`, 'success');
        } else {
            this.showToast(`📋 Đã paste ${newLinks.length} link`, 'success');
        }
    },


    async startClone() {
        if (!this.state.authenticated) {
            this.showToast('❌ Chưa đăng nhập. Vào tab Cài đặt để đăng nhập.', 'error');
            this.switchTab('settings');
            return;
        }

        const links = this._parseCloneLinks();
        if (!links.length) {
            this.showToast('❌ Vui lòng nhập ít nhất một link hoặc ID nguồn', 'error');
            return;
        }

        const btn       = document.getElementById('clone-btn');
        const logArea   = document.getElementById('clone-log-area');
        const logBox    = document.getElementById('clone-log-box');
        const statsCard = document.getElementById('clone-stats-card');
        const textarea  = document.getElementById('clone-source-input');
        const toolbar   = document.querySelector('.clone-link-toolbar');

        // Lock UI during clone
        btn.disabled            = true;
        btn.textContent         = '⏳ Đang clone...';
        logArea.style.display   = 'block';
        logBox.innerHTML        = '';
        statsCard.style.display = 'none';
        if (textarea) textarea.readOnly = true;
        // Only lock buttons with the lockable class — Paste button stays active
        document.querySelectorAll('.clone-toolbar-lockable').forEach(b => b.disabled = true);

        // Reset multi-link state
        this.state.cloneLinks        = links;
        this.state.cloneCurrentIndex = 0;
        this.state.cloneSuccessCount = 0;
        this.state.cloneErrorCount   = 0;
        this.state.cloneRunning      = true;   // ← guard beforeunload

        const autoFolderInput = document.getElementById('clone-auto-folder');
        const autoFolder = autoFolderInput ? autoFolderInput.checked : false;

        try {
            await this._runCloneQueue(links, autoFolder, btn, statsCard);
        } finally {
            // Unlock UI — always runs even if an unexpected error is thrown
            this.state.cloneRunning = false;   // ← release beforeunload guard
            if (textarea) textarea.readOnly = false;
            document.querySelectorAll('.clone-toolbar-lockable').forEach(b => b.disabled = false);

            btn.disabled    = false;
            btn.textContent = '🚀 Bắt đầu Clone';
        }
    },


    /**
     * Clone a list of links sequentially.
     * Shows a per-link header, continues even if one fails, then shows a summary.
     */
    async _runCloneQueue(links, autoFolder, btn, statsCard) {
        // NOTE: this.state.cloneLinks may grow mid-run via pasteMoreLinks()
        // Use index-based while loop so new links are picked up automatically.
        let i = 0;

        while (i < this.state.cloneLinks.length) {
            this.state.cloneCurrentIndex = i;
            const link  = this.state.cloneLinks[i];
            const total = this.state.cloneLinks.length; // snapshot for display only

            // ── Per-link header ──
            this._appendCloneQueueHeader(`📥 Clone [${i + 1}/${total}]: ${link}`);
            if (total > 1) {
                this._appendCloneLog('📂 Đích: ' + this.state.cloneDestName, 'info');
                this._appendCloneLog('─'.repeat(48), 'dim');
            }

            // Reset per-job state
            this.state.cloneJobId = null;
            this.state.cloneDone  = false;

            const payload = {
                source_id:      link,
                dest_folder_id: this.state.cloneDestId,
                auto_folder:    autoFolder,
            };

            let linkSuccess = false;
            try {
                await this._streamClone('/api/clone', 'POST', payload, btn, statsCard);
                linkSuccess = this.state.cloneDone;
            } catch (e) {
                this._appendCloneLog('❌ Lỗi kết nối: ' + e.message, 'error');
            }

            if (linkSuccess) {
                this.state.cloneSuccessCount++;
            } else {
                this.state.cloneErrorCount++;
            }

            i++;

            // Separator if more links remain (including newly added ones)
            if (i < this.state.cloneLinks.length) {
                this._appendCloneLog('', 'dim');
            }
        }

        // ── Final summary ──
        const finalTotal = this.state.cloneLinks.length;
        if (finalTotal > 1) {
            const ok  = this.state.cloneSuccessCount;
            const err = this.state.cloneErrorCount;
            const summaryEl = document.createElement('div');
            summaryEl.className = 'clone-queue-summary';
            summaryEl.textContent = `✅ Hoàn tất ${ok}/${finalTotal} link${err ? ' — ❌ ' + err + ' lỗi' : ''}`;
            const box = document.getElementById('clone-log-box');
            if (box) { box.appendChild(summaryEl); box.scrollTop = box.scrollHeight; }

            if (ok > 0) {
                this.showToast(`🎉 Clone xong ${ok}/${finalTotal} link!`, 'success');
            } else {
                this.showToast('❌ Tất cả link đều thất bại', 'error');
            }
        }
    },


    /** Append a styled queue-header line to the log box */
    _appendCloneQueueHeader(text) {
        const box = document.getElementById('clone-log-box');
        if (!box) return;
        const el = document.createElement('div');
        el.className = 'clone-queue-header';
        el.textContent = text;
        box.appendChild(el);
        box.scrollTop = box.scrollHeight;
    },

    async _streamClone(url, method, payload, btn, statsCard) {
        const MAX_RECONNECT_DELAY = 30000;  // ms
        let reconnectDelay = 2000;
        let isFirstConnect = true;

        const doStream = async (streamUrl, streamMethod, streamPayload) => {
            const opts = {
                method:  streamMethod,
                headers: { 'Content-Type': 'application/json' },
            };
            if (streamPayload) opts.body = JSON.stringify(streamPayload);

            const response = await fetch(streamUrl, opts);
            if (!response.ok) {
                const err = await response.json().catch(() => ({ error: 'Network error' }));
                throw new Error(err.error || 'HTTP ' + response.status);
            }

            const reader  = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';
                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;
                    let evt;
                    try { evt = JSON.parse(line.slice(6)); } catch (_) { continue; }
                    if (evt.type === 'ping') continue;

                    // Reset reconnect delay on successful data
                    reconnectDelay = 2000;

                    if (evt.type === 'job_id') {
                        this.state.cloneJobId = evt.job_id;

                    } else if (evt.type === 'log') {
                        this._appendCloneLog(evt.msg);

                    } else if (evt.type === 'quota_wait') {
                        this._appendCloneLog(evt.msg || ('⏳ Quota exceeded — chờ ' + evt.seconds + 's...'), 'info');
                        this._startQuotaCountdown(evt.seconds);

                    } else if (evt.type === 'quota_tick') {
                        this._updateQuotaCountdown(evt.remaining);

                    } else if (evt.type === 'done') {
                        this.state.cloneDone = true;
                        this._clearQuotaCountdown();
                        this._appendCloneLog('─'.repeat(48), 'dim');
                        this._appendCloneLog('🎉 HOÀN THÀNH!', 'success');
                        const s = evt.stats || {};
                        document.getElementById('stat-copied').textContent  = s.copied  ?? 0;
                        document.getElementById('stat-skipped').textContent = s.skipped ?? 0;
                        document.getElementById('stat-folders').textContent = s.folders_created ?? 0;
                        document.getElementById('stat-errors').textContent  = s.errors  ?? 0;
                        statsCard.style.display = 'grid';
                        // Single-link mode: show toast here; multi-link: _runCloneQueue handles it
                        if (this.state.cloneLinks.length <= 1) {
                            this.showToast('🎉 Clone hoàn tất!', 'success');
                        }
                        return true;  // finished

                    } else if (evt.type === 'error') {
                        this.state.cloneDone = true;
                        this._clearQuotaCountdown();
                        this._appendCloneLog('❌ Lỗi: ' + evt.msg, 'error');
                        if (this.state.cloneLinks.length <= 1) {
                            this.showToast('❌ ' + evt.msg, 'error');
                        }
                        return true;  // finished (with error)
                    }
                }
            }
            return false;  // stream ended but not finished
        };

        // First connection
        try {
            const finished = await doStream(url, method, payload);
            if (finished || this.state.cloneDone) return;
        } catch (e) {
            this._appendCloneLog('❌ ' + e.message, 'error');
            return;
        }

        // Auto-reconnect loop (stream dropped without done/error)
        while (!this.state.cloneDone) {
            const jobId = this.state.cloneJobId;
            if (!jobId) break;

            this._appendCloneLog(`🔄 Mất kết nối. Đang kết nối lại sau ${reconnectDelay / 1000}s...`, 'info');
            await new Promise(r => setTimeout(r, reconnectDelay));
            reconnectDelay = Math.min(reconnectDelay * 2, MAX_RECONNECT_DELAY);

            try {
                const finished = await doStream(`/api/clone/${jobId}/stream`, 'GET', null);
                if (finished || this.state.cloneDone) return;
            } catch (e) {
                this._appendCloneLog(`⚠️ Reconnect thất bại: ${e.message}`, 'error');
            }
        }
    },


    _startQuotaCountdown(seconds) {
        // Show a countdown badge in the log box header
        const box = document.getElementById('clone-log-box');
        if (!box) return;
        let badge = document.getElementById('clone-quota-badge');
        if (!badge) {
            badge = document.createElement('div');
            badge.id = 'clone-quota-badge';
            badge.className = 'clone-quota-badge';
            box.parentNode.insertBefore(badge, box);
        }
        badge.textContent = `⏳ Quota — tiếp tục sau ${seconds}s`;
        badge.style.display = 'block';
    },

    _updateQuotaCountdown(remaining) {
        const badge = document.getElementById('clone-quota-badge');
        if (badge && remaining > 0) {
            badge.textContent = `⏳ Quota — tiếp tục sau ${remaining}s`;
        } else if (badge && remaining === 0) {
            badge.textContent = '▶ Đang tiếp tục...';
        }
    },

    _clearQuotaCountdown() {
        const badge = document.getElementById('clone-quota-badge');
        if (badge) badge.style.display = 'none';
    },

    _appendCloneLog(msg, type = 'normal') {
        const box  = document.getElementById('clone-log-box');
        if (!box) return;
        const line = document.createElement('div');
        line.className = 'clone-log-line clone-log-' + type;
        line.textContent = msg;
        box.appendChild(line);
        box.scrollTop = box.scrollHeight;
    },

    // ─── Toast ─────────────────────────────────────────────────────────────────
    showToast(msg, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast     = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = msg;
        container.appendChild(toast);
        requestAnimationFrame(() => requestAnimationFrame(() => toast.classList.add('show')));
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 350);
        }, 3200);
    },

    // ─── Utils ─────────────────────────────────────────────────────────────────
    _esc(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    },
};

document.addEventListener('DOMContentLoaded', () => App.init());
