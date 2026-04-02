import { useState, useEffect } from 'react';
import { 
  Trophy, 
  Search, 
  Flag, 
  Timer, 
  TrendingUp, 
  Clock,
  MapPin,
  Share
} from 'lucide-react';
import { motion } from 'framer-motion';
import './index.css';

interface Racer {
  waku: number;
  name: string;
  rate_global: number;
  st_average: number;
  exhibition_time: number;
  exhibition_rank?: number;
  lap_time?: number;
  turn_time?: number;
  straight_time?: number;
  comment?: string;
}

interface Prediction {
  waku: number;
  score: number;
  rank_prediction: number;
}

interface VenueSchedule {
  jcd: string;
  name: string;
  status: string;
}

const BoatIcon = ({ waku, className }: { waku: number; className?: string }) => {
  return (
    <svg 
      viewBox="0 0 120 40" 
      className={`boat-svg w-svg-${waku} ${className || ''}`}
      width="80" height="32"
      xmlns="http://www.w3.org/2000/svg"
      style={{ overflow: 'visible' }}
    >
      <filter id={`pop-shadow-${waku}`}>
        <feDropShadow dx="2" dy="2" stdDeviation="1.5" floodColor="rgba(0,0,0,0.5)"/>
      </filter>
      <g filter={`url(#pop-shadow-${waku})`}>
        <path d="M 5 5 L 85 5 Q 115 20 85 35 L 5 35 L 0 20 Z" fill={`var(--waku-${waku})`} fillOpacity="1" stroke="#111" strokeWidth="2.5" />
        <path d="M 85 5 Q 115 20 85 35 L 80 20 Z" fill="rgba(255,255,255,0.25)" />
        <circle cx="28" cy="20" r="11" fill="#fff" stroke="#111" strokeWidth="2.5"/>
        <text x="28" y="25" fill="#000" fontSize="15" fontWeight="900" textAnchor="middle">{waku}</text>
      </g>
    </svg>
  );
};

