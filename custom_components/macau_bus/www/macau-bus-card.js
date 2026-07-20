class MacauBusCard extends HTMLElement {
  static getStubConfig() {
    return { entity: "sensor.macau_bus" };
  }

  setConfig(config) {
    if (!config.entity) throw new Error("請設定實體 ID");
    this._config = config;
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._config) this.render();
  }

  render() {
    if (!this._hass || !this._config) return;
    const entity = this._hass.states[this._config.entity];
    if (!entity) { this.innerHTML = `<ha-card><div class="card-content">找不到實體 ${this._config.entity}</div></ha-card>`; return; }

    const stops = entity.attributes.nearbyStops || [];
    const routes = entity.attributes.routes || [];
    const ts = entity.attributes.timestamp || "";
    const uLat = entity.attributes.user_lat;
    const uLon = entity.attributes.user_lon;

    this.innerHTML = `
      <ha-card>
        <div class="card-content">
          <style>
            .mb-table { width: 100%; border-collapse: collapse; }
            .mb-table td, .mb-table th { text-align: left; padding: 6px 4px; }
            .mb-table th { font-size: 0.8em; color: var(--secondary-text-color); border-bottom: 1px solid var(--divider-color); }
            .mb-badge {
              display: inline-block; min-width: 2.2em; text-align: center;
              padding: 2px 8px; border-radius: 4px; font-weight: bold;
              font-size: 0.9em;
            }
            .mb-c-o { background: #e8a41a; color: #000; }
            .mb-c-b { background: #4a90d9; color: #fff; }
            .mb-c-g { background: #4caf50; color: #fff; }
            .mb-plate { font-size: 0.75em; color: var(--secondary-text-color); }
            .mb-info { font-size: 0.8em; color: var(--secondary-text-color); margin-bottom: 4px; }
            .mb-foot { font-size: 0.7em; color: var(--disabled-text-color); margin-top: 4px; text-align: right; }
            .mb-empty { color: var(--disabled-text-color); font-size: 0.9em; padding: 8px 0; }
            .mb-remain { font-size: 1.1em; font-weight: bold; }
            .mb-r0 { color: var(--success-color); }
            .mb-rmid { color: var(--warning-color); }
            .mb-rfar { color: var(--primary-text-color); }
            .mb-rna { color: var(--disabled-text-color); font-size: 0.85em; }
            .mb-dist { font-size: 0.75em; color: var(--secondary-text-color); }
          </style>
          ${ stops.length ? `<div class="mb-info">附近站點：${stops.slice(0,5).map(s => {
            const d = uLat != null ? this._dist(uLat, uLon, s.latitude, s.longitude) : null;
            return `<b>${s.stationCode}</b>${d != null ? ` <span class="mb-dist">(${d}m)</span>` : ''}`;
          }).join('、')}</div>` : '' }
          ${ routes.length ? `<table class="mb-table"><tbody>
            <tr><th>路線</th><th>目的地</th><th>站點</th><th style="text-align:center">班次1</th><th style="text-align:center">班次2</th></tr>
            ${routes.map(r => {
              const cls = r.color === 'Blue' ? 'mb-c-b' : r.color === 'Green' ? 'mb-c-g' : 'mb-c-o';
              let distText = '';
              if (uLat != null && r.nearbyStop) {
                const s = stops.find(st => st.stationCode === r.nearbyStop || st.stationName === r.nearbyStop);
                if (s) distText = ` <span class="mb-dist">(${this._dist(uLat, uLon, s.latitude, s.longitude)}m)</span>`;
              }
              return `<tr>
                <td><span class="mb-badge ${cls}">${r.routeName}</span></td>
                <td>${r.destination || '-'}</td>
                <td class="mb-info">${r.nearbyStop || ''}${distText}</td>
                <td class="mb-plate" style="text-align:center">${this._busCell(r.buses && r.buses[0])}</td>
                <td class="mb-plate" style="text-align:center">${this._busCell(r.buses && r.buses[1])}</td>
              </tr>`;
            }).join('')}
          </tbody></table>` : `<div class="mb-empty">載入中...</div>` }
          ${ ts ? `<div class="mb-foot">${ts}</div>` : '' }
        </div>
      </ha-card>`;
  }

  _busCell(b) {
    if (!b) return `<span class="mb-rna">—</span>`;
    const rs = b.remainingStops;
    const cls = rs === 0 ? 'mb-r0' : rs <= 3 ? 'mb-r0' : rs <= 8 ? 'mb-rmid' : 'mb-rfar';
    return `${b.busPlate}<br><span class="mb-remain ${cls}">${ rs != null ? (rs === 0 ? '到站' : `${rs} 站`) : '—' }</span>`;
  }

  _dist(lat1, lon1, lat2, lon2) {
    const R = 6371000;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon/2) ** 2;
    return Math.round(R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)));
  }

  getCardSize() { return 3; }
}

customElements.define("macau-bus-card", MacauBusCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "macau-bus-card",
  name: "澳門巴士 Macau Bus",
  description: "顯示澳門即時巴士到站資訊",
});
