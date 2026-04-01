import { useState, useEffect } from 'react';
import { 
  Trophy, 
  Search, 
  Flag, 
  Timer, 
  TrendingUp, 
  Clock,
  MapPin,
  Share,
  PlusSquare
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

// --- Boat SVG (Original POP Style) ---
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

  const [date, setDate] = useState('20260401');
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
    // iPhone向けのPWA案内（初回のみ）
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
    if (isIOS && !isStandalone) {
      setShowPwaPrompt(true);
    }
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
      console.error(err);
    } finally {
      setTimeout(() => setLoading(false), 600);
    }
  };

  useEffect(() => {
    fetchSchedule();
    fetchData();
  }, [date]); // 日付が変わったらスケジュールも再取得

  const minExh = racers.length ? Math.min(...racers.map(r => r.exhibition_time)) : 6.6;
  const sortedPredictions = [...predictions].sort((a,b) => b.score - a.score);

  return (
    <div className="app-container">
      {/* Schedule Bar */}
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

      {/* PWA Prompt for iOS */}
      {showPwaPrompt && (
        <motion.div 
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          className="fixed bottom-4 left-4 right-4 z-50 bg-white p-4 rounded-2xl shadow-2xl border-2 border-amber-400 text-slate-800"
        >
          <div className="flex items-start gap-3">
            <div className="p-2 bg-amber-100 rounded-lg">
              <Share className="w-6 h-6 text-amber-600" />
            </div>
            <div className="flex-1 text-sm">
              <p className="font-bold mb-1 text-base">アプリとして使えます！</p>
              <p className="text-slate-600 leading-tight">
                下の <Share className="inline w-4 h-4" /> 共有ボタンから
                <span className="font-bold text-amber-700">「ホーム画面に追加」</span> を選ぶと、
                全画面でアプリのように使えます。
              </p>
            </div>
            <button onClick={() => setShowPwaPrompt(false)} className="text-slate-400 font-bold p-1">✕</button>
          </div>
        </motion.div>
      )}

      {/* POP Header */}
      <header className="glass-header">
        <div className="logo">
          <div className="icon">🏁</div>
          <h1>BoatRace <span>Analyzer POP</span></h1>
        </div>
        <div className="race-selector">
          <select value={date} onChange={e => setDate(e.target.value)}>
            <option value="20260331">2026/03/31</option>
            <option value="20260330">2026/03/30</option>
            <option value="20260329">2026/03/29</option>
          </select>
          <select value={jcd} onChange={e => setJcd(e.target.value)}>
            {venues.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
          </select>
          <select value={rno} onChange={e => setRno(e.target.value)}>
            {Array.from({length: 12}, (_, i) => i + 1).map(r => (
              <option key={r} value={r.toString()}>{r} R</option>
            ))}
          </select>
          <button className="btn-primary" onClick={fetchData} disabled={loading}>
            <Search size={18} style={{verticalAlign: 'middle', marginRight: 8}} />
            {loading ? '分析中...' : 'データを取得'}
          </button>
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
          {error && (
            <div className="glass-card error-card">
              <h2>🚨 エラー</h2>
              <p>{error}</p>
            </div>
          )}
          
          {isMock && !error && (
            <div className="glass-card mock-notice">
              <h2>💡 サンプルデータ表示中</h2>
              <p>現在、公式サイトへの接続が混み合っているため、シミュレーション用にサンプルデータを生成しました。</p>
            </div>
          )}

          <section className="glass-card">
            <h2 style={{ display: 'flex', alignItems: 'center' }}>
              <Timer size={24} style={{ marginRight: 10 }} />
              スタート体形シミュレーター
            </h2>
            <div className="simulator-box" style={{ 
              position: 'relative', 
              backgroundImage: 'repeating-linear-gradient(90deg, transparent, transparent 19px, rgba(0,0,0,0.03) 19px, rgba(0,0,0,0.03) 20px)' 
            }}>
              <div className="start-line" style={{ 
                position: 'absolute', 
                top: 0, 
                right: '220px', 
                width: '6px', 
                height: '100%', 
                background: 'var(--primary-red)', 
                zIndex: 10, 
                boxShadow: '0 0 15px rgba(230, 0, 18, 0.4)' 
              }}></div>
              {racers.map(r => {
                const diff = r.exhibition_time - minExh;
                const lag = (diff / 0.01) * 8; // 1秒 = 800px相当のスケール
                return (
                  <div key={r.waku} className="sim-lane" style={{ position: 'relative', height: '42px', borderBottom: '1px dashed rgba(0,0,0,0.05)' }}>
                    <div className={`w-badge w-${r.waku}`} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', zIndex: 1, fontSize: '0.9rem', width: '28px', height: '28px' }}>{r.waku}</div>
                    <div className="lane-track" style={{ position: 'absolute', left: '45px', right: 0, height: '100%' }}>
                      <motion.div 
                        className="lane-boat-wrapper"
                        style={{ position: 'absolute', right: '220px', transformOrigin: 'right center' }}
                        animate={{ x: loading ? -100 : -lag }}
                        transition={{ duration: 1.2, ease: "easeOut" }}
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
            <h2><Trophy size={24} style={{ marginRight: 10, verticalAlign: 'middle' }} /> AI 予想結果</h2>
            <div className="podium">
              {sortedPredictions.slice(0, 3).map((p, i) => {
                const rankClass = i === 0 ? 'rank-1' : i === 1 ? 'rank-2' : 'rank-3';
                const label = i === 0 ? '1着(本命)' : i === 1 ? '2着(対抗)' : '3着(単穴)';
                return (
                  <div key={p.waku} className={`podium-item ${rankClass}`}>
                     <div className={`w-badge w-${p.waku}`} style={{ marginBottom: 10, width: 45, height: 45, fontSize: '1.5rem' }}>{p.waku}</div>
                     <div className="podium-bar">{label}</div>
                  </div>
                );
              })}
            </div>
          </section>
        </div>

        <div className="right-panel">
          <section className="glass-card">
            <h2><Flag size={24} style={{ marginRight: 10, verticalAlign: 'middle' }} /> 出走・展示データ</h2>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>枠</th>
                    <th>選手名</th>
                    <th>勝率</th>
                    <th>ST</th>
                    <th>展示</th>
                    <th>一周</th>
                    <th>まわり</th>
                    <th>直線</th>
                    <th>コメント</th>
                  </tr>
                </thead>
                <tbody>
                  {racers.map((r) => (
                    <tr key={r.waku}>
                      <td><div className={`w-badge w-${r.waku}`}>{r.waku}</div></td>
                      <td style={{ textAlign: 'left', whiteSpace: 'nowrap', fontWeight: 'bold' }}>{r.name}</td>
                      <td>{r.rate_global.toFixed(2)}</td>
                      <td>{r.st_average.toFixed(2)}</td>
                      <td style={{ color: r.exhibition_time === minExh ? 'var(--primary-red)' : 'inherit', fontWeight: 'bold' }}>
                        {r.exhibition_time.toFixed(2)}
                      </td>
                      <td>{r.lap_time ? r.lap_time.toFixed(2) : '-'}</td>
                      <td>{r.turn_time ? r.turn_time.toFixed(2) : '-'}</td>
                      <td>{r.straight_time ? r.straight_time.toFixed(2) : '-'}</td>
                      <td className="comment-cell">{r.comment || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="tip-box">
             <div className="tip-title">
               <TrendingUp size={20} />
               予想のヒント
             </div>
             <p style={{ fontSize: '0.82rem', lineHeight: 1.5 }}>
               丸亀競艇場など、個別対応会場では「まわり足」や「一周タイム」を反映中。コメントも参考に！
             </p>
          </section>
        </div>
      </main>
    </div>
  );
}
