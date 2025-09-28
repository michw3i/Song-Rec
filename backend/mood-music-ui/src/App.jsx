// App.jsx
// A tiny, single-file UI that:
//  - lets you pick a mood,
//  - shows Spotify tracks,
//  - lets you log the mood with a chosen track,
//  - manage favorites,
//  - view recent logs and basic stats.
//
// Everything is plain React + fetch; comments explain the why.

import { useEffect, useMemo, useState } from "react";
import {
  getRecs,
  logMood,
  getRecent,
  addFavorite,
  getFavorites,
  deleteFav,
  getStats,
} from "./api";

// A little card component for tracks to avoid repetition
function TrackCard({ track, onLog, onFav }) {
  return (
    <div className="card">
      <img className="cover" src={track.cover_url || ""} alt="" />
      <div className="meta">
        <div className="title">{track.title}</div>
        <div className="artist">{track.artist}</div>
        <div className="row">
          {/* Preview audio if Spotify provides one */}
          {track.preview_url ? (
            <audio controls src={track.preview_url} />
          ) : (
            <span className="muted">No preview</span>
          )}
        </div>
        <div className="row">
          <a className="btn" href={track.external_url} target="_blank" rel="noreferrer">
            Open in Spotify
          </a>
          <button className="btn" onClick={() => onLog(track)}>Log mood</button>
          <button className="btn" onClick={() => onFav(track)}>❤️ Favorite</button>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  // ---- app state ----
  const [mood, setMood] = useState("");        // chosen mood
  const [tracks, setTracks] = useState([]);    // current recommendations
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const [recent, setRecent] = useState([]);    // recent mood logs
  const [favs, setFavs] = useState([]);        // favorite tracks
  const [stats, setStats] = useState({ total: 0, by_mood: [] });

  const moods = useMemo(() => ["happy", "sad", "calm", "angry"], []);

  // Load side panels initially
  useEffect(() => {
    refreshRecent();
    refreshFavs();
    refreshStats();
  }, []);

  // ---- handlers ----
  async function pickMood(m) {
    setMood(m);
    setErr("");
    setLoading(true);
    try {
      const data = await getRecs(m, 5);
      if (data.error) setErr(data.error);
      setTracks(data.tracks || []);
    } catch (e) {
      setErr(e.message);
      setTracks([]);
    } finally {
      setLoading(false);
    }
  }

  async function handleLog(track) {
    try {
      await logMood(mood || "happy", track); // if user forgot to click a mood, default
      await refreshRecent();                 // show it immediately
      alert("Mood logged!");
    } catch (e) {
      alert("Log failed: " + e.message);
    }
  }

  async function handleFav(track) {
    try {
      await addFavorite({
        title: track.title,
        artist: track.artist,
        external_url: track.external_url,
        cover_url: track.cover_url,
        preview_url: track.preview_url,
      });
      await refreshFavs();
      alert("Added to favorites!");
    } catch (e) {
      alert("Favorite failed: " + e.message);
    }
  }

  async function refreshRecent() {
    try {
      const data = await getRecent(10);
      setRecent(data.items || []);
    } catch (e) {
      console.error(e);
    }
  }

  async function refreshFavs() {
    try {
      const data = await getFavorites();
      setFavs(data.items || []);
    } catch (e) {
      console.error(e);
    }
  }

  async function refreshStats() {
    try {
      const data = await getStats();
      setStats(data);
    } catch (e) {
      console.error(e);
    }
  }

  return (
    <div className="container">
      <h1>Mood → Music</h1>

      {/* Mood picker */}
      <div className="moods">
        {moods.map((m) => (
          <button
            key={m}
            className={`pill ${mood === m ? "active" : ""}`}
            onClick={() => pickMood(m)}
          >
            {m}
          </button>
        ))}
      </div>

      {/* Error + loading */}
      {err && <div className="error">⚠️ {err}</div>}
      {loading && <div className="loading">Loading recommendations…</div>}

      {/* Recommendations */}
      <h2>Recommendations {mood ? `for "${mood}"` : ""}</h2>
      {tracks.length === 0 && !loading && <div className="muted">Pick a mood to see tracks.</div>}
      <div className="grid">
        {tracks.map((t, i) => (
          <TrackCard key={i} track={t} onLog={handleLog} onFav={handleFav} />
        ))}
      </div>

      <div className="columns">
        {/* Recent logs */}
        <div className="panel">
          <h3>Recent logs</h3>
          <button className="link" onClick={refreshRecent}>↻ Refresh</button>
          <ul className="list">
            {recent.map((r) => (
              <li key={r.id}>
                <b>{r.mood}</b> — <span className="muted">{new Date(r.created_at).toLocaleString()}</span>
                {r.top_track?.title && (
                  <>
                    <br />
                    <a href={r.top_track.external_url} target="_blank" rel="noreferrer">
                      {r.top_track.title}
                    </a>{" "}
                    <span className="muted">by {r.top_track.artist}</span>
                  </>
                )}
              </li>
            ))}
            {recent.length === 0 && <li className="muted">No logs yet.</li>}
          </ul>
        </div>

        {/* Favorites */}
        <div className="panel">
          <h3>Favorites</h3>
          <button className="link" onClick={refreshFavs}>↻ Refresh</button>
          <ul className="list">
            {favs.map((f) => (
              <li key={f.id}>
                <a href={f.external_url} target="_blank" rel="noreferrer">{f.title}</a>
                <span className="muted"> — {f.artist}</span>
                <button className="tiny danger" onClick={async () => { await deleteFav(f.id); await refreshFavs(); }}>
                  delete
                </button>
              </li>
            ))}
            {favs.length === 0 && <li className="muted">No favorites yet.</li>}
          </ul>
        </div>

        {/* Stats */}
        <div className="panel">
          <h3>Stats</h3>
          <button className="link" onClick={refreshStats}>↻ Refresh</button>
          <div className="bars">
            {stats.by_mood?.map((row) => (
              <div className="barrow" key={row.mood}>
                <div className="barlabel">{row.mood}</div>
                <div className="bar" style={{ width: `${Math.max(5, (row.count / Math.max(1, stats.total)) * 100)}%` }}>
                  {row.count}
                </div>
              </div>
            ))}
            {(!stats.by_mood || stats.by_mood.length === 0) && (
              <div className="muted">No data yet.</div>
            )}
          </div>
        </div>
      </div>

      <footer>
        <span className="muted">API: {import.meta.env.VITE_API_URL}</span>
      </footer>
    </div>
  );
}
