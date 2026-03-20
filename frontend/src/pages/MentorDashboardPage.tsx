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

interface ExerciseDetail {
  exercise_id: number;
  name: string;
  status: 'not_started' | 'in_progress' | 'completed';
  classroom_url: string | null;
}

interface ModuleDetail {
  module_id: number;
  module_name: string;
  exercises: ExerciseDetail[];
}

interface StudentExercises {
  course_name: string;
  username: string;
  modules: ModuleDetail[];
}

const STATUS_LABEL: Record<string, { text: string; color: string }> = {
  completed: { text: '✅ Kész', color: 'var(--color-success, #22c55e)' },
  in_progress: { text: '🔄 Folyamatban', color: 'var(--color-warning, #f59e0b)' },
  not_started: { text: '⬜ Nem kezdte', color: 'var(--color-text-light)' },
};

export default function MentorDashboardPage() {
  const navigate = useNavigate();
  const [courses, setCourses] = useState<CourseListItem[]>([]);
  const [expandedCourse, setExpandedCourse] = useState<number | null>(null);
  const [studentData, setStudentData] = useState<Record<number, CourseStudents>>({});
  const [expandedStudent, setExpandedStudent] = useState<string | null>(null); // "courseId-userId"
  const [studentExercises, setStudentExercises] = useState<Record<string, StudentExercises>>({});
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

  const toggleStudent = useCallback(
    async (courseId: number, userId: number) => {
      const key = `${courseId}-${userId}`;
      if (expandedStudent === key) {
        setExpandedStudent(null);
        return;
      }
      setExpandedStudent(key);
      if (!studentExercises[key]) {
        const res = await fetch(`/api/courses/${courseId}/students/${userId}/exercises`, {
          credentials: 'same-origin',
        });
        if (res.ok) {
          const data: StudentExercises = await res.json();
          setStudentExercises((prev) => ({ ...prev, [key]: data }));
        }
      }
    },
    [expandedStudent, studentExercises],
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
                      .map((s) => {
                        const key = `${c.id}-${s.user_id}`;
                        const isExpanded = expandedStudent === key;
                        return (
                          <tr
                            key={s.user_id}
                            style={{ borderBottom: '1px solid var(--color-border)' }}
                          >
                            <td colSpan={4} style={{ padding: 0 }}>
                              <div
                                style={{ display: 'flex', cursor: 'pointer', padding: '8px 12px' }}
                                onClick={() => toggleStudent(c.id, s.user_id)}
                              >
                                <div style={{ flex: 1 }}>
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
                                      onClick={(e) => e.stopPropagation()}
                                    >
                                      {s.username}
                                    </a>
                                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-light)' }}>
                                      {isExpanded ? '▲' : '▼'}
                                    </span>
                                  </div>
                                </div>
                                <div style={{ minWidth: 150, padding: '0 12px' }}>
                                  <ProgressBar percent={s.progress_percent} />
                                </div>
                                <div style={{ minWidth: 80, textAlign: 'center', padding: '0 12px' }}>
                                  {s.completed_exercises}/{s.total_exercises}
                                </div>
                                <div
                                  style={{
                                    minWidth: 100,
                                    fontSize: '0.8rem',
                                    color: 'var(--color-text-light)',
                                    padding: '0 12px',
                                  }}
                                >
                                  {s.enrolled_at
                                    ? new Date(s.enrolled_at).toLocaleDateString('hu-HU')
                                    : '—'}
                                </div>
                              </div>

                              {isExpanded && studentExercises[key] && (
                                <div
                                  style={{
                                    padding: '8px 12px 16px 48px',
                                    background: 'var(--color-bg-light, rgba(0,0,0,0.02))',
                                  }}
                                >
                                  {studentExercises[key].modules.map((mod) => (
                                    <div key={mod.module_id} style={{ marginBottom: 12 }}>
                                      <strong style={{ fontSize: '0.85rem' }}>{mod.module_name}</strong>
                                      <ul style={{ listStyle: 'none', padding: 0, margin: '4px 0 0' }}>
                                        {mod.exercises.map((ex) => {
                                          const st = STATUS_LABEL[ex.status] ?? STATUS_LABEL.not_started;
                                          return (
                                            <li
                                              key={ex.exercise_id}
                                              style={{
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: 8,
                                                padding: '3px 0',
                                                fontSize: '0.85rem',
                                              }}
                                            >
                                              <span style={{ color: st.color, minWidth: 130 }}>{st.text}</span>
                                              <span>{ex.name}</span>
                                              {ex.classroom_url && (
                                                <a
                                                  href={ex.classroom_url}
                                                  target="_blank"
                                                  rel="noopener noreferrer"
                                                  style={{
                                                    marginLeft: 'auto',
                                                    fontSize: '0.8rem',
                                                    color: 'var(--color-primary)',
                                                  }}
                                                  onClick={(e) => e.stopPropagation()}
                                                >
                                                  GitHub Classroom ↗
                                                </a>
                                              )}
                                            </li>
                                          );
                                        })}
                                      </ul>
                                    </div>
                                  ))}
                                </div>
                              )}
                              {isExpanded && !studentExercises[key] && (
                                <div style={{ padding: '8px 12px 16px 48px', fontSize: '0.85rem', color: 'var(--color-text-light)' }}>
                                  Betöltés...
                                </div>
                              )}
                            </td>
                          </tr>
                        );
                      })}
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
