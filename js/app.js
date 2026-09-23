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
    if(tabName === 'trend') {
        setTimeout(() => renderTrendChart(), 50);
    }
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

// 讀取 V2 架構的 market.json
function fetchMarketNews() {
    fetch('data/market.json')
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('news-container');
            container.innerHTML = '';
            document.getElementById('update-time').innerText = '最後更新: ' + new Date().toLocaleString('zh-TW', {month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit'});
            
            if (data.length === 0) return container.innerHTML = '<div style="text-align:center;">尚無情報</div>';

            data.forEach(item => {
                let mainTitle = item.title;
                let tagsHtml = '';
                const tagMatch = item.title.match(/\[(.*?)\]/);
                if (tagMatch) {
                    mainTitle = item.title.replace(tagMatch[0], '').trim();
                    tagMatch[1].split('|').forEach(t => {
                        t = t.trim();
                        const isHighlight = t.includes('優惠') || t.includes('新站') ? 'highlight' : '';
                        tagsHtml += `<span class="spec-tag ${isHighlight}">${t}</span>`;
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
                    </div>
                `;
            });
        }).catch(err => console.log("等待 market.json 生成...", err));
}

// 讀取 V2 架構的 pricing.json
function fetchPricingData() {
    fetch('data/pricing.json')
        .then(res => res.json())
        .then(data => {
            cpoPricingData = data;
        }).catch(err => console.log("等待 pricing.json 生成...", err));
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
        let otherPrices = prices.slice(1);
        let minOtherPrice = Math.min(...otherPrices);
        
        cposForCompare.forEach((cpo, index) => {
            let price = prices[index];
            let isFet = index === 0;
            let cellClass = isFet ? 'col-fet' : '';
            rowHtml += `<td class="${cellClass}">$${price.toFixed(1)}</td>`;
        });
        
        let analysisHtml = '';
        let diff = (fetPrice - minOtherPrice).toFixed(1);
        if (fetPrice < minOtherPrice) {
            analysisHtml = `<span class="cell-win">🏆 完勝 (省 $${Math.abs(diff)})</span>`;
        } else if (fetPrice === minOtherPrice) {
            analysisHtml = `<span class="cell-tie">🤝 平手</span>`;
        } else {
            analysisHtml = `<span class="cell-lose">⚠️ 偏貴 (多 $${diff})</span>`;
        }
        
        rowHtml += `<td>${analysisHtml}</td></tr>`;
        tbody.innerHTML += rowHtml;
    }
}

function renderRate(cpo) {
    if (Object.keys(cpoPricingData).length === 0) return;
    document.querySelectorAll('.cpo-btn').forEach(btn => {
        btn.style.backgroundColor = 'white'; btn.style.color = '#64748b'; btn.style.borderColor = '#cbd5e1';
    });
    const config = cpoPricingData[cpo];
    let activeBtn = document.getElementById('btn-' + cpo.toLowerCase().replace('-',''));
    activeBtn.style.backgroundColor = config.color; activeBtn.style.color = 'white'; activeBtn.style.borderColor = config.color;
    
    const summaryDiv = document.getElementById('rate-summary');
    const tbody = document.getElementById('rate-tbody');
    document.getElementById('rate-table-ui').style.borderColor = config.color;

    if (config.type === 'TOU') {
        summaryDiv.innerHTML = `
            <div class="rate-box" style="border-color: #86efac; color: #14532d;">
                <div class="rate-box-title">離峰時段</div><div class="rate-box-price">${config.offPeak}<span class="unit">元/kWh</span></div>
            </div>
            <div class="rate-box" style="border-color: #fdba74; color: #7c2d12;">
                <div class="rate-box-title">尖峰時段 ${config.peakStart}:00-${config.peakEnd+1}:00</div><div class="rate-box-price">${config.peak}<span class="unit">元/kWh</span></div>
            </div>
            <div class="rate-box" style="border-color: #d9f99d; color: #3f6212;">
                <div class="rate-box-title">假日時段</div><div class="rate-box-price">${config.holiday}<span class="unit">元/kWh</span></div>
            </div>
        `;
    } else {
        summaryDiv.innerHTML = `
            <div class="rate-box" style="border-color: ${config.color}; color: ${config.color};">
                <div class="rate-box-title">全時段單一費率</div><div class="rate-box-price">${config.price}<span class="unit">元/kWh</span></div>
            </div>
        `;
    }

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
        rowHtml += `</tr>`;
        tbody.innerHTML += rowHtml;
    }
}

// 讀取 V2 架構的 price_history.json
function renderTrendChart() {
    const ctx = document.getElementById('expansionChart').getContext('2d');
    if (trendChartInstance) {
        trendChartInstance.destroy();
    }

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
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'top', labels: { font: { family: 'Noto Sans TC', size: 13 } } }, tooltip: { mode: 'index', intersect: false } },
                    scales: { y: { beginAtZero: true, title: { display: true, text: '累計 DC 快充站數', font: { size: 14, weight: 'bold' } } }, x: { grid: { display: false } } },
                    interaction: { mode: 'nearest', axis: 'x', intersect: false }
                }
            });
        }).catch(err => console.log('等待 price_history.json 生成...', err));
}
