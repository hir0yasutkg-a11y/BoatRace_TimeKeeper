import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Trophy, 
  Flag, 
  Timer, 
  TrendingUp, 
  Clock, 
  MapPin, 
  RotateCw,
  Share
} from 'lucide-react';
import './App.css';

// ----------------------------------------------------------------------------
// Types & Interfaces
// ----------------------------------------------------------------------------
interface Racer {
  waku: number;
  name: string;
  rank: string;
  rate_global: number;
  st_average: number;
  exhibition_time: number;
  lap_time: number;
  turn_time: number;
  straight_time: number;
  comment?: string;
  series_results?: Array<{
    date: string;
    rno: string;
    rank: string;
    course: string;
    st: string;
  }>;
}

interface Prediction {
  waku: number;
  score: number;
}

interface VenueSchedule {
  jcd: string;
  name: string;
  status: string;
  next_race: string | number;
  deadline: string;
  grade?: string;
  event?: string;
  has_exh_data: boolean;
  series_name?: string;
  series_day?: string;
  series_day_num?: number;
}

const AVAILABLE_DATES = [
  { label: '本日 (4/7)', value: '20260407' },
  { label: '昨日 (4/6)', value: '20260406' },
  { label: '4/5', value: '20260405' },
];

// ----------------------------------------------------------------------------
// Components
// ----------------------------------------------------------------------------

const TimeVisualizer = ({ title, racers, timeKey, icon, speedKmh = 50 }: { 
  title: string, 
  racers: Racer[], 
  timeKey: keyof Racer,
  icon: React.ReactNode,
  speedKmh?: number 
}) => {
  const times = racers.map(r => r[timeKey] as number).filter(t => t > 0);
  const min = Math.min(...times);
  const max = Math.max(...times);

  return (
    <section className="glass-card visualizer-card">
      <h3>{icon} {title}</h3>
      <div className="vis-container">
        {racers.map(r => {
          const val = r[timeKey] as number;
          if (!val) return null;
          const diff = val - min;
          const normalized = (max - min) > 0 ? (diff / (max - min)) : 0;
          return (
            <div key={r.waku} className="vis-row">
              <div className={`w-badge w-${r.waku}`}>{r.waku}</div>
              <div className="vis-track">
                <motion.div 
                  className="vis-ship"
                  initial={{ left: 0 }}
                  animate={{ left: `${normalized * 75}%` }}
                  transition={{ duration: 1, ease: "easeOut" }}
                >
                  <div className="ship-dot"></div>
                </motion.div>
              </div>
              <div className="vis-val">{val.toFixed(2)}</div>
            </div>
          );
        })}
      </div>
    </section>
  );
};

const TotalVisualizer = ({ racers }: { racers: Racer[] }) => {
  const getScore = (r: Racer) => {
    let s = (7 - r.exhibition_time) * 10;
    if (r.lap_time) s += (40 - r.lap_time) * 5;
    if (r.turn_time) s += (20 - r.turn_time) * 15;
    return s;
  };

  const scores = racers.map(r => ({ waku: r.waku, total: getScore(r) }));
  const maxScore = Math.max(...scores.map(s => s.total));

  return (
    <section className="glass-card total-vis-card">
      <h3><Trophy size={20} /> 総合足色シミュレート</h3>
      <div className="total-vis-container">
        {scores.map(s => (
          <div key={s.waku} className="total-vis-column">
            <div className="total-bar-wrapper">
              <motion.div 
                className={`total-bar w-${s.waku}-bg`}
                initial={{ height: 0 }}
                animate={{ height: `${(s.total / maxScore) * 100}%` }}
              />
            </div>
            <div className={`w-badge w-${s.waku}`}>{s.waku}</div>
          </div>
        ))}
      </div>
    </section>
  );
};

// ----------------------------------------------------------------------------
// Main Application
// ----------------------------------------------------------------------------

