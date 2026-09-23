let trendChartInstance = null;
let cpoPricingData = {};

document.addEventListener("DOMContentLoaded", () => {
    fetchMarketNews();
    fetchPricingData();
});

function switchMainTab(tabName) {
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.section').forEach(sec => sec.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById('section-' + tabName).classList.add('active');
    
    if(tabName === 'rates' && document.getElementById('rate-tbody').innerHTML === '') renderRate('FET');
    if(tabName === 'compare' && document.getElementById('compare-tbody').innerHTML === '') renderCompare(false);
    if(tabName === 'trend') setTimeout(() => renderTrendChart(), 50);
}

const getCpoClass = (cpo) => {
    const lower = cpo.toLowerCase();
    if(lower.includes('遠傳') || lower.includes('fet')) return 'cpo-fet';
    if(lower.includes('evalue')) return 'cpo-evalue';
    if(lower.includes('icharging') || lower.includes('cblok')) return 'cpo-icharging';
    if(lower.includes('u-power')) return 'cpo-upower';
    if(lower.includes('tail')) return 'cpo-tail';
    if(lower.includes('yes')) return 'cpo-yes';
    return 'cpo-default';
};

function fetchMarketNews() {
    // 讀取 V2.2 的 data/market.json
    fetch('data/market.json')
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('news-container');
            container.innerHTML = '';
            document.getElementById('update-time').innerText = '最後更新: ' + new Date().toLocaleString('zh-TW', {month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit'});
            document.getElementById('kpi-news-count').innerText = data.length + ' 筆';
            
            if (data.length === 0) return container.innerHTML = '<div style="text-align:center;">尚無情報</div>';

            data.forEach(item => {
                let mainTitle = item.title;
                let tagsHtml = '';
                const tagMatch = item.title.match(/\[(.*?)\]/);
                if (tagMatch) {
                    mainTitle = item.title.replace(tagMatch[0], '').trim();
                    tagMatch[1].split('|').forEach(t => {
                        const isHighlight = t.includes('優惠') || t.includes('新站') ? 'highlight' : '';
                        tagsHtml += `<span class="spec-tag ${isHighlight}">${t.trim()}</span>`;
                    });
                }
                container.innerHTML += `
                    <div class="news-card">
                        <div class="news-cpo ${getCpoClass(item.cpo)}">${item.cpo}</div>
                        <div class="news-content">
                            <a href="${item.url}" target="_blank" class="news-link">${mainTitle}</a>
                            <div class="spec-tags">${tagsHtml}</div>
                        </div>
                        <div class="news-date">${item.date}</div>
                    </div>`;
            });
        }).catch(e => console.log("等待 data/market.json 產生...", e));
}

function fetchPricingData() {
    fetch('data/pricing.json')
        .then(res => res.json())
        .then(data => { cpoPricingData = data; })
        .catch(() => console.log("等待 data/pricing.json 產生..."));
}

function getPriceAtHour(cpo, hour, isWeekend) {
    const config = cpoPricingData[cpo];
    if (!config) return 0;
    if (config.type === 'FLAT') return config.price;
    if (isWeekend) return config.holiday;
    if (hour >= config.peakStart && hour <= config.peakEnd) return config.peak;
    return config.offPeak;
}

function renderCompare(isWeekend) {
    if (Object.keys(cpoPricingData).length === 0) return;
    const cposForCompare = ['FET', 'EVALUE', 'iCharging', 'TAIL', 'U-POWER', 'YES'];
    document.getElementById('toggle-weekday').className = 'toggle-btn' + (!isWeekend ? ' active' : '');
    document.getElementById('toggle-weekend').className = 'toggle-btn' + (isWeekend ? ' active' : '');
    
    const tbody = document.getElementById('compare-tbody');
    tbody.innerHTML = '';

    for (let h = 0; h < 24; h++) {
        const timeStr = String(h).padStart(2, '0') + ':00';
        let rowHtml = `<tr><td class="time-col">${timeStr}</td>`;
        
        let prices = cposForCompare.map(cpo => getPriceAtHour(cpo, h, isWeekend));
        let fetPrice = prices[0];
        let minOtherPrice = Math.min(...prices.slice(1));
        
        cposForCompare.forEach((cpo, index) => {
            rowHtml += `<td class="${index === 0 ? 'col-fet' : ''}">$${prices[index].toFixed(1)}</td>`;
        });
        
        let diff = (fetPrice - minOtherPrice).toFixed(1);
        if (fetPrice < minOtherPrice) rowHtml += `<td><span class="cell-win">🏆 完勝 (省 $${Math.abs(diff)})</span></td></tr>`;
        else if (fetPrice === minOtherPrice) rowHtml += `<td><span class="cell-tie">🤝 平手</span></td></tr>`;
        else rowHtml += `<td><span class="cell-lose">⚠️ 偏貴 (多 $${diff})</span></td></tr>`;
        
        tbody.innerHTML += rowHtml;
    }
}

