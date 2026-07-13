// site/js/render.js
// Three-zone rendering: discovery, tool overview, search table
// Virtual scroll for table, detail panel, report rendering
const SIC_render = {
  PAGE_SIZE: 50,
  currentPage: 0,
  renderedCount: 0,
  currentFiltered: [],

  $: id => document.getElementById(id),
  esc: s => String(s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),
  safeUrl: raw => { try { const u = new URL(String(raw||''), location.href); if (['http:','https:'].includes(u.protocol)) return u.href; } catch(_){} return '#'; },
  pills: xs => (xs||[]).map(x => `<span class="pill">${SIC_render.esc(x)}</span>`).join(''),
  safeNum: v => { const n = Number(v); return Number.isFinite(n) ? String(n) : '0'; },

  renderAll() {
    SIC_i18n.applyLanguage();
    this.renderMetrics();
    this.renderDiscovery();
    this.renderToolOverview();
    this.renderSearchZone();
    SIC_filters.writeState();
  },

  renderMetrics() {
    const m = SIC_data.metrics;
    const keys = ['projects', 'curated', 'rejected', 'official_tools', 'ecosystem_projects'];
    this.$('metrics').innerHTML = keys.map(k =>
      `<div class="stat"><b>${this.safeNum(m[k] ?? 0)}</b><br><span class="muted">${SIC_i18n.t('metrics')[k]}</span></div>`
    ).join('');
  },

  renderDiscovery() {
    // Show projects added in last 7 days, sorted by score, top 12
    const now = new Date();
    const cutoff = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
    const recent = SIC_data.projects
      .filter(p => (p.first_seen || p.last_seen || '') >= cutoff && p.tracking_priority !== 'reject')
      .sort((a, b) => (b.total_score || 0) - (a.total_score || 0))
      .slice(0, 12);

    if (recent.length === 0) {
      this.$('discovery').innerHTML = `<p class="hint">${SIC_i18n.t('discoveryHint')}</p>`;
      return;
    }

    this.$('discovery').innerHTML = recent.map(p => `
      <div class="discovery-card" onclick="SIC_render.openDetail('${this.esc(p.id)}')">
        <span class="score-badge">${this.safeNum(p.total_score)}</span>
        <b>${this.esc(SIC_i18n.textOf(p, 'name'))}</b><br>
        <span class="muted">${this.esc((SIC_i18n.textOf(p, 'summary') || '').slice(0, 80))}</span><br>
        ${this.pills(p.resource_type)}
      </div>
    `).join('');
  },

  renderToolOverview() {
    const tools = SIC_data.tools.filter(t => t.id !== 'general-ai-coding');
    this.$('toolOverview').innerHTML = tools.map(t => {
      const count = SIC_data.projects.filter(p =>
        (p.target_tools || []).includes(t.id) && p.tracking_priority !== 'reject'
      ).length;
      const curated = SIC_data.curated.filter(p => (p.target_tools || []).includes(t.id)).length;
      return `
        <div class="tool-card" onclick="SIC_filters.selectedTools.clear(); SIC_filters.selectedTools.add('${this.esc(t.id)}'); SIC_render.renderSearchZone(); document.getElementById('searchZone').scrollIntoView();">
          <h3>${this.esc(SIC_i18n.textOf(t, 'name') || t.name)}</h3>
          <div class="tool-stats">${count} ${SIC_i18n.lang === 'zh' ? '个项目' : ' projects'} · ${curated} ${SIC_i18n.lang === 'zh' ? '推荐' : ' curated'}</div>
        </div>
      `;
    }).join('');
  },

  renderSearchZone() {
    const curatedIds = SIC_data.curatedIds();
    this.currentFiltered = SIC_filters.apply(SIC_data.projects, curatedIds);
    this.currentPage = 0;
    this.renderedCount = 0;
    this.$('rows').innerHTML = '';

    if (this.currentFiltered.length === 0) {
      this.$('rows').innerHTML = `<tr><td colspan="6" class="empty-box">${SIC_i18n.t('noResults')}<br><span class="muted">${SIC_i18n.t('adjustFilter')}</span></td></tr>`;
      return;
    }

    this.renderMore();
  },

  renderMore() {
    const start = this.renderedCount;
    const end = Math.min(start + this.PAGE_SIZE, this.currentFiltered.length);
    const curatedIds = SIC_data.curatedIds();
    const html = this.currentFiltered.slice(start, end).map(p => {
      const isFav = SIC_data.isFav(p.id);
      const isCurated = curatedIds.has(p.id);
      return `<tr>
        <td>
          <b>${this.esc(SIC_i18n.textOf(p, 'name'))}</b><br>
          <span class="muted">${this.esc((SIC_i18n.textOf(p, 'summary') || '').slice(0, 100))}</span>
        </td>
        <td>${this.pills(p.resource_type)}</td>
        <td>${this.esc((p.target_tools || []).join(', '))}</td>
        <td><b>${this.safeNum(p.total_score)}</b></td>
        <td>${this.safeNum(p.stars)}</td>
        <td>
          <a href="${this.safeUrl(p.url)}" target="_blank" rel="noopener noreferrer">${SIC_i18n.t('open')}</a>
          <button class="fav-btn ${isFav ? 'active' : ''}" onclick="SIC_render.toggleFav('${this.esc(p.id)}', this)">★</button>
          ${isCurated ? `<span class="pill">${SIC_i18n.t('curated')}</span>` : ''}
          <button onclick="SIC_render.openDetail('${this.esc(p.id)}')">${SIC_i18n.t('details')}</button>
        </td>
      </tr>`;
    }).join('');
    this.$('rows').insertAdjacentHTML('beforeend', html);
    this.renderedCount = end;

    // Show "load more" or use IntersectionObserver
    if (this.renderedCount < this.currentFiltered.length) {
      if (!this._observer) {
        this._observer = new IntersectionObserver(entries => {
          if (entries[0].isIntersecting && this.renderedCount < this.currentFiltered.length) {
            this.renderMore();
          }
        });
      }
      // Observe the last row
      const lastRow = this.$('rows').lastElementChild;
      if (lastRow) this._observer.observe(lastRow);
    }
  },

  // Detail panel
  async openDetail(projectId) {
    const p = SIC_data.projects.find(x => x.id === projectId);
    if (!p) return;
    const detail = await SIC_data.loadDetail(projectId);
    const overlay = this.$('detailOverlay');
    const curatedIds = SIC_data.curatedIds();
    const isFav = SIC_data.isFav(p.id);
    const qScore = p.quantifiable_score || 0;
    const qualityScore = p.quality_score || 0;
    const total = p.total_score || 0;

    overlay.innerHTML = `
      <button class="detail-close" onclick="SIC_render.closeDetail()">&times;</button>
      <h2>${this.esc(SIC_i18n.textOf(p, 'name'))}</h2>
      <p class="muted">${this.esc(SIC_i18n.textOf(p, 'summary') || '')}</p>

      <div class="detail-section">
        <h3>${SIC_i18n.t('scoreDetail')}</h3>
        <div style="display:flex;gap:12px;align-items:center;margin-bottom:8px;">
          <span class="score-badge" style="font-size:20px;padding:4px 12px;background:var(--color-accent);color:white;border-radius:8px;">${this.safeNum(total)}</span>
          <span class="muted">/ 100</span>
        </div>
        <div style="margin-bottom:6px;">${SIC_i18n.t('quantifiable')}: ${this.safeNum(qScore)}/60
          <div class="score-bar"><div class="score-bar-fill" style="width:${qScore/60*100}%"></div></div>
        </div>
        <div>${SIC_i18n.t('quality')}: ${this.safeNum(qualityScore)}/40
          <div class="score-bar"><div class="score-bar-fill" style="width:${qualityScore/40*100}%"></div></div>
        </div>
      </div>

      <div class="detail-section">
        <h3>${SIC_i18n.t('details')}</h3>
        <p>${this.pills(p.resource_type)}</p>
        <p>${this.esc((p.target_tools || []).join(', '))}</p>
        <p class="muted">Stars: ${this.safeNum(p.stars)} · Forks: ${this.safeNum(p.forks)}</p>
        <p class="muted">License: ${this.esc(p.license || 'N/A')}</p>
        <p class="muted">Languages: ${this.esc((p.languages || []).join(', '))}</p>
        <p class="muted">First seen: ${this.esc(p.first_seen)} · Last seen: ${this.esc(p.last_seen)}</p>
        <p class="muted">Tracking: ${this.esc(p.tracking_priority)}</p>
      </div>

      ${detail?.llm_summary ? `<div class="detail-section"><h3>LLM Summary</h3><p>${this.esc(SIC_i18n.textOf(detail, 'llm_summary') || '')}</p></div>` : ''}

      ${detail?.benchmark_ref ? `<div class="detail-section"><h3>${SIC_i18n.t('benchmarkRef')}</h3><p class="muted">${this.esc(detail.benchmark_ref)}</p></div>` : ''}

      <div class="detail-section">
        <h3>${SIC_i18n.t('relatedProjects')}</h3>
        <div id="relatedProjects">...</div>
      </div>

      <div class="detail-section">
        <a href="${this.safeUrl(p.url)}" target="_blank" rel="noopener noreferrer">${SIC_i18n.t('open')} -></a>
        <button class="fav-btn ${isFav ? 'active' : ''}" onclick="SIC_render.toggleFav('${this.esc(p.id)}', this)">${isFav ? SIC_i18n.t('favorited') : SIC_i18n.t('favorite')}</button>
      </div>
    `;
    overlay.classList.add('open');

    // Load related projects (same resource_type or shared tools)
    const related = SIC_data.projects
      .filter(x => x.id !== p.id && x.tracking_priority !== 'reject')
      .filter(x => {
        const sharedType = (x.resource_type || []).some(rt => (p.resource_type || []).includes(rt));
        const sharedTool = (x.target_tools || []).some(tt => (p.target_tools || []).includes(tt));
        return sharedType || sharedTool;
      })
      .sort((a, b) => (b.total_score || 0) - (a.total_score || 0))
      .slice(0, 5);
    const relatedEl = document.getElementById('relatedProjects');
    if (relatedEl) {
      relatedEl.innerHTML = related.length ? related.map(r =>
        `<div style="margin-bottom:6px;"><a href="javascript:void(0)" onclick="SIC_render.openDetail('${this.esc(r.id)}')">${this.esc(SIC_i18n.textOf(r, 'name'))}</a> <span class="muted">(${this.safeNum(r.total_score)})</span></div>`
      ).join('') : '<span class="muted">N/A</span>';
    }
  },

  closeDetail() {
    this.$('detailOverlay').classList.remove('open');
  },

  toggleFav(id, btn) {
    SIC_data.toggleFav(id);
    if (btn) btn.classList.toggle('active');
  },

  // Report rendering (simple markdown to HTML)
  renderReport(md) {
    let html = this.esc(md);
    // Headers
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
    // Tables
    html = html.replace(/^\|(.+)\|$/gm, (match) => {
      const cells = match.split('|').filter(c => c.trim());
      if (cells.every(c => /^[\s-]+$/.test(c))) return ''; // separator row
      return '<tr>' + cells.map(c => `<td>${c.trim()}</td>`).join('') + '</tr>';
    });
    html = html.replace(/(<tr>[\s\S]*?<\/tr>)/g, '<table>$1</table>');
    // Code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    // Line breaks
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<div class="report-content"><p>' + html + '</p></div>';
    return html;
  },

  // Skeleton screen
  showSkeleton() {
    this.$('metrics').innerHTML = [1,2,3,4,5].map(() => '<div class="stat skeleton skeleton-row" style="width:100px;height:60px;"></div>').join('');
    this.$('discovery').innerHTML = [1,2,3].map(() => '<div class="discovery-card skeleton" style="height:100px;"></div>').join('');
    this.$('toolOverview').innerHTML = [1,2,3,4].map(() => '<div class="tool-card skeleton" style="height:80px;"></div>').join('');
    this.$('rows').innerHTML = [1,2,3,4,5].map(() => `<tr><td colspan="6"><div class="skeleton skeleton-row"></div></td></tr>`).join('');
  },

  // Error state
  showError() {
    this.$('rows').innerHTML = `<tr><td colspan="6" class="error-box">
      ${SIC_i18n.t('loadError')}<br>
      <button onclick="location.reload()">${SIC_i18n.t('retry')}</button>
    </td></tr>`;
  },
};