export default function App() {
  const [schedule, setSchedule] = useState<VenueSchedule[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isFetched, setIsFetched] = useState(false);
  
  const [racers, setRacers] = useState<Racer[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [roughAlerts, setRoughAlerts] = useState<{type:string, message:string}[]>([]);
  const [sourceUrls, setSourceUrls] = useState({ list: '', before: '' });
  const [isMock, setIsMock] = useState(false);
  
  const [showPwaPrompt, setShowPwaPrompt] = useState(false);
  const [date, setDate] = useState(AVAILABLE_DATES[0].value);
  const [jcd, setJcd] = useState('02'); 
  const [rno, setRno] = useState('1'); 
  const [seriesDay, setSeriesDay] = useState<number>(1);

  useEffect(() => {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
    if (isIOS && !isStandalone) setShowPwaPrompt(true);
  }, []);

  const API_BASE = ''; // 鋼鉄の相対パス： 1 mm の不備も許さない 100% の自律性

  const fetchSchedule = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/schedule/${date}`);
      if (res.ok) {
        const data = await res.json();
        setSchedule(data);
      }
    } catch (e) { console.error("Schedule fetch failed"); }
  };

  const fetchData = async (targetJcd?: string, targetRno?: string, targetDay?: number) => {
    const activeJcd = targetJcd || jcd;
    const activeRno = targetRno || rno;
    const activeDayNum = targetDay || seriesDay;
    
    let targetDate = date;
    const vInfo = schedule.find(v => v.jcd === activeJcd);
    if (vInfo && vInfo.series_day_num) {
        const diff = vInfo.series_day_num - activeDayNum;
        const d = new Date(date.slice(0,4)+"-"+date.slice(4,6)+"-"+date.slice(6,8));
        d.setDate(d.getDate() - diff);
        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, '0');
        const dd = String(d.getDate()).padStart(2, '0');
        targetDate = `${yyyy}${mm}${dd}`;
    }

    if (!activeJcd) return;
    setLoading(true);
    setError('');
    setIsFetched(false);
    try {
      const fetchUrl = `${API_BASE}/api/prediction/${targetDate}/${activeJcd}/${activeRno}?t=${Date.now()}`;
      const res = await fetch(fetchUrl);
      if (!res.ok) throw new Error(`API Error: ${res.status}`);
      const data = await res.json();
      if (data.error) {
        setError(data.error);
        return;
      }
      const activeRacers = (data.racers || []).filter((r: any) => 
        r.name !== "Unknown" && !r.name.includes("欠場")
      );
      setRacers(activeRacers);
      setPredictions(data.predictions || []);
      setIsMock(!!data.is_mock);
      setSourceUrls({ list: data.racelist_url, before: data.beforeinfo_url });
      setRoughAlerts(data.rough_alerts || []);
      setIsFetched(true);
    } catch (err) {
      setError('データの取得に失敗しました。');
    } finally {
      setTimeout(() => setLoading(false), 600);
    }
  };

  useEffect(() => {
    fetchSchedule();
    setIsFetched(false);
  }, [date]);

  useEffect(() => {
    setIsFetched(false);
  }, [jcd, rno]);

  const minExh = racers.length ? Math.min(...racers.map(r => r.exhibition_time)) : 6.6;
  const sortedPredictions = [...predictions].sort((a,b) => b.score - a.score);

  return (
    <div className="app-container">
      {loading && (
        <div className="loading-overlay">
          <motion.div 
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            className="loading-spinner"
          />
          <p>データを取得中...</p>
        </div>
      )}

      {error && (
        <div className="error-banner">
          <Flag size={20} />
          {error}
          <button onClick={() => fetchData()}>再試行</button>
        </div>
      )}

      {isMock && (
        <div className="mock-badge">
          注意: 現在はモックデータを表示しています
        </div>
      )}

      {showPwaPrompt && (
        <div className="pwa-prompt">
          <div className="pwa-content">
            <Share size={20} />
            <span>ホーム画面に追加してアプリとして利用できます（共有 &gt; ホーム画面に追加）</span>
            <button onClick={() => setShowPwaPrompt(false)}>閉じる</button>
          </div>
        </div>
      )}

      <div className="schedule-bar">
        <div className="bar-label">
          <Clock size={14} /> 本日の開催
          <button className="btn-refresh-schedule" onClick={() => fetchSchedule()} title="開催情報を更新">
            <RotateCw size={12} />
          </button>
        </div>
        <div className="venue-list">
          {schedule.length > 0 ? schedule.map(v => (
            <div 
              key={v.jcd} 
              className={`venue-chip ${v.jcd === jcd ? 'is-active' : ''} ${v.status === '終了' || v.status === 'Cancelled' ? 'is-finished' : ''} grade-${v.grade || 'General'}`}
              onClick={() => {
                if (v.status === 'Cancelled') return; 
                setJcd(v.jcd);
                const nextR = v.next_race ? String(v.next_race) : "1";
                setRno(nextR);
                const currentDayNum = v.series_day_num || 1;
                setSeriesDay(currentDayNum);
                fetchData(v.jcd, nextR, currentDayNum);
              }}
              style={{ position: 'relative' }} 
            >
              {v.has_exh_data && (
                <span className="live-indicator-dot" title="展示データ受信中" />
              )}
              <span className="v-name">
                {v.grade && v.grade !== 'General' && (
                  <span className={`grade-badge ${v.grade.toLowerCase()}`}>{v.grade}</span>
                )}
                {v.name}
              </span>
              {v.status === 'canceled' ? (
                <span className="v-finished">中止順延</span>
              ) : v.status === '終了' ? (
                <span className="v-finished">終了</span>
              ) : (
                <span className="v-deadline">
                  {v.next_race}R <span className="v-time">{v.deadline}</span>
                </span>
              )}
            </div>
          )) : (
            <span style={{fontSize: '0.8rem', color: '#00f2ff', opacity: 0.9, paddingLeft: '10px'}}>
              開催情報をスキャン中...
            </span>
          )}
        </div>
      </div>

      <header className="glass-header">
        <div className="logo">
          <div className="icon">潤</div>
          <h1>BoatRace <span>Cockpit [FINAL]</span></h1>
        </div>
        
        {isFetched && racers.length > 0 && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="series-info-hud">
            <div className="series-hud-label">CURRENT_SERIES_DATA</div>
            <div className="series-hud-content">
              <span className="series-name">{schedule.find(v => v.jcd === jcd)?.series_name || '一般戦'}</span>
              <span className="series-day-badge">{schedule.find(v => v.jcd === jcd)?.series_day || '開催中'}</span>
            </div>
          </motion.div>
        )}

        <div className="race-selector">
          <div className="selector-item">
            <label>日付</label>
            <select value={date} onChange={e => setDate(e.target.value)}>
              {AVAILABLE_DATES.map(d => (
                <option key={d.value} value={d.value}>{d.label}</option>
              ))}
            </select>
          </div>
        </div>
      </header>

      <div className="control-bar-container">
        <div className="control-divider"></div>
        <div className="control-panels">
          <div className="series-day-panel">
            <span className="panel-label">節間</span>
            <div className="series-day-list">
              {Array.from({ length: (schedule.find(v => v.jcd === jcd)?.series_day_num || 1) }, (_, i) => i + 1).map(d => (
                <button key={d} className={`day-btn ${seriesDay === d ? 'is-active' : ''}`} onClick={() => { setSeriesDay(d); fetchData(jcd, rno, d); }}>
                  {d === (schedule.find(v => v.jcd === jcd)?.series_day_num) ? '今日' : `${d}日目`}
                </button>
              ))}
            </div>
          </div>
          
          <div className="vertical-divider"></div>

          <div className="race-number-panel">
            <span className="panel-label">レース番号</span>
            <div className="race-number-list">
              {[1,2,3,4,5,6,7,8,9,10,11,12].map(n => {
                const nextR = parseInt(schedule.find(v => v.jcd === jcd)?.next_race || "13");
                const isFinished = n < nextR && seriesDay === (schedule.find(v => v.jcd === jcd)?.series_day_num);
                return (
                  <button key={n} className={`race-btn ${rno === String(n) ? 'is-active' : ''} ${isFinished ? 'is-finished' : ''}`} onClick={() => { setRno(String(n)); fetchData(jcd, String(n), seriesDay); }}>
                    {n}<span className="unit">R</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {!isFetched && !loading ? (
        <div className="welcome-card">
          <div className="welcome-icon">噫</div>
          <h2>会場とレース番号を選択して、解析を開始してください</h2>
          <p>最新の出走表、展示タイム、選手コメントをリアルタイムに解析します。</p>
        </div>
      ) : (
        <main className="dashboard-layout">
          {roughAlerts && roughAlerts.length > 0 && (
            <div className="alerts-container">
              {roughAlerts.map((alert, idx) => (
                <motion.div key={idx} className={`alert-card ${alert.type}`} initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
                  {alert.message}
                </motion.div>
              ))}
            </div>
          )}
          <div className="info-row">
            <section className="glass-card racer-info-section">
              <h3><Flag size={20} /> 出走表 & 展示情報</h3>
              <div className="table-wrapper">
                <div className="cards-header">
                  <div>枠</div><div>選手名</div><div>勝率</div><div>平均ST</div><div>展示</div><div>1周</div><div>まわり</div><div>直線</div>
                </div>
                <div className="racer-cards-container">
                  {racers.map((r) => (
                    <div key={r.waku} className="racer-card">
                      <div className="col-waku"><div className={`w-badge w-${r.waku}`}>{r.waku}</div></div>
                      <div className="col-name">
                        <div className="racer-meta">{r.waku}号艇 {r.rank && <span className={`rank-badge rank-${r.rank.charAt(0)}`}>{r.rank}</span>}</div>
                        <div className="racer-full-name">{r.name}</div>
                        {r.series_results && r.series_results.length > 0 && (
                          <div className="series-history-bar">
                            {r.series_results.map((sr, idx) => (
                              <div key={idx} className={`sr-chip rank-${sr.rank}`} title={`${sr.date} ${sr.rno}R: ${sr.rank}着`}>{sr.rank}</div>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="col-stat">{r.rate_global.toFixed(2)}</div>
                      <div className="col-stat">{r.st_average.toFixed(2)}</div>
                      <div className="col-stat" style={{ color: r.exhibition_time === minExh ? '#ff4500' : 'inherit', fontWeight: '900' }}>{r.exhibition_time.toFixed(2)}</div>
                      <div className="col-stat text-lap">{r.lap_time ? r.lap_time.toFixed(2) : '-'}</div>
                      <div className="col-stat text-maw">{r.turn_time ? r.turn_time.toFixed(2) : '-'}</div>
                      <div className="col-stat text-str">{r.straight_time ? r.straight_time.toFixed(2) : '-'}</div>
                    </div>
                  ))}
                </div>
              </div>
            </section>
            <section className="glass-card comment-section">
              <h3><TrendingUp size={20} /> 選手コメント</h3>
              <div className="comment-list">
                {racers.map(r => (
                  <div key={r.waku} className="comment-row">
                    <div className={`w-badge w-${r.waku}`}>{r.waku}</div>
                    <div className="comment-text">
                      {r.comment ? r.comment.split('前日').map((part, i) => {
                        const cleanText = part.replace('当日', '').replace(':', '').replace('：', '').trim();
                        if (!cleanText && i === 1) return null;
                        return <div key={i} className={i === 0 ? 'c-today' : 'c-yesterday'}><span className="c-label">{i === 0 ? '当日:' : '前日:'}</span>{cleanText}</div>;
                      }) : <span className="no-comment">(コメントなし)</span>}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>
          <div className="simulators-row">
            <TimeVisualizer title="展示タイム" icon={<Timer size={18} />} timeKey="exhibition_time" racers={racers} />
            <TimeVisualizer title="まわり足" icon={<TrendingUp size={18} />} timeKey="turn_time" racers={racers} />
            <TimeVisualizer title="直線タイム" icon={<TrendingUp size={18} />} timeKey="straight_time" racers={racers} />
          </div>
          <div className="total-row"><TotalVisualizer racers={racers} /></div>
          <div className="predictions-row">
            <section className="glass-card predictions-section">
              <h2><Trophy size={24} /> AI 着順予測</h2>
              <div className="podium-box">
                {[1, 0, 2].map((idx) => {
                  const p = sortedPredictions[idx];
                  if (!p) return <div key={idx} className="podium-rank"></div>;
                  return (
                    <div key={p.waku} className={`podium-rank p-${idx === 0 ? '1st' : idx === 1 ? '2nd' : '3rd'}`}>
                      <div className={`w-badge w-${p.waku}`}>{p.waku}</div>
                      <div className="podium-base">{idx === 0 ? '1着' : idx === 1 ? '2着' : '3着'}</div>
                    </div>
                  );
                })}
              </div>
              <div className="score-bars">
                {sortedPredictions.map((p) => (
                  <div key={p.waku} className="score-row">
                    <div className={`w-badge w-${p.waku}`}>{p.waku}</div>
                    <div className="progress-container"><motion.div className="progress-fill" initial={{ width: 0 }} animate={{ width: `${(p.score / 120) * 100}%` }} /></div>
                    <div className="score-val">{p.score.toFixed(1)}</div>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </main>
      )}
    </div>
  );
}
// FORCE_DEPLOY_FINAL_V6_MANIFEST_202604070132