function renderRate(cpo) {
    if (Object.keys(cpoPricingData).length === 0) return;
    document.querySelectorAll('.cpo-btn').forEach(btn => { btn.style.backgroundColor = 'white'; btn.style.color = '#64748b'; btn.style.borderColor = '#cbd5e1'; });
    const config = cpoPricingData[cpo];
    let activeBtn = document.getElementById('btn-' + cpo.toLowerCase().replace('-',''));
    if(activeBtn) { activeBtn.style.backgroundColor = config.color; activeBtn.style.color = 'white'; activeBtn.style.borderColor = config.color; }
    
    document.getElementById('rate-table-ui').style.borderColor = config.color;
    const summaryDiv = document.getElementById('rate-summary');
    if (config.type === 'TOU') {
        summaryDiv.innerHTML = `<div class="rate-box" style="border-color:#16a34a;color:#16a34a;"><div class="rate-box-title">離峰時段</div><div class="rate-box-price">${config.offPeak}<span class="unit">元/kWh</span></div></div>
                                <div class="rate-box" style="border-color:#ea580c;color:#ea580c;"><div class="rate-box-title">尖峰時段 ${config.peakStart}:00-${config.peakEnd+1}:00</div><div class="rate-box-price">${config.peak}<span class="unit">元/kWh</span></div></div>
                                <div class="rate-box" style="border-color:#ca8a04;color:#ca8a04;"><div class="rate-box-title">假日時段</div><div class="rate-box-price">${config.holiday}<span class="unit">元/kWh</span></div></div>`;
    } else {
        summaryDiv.innerHTML = `<div class="rate-box" style="border-color:${config.color};color:${config.color};"><div class="rate-box-title">全時段單一費率</div><div class="rate-box-price">${config.price}<span class="unit">元/kWh</span></div></div>`;
    }

    const tbody = document.getElementById('rate-tbody');
    tbody.innerHTML = '';
    for (let h = 0; h < 24; h++) {
        const timeStr = String(h).padStart(2, '0') + ':00~';
        let rowHtml = `<tr><td class="time-col">${timeStr}</td>`;
        for (let d = 1; d <= 7; d++) {
            let price = '', cellClass = '';
            if (config.type === 'TOU') {
                if (d >= 6) { price = config.holiday; cellClass = 'cell-holiday'; }
                else if (h >= config.peakStart && h <= config.peakEnd) { price = config.peak; cellClass = 'cell-peak'; }
                else { price = config.offPeak; cellClass = 'cell-off-peak'; }
            } else { price = config.price; cellClass = 'cell-flat'; }
            rowHtml += `<td class="${cellClass}">$${price.toFixed(1)}</td>`;
        }
        tbody.innerHTML += rowHtml + `</tr>`;
    }
}

function renderTrendChart() {
    const ctx = document.getElementById('expansionChart').getContext('2d');
    if (trendChartInstance) trendChartInstance.destroy();
    
    fetch('data/price_history.json')
        .then(res => res.json())
        .then(historyData => {
            trendChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: historyData.labels,
                    datasets: [
                        { label: '遠傳 (FET)', data: historyData.datasets['FET'], borderColor: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)', borderWidth: 3, tension: 0.3, fill: true },
                        { label: 'U-POWER', data: historyData.datasets['U-POWER'], borderColor: '#0369a1', borderWidth: 2, tension: 0.3 },
                        { label: 'EVALUE', data: historyData.datasets['EVALUE'], borderColor: '#4CAF50', borderWidth: 2, tension: 0.3 },
                        { label: 'TAIL', data: historyData.datasets['TAIL'], borderColor: '#0891b2', borderWidth: 2, borderDash: [5, 5], tension: 0.3 }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { position: 'top', labels: { font: { family: 'Noto Sans TC', size: 13 } } } },
                    scales: { y: { beginAtZero: true, title: { display: true, text: '累計 DC 快充站數', font: { size: 13, weight: 'bold' } } }, x: { grid: { display: false } } },
                }
            });
        }).catch(err => console.log('等待 data/price_history.json 生成...'));
}
