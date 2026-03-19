import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import type { CourseListItem, User } from '../lib/types';
import ProgressBar from '../components/ProgressBar';

interface StudentProgress {
  user_id: number;
  username: string;
  avatar_url: string | null;
  total_exercises: number;
  completed_exercises: number;
  progress_percent: number;
  enrolled_at: string | null;
}

interface CourseStudents {
  course_name: string;
  students: StudentProgress[];
}

export default function MentorDashboardPage() {
  const navigate = useNavigate();
  const [courses, setCourses] = useState<CourseListItem[]>([]);
  const [expandedCourse, setExpandedCourse] = useState<number | null>(null);
  const [studentData, setStudentData] = useState<Record<number, CourseStudents>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      const meRes = await fetch('/api/auth/me', { credentials: 'same-origin' });
      if (!meRes.ok) {
        navigate('/login');
        return;
      }
      const me: User = await meRes.json();
      if (me.role !== 'mentor' && me.role !== 'admin') {
        setError('Csak mentorok és adminok férhetnek hozzá.');
        setLoading(false);
        return;
      }

      const coursesRes = await fetch('/api/courses');
      if (!coursesRes.ok) {
        setError('Hiba a kurzusok betöltésekor.');
        setLoading(false);
        return;
      }
      const body = await coursesRes.json();
      setCourses(body.data);
      setLoading(false);
    }
    load();
  }, [navigate]);

  const toggleCourse = useCallback(
    async (courseId: number) => {
      if (expandedCourse === courseId) {
        setExpandedCourse(null);
        return;
      }
      setExpandedCourse(courseId);
      if (!studentData[courseId]) {
        const res = await fetch(`/api/courses/${courseId}/students`, {
          credentials: 'same-origin',
        });
        if (res.ok) {
          const data: CourseStudents = await res.json();
          setStudentData((prev) => ({ ...prev, [courseId]: data }));
        }
      }
    },
    [expandedCourse, studentData],
  );

  if (loading)
    return (
      <div className="container page">
        <p>Betöltés...</p>
      </div>
    );
  if (error)
    return (
      <div className="container page">
        <p style={{ color: 'var(--color-accent)' }}>{error}</p>
      </div>
    );

  return (
    <section className="page container">
      <h1>Mentor Dashboard</h1>
      <p style={{ color: 'var(--color-text-light)', marginBottom: 24 }}>
        Diákok haladásának áttekintése kurzusonként.
      </p>

      {courses.length === 0 && <p>Nincsenek kurzusok.</p>}

      {courses.map((c) => (
        <div className="card" style={{ marginBottom: 16 }} key={c.id}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              cursor: 'pointer',
            }}
            onClick={() => toggleCourse(c.id)}
          >
            <h3 style={{ margin: 0 }}>{c.name}</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-light)' }}>
              {expandedCourse === c.id ? '▲ Bezárás' : '▼ Diákok'}
            </span>
          </div>

          {expandedCourse === c.id && studentData[c.id] && (
            <div style={{ marginTop: 16 }}>
              {studentData[c.id].students.length === 0 ? (
                <p style={{ color: 'var(--color-text-light)', fontSize: '0.9rem' }}>
                  Nincs beiratkozott diák.
                </p>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                  <thead>
                    <tr
                      style={{
                        borderBottom: '2px solid var(--color-border)',
                        textAlign: 'left',
                      }}
                    >
                      <th style={{ padding: '8px 12px' }}>Diák</th>
                      <th style={{ padding: '8px 12px' }}>Haladás</th>
                      <th style={{ padding: '8px 12px', textAlign: 'center' }}>Feladatok</th>
                      <th style={{ padding: '8px 12px' }}>Beiratkozás</th>
                    </tr>
                  </thead>
                  <tbody>
                    {studentData[c.id].students
                      .sort((a, b) => b.progress_percent - a.progress_percent)
                      .map((s) => (
                        <tr
                          key={s.user_id}
                          style={{ borderBottom: '1px solid var(--color-border)' }}
                        >
                          <td style={{ padding: '8px 12px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                              {s.avatar_url && (
                                <img
                                  src={s.avatar_url}
                                  alt=""
                                  style={{ width: 28, height: 28, borderRadius: '50%' }}
                                />
                              )}
                              <a
                                href={`https://github.com/${s.username}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{ color: 'var(--color-primary)' }}
                              >
                                {s.username}
                              </a>
                            </div>
                          </td>
                          <td style={{ padding: '8px 12px', minWidth: 150 }}>
                            <ProgressBar percent={s.progress_percent} />
                          </td>
                          <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                            {s.completed_exercises}/{s.total_exercises}
                          </td>
                          <td
                            style={{
                              padding: '8px 12px',
                              fontSize: '0.8rem',
                              color: 'var(--color-text-light)',
                            }}
                          >
                            {s.enrolled_at
                              ? new Date(s.enrolled_at).toLocaleDateString('hu-HU')
                              : '—'}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              )}
              <div
                style={{
                  marginTop: 12,
                  fontSize: '0.8rem',
                  color: 'var(--color-text-light)',
                }}
              >
                Összesen: {studentData[c.id].students.length} diák
              </div>
            </div>
          )}
        </div>
      ))}
    </section>
  );
}