export default function App() {
  const [racers, setRacers] = useState<Racer[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [schedule, setSchedule] = useState<VenueSchedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isMock, setIsMock] = useState(false);
  const [sourceUrls, setSourceUrls] = useState<{list?: string, before?: string}>({});
  const [showPwaPrompt, setShowPwaPrompt] = useState(false);

  const getAvailableDates = () => {
    const dates = [];
    const now = new Date();
    for (let i = 0; i < 4; i++) {
        const d = new Date(now);
        d.setDate(now.getDate() - i);
        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, '0');
        const dd = String(d.getDate()).padStart(2, '0');
        dates.push({ value: `${yyyy}${mm}${dd}`, label: `${yyyy}/${mm}/${dd}` });
    }
    return dates;
  };

  const [date, setDate] = useState(getAvailableDates()[0].value);
  const [jcd, setJcd] = useState('22'); 
  const [rno, setRno] = useState('1'); 

  const venues = [
    { id: '01', name: '桐生' }, { id: '02', name: '戸田' }, { id: '03', name: '江戸川' },
    { id: '04', name: '平和島' }, { id: '05', name: '多摩川' }, { id: '06', name: '浜名湖' },
    { id: '07', name: '蒲郡' }, { id: '08', name: '常滑' }, { id: '09', name: '津' },
    { id: '10', name: '三国' }, { id: '11', name: 'びわこ' }, { id: '12', name: '住之江' },
    { id: '13', name: '尼崎' }, { id: '14', name: '鳴門' }, { id: '15', name: '丸亀' },
    { id: '16', name: '児島' }, { id: '17', name: '宮島' }, { id: '18', name: '徳山' },
    { id: '19', name: '下関' }, { id: '20', name: '若松' }, { id: '21', name: '芦屋' },
    { id: '22', name: '福岡' }, { id: '23', name: '唐津' }, { id: '24', name: '大村' }
  ];

  useEffect(() => {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
    if (isIOS && !isStandalone) setShowPwaPrompt(true);
  }, []);

  const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

  const fetchSchedule = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/schedule/${date}`);
      if (res.ok) {
        const data = await res.json();
        setSchedule(data);
      }
    } catch (e) { console.error("Schedule fetch failed"); }
  };

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/api/prediction/${date}/${jcd}/${rno}?t=${Date.now()}`);
      if (!res.ok) throw new Error('API Error');
      const data = await res.json();
      if (data.error) {
        setError(data.error);
        return;
      }
      setRacers(data.racers);
      setPredictions(data.predictions);
      setIsMock(!!data.is_mock);
      setSourceUrls({ list: data.racelist_url, before: data.beforeinfo_url });
    } catch (err) {
      setError('データが取得できませんでした。');
    } finally {
      setTimeout(() => setLoading(false), 600);
    }
  };

  useEffect(() => {
    fetchSchedule();
    fetchData();
  }, [date, jcd, rno]);

  const minExh = racers.length ? Math.min(...racers.map(r => r.exhibition_time)) : 6.6;
  const sortedPredictions = [...predictions].sort((a,b) => b.score - a.score);

  return (
    <div className="app-container">
      <div className="schedule-bar">
        <div className="bar-label"><Clock size={14} /> 本日の開催</div>
        <div className="venue-list">
          {schedule.length > 0 ? schedule.map(v => (
            <div 
              key={v.jcd} 
              className={`venue-chip ${v.jcd === jcd ? 'is-active' : ''}`}
              onClick={() => setJcd(v.jcd)}
            >
              {v.name}
            </div>
          )) : (
            <span style={{fontSize: '0.8rem', opacity: 0.7}}>開催情報を取得中...</span>
          )}
        </div>
      </div>

      <header className="glass-header">
        <div className="logo">
          <div className="icon">🏁</div>
          <h1>BoatRace <span>Analyzer POP</span></h1>
        </div>
        <div className="race-selector">
          <select value={date} onChange={e => setDate(e.target.value)}>
            {getAvailableDates().map(d => (
              <option key={d.value} value={d.value}>{d.label}</option>
            ))}
          </select>
          <select value={jcd} onChange={e => setJcd(e.target.value)}>
            {venues.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
          </select>
          <select value={rno} onChange={e => setRno(e.target.value)}>
            {[1,2,3,4,5,6,7,8,9,10,11,12].map(r => (
              <option key={r} value={r.toString()}>{r} R</option>
            ))}
          </select>
        </div>
      </header>

      {sourceUrls.list && (
        <div className="source-links-bar">
          <MapPin size={14} style={{ marginRight: 6 }} />
          <span>取得元URL: </span>
          <a href={sourceUrls.list} target="_blank" rel="noreferrer">出走表</a>
          <span style={{margin: '0 8px'}}>|</span>
          <a href={sourceUrls.before} target="_blank" rel="noreferrer">直前情報</a>
        </div>
      )}

      <main className="dashboard-grid">
        <div className="left-panel">
          <section className="glass-card">
            <h2 style={{ display: 'flex', alignItems: 'center' }}>
              <Timer size={24} style={{ marginRight: 10 }} />
              スタート体形シミュレーター
            </h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-sub)', marginBottom: '15px', fontWeight: 'bold' }}>
              横一線と仮定した展示タイムだけの差（0.01秒=8px遅れ）
            </p>
            <div className="simulator-box">
              <div className="start-line"></div>
              {racers.map(r => {
                const diff = r.exhibition_time - minExh;
                const lag = (diff / 0.01) * 8;
                return (
                  <div key={r.waku} className="sim-lane" style={{ position: 'relative' }}>
                    <div className={`w-badge w-${r.waku}`} style={{ marginLeft: '10px', zIndex: 11 }}>{r.waku}</div>
                    <div className="lane-track" style={{ position: 'relative', flex: 1, height: '100%' }}>
                      <motion.div 
                        className="lane-boat-wrapper"
                        initial={{ x: -100 }}
                        animate={{ x: -lag }}
                        transition={{ duration: 1.2, ease: "easeOut" }}
                        style={{ position: 'absolute', right: '220px' }}
                      >
                        <BoatIcon waku={r.waku} />
                        <span className="diff-tag" style={{ marginLeft: '10px', fontWeight: 900, fontSize: '0.8rem', color: diff === 0 ? 'var(--primary-red)' : 'var(--text-sub)' }}>
                          {diff === 0 ? "Fastest!" : `+${diff.toFixed(2)}s`}
                        </span>
                      </motion.div>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          <section className="glass-card">
            <h2><Trophy size={24} style={{ marginRight: 10, verticalAlign: 'middle' }} /> AI 着順予測</h2>
            <div className="podium-box">
              {[1, 0, 2].map((idx) => {
                const p = sortedPredictions[idx];
                if (!p) return <div key={idx} className="podium-rank"></div>;
                const rankClass = idx === 0 ? 'p-1st' : idx === 1 ? 'p-2nd' : 'p-3rd';
                const label = idx === 0 ? '1着' : idx === 1 ? '2着' : '3着';
                return (
                  <div key={p.waku} className={`podium-rank ${rankClass}`}>
                     <div className={`w-badge w-${p.waku}`} style={{ marginBottom: 10, width: 45, height: 45, fontSize: '1.5rem' }}>{p.waku}</div>
                     <div className="podium-base">{label}</div>
                  </div>
                );
              })}
            </div>

            <div className="score-bars">
              <h3 style={{ fontWeight: 900, marginBottom: 15, fontSize: '1rem', display: 'inline-block', background: 'var(--secondary)', padding: '2px 10px', border: '2px solid var(--border-dark)', borderRadius: '20px' }}>総合スコア</h3>
              {sortedPredictions.map((p) => (
                <div key={p.waku} className="score-row">
                  <div className={`w-badge w-${p.waku}`}>{p.waku}</div>
                  <div className="progress-container">
                    <motion.div 
                      className="progress-hatched" 
                      initial={{ width: 0 }}
                      animate={{ width: `${(p.score / 120) * 100}%` }}
                    />
                  </div>
                  <div style={{ fontWeight: 900, width: 45, textAlign: 'right' }}>{p.score.toFixed(1)}</div>
                </div>
              ))}
            </div>
          </section>
        </div>

        <div className="right-panel">
          <section className="glass-card" style={{ padding: '0px', overflow: 'hidden', border: 'none', background: 'transparent', boxShadow: 'none' }}>
            <div style={{ background: 'white', border: '3px solid var(--border-dark)', borderRadius: '12px', overflow: 'hidden', boxShadow: 'var(--pop-shadow)' }}>
              <h2 style={{ padding: '20px', margin: 0, borderBottom: '4px solid var(--primary-red)' }}>
                <Flag size={24} style={{ marginRight: 10, verticalAlign: 'middle' }} /> 
                出走表 & 直前情報 (オリジナル展示対応)
              </h2>
              
              <div className="cards-header">
                <div>枠</div>
                <div>選手名</div>
                <div>勝率</div>
                <div>平均ST</div>
                <div>展示</div>
                <div>1周</div>
                <div>まわり</div>
                <div>直線</div>
                <div style={{ textAlign: 'left', paddingLeft: 15 }}>選手コメント (前日/直前)</div>
              </div>

              <div className="racer-cards-container" style={{ padding: '15px', background: '#f8f9fa' }}>
                {racers.map((r) => (
                  <div key={r.waku} className="racer-card">
                    <div className="col-waku">
                      <div className={`w-badge w-${r.waku}`}>{r.waku}</div>
                    </div>
                    <div className="col-name">
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-sub)', fontWeight: 'bold' }}>{r.waku}号艇</div>
                      {r.name}
                    </div>
                    <div className="col-stat">{r.rate_global.toFixed(2)}</div>
                    <div className="col-stat">{r.st_average.toFixed(2)}</div>
                    <div className="col-stat" style={{ color: r.exhibition_time === minExh ? 'var(--primary-red)' : 'inherit', fontWeight: '900' }}>
                      {r.exhibition_time.toFixed(2)}
                    </div>
                    <div className="col-stat text-lap">{r.lap_time ? r.lap_time.toFixed(2) : '-'}</div>
                    <div className="col-stat text-maw">{r.turn_time ? r.turn_time.toFixed(2) : '-'}</div>
                    <div className="col-stat text-str">{r.straight_time ? r.straight_time.toFixed(2) : '-'}</div>
                    <div className="col-comment">
                      {r.comment || <span style={{ opacity: 0.3 }}>コメントなし</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <div className="stats-grid">
            <div className="trend-card">
               <h3 style={{ fontWeight: 900, marginBottom: 15, fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                 <TrendingUp size={18} /> 節間 STトレンド
               </h3>
               {racers.slice(0, 4).map(r => (
                 <div key={r.waku} className="trend-item">
                    <div className={`w-badge w-${r.waku}`} style={{ width: 22, height: 22, fontSize: '0.7rem' }}>{r.waku}</div>
                    <div className="simple-bar">
                      <div className="bar-fill" style={{ width: `${60 + Math.random() * 30}%`, background: `var(--waku-${r.waku})` }}></div>
                    </div>
                    <div className="rank-badge">順{(r.waku % 3) + 1}</div>
                 </div>
               ))}
            </div>
            <div className="trend-card">
               <h3 style={{ fontWeight: 900, marginBottom: 15, fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                 <TrendingUp size={18} /> 枠番別 ST実績
               </h3>
               {racers.slice(0, 4).map(r => (
                 <div key={r.waku} className="trend-item">
                    <div className={`w-badge w-${r.waku}`} style={{ width: 22, height: 22, fontSize: '0.7rem' }}>{r.waku}</div>
                    <div className="simple-bar">
                      <div className="bar-fill" style={{ width: `${50 + Math.random() * 40}%`, background: `var(--waku-${r.waku})` }}></div>
                    </div>
                    <div className="rank-badge">順{r.waku}</div>
                 </div>
               ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
