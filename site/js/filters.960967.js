// site/js/filters.js
// Multi-select tag button filters, OR/AND toggle, 6 sort modes, URL state
const SIC_filters = {
  selectedTools: new Set(),   // selected tool IDs
  selectedTypes: new Set(),   // selected resource_type values
  searchQuery: '',
  sortBy: 'score',
  matchMode: 'or',            // 'or' or 'and'
  curatedOnly: false,
  recentOnly: false,

  toggleTool(id) {
    if (this.selectedTools.has(id)) this.selectedTools.delete(id);
    else this.selectedTools.add(id);
  },
  toggleType(type) {
    if (this.selectedTypes.has(type)) this.selectedTypes.delete(type);
    else this.selectedTypes.add(type);
  },
  toggleMode() {
    this.matchMode = this.matchMode === 'or' ? 'and' : 'or';
  },

  apply(projects, curatedIds) {
    let rows = projects.filter(p => {
      // Exclude rejected and official-seed from search results
      if (p.source_type === 'official-seed') return false;
      if (p.tracking_priority === 'reject') return false;

      // Search query
      if (this.searchQuery) {
        const q = this.searchQuery.toLowerCase();
        const text = JSON.stringify(p).toLowerCase();
        if (!text.includes(q)) return false;
      }

      // Tool filter
      if (this.selectedTools.size > 0) {
        const pTools = p.target_tools || [];
        if (this.matchMode === 'and') {
          if (![...this.selectedTools].every(t => pTools.includes(t))) return false;
        } else {
          if (![...this.selectedTools].some(t => pTools.includes(t))) return false;
        }
      }

      // Resource type filter
      if (this.selectedTypes.size > 0) {
        const pTypes = p.resource_type || [];
        if (this.matchMode === 'and') {
          if (![...this.selectedTypes].every(t => pTypes.includes(t))) return false;
        } else {
          if (![...this.selectedTypes].some(t => pTypes.includes(t))) return false;
        }
      }

      // Curated only
      if (this.curatedOnly && !curatedIds.has(p.id)) return false;

      return true;
    });

    // Sort
    rows.sort((a, b) => {
      switch (this.sortBy) {
        case 'name': return SIC_i18n.textOf(a, 'name').localeCompare(SIC_i18n.textOf(b, 'name'));
        case 'stars': return (b.stars || 0) - (a.stars || 0);
        case 'updated': return String(b.last_updated || '').localeCompare(String(a.last_updated || ''));
        case 'recent': return String(b.first_seen || b.last_seen || '').localeCompare(String(a.first_seen || a.last_seen || ''));
        case 'match': {
          // Tag match count descending, then score
          const aMatch = this._matchCount(a);
          const bMatch = this._matchCount(b);
          if (bMatch !== aMatch) return bMatch - aMatch;
          return (b.total_score || 0) - (a.total_score || 0);
        }
        default: return (b.total_score || 0) - (a.total_score || 0); // 'score'
      }
    });

    return rows;
  },

  _matchCount(p) {
    let count = 0;
    const pTools = p.target_tools || [];
    const pTypes = p.resource_type || [];
    for (const t of this.selectedTools) if (pTools.includes(t)) count++;
    for (const t of this.selectedTypes) if (pTypes.includes(t)) count++;
    return count;
  },

  // URL state
  readState() {
    const qs = new URLSearchParams(location.search);
    if (qs.get('q')) this.searchQuery = qs.get('q');
    if (qs.get('tools')) qs.get('tools').split(',').forEach(t => this.selectedTools.add(t));
    if (qs.get('types')) qs.get('types').split(',').forEach(t => this.selectedTypes.add(t));
    if (qs.get('sort')) this.sortBy = qs.get('sort');
    if (qs.get('mode')) this.matchMode = qs.get('mode');
    if (qs.get('curated') === '1') this.curatedOnly = true;
    if (qs.get('recent') === '1') this.recentOnly = true;
    // Favorites from hash
    if (location.hash.startsWith('#favorites=')) {
      const ids = location.hash.slice(12).split(',').filter(Boolean);
      ids.forEach(id => SIC_data.favorites.add(id));
      localStorage.setItem('sic_favorites', JSON.stringify([...SIC_data.favorites]));
    }
  },

  writeState() {
    const qs = new URLSearchParams();
    if (this.searchQuery) qs.set('q', this.searchQuery);
    if (this.selectedTools.size) qs.set('tools', [...this.selectedTools].join(','));
    if (this.selectedTypes.size) qs.set('types', [...this.selectedTypes].join(','));
    if (this.sortBy !== 'score') qs.set('sort', this.sortBy);
    if (this.matchMode === 'and') qs.set('mode', 'and');
    if (this.curatedOnly) qs.set('curated', '1');
    if (this.recentOnly) qs.set('recent', '1');
    history.replaceState(null, '', `${location.pathname}${qs.toString() ? '?' + qs : ''}`);
  },
};
