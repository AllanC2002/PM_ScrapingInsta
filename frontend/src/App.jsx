import { useState } from "react";

const API_BASE = "http://localhost:8000";

function formatNumber(n) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
  return n.toLocaleString();
}

function PostCard({ post, index }) {
  const [imgError, setImgError] = useState(false);

  return (
    <div
      className="post-card"
      style={{ animationDelay: `${index * 60}ms` }}
      onClick={() => window.open(post.url, "_blank")}
    >
      <div className="post-image-wrapper">
        {!imgError ? (
          <img
            src={post.imagen_url}
            alt={post.caption || "Post de Instagram"}
            onError={() => setImgError(true)}
            loading="lazy"
          />
        ) : (
          <div className="img-fallback">
            <span>{post.tipo === "Video" ? "▶" : post.tipo === "Carrusel" ? "⧉" : "◻"}</span>
          </div>
        )}
        <div className="post-overlay">
          <div className="post-stats">
            <span>❤ {formatNumber(post.likes)}</span>
            <span>💬 {formatNumber(post.comentarios)}</span>
          </div>
        </div>
        <div className="post-type-badge">{post.tipo}</div>
      </div>
      <div className="post-meta">
        <p className="post-date">{post.fecha}</p>
        {post.caption && (
          <p className="post-caption">{post.caption.slice(0, 80)}{post.caption.length > 80 ? "…" : ""}</p>
        )}
      </div>
    </div>
  );
}

