import { useState, useEffect } from 'react';
import './App.css';

interface Racer {
  waku: number;
  name: string;
  rate_global: number;
  st_average: number;
  exhibition_time: number;
  lap_time?: number;
  turn_time?: number;
  straight_time?: number;
  // --- New Mock Data for Start Simulator ---
  st_series_avg?: number;     // 節間平均ST
  st_series_rank?: number;    // 節間平均スタート順
  st_course_avg?: number;     // 枠番別平均ST
  st_course_rank?: number;    // 枠番別平均スタート順
}

interface Prediction {
  waku: number;
  score: number;
  rank_prediction: number;
}

// --- Boat SVG Component ---
const BoatIcon = ({ waku, className }: { waku: number, className?: string }) => {
  // SVG of a racing boat facing RIGHT.
  // The 'fill' will be inherited through CSS (.w-1, .w-2, etc.)
  return (
    <svg 
      viewBox="0 0 120 40" 
      className={`boat-svg w-svg-${waku} ${className || ''}`}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Outer Glow/Shadow for pop effect */}
      <filter id="pop-shadow">
        <feDropShadow dx="2" dy="2" stdDeviation="0" floodColor="#000"/>
      </filter>
      
      <g filter="url(#pop-shadow)">
        {/* Main Hull */}
        <path d="M 5 5 L 85 5 Q 115 20 85 35 L 5 35 L 0 20 Z" className="boat-hull" stroke="#111" strokeWidth="2" />
        {/* Anti-splash guards / side stripes */}
        <path d="M 10 8 L 80 8 Q 105 20 80 32 L 10 32 Z" fill="rgba(255,255,255,0.2)" />
        
        {/* Motor */}
        <rect x="0" y="14" width="8" height="12" fill="#333" stroke="#111" strokeWidth="2" rx="2" />
        <rect x="-4" y="18" width="5" height="4" fill="#666" stroke="#111" strokeWidth="1" />
        
        {/* Cockpit / Cowling */}
        <rect x="50" y="12" width="25" height="16" fill="#111" stroke="#333" strokeWidth="2" rx="4" />
        <path d="M 55 12 L 70 12 L 75 20 L 70 28 L 55 28 Z" fill="#222" />
        
        {/* Waku Number Circle */}
        <circle cx="28" cy="20" r="10" fill="#fff" stroke="#111" strokeWidth="2"/>
        <text x="28" y="24" fill="#000" fontSize="12" fontWeight="900" textAnchor="middle">{waku}</text>
      </g>
    </svg>
  );
};

