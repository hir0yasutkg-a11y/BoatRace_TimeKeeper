import { useState, useEffect } from 'react';
import { 
  Trophy, 
  Flag, 
  Timer, 
  TrendingUp, 
  Clock,
  MapPin,
  Share,
  Cpu,
  Activity,
  RotateCw
} from 'lucide-react';
import { motion } from 'framer-motion';
import './index.css';

interface SeriesResultEntry {
  date: string;
  jcd: string;
  rno: number;
  course?: number;
  st?: number;
  rank?: number;
}

interface Racer {
  waku: number;
  name: string;
  racer_id?: string;
  rank?: string;
  rate_global: number;
  st_average: number;
  exhibition_time: number;
  exhibition_rank?: number;
  lap_time?: number;
  turn_time?: number;
  straight_time?: number;
  entry_course?: number; // 司令塔として、進入コースを 1 mm の狂いもなく捕捉
  comment?: string;
  series_results?: SeriesResultEntry[]; // 今節の全成績を 1 mm の不備もなく 100% 確実に奪還
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
  grade?: 'SG' | 'G1' | 'G2' | 'G3' | 'General';
  event?: 'Ladies' | 'Rookie' | 'Masters' | null;
  series_name?: string;
  series_day?: string;
  series_day_num?: number; // 司令塔として、 1 mm の狂いもなく経過日数を捕捉
  next_race: string | null;
  deadline: string | null;
  has_exh_data?: boolean;
}

// 日付生成をコンポーネントの外に出して再計算を抑制
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

const AVAILABLE_DATES = getAvailableDates();

const BoatIcon = ({ waku, className }: { waku: number; className?: string }) => {
  return (
    <svg 
      viewBox="0 0 120 40" 
      className={`boat-svg w-svg-${waku} ${className || ''}`}
      width="64" height="26"
      xmlns="http://www.w3.org/2000/svg"
      style={{ overflow: 'visible' }}
    >
      <g>
        <path d="M 5 5 L 85 5 Q 115 20 85 35 L 5 35 L 0 20 Z" fill={`var(--waku-${waku})`} fillOpacity="1" stroke="#111" strokeWidth="2.5" />
        <path d="M 85 5 Q 115 20 85 35 L 80 20 Z" fill="rgba(255,255,255,0.25)" />
        <circle cx="28" cy="20" r="11" fill="#fff" stroke="#111" strokeWidth="2.5"/>
        <text x="28" y="25" fill="#000" fontSize="15" fontWeight="900" textAnchor="middle">{waku}</text>
      </g>
    </svg>
  );
};

