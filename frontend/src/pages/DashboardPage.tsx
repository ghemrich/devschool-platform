import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import type { DashboardCourse, Certificate, ModuleProgress, Course, User } from '../lib/types';
import { apiFetch } from '../lib/api';

function statusPrefix(status: string): string {
  switch (status) {
    case 'in_progress':
      return '✏️';
    case 'completed':
      return '✅';
    default:
      return '🔴';
  }
}

function statusLabel(status: string): string {
  switch (status) {
    case 'in_progress':
      return '(Folyamatban)';
    case 'completed':
      return '(Teljesített)';
    default:
      return '(Nincs elkezdve)';
  }
}

function statusColor(status: string): string {
  switch (status) {
    case 'completed':
      return 'green';
    case 'in_progress':
      return 'orange';
    default:
      return 'gray';
  }
}

export default function DashboardPage() {
  const [courses, setCourses] = useState<DashboardCourse[]>([]);
  const [certs, setCerts] = useState<Certificate[]>([]);
  const [progressMap, setProgressMap] = useState<Record<number, ModuleProgress[]>>({});
  const [courseDataMap, setCourseDataMap] = useState<Record<number, Course>>({});
  const [expandedModules, setExpandedModules] = useState<Record<number, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [syncMsg, setSyncMsg] = useState('');
  const [syncing, setSyncing] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [discordId, setDiscordId] = useState('');
  const [discordMsg, setDiscordMsg] = useState('');
  const [discordSaving, setDiscordSaving] = useState(false);

  const loadDashboard = useCallback(async () => {
    try {
      const [dashRes, certRes, meRes] = await Promise.all([
        fetch('/api/me/dashboard', { credentials: 'same-origin' }),
        fetch('/api/me/certificates', { credentials: 'same-origin' }),
        fetch('/api/auth/me', { credentials: 'same-origin' }),
      ]);

      if (dashRes.status === 401 || dashRes.status === 403) {
        window.location.href = '/login';
        return;
      }

      const dashData: DashboardCourse[] = await dashRes.json();
      const certData: Certificate[] = certRes.ok ? await certRes.json() : [];
      if (meRes.ok) {
        const userData = await meRes.json();
        setUser(userData);
        setDiscordId(userData.discord_id || '');
      }
      setCourses(dashData);
      setCerts(certData);

      const pMap: Record<number, ModuleProgress[]> = {};
      const cMap: Record<number, Course> = {};

      await Promise.all(
        dashData.map(async (c) => {
          const [progressRes, courseRes] = await Promise.all([
            fetch(`/api/me/courses/${c.course_id}/progress`, { credentials: 'same-origin' }),
            fetch(`/api/courses/${c.course_id}`, { credentials: 'same-origin' }),
          ]);
          if (progressRes.ok) pMap[c.course_id] = await progressRes.json();
          if (courseRes.ok) cMap[c.course_id] = await courseRes.json();
        }),
      );

      setProgressMap(pMap);
      setCourseDataMap(cMap);
    } catch {
      // error handled by empty state
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const handleSync = async () => {
    setSyncing(true);
    setSyncMsg('');
    try {
      const r = await apiFetch('/api/me/sync-progress', { method: 'POST' });
      if (r.ok) {
        setSyncMsg('Haladás frissítve!');
        setTimeout(() => window.location.reload(), 1000);
      } else {
        const d = await r.json();
        setSyncMsg(d.detail || 'Hiba történt.');
      }
    } catch {
      setSyncMsg('Hiba történt a szinkronizálás során.');
    } finally {
      setSyncing(false);
    }
  };

  const handleDownloadCert = async (certId: string) => {
    const r = await fetch(`/api/me/certificates/${certId}/pdf`, {
      credentials: 'same-origin',
    });
    if (r.ok) {
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `certificate-${certId}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } else {
      alert('Nem sikerült letölteni a PDF-et.');
    }
  };

  const handleRequestCert = async (courseId: number) => {
    const r = await fetch(`/api/me/courses/${courseId}/certificate`, {
      method: 'POST',
      credentials: 'same-origin',
    });
    if (r.status === 201) {
      window.location.reload();
    } else {
      const d = await r.json();
      alert(d.detail || 'Hiba történt.');
    }
  };

  const toggleModules = (courseId: number) => {
    setExpandedModules((prev) => ({ ...prev, [courseId]: !prev[courseId] }));
  };

  const certMap: Record<number, Certificate> = {};
  certs.forEach((c) => {
    certMap[c.course_id] = c;
  });

  if (loading)
    return (
      <div className="container page">
        <p>Betöltés...</p>
      </div>
    );

  return (
    <div className="container page">
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
        <h1 style={{ margin: 0 }}>Dashboard</h1>
        {user && (
          <span className={`role-badge role-badge--${user.role}`}>
            {user.role === 'admin'
              ? '🛡️ Admin'
              : user.role === 'mentor'
                ? '🎓 Mentor'
                : '📚 Tanuló'}
          </span>
        )}
      </div>
      <button
        className="btn btn-secondary"
        style={{ marginBottom: 20 }}
        onClick={handleSync}
        disabled={syncing}
      >
        {syncing ? '⏳ Szinkronizálás...' : '🔄 Haladás szinkronizálása GitHub-ból'}
      </button>
      {syncMsg && (
        <p style={{ color: syncMsg.includes('frissítve') ? 'green' : 'red' }}>{syncMsg}</p>
      )}

      <div className="card" style={{ marginBottom: 20, padding: 16 }}>
        <h3 style={{ marginTop: 0 }}>🔗 Discord összekapcsolás</h3>
        <p style={{ fontSize: '0.9rem', color: '#666', margin: '4px 0 12px' }}>
          Add meg a Discord felhasználói ID-dat a szerepkör szinkronizáláshoz. Discord Beállítások →
          Alkalmazás beállításai → Haladó → kapcsold be a Fejlesztői módot. Ezután menj vissza
          bármely szerverre, jobb klikk a nevedre a taglistában → ID másolása.
        </p>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <input
            type="text"
            placeholder="Discord User ID (pl. 123456789012345678)"
            value={discordId}
            onChange={(e) => setDiscordId(e.target.value)}
            style={{ padding: '6px 10px', borderRadius: 6, border: '1px solid #ccc', width: 300 }}
          />
          <button
            className="btn btn-primary"
            disabled={discordSaving}
            onClick={async () => {
              setDiscordSaving(true);
              setDiscordMsg('');
              try {
                const r = await fetch('/api/auth/me', {
                  method: 'PATCH',
                  credentials: 'same-origin',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ discord_id: discordId || '' }),
                });
                if (r.ok) {
                  setDiscordMsg(discordId ? 'Discord összekapcsolva!' : 'Discord leválasztva.');
                } else {
                  const d = await r.json();
                  setDiscordMsg(d.detail || 'Hiba történt.');
                }
              } catch {
                setDiscordMsg('Hiba történt.');
              } finally {
                setDiscordSaving(false);
              }
            }}
          >
            {discordSaving ? '⏳' : discordId ? 'Mentés' : 'Leválasztás'}
          </button>
        </div>
        {discordMsg && (
          <p style={{ color: discordMsg.includes('!') ? 'green' : 'red', marginTop: 8 }}>
            {discordMsg}
          </p>
        )}
      </div>

      {courses.length === 0 ? (
        <div>
          <p>Még nem iratkoztál be semmilyen kurzusra.</p>
          <Link to="/courses" className="btn btn-primary" style={{ marginTop: 16 }}>
            Kurzusok böngészése
          </Link>
        </div>
      ) : (
        courses.map((c) => {
          const cert = certMap[c.course_id];
          const isComplete = c.progress_percent >= 100;
          const progress = progressMap[c.course_id] || [];
          const courseData = courseDataMap[c.course_id];
          const successfulModules = progress.filter((m) =>
            m.exercises.every((ex) => ex.status === 'completed'),
          ).length;

          return (
            <div className="card" style={{ marginBottom: 16 }} key={c.course_id}>
              <h3>{c.course_name}</h3>
              <div className="progress-wrapper">
                <div className="progress-bar">
                  <div className="progress-bar-fill" style={{ width: `${c.progress_percent}%` }} />
                </div>
                <span style={{ fontWeight: 600, marginLeft: 12 }}>
                  {c.completed_exercises}/{c.total_exercises} — {c.progress_percent}%
                </span>
              </div>

              {progress.length > 0 && (
                <div>
                  <div className="modulelists-container">
                    <h2>
                      Modulok - teljesítve: {successfulModules}/{progress.length}
                    </h2>
                    <button className="btn btn-primary" onClick={() => toggleModules(c.course_id)}>
                      Részletek
                    </button>
                  </div>
                  {expandedModules[c.course_id] && (
                    <div className="modulelists card">
                      {progress.map((mod) => {
                        const courseModule = courseData?.modules?.find(
                          (m) => m.id === mod.module_id,
                        );
                        return (
                          <div className="modulelists_info" key={mod.module_id}>
                            <strong className="modulelists_title">
                              {mod.module_name} - teljesítve:{' '}
                              {mod.exercises.filter((ex) => ex.status === 'completed').length} /{' '}
                              {mod.exercises.length}
                            </strong>
                            <ul className="modulelists_dropdownlist">
                              {mod.exercises.map((ex) => {
                                const exercise = courseModule?.exercises.find(
                                  (e) => e.id === ex.id,
                                );
                                return (
                                  <li className="modulelists_dropdownlist-item" key={ex.id}>
                                    <span>{statusPrefix(ex.status)}</span>
                                    {exercise?.classroom_url &&
                                    ex.status !== 'completed' &&
                                    ex.status !== 'in_progress' ? (
                                      <a
                                        href={exercise.classroom_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                      >
                                        {ex.name} 📎
                                      </a>
                                    ) : (
                                      <span>{ex.name}</span>
                                    )}
                                    <span
                                      className="moduleslists_dropdownlist-item-status"
                                      style={{
                                        color: statusColor(ex.status),
                                        fontWeight: 500,
                                        fontSize: 10,
                                      }}
                                    >
                                      {statusLabel(ex.status)}
                                    </span>
                                  </li>
                                );
                              })}
                            </ul>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {cert && (
                <button
                  className="btn btn-secondary"
                  style={{ marginTop: 8 }}
                  onClick={() => handleDownloadCert(cert.cert_id)}
                >
                  PDF letöltése
                </button>
              )}
              {!cert && isComplete && (
                <button
                  className="btn btn-primary"
                  style={{ marginTop: 8 }}
                  onClick={() => handleRequestCert(c.course_id)}
                >
                  Tanúsítvány igénylése
                </button>
              )}
            </div>
          );
        })
      )}
    </div>
  );
}