function ProfileHeader({ data }) {
  const [imgError, setImgError] = useState(false);

  return (
    <div className="profile-header">
      <div className="profile-pic-wrap">
        {!imgError ? (
          <img
            src={data.profile_pic}
            alt={data.username}
            className="profile-pic"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="profile-pic profile-pic-fallback">
            {data.username[0].toUpperCase()}
          </div>
        )}
        <div className="profile-ring" />
      </div>
      <div className="profile-info">
        <h2 className="profile-username">@{data.username}</h2>
        <p className="profile-fullname">{data.full_name}</p>
        {data.bio && <p className="profile-bio">{data.bio}</p>}
        <div className="profile-stats">
          <div className="stat">
            <span className="stat-value">{formatNumber(data.followers)}</span>
            <span className="stat-label">seguidores</span>
          </div>
          <div className="stat-divider" />
          <div className="stat">
            <span className="stat-value">{formatNumber(data.following)}</span>
            <span className="stat-label">siguiendo</span>
          </div>
          <div className="stat-divider" />
          <div className="stat">
            <span className="stat-value">{data.posts.length}</span>
            <span className="stat-label">posts cargados</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [username, setUsername]   = useState("");
  const [numPosts, setNumPosts]   = useState(10);
  const [loading, setLoading]     = useState(false);
  const [data, setData]           = useState(null);
  const [error, setError]         = useState("");

  const handleSearch = async () => {
    const u = username.trim().replace(/^@/, "");
    if (!u) return;

    setLoading(true);
    setError("");
    setData(null);

    try {
      const res = await fetch(`${API_BASE}/scrape/${u}?num_posts=${numPosts}`);
      const json = await res.json();

      if (!res.ok) {
        throw new Error(json.detail || `Error ${res.status}`);
      }

      setData(json);
    } catch (err) {
      setError(err.message || "Error al conectar con el servidor.");
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter") handleSearch();
  };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        :root {
          --bg:        #0a0a0f;
          --surface:   #111118;
          --border:    #1e1e2a;
          --accent:    #e8ff47;
          --accent2:   #ff6b6b;
          --text:      #f0f0f5;
          --muted:     #6b6b80;
          --card-bg:   #13131c;
          --radius:    12px;
        }

        body {
          background: var(--bg);
          color: var(--text);
          font-family: 'DM Sans', sans-serif;
          min-height: 100vh;
          overflow-x: hidden;
        }

        /* ── Noise texture overlay ── */
        body::before {
          content: '';
          position: fixed;
          inset: 0;
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
          pointer-events: none;
          z-index: 0;
          opacity: 0.4;
        }

        .app {
          position: relative;
          z-index: 1;
          max-width: 1100px;
          margin: 0 auto;
          padding: 48px 24px 80px;
        }

        /* ── Header ── */
        .app-header {
          text-align: center;
          margin-bottom: 56px;
        }

        .app-eyebrow {
          display: inline-block;
          font-family: 'DM Sans', sans-serif;
          font-size: 11px;
          font-weight: 500;
          letter-spacing: 0.2em;
          text-transform: uppercase;
          color: var(--accent);
          border: 1px solid var(--accent);
          padding: 4px 14px;
          border-radius: 100px;
          margin-bottom: 20px;
        }

        .app-title {
          font-family: 'Syne', sans-serif;
          font-size: clamp(2.4rem, 6vw, 4.5rem);
          font-weight: 800;
          line-height: 1;
          letter-spacing: -0.03em;
          color: var(--text);
        }

        .app-title span {
          color: var(--accent);
        }

        .app-subtitle {
          margin-top: 16px;
          font-size: 15px;
          color: var(--muted);
          font-weight: 300;
        }

        /* ── Search box ── */
        .search-box {
          display: flex;
          gap: 12px;
          max-width: 600px;
          margin: 0 auto 16px;
          flex-wrap: wrap;
        }

        .input-wrap {
          flex: 1;
          position: relative;
          min-width: 200px;
        }

        .input-at {
          position: absolute;
          left: 16px;
          top: 50%;
          transform: translateY(-50%);
          color: var(--accent);
          font-family: 'Syne', sans-serif;
          font-weight: 700;
          font-size: 18px;
          pointer-events: none;
        }

        input[type="text"] {
          width: 100%;
          background: var(--surface);
          border: 1px solid var(--border);
          color: var(--text);
          font-family: 'DM Sans', sans-serif;
          font-size: 15px;
          padding: 14px 16px 14px 36px;
          border-radius: var(--radius);
          outline: none;
          transition: border-color 0.2s;
        }

        input[type="text"]:focus {
          border-color: var(--accent);
        }

        .posts-select {
          background: var(--surface);
          border: 1px solid var(--border);
          color: var(--muted);
          font-family: 'DM Sans', sans-serif;
          font-size: 14px;
          padding: 14px 16px;
          border-radius: var(--radius);
          outline: none;
          cursor: pointer;
          transition: border-color 0.2s;
        }

        .posts-select:focus {
          border-color: var(--accent);
          color: var(--text);
        }

        .btn-search {
          background: var(--accent);
          color: #0a0a0f;
          border: none;
          font-family: 'Syne', sans-serif;
          font-weight: 700;
          font-size: 14px;
          letter-spacing: 0.05em;
          padding: 14px 28px;
          border-radius: var(--radius);
          cursor: pointer;
          transition: opacity 0.2s, transform 0.15s;
          white-space: nowrap;
        }

        .btn-search:hover:not(:disabled) { opacity: 0.88; transform: translateY(-1px); }
        .btn-search:active:not(:disabled) { transform: translateY(0); }
        .btn-search:disabled { opacity: 0.4; cursor: not-allowed; }

        /* ── Error ── */
        .error-box {
          max-width: 600px;
          margin: 24px auto 0;
          background: rgba(255, 107, 107, 0.1);
          border: 1px solid rgba(255, 107, 107, 0.3);
          color: var(--accent2);
          padding: 14px 20px;
          border-radius: var(--radius);
          font-size: 14px;
          text-align: center;
        }

        /* ── Loading ── */
        .loading-wrap {
          text-align: center;
          padding: 80px 0;
        }

        .spinner {
          width: 40px;
          height: 40px;
          border: 2px solid var(--border);
          border-top-color: var(--accent);
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
          margin: 0 auto 20px;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        .loading-text {
          color: var(--muted);
          font-size: 14px;
          letter-spacing: 0.1em;
          text-transform: uppercase;
        }

        /* ── Profile header ── */
        .profile-header {
          display: flex;
          align-items: center;
          gap: 32px;
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 20px;
          padding: 32px;
          margin-bottom: 40px;
          animation: fadeUp 0.4s ease both;
        }

        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(16px); }
          to   { opacity: 1; transform: translateY(0); }
        }

        .profile-pic-wrap {
          position: relative;
          flex-shrink: 0;
        }

        .profile-pic {
          width: 88px;
          height: 88px;
          border-radius: 50%;
          object-fit: cover;
          display: block;
        }

        .profile-pic-fallback {
          width: 88px;
          height: 88px;
          border-radius: 50%;
          background: var(--border);
          display: flex;
          align-items: center;
          justify-content: center;
          font-family: 'Syne', sans-serif;
          font-size: 32px;
          font-weight: 800;
          color: var(--accent);
        }

        .profile-ring {
          position: absolute;
          inset: -3px;
          border-radius: 50%;
          border: 2px solid var(--accent);
          pointer-events: none;
        }

        .profile-username {
          font-family: 'Syne', sans-serif;
          font-weight: 700;
          font-size: 22px;
          letter-spacing: -0.02em;
          color: var(--text);
        }

        .profile-fullname {
          color: var(--muted);
          font-size: 14px;
          margin-top: 2px;
        }

        .profile-bio {
          color: var(--text);
          font-size: 13px;
          font-weight: 300;
          margin-top: 8px;
          max-width: 400px;
          line-height: 1.5;
        }

        .profile-stats {
          display: flex;
          align-items: center;
          gap: 20px;
          margin-top: 16px;
        }

        .stat { text-align: center; }

        .stat-value {
          display: block;
          font-family: 'Syne', sans-serif;
          font-weight: 700;
          font-size: 18px;
          color: var(--accent);
        }

        .stat-label {
          font-size: 11px;
          color: var(--muted);
          text-transform: uppercase;
          letter-spacing: 0.1em;
        }

        .stat-divider {
          width: 1px;
          height: 32px;
          background: var(--border);
        }

        /* ── Grid ── */
        .section-title {
          font-family: 'Syne', sans-serif;
          font-size: 13px;
          font-weight: 600;
          letter-spacing: 0.15em;
          text-transform: uppercase;
          color: var(--muted);
          margin-bottom: 20px;
        }

        .posts-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 16px;
        }

        /* ── Post card ── */
        .post-card {
          background: var(--card-bg);
          border: 1px solid var(--border);
          border-radius: var(--radius);
          overflow: hidden;
          cursor: pointer;
          transition: transform 0.2s, border-color 0.2s;
          animation: fadeUp 0.4s ease both;
        }

        .post-card:hover {
          transform: translateY(-4px);
          border-color: var(--accent);
        }

        .post-image-wrapper {
          position: relative;
          aspect-ratio: 1 / 1;
          overflow: hidden;
          background: var(--surface);
        }

        .post-image-wrapper img {
          width: 100%;
          height: 100%;
          object-fit: cover;
          display: block;
          transition: transform 0.4s ease;
        }

        .post-card:hover .post-image-wrapper img {
          transform: scale(1.05);
        }

        .img-fallback {
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 40px;
          color: var(--muted);
        }

        .post-overlay {
          position: absolute;
          inset: 0;
          background: rgba(0,0,0,0.55);
          display: flex;
          align-items: center;
          justify-content: center;
          opacity: 0;
          transition: opacity 0.25s;
        }

        .post-card:hover .post-overlay { opacity: 1; }

        .post-stats {
          display: flex;
          gap: 24px;
          color: #fff;
          font-family: 'Syne', sans-serif;
          font-weight: 700;
          font-size: 15px;
        }

        .post-type-badge {
          position: absolute;
          top: 10px;
          right: 10px;
          background: rgba(0,0,0,0.7);
          color: var(--accent);
          font-size: 10px;
          font-weight: 600;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          padding: 3px 8px;
          border-radius: 100px;
          border: 1px solid rgba(232,255,71,0.3);
        }

        .post-meta {
          padding: 12px 14px 14px;
        }

        .post-date {
          font-size: 11px;
          color: var(--muted);
          letter-spacing: 0.05em;
          margin-bottom: 4px;
        }

        .post-caption {
          font-size: 12px;
          color: var(--text);
          font-weight: 300;
          line-height: 1.4;
          opacity: 0.7;
        }

        @media (max-width: 600px) {
          .profile-header { flex-direction: column; text-align: center; }
          .profile-stats { justify-content: center; }
          .search-box { flex-direction: column; }
          .btn-search { width: 100%; }
        }
      `}</style>

      <div className="app">
        <header className="app-header">
          <div className="app-eyebrow">Instagram Scraper</div>
          <h1 className="app-title">
            Explora cualquier<br /><span>perfil público</span>
          </h1>
          <p className="app-subtitle">Ingresa un usuario y visualiza sus publicaciones al instante</p>
        </header>

        <div className="search-box">
          <div className="input-wrap">
            <span className="input-at">@</span>
            <input
              type="text"
              placeholder="usuario"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onKeyDown={handleKey}
              disabled={loading}
            />
          </div>
          <select
            className="posts-select"
            value={numPosts}
            onChange={(e) => setNumPosts(Number(e.target.value))}
            disabled={loading}
          >
            {[5, 10, 15, 20].map(n => (
              <option key={n} value={n}>{n} posts</option>
            ))}
          </select>
          <button
            className="btn-search"
            onClick={handleSearch}
            disabled={loading || !username.trim()}
          >
            {loading ? "Buscando..." : "Buscar →"}
          </button>
        </div>

        {error && <div className="error-box">⚠ {error}</div>}

        {loading && (
          <div className="loading-wrap">
            <div className="spinner" />
            <p className="loading-text">Obteniendo posts...</p>
          </div>
        )}

        {data && !loading && (
          <div>
            <ProfileHeader data={data} />
            <p className="section-title">Publicaciones recientes</p>
            <div className="posts-grid">
              {data.posts.map((post, i) => (
                <PostCard key={post.id || i} post={post} index={i} />
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
}