function App() {
  const [racers, setRacers] = useState<Racer[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const [date, setDate] = useState('20260330');
  const [jcd, setJcd] = useState('12');
  const [rno, setRno] = useState('1');
  const [errorMessage, setErrorMessage] = useState<string>('');

  const fetchData = async () => {
    setLoading(true);
    setErrorMessage('');
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/prediction/${date}/${jcd}/${rno}`);
      if (!res.ok) throw new Error('API Error');
      const data = await res.json();
      
      if (data.error || !data.racers || data.racers.length === 0) {
        setErrorMessage(data.error || 'データがありませんでした。日付やレース場を変更してください。');
        setRacers([]);
        setPredictions([]);
        return;
      }
      
      // Inject the Mock data for Phase 3 visual testing
      const mockedRacers = data.racers.map((r: Racer) => ({
        ...r,
        // Mocking Series and Course stats randomly for prototype
        st_series_avg: Number((0.10 + (Math.random() * 0.10)).toFixed(2)),
        st_series_rank: Math.floor(Math.random() * 6) + 1,
        st_course_avg: Number((0.12 + (Math.random() * 0.12)).toFixed(2)),
        st_course_rank: Math.floor(Math.random() * 6) + 1,
      }));

      setRacers(mockedRacers);
      setPredictions(data.predictions);
    } catch (err) {
      console.error(err);
    } finally {
      setTimeout(() => setLoading(false), 600);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleLoad = () => {
    fetchData();
  };

  const podiumTop3 = [...predictions].sort((a,b) => b.score - a.score).slice(0, 3);
  const visualPodium = podiumTop3.length === 3 ? [podiumTop3[1], podiumTop3[0], podiumTop3[2]] : [];
  const maxScore = predictions.length ? Math.max(...predictions.map(p => p.score)) : 100;

  // For Exhibition Simulator 
  // Fastest time is Front (X=0), Slower is Back (negative X visually, or just less pixel translation)
  // Let's say 0.01s diff = 8 pixels of drag back.
  const times = racers.map(r => r.exhibition_time);
  const minTime = times.length ? Math.min(...times) : 0;

  return (
    <div className="app-container">
      <header className="glass-header">
        <div className="logo">
          <span className="icon">🏁</span>
          <h1>BoatRace <span>Analyzer POP</span></h1>
        </div>
        <div className="race-selector">
          <select value={date} onChange={(e) => setDate(e.target.value)}>
             <option value="20260330">本日 (2026/03/30)</option>
            <option value="20260329">前日 (2026/03/29)</option>
            <option value="20260328">2日前 (2026/03/28)</option>
            <option value="20260327">3日前 (2026/03/27)</option>
            <option value="20240325">2024/03/25 (モック用)</option>
          </select>
          <select value={jcd} onChange={(e) => setJcd(e.target.value)}>
             <option value="01">桐生</option>
             <option value="02">戸田</option>
             <option value="03">江戸川</option>
             <option value="04">平和島</option>
             <option value="05">多摩川</option>
             <option value="06">浜名湖</option>
             <option value="07">蒲郡</option>
             <option value="08">常滑</option>
             <option value="09">津</option>
             <option value="10">三国</option>
             <option value="11">びわこ</option>
             <option value="12">住之江</option>
             <option value="13">尼崎</option>
             <option value="14">鳴門</option>
             <option value="15">丸亀</option>
             <option value="16">児島</option>
             <option value="17">宮島</option>
             <option value="18">徳山</option>
             <option value="19">下関</option>
             <option value="20">若松</option>
             <option value="21">芦屋</option>
             <option value="22">福岡</option>
             <option value="23">唐津</option>
             <option value="24">大村</option>
          </select>
          <select value={rno} onChange={(e) => setRno(e.target.value)}>
            <option value="1">1 R</option>
            <option value="12">12 R (優勝戦)</option>
          </select>
          <button className="btn-primary" onClick={handleLoad} disabled={loading}>
            {loading ? 'ANALYZING...' : 'データ取得'}
          </button>
        </div>
      </header>

      <main className="dashboard-grid">
        
        {/* --- LEFT COLUMN --- */}
        <section className="left-panel">
          {errorMessage && (
            <div className="glass-card mb-30" style={{border: '4px solid #e60012', background: '#ffebee'}}>
              <h2 style={{color: '#e60012', borderBottom: 'none'}}>🚨 エラー</h2>
              <p style={{fontWeight: 900, fontSize: '1.2rem'}}>{errorMessage}</p>
            </div>
          )}
          
          {/* Start Formation Simulator */}
          <div className="glass-card mb-30" style={{ overflow: "hidden" }}>
            <h2>🚀 スタート体形シミュレーター</h2>
            <p className="sim-desc">横一線と仮定した展示タイムだけの差（0.01秒＝8px遅れ）</p>
            <div className="simulator-box">
              <div className="start-line"></div>
              {racers.map(r => {
                // Calculate diff
                const diffSec = r.exhibition_time - minTime;
                // 1 unit of 0.01 sec = 8 pixels backward
                const lagPixels = (diffSec / 0.01) * 8; 
                
                return (
                  <div key={r.waku} className="sim-lane">
                     <div className="lane-waku w-badge w-bg">{r.waku}</div>
                     <div className="lane-track">
                       <div 
                         className="lane-boat-wrapper" 
                         style={{ 
                           transform: loading ? `translateX(-50px)` : `translateX(-${lagPixels}px)`,
                           transition: loading ? "none" : "transform 1.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)"
                         }}
                       >
                         <BoatIcon waku={r.waku} />
                         <span className="diff-label">+{diffSec.toFixed(2)}s</span>
                       </div>
                     </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="glass-card">
            <h2>AI 着順予測</h2>
            <div className="prediction-podium">
              {visualPodium.map((pred, idx) => {
                const rank = idx === 1 ? 1 : idx === 0 ? 2 : 3;
                return (
                  <div key={pred.waku} className={`podium-place rank-${rank}`}>
                    <div className={`podium-waku w-${pred.waku}`}>{pred.waku}</div>
                    <div className="podium-bar">{rank}着</div>
                  </div>
                );
              })}
            </div>

            <h3 className="sub-heading">総合スコア</h3>
            <div className="score-list">
              {[...predictions].sort((a,b) => b.score - a.score).map((pred) => {
                const width = `${(pred.score / maxScore) * 100}%`;
                return (
                  <div key={pred.waku} className="score-row">
                    <div className={`score-waku w-${pred.waku}`}>{pred.waku}</div>
                    <div className="score-bar-bg">
                      <div className="score-bar-fill" style={{ width: !loading ? width : '0%' }}></div>
                    </div>
                    <div className="score-value">{pred.score.toFixed(1)}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* --- RIGHT COLUMN --- */}
        <section className="right-panel">
          
          <div className="glass-card table-card table-wrapper mb-30">
            <h2>出走表＆直前情報</h2>
            <table>
              <thead>
                <tr>
                  <th>枠</th>
                  <th>選手名</th>
                  <th>勝率</th>
                  <th>平均ST</th>
                  <th className="highlight-column">展示<br/>タイム</th>
                  <th>周回<br/>タイム</th>
                </tr>
              </thead>
              <tbody>
                {racers.map(r => (
                  <tr key={r.waku}>
                    <td><span className={`table-waku w-${r.waku}`}>{r.waku}</span></td>
                    <td><strong>{r.name}</strong></td>
                    <td>{r.rate_global.toFixed(2)}</td>
                    <td>{r.st_average.toFixed(2)}</td>
                    <td className="highlight-val">{r.exhibition_time.toFixed(2)}</td>
                    <td>{r.lap_time ? r.lap_time.toFixed(1) : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="st-stats-grid">
            {/* Series ST Chart */}
            <div className="glass-card st-card">
              <h2>節間 STトレンド</h2>
              <div className="st-bars">
                {racers.map(r => {
                  const barW = Math.max(10, 100 - (r.st_series_avg! * 200));
                  return (
                    <div key={`series-${r.waku}`} className="st-row">
                      <span className={`w-badge w-bg w-${r.waku}`}>{r.waku}</span>
                      <div className="st-bar-container">
                        <div className="st-bar-fill series-fill" style={{ width: !loading ? `${barW}%` : '0%' }}>
                          <span>{r.st_series_avg?.toFixed(2)}</span>
                        </div>
                      </div>
                      <span className="rank-badge">順 {r.st_series_rank}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Course ST Chart */}
            <div className="glass-card st-card">
              <h2>枠番別 ST実績</h2>
              <div className="st-bars">
                {racers.map(r => {
                  const barW = Math.max(10, 100 - (r.st_course_avg! * 200));
                  return (
                    <div key={`course-${r.waku}`} className="st-row">
                      <span className={`w-badge w-bg w-${r.waku}`}>{r.waku}</span>
                      <div className="st-bar-container">
                        <div className="st-bar-fill course-fill" style={{ width: !loading ? `${barW}%` : '0%' }}>
                           <span>{r.st_course_avg?.toFixed(2)}</span>
                        </div>
                      </div>
                      <span className="rank-badge">順 {r.st_course_rank}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

        </section>
      </main>
    </div>
  );
}

export default App;
