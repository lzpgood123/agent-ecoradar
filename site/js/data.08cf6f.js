// site/js/data.js
// Data loading (progressive fetch), state management, favorites
// Batch 2: search-index Map + detail shards (no monolithic projects-detail.json)
const SIC_data = {
  projects: [], curated: [], tools: [], metrics: {},
  projectDetails: {}, // lazy-loaded detail data by project id
  searchMap: {},      // id -> lightweight search text
  _detailIndex: null, // project_id -> chunk index
  _detailIndexLoading: null,
  favorites: new Set(JSON.parse(localStorage.getItem('sic_favorites') || '[]')),
  loadError: false,

  async loadAll(onProgress) {
    this.loadError = false;
    try {
      // Progressive: metrics first (1KB), then tools/projects/curated, then search-index
      this.metrics = await this.fetchJSON('data/metrics.json', onProgress, 'metrics');
      this.tools = await this.fetchJSON('data/tools.json', onProgress, 'tools');
      this.projects = await this.fetchJSON('data/projects.json', onProgress, 'projects');
      this.curated = await this.fetchJSON('data/curated-projects.json', onProgress, 'curated');
      const searchIndex = await this.fetchJSON('data/search-index.json', onProgress, 'search-index');
      this.searchMap = {};
      for (const e of searchIndex || []) {
        if (e && e.id != null) this.searchMap[e.id] = e.text || '';
      }
    } catch (e) {
      console.error('Data load error:', e);
      this.loadError = true;
    }
    return !this.loadError;
  },

  async fetchJSON(url, onProgress, label) {
    if (onProgress) onProgress(label);
    const r = await fetch(url);
    if (!r.ok) throw new Error(`HTTP ${r.status} for ${url}`);
    return r.json();
  },

  async _ensureDetailIndex() {
    if (this._detailIndex) return this._detailIndex;
    if (this._detailIndexLoading) return this._detailIndexLoading;
    this._detailIndexLoading = this.fetchJSON('data/detail-index.json')
      .then((idx) => {
        this._detailIndex = idx || {};
        return this._detailIndex;
      })
      .catch((e) => {
        console.error('Detail index load error:', e);
        this._detailIndex = {};
        return this._detailIndex;
      })
      .finally(() => {
        this._detailIndexLoading = null;
      });
    return this._detailIndexLoading;
  },

  async loadDetail(projectId) {
    // Cache hit
    if (this.projectDetails[projectId]) return this.projectDetails[projectId];

    try {
      const index = await this._ensureDetailIndex();
      const chunkIdx = index[projectId];
      if (chunkIdx === undefined || chunkIdx === null) return null;

      // No monolithic projects-detail.json fallback (batch 2)
      const chunk = await this.fetchJSON(`data/detail/${chunkIdx}.json`);
      if (Array.isArray(chunk)) {
        for (const d of chunk) {
          if (d && d.id != null) this.projectDetails[d.id] = d;
        }
      }
      return this.projectDetails[projectId] || null;
    } catch (e) {
      console.error('Detail load error:', e);
      return null;
    }
  },

  // Favorites
  isFav(id) { return this.favorites.has(id); },
  toggleFav(id) {
    if (this.favorites.has(id)) this.favorites.delete(id);
    else this.favorites.add(id);
    localStorage.setItem('sic_favorites', JSON.stringify([...this.favorites]));
  },
  getFavorites() {
    return this.projects.filter(p => this.favorites.has(p.id));
  },
  exportFavoritesUrl() {
    const ids = [...this.favorites];
    return `${location.origin}${location.pathname}#favorites=${ids.join(',')}`;
  },

  // Curated IDs set
  curatedIds() { return new Set(this.curated.map(p => p.id)); },
};