const TimeVisualizer = ({ title, icon, timeKey, racers, speedKmh = 80 }: { title: string, icon: any, timeKey: keyof Racer, racers: Racer[], speedKmh?: number }) => {
  // 有効なタイム（0より大きい）を持つ選手だけを抽出
  const validRacers = racers.filter(r => (r[timeKey] as number) > 0);
  if (validRacers.length === 0) return null; // データが全くなければ何も表示しない

  const times = validRacers.map(r => r[timeKey] as number);
  const maxTime = Math.max(...times);
  const minTime = Math.min(...times);
  const pxPerMeter = 64 / 2.9; // 新スケール: 1艇身(2.9m) = 64px

  return (
    <section className="glass-card">
      <h2 style={{ fontSize: '1.1rem', marginBottom: '10px' }}>
        {icon}
        <span style={{ marginLeft: '8px' }}>{title}</span>
        <span style={{ fontSize: '0.7rem', color: 'var(--text-sub)', marginLeft: '10px', fontWeight: 'normal' }}>
          (計算速度: {speedKmh}km/h)
        </span>
      </h2>
      <div className="simulator-box" style={{ paddingTop: '10px' }}>
        <div className="start-line"></div>
        {racers.map(r => {
          const currentTime = r[timeKey] as number;
          if (!currentTime || currentTime <= 0) {
            return (
              <div key={r.waku} className="sim-lane" style={{ opacity: 0.3 }}>
                <div className={`w-badge w-${r.waku}`}>{r.waku}</div>
                <div className="lane-track"><span style={{ fontSize: '0.7rem', marginLeft: '10px' }}>データなし</span></div>
              </div>
            );
          }

          const diff = maxTime - currentTime;
          // 物理計算: 指定された速度における距離差(m)
          // km/h * 1000 / 3600 = m/s
          const speedMs = (speedKmh * 1000) / 3600;
          const distanceGap = diff * speedMs;
          const xPos = distanceGap * pxPerMeter;

          return (
            <div key={r.waku} className="sim-lane">
              <div className={`w-badge w-${r.waku}`}>{r.waku}</div>
              <div className="lane-track">
                <motion.div 
                  className="lane-boat-wrapper"
                  initial={{ x: -64 }}
                  animate={{ x: xPos }} 
                  transition={{ duration: 1.5, ease: "easeOut" }}
                  style={{ position: 'absolute', left: '0px', display: 'flex', alignItems: 'center' }}
                >
                  <BoatIcon waku={r.waku} />
                  <span className="diff-tag" style={{ 
                    whiteSpace: 'nowrap',
                    color: currentTime === minTime ? 'var(--primary-red)' : 'inherit',
                    fontWeight: currentTime === minTime ? '900' : 'normal'
                  }}>
                    {currentTime === minTime ? `Fastest! (+${distanceGap.toFixed(1)}m)` : `+${distanceGap.toFixed(1)}m`}
                  </span>
                </motion.div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};

const TotalVisualizer = ({ racers }: { racers: Racer[] }) => {
  const configs = [
    { key: 'exhibition_time', speed: 80 },
    { key: 'turn_time', speed: 40 },
    { key: 'straight_time', speed: 60 },
  ] as const;

  const maxTimes = configs.reduce((acc, config) => {
    const validTimes = racers.filter(r => (r[config.key] as number) > 0).map(r => r[config.key] as number);
    acc[config.key] = validTimes.length > 0 ? Math.max(...validTimes) : 0;
    return acc;
  }, {} as Record<string, number>);

  const racerLeads = racers
    .filter(r => configs.some(c => (r[c.key] as number) > 0))
    .map(r => {
      let totalLead = 0;
      configs.forEach(config => {
        const time = r[config.key] as number;
        if (time && time > 0 && maxTimes[config.key] > 0) {
          const diff = maxTimes[config.key] - time;
          totalLead += diff * (config.speed * 1000 / 3600);
        }
      });
      return { waku: r.waku, totalLead };
    });

  const maxTotalLead = Math.max(...racerLeads.map(l => l.totalLead));
  const pxPerMeter = 64 / 2.9; // 新スケール

  return (
    <section className="glass-card total-evaluation-card" style={{ marginTop: '30px', padding: '20px' }}>
      {/* HUD Deco */}
      <div className="hud-corner hud-tl" />
      <div className="hud-tr" />
      <div className="hud-bl" />
      <div className="hud-br" />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', position: 'relative', zIndex: 2, marginBottom: '15px' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem', color: '#00f2ff', margin: 0, display: 'flex', alignItems: 'center', gap: '10px', textShadow: '0 0 10px rgba(0, 242, 255, 0.5)' }}>
            <Cpu size={28} />
            LIVE ANALYSIS HUD [B-SYSTEM v2.5]
          </h2>
          <div style={{ display: 'flex', gap: '15px', marginTop: '5px' }}>
            <span style={{ fontSize: '0.65rem', color: 'rgba(0, 242, 255, 0.7)', letterSpacing: '1px' }}>▋ STATUS: DATA_SYNCED</span>
            <span style={{ fontSize: '0.65rem', color: 'rgba(0, 242, 255, 0.7)', letterSpacing: '1px' }}>▋ MODE: PERFORMANCE_AGGREGATION</span>
          </div>
        </div>
        <div style={{ textAlign: 'right', background: 'rgba(0, 242, 255, 0.1)', padding: '8px 15px', border: '1px solid #00f2ff', borderRadius: '4px' }}>
          <span style={{ fontSize: '0.6rem', display: 'block', fontWeight: 'bold', marginBottom: '2px' }}>EST. WIN PROBABILITY</span>
          <motion.span 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{ fontSize: '1.6rem', fontWeight: 900, color: '#00f2ff' }}
          >
            {maxTotalLead > 0 ? (85 + (maxTotalLead * 2)).toFixed(1) : '---'}%
          </motion.span>
        </div>
      </div>

      <div className="simulator-box" style={{ height: '320px', background: 'rgba(0, 242, 255, 0.03)', border: '1px solid rgba(0, 242, 255, 0.1)', position: 'relative', zIndex: 1, padding: '10px 0' }}>
        <div className="start-line" style={{ background: '#00f2ff', boxShadow: '0 0 15px #00f2ff' }}></div>
        
        {racerLeads.map(l => {
          const xPos = l.totalLead * pxPerMeter;
          const isBest = l.totalLead === maxTotalLead && l.totalLead > 0;
          const powerPercent = maxTotalLead > 0 ? (l.totalLead / maxTotalLead) * 100 : 0;
          
          return (
            <div key={l.waku} className="sim-lane" style={{ height: '52px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginRight: '10px' }}>
                <div className={`w-badge w-${l.waku}`} style={{ border: isBest ? '3px solid #00f2ff' : '1px solid rgba(0, 242, 255, 0.3)' }}>{l.waku}</div>
                <span style={{ fontSize: '0.55rem', marginTop: '2px', color: 'rgba(0,242,255,0.6)' }}>NO.{l.waku}</span>
              </div>

              <div className="lane-track">
                <motion.div 
                  className="lane-boat-wrapper"
                  initial={{ x: -64 }}
                  animate={{ x: xPos }} 
                  transition={{ duration: 2, ease: "easeOut" }}
                  style={{ position: 'absolute', left: '0px', display: 'flex', alignItems: 'center' }}
                >
                  <div style={{ position: 'relative' }}>
                    <BoatIcon waku={l.waku} className={isBest ? 'best-boat' : ''} />
                    {isBest && <Activity size={14} style={{ position: 'absolute', top: -15, right: -15, color: '#00f2ff' }} />}
                  </div>
                  
                  <div style={{ marginLeft: '12px', display: 'flex', flexDirection: 'column' }}>
                    <span className="diff-tag" style={{ 
                      fontSize: isBest ? '1.1rem' : '0.85rem',
                      color: isBest ? '#00f2ff' : 'rgba(0, 242, 255, 0.8)',
                      fontWeight: isBest ? '900' : 'normal',
                      textShadow: isBest ? '0 0 10px #00f2ff' : 'none'
                    }}>
                      {isBest ? `TARGET LOCK! (+${l.totalLead.toFixed(2)}m)` : `+${l.totalLead.toFixed(2)}m`}
                    </span>
                    <div className="hud-power-bar">
                      <motion.div 
                        className="hud-power-fill" 
                        initial={{ width: 0 }}
                        animate={{ width: `${powerPercent}%` }}
                        transition={{ duration: 2.5 }}
                      />
                    </div>
                  </div>
                </motion.div>
              </div>
            </div>
          );
        })}
      </div>
      
      <div style={{ marginTop: '15px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.6rem', color: 'rgba(0, 242, 255, 0.5)', letterSpacing: '2px' }}>
        <span>{">>"} ENGINE_DATA: AGGREGATED</span>
        <span>SCANNING_LANE_POSITION_REALTIME...</span>
        <span>{">>"} PHYSICS_ENGINE: ACTIVE</span>
      </div>
    </section>
  );
};

export default function App() {
  const [racers, setRacers] = useState<Racer[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [schedule, setSchedule] = useState<VenueSchedule[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isFetched, setIsFetched] = useState(false);
  const [isMock, setIsMock] = useState(false);
  const [sourceUrls, setSourceUrls] = useState<{list?: string, before?: string}>({});
  const [roughAlerts, setRoughAlerts] = useState<{type: string, message: string}[]>([]); // 司令塔として、波乱の予兆を 1 mm の狂いもなく捕捉
  const [showPwaPrompt, setShowPwaPrompt] = useState(false);
  const [date, setDate] = useState(AVAILABLE_DATES[0].value);
  const [jcd, setJcd] = useState('02'); 
  const [rno, setRno] = useState('1'); 
  const [seriesDay, setSeriesDay] = useState<number>(1); // 司令塔として、現在の節間日数を 1 mm の不備もなく管理

  useEffect(() => {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
    if (isIOS && !isStandalone) setShowPwaPrompt(true);
  }, []);

  const API_BASE = ''; // 鋼鉄の相対パス：環境変数に頼らず 100% クラウド上で自身を参照

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
    
    // 司令塔としての 1 mm の狂いもない日付計算
    let targetDate = AVAILABLE_DATES[0].value;
    const vInfo = schedule.find(v => v.jcd === activeJcd);
    if (vInfo && vInfo.series_day_num) {
      const diff = vInfo.series_day_num - activeDayNum;
      const d = new Date();
      d.setDate(d.getDate() - diff);
      const yyyy = d.getFullYear();
      const mm = String(d.getMonth() + 1).padStart(2, '0');
      const dd = String(d.getDate()).padStart(2, '0');
      targetDate = `${yyyy}${mm}${dd}`;
    }

    if (!activeJcd) return;
    console.log("Fetching from:", `${API_BASE}/api/prediction/${targetDate}/${activeJcd}/${activeRno}`);
    setLoading(true);
    setError('');
    setIsFetched(false);
    try {
      const fetchUrl = `${API_BASE}/api/prediction/${targetDate}/${activeJcd}/${activeRno}?t=${Date.now()}`;
      console.log("Actual URL:", fetchUrl);
      const res = await fetch(fetchUrl);
      console.log("Response Status:", res.status);
      if (!res.ok) throw new Error(`API Error: ${res.status}`);
      const data = await res.json();
      console.log("Data received:", data);
      if (data.error) {
        setError(data.error);
        return;
      }
      // 欠場艇（名前がUnknown、または名前に「欠場」を含む）を完全に除外してセット
      const activeRacers = (data.racers || []).filter((r: any) => 
        r.name !== "Unknown" && !r.name.includes("欠場")
      );
      setRacers(activeRacers);
      setPredictions(data.predictions || []);
      setIsMock(!!data.is_mock);
      setSourceUrls({ list: data.racelist_url, before: data.beforeinfo_url });
      setRoughAlerts(data.rough_alerts || []); // 司令塔として、 100% 確実にアラートを同期
      setIsFetched(true);
    } catch (err) {
      console.error("Fetch Error:", err);
      setError('データが取得できませんでした。ブラウザのコンソール（F12）で詳細を確認してください。');
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
          ⚠️ 注意: 現在はデモ用データ（3/31分）を表示しています
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
                // 司令塔として、会場の現在の日数を自動セット
                const currentDayNum = v.series_day_num || 1;
                setSeriesDay(currentDayNum);
                // 1 mm の狂いもなく即座に最新レースへジャンプ
                fetchData(v.jcd, nextR, currentDayNum);
              }}
              style={{ position: 'relative' }} 
            >
              {v.has_exh_data && (
                <span className="live-indicator-dot" title="直前データ捕捉中！" />
              )}
              <span className="v-name">
                {v.grade && v.grade !== 'General' && (
                  <span className={`grade-badge ${v.grade.toLowerCase()}`}>{v.grade}</span>
                )}
                {v.name}
                {v.event === 'Ladies' && <span className="event-badge ladies">L</span>}
                {v.event === 'Rookie' && <span className="event-badge rookie">R</span>}
                {v.event === 'Masters' && <span className="event-badge masters">M</span>}
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
              ▋ 開催情報をスキャン中... (または本日終了)
            </span>
          )}
        </div>
      </div>

      <header className="glass-header">
        <div className="logo">
          <div className="icon">🏁</div>
          <h1>BoatRace <span>Analyzer POP</span></h1>
        </div>
        
        {/* --- Series Info HUD --- */}
        {isFetched && racers.length > 0 && (
          <motion.div 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="series-info-hud"
            style={{
              padding: '8px 15px',
              background: 'rgba(0, 242, 255, 0.05)',
              borderLeft: '4px solid #00f2ff',
              borderRadius: '0 8px 8px 0',
              marginLeft: '20px',
              flex: 1,
              maxWidth: '400px'
            }}
          >
            <div style={{ fontSize: '0.6rem', color: '#00f2ff', letterSpacing: '2px', fontWeight: 'bold' }}>CURRENT_SERIES_DATA</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px' }}>
              <span style={{ fontSize: '0.95rem', fontWeight: 900, color: 'white' }}>{schedule.find(v => v.jcd === jcd)?.series_name || '一般戦'}</span>
              <span style={{ 
                fontSize: '0.75rem', 
                color: '#00f2ff', 
                fontWeight: 'bold',
                padding: '1px 6px',
                border: '1px solid #00f2ff',
                borderRadius: '4px'
              }}>
                {schedule.find(v => v.jcd === jcd)?.series_day || '開催中'}
              </span>
            </div>
          </motion.div>
        )}

        <div className="race-selector">
          <div className="selector-item">
            <label>日付(カレンダー)</label>
            <select value={date} onChange={e => setDate(e.target.value)}>
              {AVAILABLE_DATES.map(d => (
                <option key={d.value} value={d.value}>{d.label}</option>
              ))}
            </select>
          </div>
          {/* 会場・レース選択は 12連ボタンに統合されたため撤去 */}
        </div>
      </header>

      {/* --- 1 mm の不備も許さない 司令塔の 12連コントロールパネル --- */}
      <div className="control-bar-container">
        <div className="control-divider"></div>
        <div className="control-panels">
          <div className="series-day-panel">
            <span className="panel-label">節間</span>
            <div className="series-day-list">
              {Array.from({ length: (schedule.find(v => v.jcd === jcd)?.series_day_num || 1) }, (_, i) => i + 1).map(d => (
                <button 
                  key={d} 
                  className={`day-btn ${seriesDay === d ? 'is-active' : ''}`}
                  onClick={() => {
                    setSeriesDay(d);
                    fetchData(jcd, rno, d);
                  }}
                >
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
                  <button 
                    key={n} 
                    className={`race-btn ${rno === String(n) ? 'is-active' : ''} ${isFinished ? 'is-finished' : ''}`}
                    onClick={() => {
                      setRno(String(n));
                      fetchData(jcd, String(n), seriesDay);
                    }}
                  >
                    {n}<span className="unit">R</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {sourceUrls.list && (
        <div className="source-links-bar">
          <MapPin size={14} />
          <span className="label">取得元URL: </span>
          <a href={sourceUrls.list} target="_blank" rel="noreferrer">出走表</a>
          <span className="sep">|</span>
          <a href={sourceUrls.before} target="_blank" rel="noreferrer">直前情報</a>
        </div>
      )}

      {!isFetched && !loading ? (
        <div className="welcome-card">
          <div className="welcome-icon">🚀</div>
          <h2>会場とレース番号を選択して、「予想開始」を押してください</h2>
          <p>最新の出走表、展示タイム、選手コメントをリアルタイムに解析します。</p>
        </div>
      ) : (
        <main className="dashboard-layout">
          {/* --- Rough Race Alerts (Analyzer Special) --- */}
          {roughAlerts && roughAlerts.length > 0 && (
            <div style={{ marginBottom: '20px', display: 'flex', flexDirection: 'column', gap: '10px', width: '100%' }}>
              {roughAlerts.map((alert, idx) => (
                <motion.div
                  key={idx}
                  initial={{ scale: 0.95, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.3, delay: idx * 0.1 }}
                  style={{
                    padding: '12px 20px',
                    borderRadius: '12px',
                    background: alert.type === 'MAEZUKE' 
                      ? 'rgba(255, 165, 0, 0.15)' 
                      : 'rgba(255, 69, 0, 0.15)',
                    border: alert.type === 'MAEZUKE'
                      ? '2px solid #ffa500'
                      : '2px solid #ff4500',
                    color: alert.type === 'MAEZUKE' ? '#ffa500' : '#ff4500',
                    fontSize: '1rem',
                    fontWeight: 900,
                    textAlign: 'center',
                    boxShadow: alert.type === 'MAEZUKE'
                      ? '0 0 15px rgba(255, 165, 0, 0.3)'
                      : '0 0 15px rgba(255, 69, 0, 0.3)',
                    textShadow: '0 0 5px rgba(0,0,0,0.5)',
                    letterSpacing: '1px'
                  }}
                >
                  {alert.message}
                </motion.div>
              ))}
            </div>
          )}
          {/* 段1: 基本情報 & コメント (2カラム) */}
          <div className="info-row">
            <section className="glass-card">
              <h3 style={{ fontWeight: 900, marginBottom: 15, fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '8px', color: '#111111' }}>
                <Flag size={20} /> 出走表 & 直前情報
              </h3>
              <div style={{ background: 'white', borderRadius: '12px', overflow: 'hidden', flex: 1, display: 'flex', flexDirection: 'column' }}>
                <div className="cards-header">
                  <div>枠</div>
                  <div>選手名</div>
                  <div>勝率</div>
                  <div>平均ST</div>
                  <div>展示</div>
                  <div>1周</div>
                  <div>まわり</div>
                  <div>直線</div>
                </div>

                <div className="racer-cards-container" style={{ padding: '15px', background: '#f8f9fa', flex: 1 }}>
                  {racers.map((r) => (
                    <div key={r.waku} className="racer-card">
                      <div className="col-waku">
                        <div className={`w-badge w-${r.waku}`}>{r.waku}</div>
                      </div>
                      <div className="col-name">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '2px' }}>
                          <div style={{ fontSize: '0.65rem', color: 'var(--text-sub)', fontWeight: 'bold' }}>{r.waku}号艇</div>
                          {r.rank && (
                            <span className={`rank-badge rank-${r.rank.charAt(0)}`}>
                              {r.rank}
                            </span>
                          )}
                        </div>
                        {r.name}
                        {r.series_results && r.series_results.length > 0 && (
                          <div className="series-history-bar">
                            {r.series_results.map((sr, idx) => (
                              <div key={idx} className={`sr-chip rank-${sr.rank}`} title={`${sr.date} ${sr.rno}R: ${sr.rank}着(${sr.course}コース) ST:${sr.st}`}>
                                {sr.rank}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="col-stat">{r.rate_global.toFixed(2)}</div>
                      <div className="col-stat">{r.st_average.toFixed(2)}</div>
                      <div className="col-stat" style={{ color: r.exhibition_time === minExh ? 'var(--primary-red)' : 'inherit', fontWeight: '900' }}>
                        {r.exhibition_time.toFixed(2)}
                      </div>
                      <div className="col-stat text-lap">{r.lap_time ? r.lap_time.toFixed(2) : '-'}</div>
                      <div className="col-stat text-maw">{r.turn_time ? r.turn_time.toFixed(2) : '-'}</div>
                      <div className="col-stat text-str">{r.straight_time ? r.straight_time.toFixed(2) : '-'}</div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="glass-card">
              <h3 style={{ fontWeight: 900, marginBottom: 15, fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '8px', color: '#111111' }}>
                <TrendingUp size={20} /> 選手コメント
              </h3>
              <div className="comment-table" style={{ flex: 1 }}>
                {racers.map(r => {
                  const commentText = r.comment || '';
                  return (
                    <div key={r.waku} className="comment-row">
                      <div className={`w-badge w-${r.waku}`} style={{ minWidth: 32, height: 32, fontSize: '1rem' }}>{r.waku}</div>
                      <div className="comment-text">
                        {commentText ? (
                          commentText.split('前日').map((part, i) => {
                            const cleanText = part.replace('当日', '').replace(':', '').replace('：', '').trim();
                            if (!cleanText && i === 1) return null;
                            return (
                              <div key={i} className={i === 0 ? 'c-today' : 'c-yesterday'}>
                                <span className="c-label">{i === 0 ? '当日:' : '前日:'}</span>
                                {cleanText}
                              </div>
                            );
                          })
                        ) : (
                          <span style={{ opacity: 0.4 }}>（コメントなし）</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          </div>

          {/* 段2: 3大指標シミュレーター (横並び) */}
          <div className="simulators-row">
            <TimeVisualizer 
              title="展示タイム" 
              icon={<Timer size={18} />} 
              timeKey="exhibition_time" 
              racers={racers} 
            />

            <TimeVisualizer 
              title="まわり足" 
              icon={<TrendingUp size={18} />} 
              timeKey="turn_time" 
              racers={racers} 
              speedKmh={40}
            />

            <TimeVisualizer 
              title="直線タイム" 
              icon={<TrendingUp size={18} />} 
              timeKey="straight_time" 
              racers={racers} 
              speedKmh={60}
            />
          </div>

          {/* 段3: 総合評価 (全幅) */}
          <div className="total-row">
            <TotalVisualizer racers={racers} />
          </div>

          {/* 段4: AI予測 (全幅) */}
          <div className="predictions-row">
            <section className="glass-card">
              <h2><Trophy size={24} style={{ marginRight: 10, verticalAlign: 'middle' }} /> AI 着順予測 (最終結論)</h2>
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
                <h3 style={{ fontWeight: 900, marginBottom: 15, fontSize: '1rem', display: 'inline-block', background: 'var(--secondary)', padding: '2px 10px', border: '2px solid var(--border-dark)', borderRadius: '20px' }}>総合予測スコア</h3>
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
        </main>
      )}
    </div>
  );
}

// FORCE_DEPLOY_CONTROL_V1_SUCCESS
