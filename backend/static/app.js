document.addEventListener('DOMContentLoaded', () => {
    const loadBtn = document.getElementById('loadBtn');
    
    // Initial load
    fetchData();

    loadBtn.addEventListener('click', () => {
        const btnOrigText = loadBtn.innerText;
        loadBtn.innerText = 'Analyzing...';
        loadBtn.disabled = true;
        
        // Simulate delay for dramatic effect in prototype
        setTimeout(() => {
            fetchData();
            loadBtn.innerText = btnOrigText;
            loadBtn.disabled = false;
        }, 800);
    });
});

async function fetchData() {
    const date = document.getElementById('dateSelect').value;
    const jcd = document.getElementById('jcdSelect').value;
    const rno = document.getElementById('raceSelect').value;

    try {
        const res = await fetch(`/api/prediction/${date}/${jcd}/${rno}`);
        const data = await res.json();
        
        renderTable(data.racers);
        renderPodium(data.predictions);
        renderScoreList(data.predictions);
        renderChart(data.racers);
        
    } catch (err) {
        console.error("Failed to fetch prediction data:", err);
    }
}

function renderTable(racers) {
    const tbody = document.getElementById('racerTableBody');
    tbody.innerHTML = '';

    racers.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><span class="table-waku w-${r.waku}">${r.waku}</span></td>
            <td><strong>${r.name}</strong></td>
            <td>${r.rate_global.toFixed(2)}</td>
            <td>${r.st_average.toFixed(2)}</td>
            <td class="highlight-val">${r.exhibition_time.toFixed(2)}</td>
            <td>${r.lap_time ? r.lap_time.toFixed(1) : '-'}</td>
            <td>${r.turn_time ? r.turn_time.toFixed(1) : '-'}</td>
            <td>${r.straight_time ? r.straight_time.toFixed(1) : '-'}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderPodium(predictions) {
    const podiumContainer = document.getElementById('predictionPodium');
    podiumContainer.innerHTML = '';
    
    // Sort to find top 3
    const top3 = [...predictions].sort((a,b) => b.score - a.score).slice(0, 3);
    
    // order visually: 2nd, 1st, 3rd
    const visualOrder = [top3[1], top3[0], top3[2]];

    visualOrder.forEach((pred, idx) => {
        if (!pred) return;
        const rank = idx === 1 ? 1 : idx === 0 ? 2 : 3;
        const div = document.createElement('div');
        div.className = `podium-place rank-${rank}`;
        div.innerHTML = `
            <div class="podium-waku w-${pred.waku}">${pred.waku}</div>
            <div class="podium-bar">${rank}着</div>
        `;
        podiumContainer.appendChild(div);
    });
}

function renderScoreList(predictions) {
    const listContainer = document.getElementById('scoreList');
    listContainer.innerHTML = '';

    // Sort all by score descending
    const sorted = [...predictions].sort((a,b) => b.score - a.score);
    const maxScore = Math.max(...sorted.map(p => p.score));

    sorted.forEach((pred) => {
        const row = document.createElement('div');
        row.className = 'score-row';
        
        const widthPercent = (pred.score / maxScore) * 100;

        row.innerHTML = `
            <div class="score-waku w-${pred.waku}">${pred.waku}</div>
            <div class="score-bar-bg">
                <div class="score-bar-fill" style="width: 0%;" data-target="${widthPercent}%"></div>
            </div>
            <div class="score-value">${pred.score.toFixed(1)}</div>
        `;
        listContainer.appendChild(row);
    });

    // trigger animation
    setTimeout(() => {
        const fills = document.querySelectorAll('.score-bar-fill');
        fills.forEach(fill => {
            fill.style.width = fill.getAttribute('data-target');
        });
    }, 100);
}

function renderChart(racers) {
    // Simple bar chart for exhibition times (reversed: lower is better)
    const chart = document.getElementById('barChart');
    chart.innerHTML = '';
    
    // Find min/max for normalization to make differences visible
    const times = racers.map(r => r.exhibition_time);
    const minTime = Math.min(...times);
    const maxTime = Math.max(...times);
    
    racers.forEach(r => {
        const diff = maxTime - minTime;
        // Invert so smaller time means taller bar
        const normalized = diff === 0 ? 50 : 100 - (((r.exhibition_time - minTime) / diff) * 100);
        
        // Ensure some minimum height
        const heightPercent = Math.max(10, normalized);

        const bar = document.createElement('div');
        bar.className = `chart-bar w-${r.waku}`;
        bar.style.height = '0%';
        bar.title = `${r.waku}枠: ${r.exhibition_time.toFixed(2)}`;
        
        chart.appendChild(bar);

        // animate
        setTimeout(() => {
            bar.style.height = `${heightPercent}%`;
        }, 100);
    });
}
