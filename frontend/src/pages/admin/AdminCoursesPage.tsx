import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import type { Course, User } from '../../lib/types';

interface ClassroomItem {
  id: number;
  name: string;
}

interface AssignmentItem {
  id: number;
  title: string;
  slug: string;
  invite_link: string;
  already_imported: boolean;
}

export default function AdminCoursesPage() {
  const navigate = useNavigate();
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createMsg, setCreateMsg] = useState('');
  const [expandedCourseId, setExpandedCourseId] = useState<number | null>(null);
  const [courseDetails, setCourseDetails] = useState<Record<number, Course>>({});

  // Form states
  const [newCourseName, setNewCourseName] = useState('');
  const [newCourseDesc, setNewCourseDesc] = useState('');

  const loadCourses = useCallback(async () => {
    const meRes = await fetch('/api/auth/me', { credentials: 'same-origin' });
    if (!meRes.ok) {
      navigate('/login');
      return;
    }
    const me: User = await meRes.json();
    if (me.role !== 'admin') {
      setError('Nincs jogosultságod.');
      setLoading(false);
      return;
    }

    const res = await fetch('/api/courses');
    if (!res.ok) {
      setError('Hiba történt.');
      setLoading(false);
      return;
    }
    const body = await res.json();
    setCourses(body.data);
    setLoading(false);
  }, [navigate]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadCourses();
  }, [loadCourses]);

  const handleCreateCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCourseName.trim()) return;
    const r = await fetch('/api/courses', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ name: newCourseName.trim(), description: newCourseDesc.trim() }),
    });
    if (r.ok) {
      setCreateMsg('Kurzus létrehozva!');
      setNewCourseName('');
      setNewCourseDesc('');
      await loadCourses();
    } else {
      const d = await r.json();
      setCreateMsg(d.detail || 'Hiba történt.');
    }
  };

  const handleDeleteCourse = async (courseId: number) => {
    if (!confirm('Biztosan törölni szeretnéd ezt a kurzust?')) return;
    const r = await fetch(`/api/admin/courses/${courseId}`, {
      method: 'DELETE',
      credentials: 'same-origin',
    });
    if (r.ok) {
      setCourses(courses.filter((c) => c.id !== courseId));
    } else {
      const d = await r.json();
      alert(d.detail || 'Hiba történt.');
    }
  };

  const toggleDetails = async (courseId: number) => {
    if (expandedCourseId === courseId) {
      setExpandedCourseId(null);
      return;
    }
    setExpandedCourseId(courseId);
    if (!courseDetails[courseId]) {
      const res = await fetch(`/api/courses/${courseId}`);
      if (res.ok) {
        const data: Course = await res.json();
        setCourseDetails((prev) => ({ ...prev, [courseId]: data }));
      }
    }
  };

  const handleAddModule = async (courseId: number, name: string, order: number) => {
    const r = await fetch(`/api/courses/${courseId}/modules`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ name, order }),
    });
    if (r.ok) {
      const res = await fetch(`/api/courses/${courseId}`);
      if (res.ok) {
        const data: Course = await res.json();
        setCourseDetails((prev) => ({ ...prev, [courseId]: data }));
      }
    } else {
      const d = await r.json();
      alert(d.detail || 'Hiba');
    }
  };

  const handleDeleteModule = async (courseId: number, moduleId: number) => {
    if (!confirm('Biztosan törölni szeretnéd ezt a modult?')) return;
    const r = await fetch(`/api/admin/modules/${moduleId}`, {
      method: 'DELETE',
      credentials: 'same-origin',
    });
    if (r.ok) {
      const res = await fetch(`/api/courses/${courseId}`);
      if (res.ok) {
        const data: Course = await res.json();
        setCourseDetails((prev) => ({ ...prev, [courseId]: data }));
      }
    } else {
      const d = await r.json();
      alert(d.detail || 'Hiba');
    }
  };

  const handleAddExercise = async (
    courseId: number,
    moduleId: number,
    name: string,
    repoPrefix: string,
    classroomUrl: string,
    order: number,
  ) => {
    const r = await fetch(`/api/courses/${courseId}/modules/${moduleId}/exercises`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({
        name,
        repo_prefix: repoPrefix,
        classroom_url: classroomUrl,
        order,
      }),
    });
    if (r.ok) {
      const res = await fetch(`/api/courses/${courseId}`);
      if (res.ok) {
        const data: Course = await res.json();
        setCourseDetails((prev) => ({ ...prev, [courseId]: data }));
      }
    } else {
      const d = await r.json();
      alert(d.detail || 'Hiba');
    }
  };

  const handleDeleteExercise = async (courseId: number, exerciseId: number) => {
    const r = await fetch(`/api/admin/exercises/${exerciseId}`, {
      method: 'DELETE',
      credentials: 'same-origin',
    });
    if (r.ok) {
      const res = await fetch(`/api/courses/${courseId}`);
      if (res.ok) {
        const data: Course = await res.json();
        setCourseDetails((prev) => ({ ...prev, [courseId]: data }));
      }
    } else {
      const d = await r.json();
      alert(d.detail || 'Hiba');
    }
  };

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
      <h1>Kurzusok kezelése</h1>
      <div
        className="admin-nav"
        style={{ marginBottom: 32, display: 'flex', gap: 12, flexWrap: 'wrap' }}
      >
        <Link to="/admin" className="btn btn-secondary">
          Áttekintés
        </Link>
        <Link to="/admin/users" className="btn btn-secondary">
          Felhasználók
        </Link>
        <Link to="/admin/courses" className="btn btn-primary">
          Kurzusok
        </Link>{' '}
        <Link to="/admin/promotion" className="btn btn-secondary">
          Előléptetés
        </Link>{' '}
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <h3 style={{ marginBottom: 16 }}>Új kurzus létrehozása</h3>
        <form
          onSubmit={handleCreateCourse}
          style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'end' }}
        >
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: 4 }}>Név</label>
            <input
              type="text"
              value={newCourseName}
              onChange={(e) => setNewCourseName(e.target.value)}
              required
              style={{
                padding: '8px 12px',
                border: '1px solid var(--color-border)',
                borderRadius: 4,
                fontSize: '0.95rem',
                width: 250,
              }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: 4 }}>Leírás</label>
            <input
              type="text"
              value={newCourseDesc}
              onChange={(e) => setNewCourseDesc(e.target.value)}
              style={{
                padding: '8px 12px',
                border: '1px solid var(--color-border)',
                borderRadius: 4,
                fontSize: '0.95rem',
                width: 350,
              }}
            />
          </div>
          <button type="submit" className="btn btn-primary" style={{ padding: '8px 20px' }}>
            Létrehozás
          </button>
        </form>
        {createMsg && (
          <p
            style={{
              marginTop: 8,
              color: createMsg.includes('létrehozva')
                ? 'var(--color-success)'
                : 'var(--color-accent)',
            }}
          >
            {createMsg}
          </p>
        )}
      </div>

      {courses.map((c) => (
        <div className="card" style={{ marginBottom: 16 }} key={c.id}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 12,
            }}
          >
            <h3>{c.name}</h3>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                className="btn btn-secondary"
                style={{ padding: '6px 14px', fontSize: '0.85rem' }}
                onClick={() => toggleDetails(c.id)}
              >
                Részletek
              </button>
              <button
                className="btn"
                style={{
                  padding: '6px 14px',
                  fontSize: '0.85rem',
                  background: '#e74c3c',
                  color: '#fff',
                }}
                onClick={() => handleDeleteCourse(c.id)}
              >
                Törlés
              </button>
            </div>
          </div>
          <p style={{ color: 'var(--color-text-light)' }}>{c.description || 'Nincs leírás'}</p>

          {expandedCourseId === c.id && courseDetails[c.id] && (
            <CourseDetailsPanel
              course={courseDetails[c.id]}
              onAddModule={(name, order) => handleAddModule(c.id, name, order)}
              onDeleteModule={(moduleId) => handleDeleteModule(c.id, moduleId)}
              onAddExercise={(moduleId, name, repo, classroom, order) =>
                handleAddExercise(c.id, moduleId, name, repo, classroom, order)
              }
              onDeleteExercise={(exerciseId) => handleDeleteExercise(c.id, exerciseId)}
              onImportDone={async () => {
                const res = await fetch(`/api/courses/${c.id}`);
                if (res.ok) {
                  const data: Course = await res.json();
                  setCourseDetails((prev) => ({ ...prev, [c.id]: data }));
                }
              }}
            />
          )}
        </div>
      ))}
    </section>
  );
}

interface CourseDetailsPanelProps {
  course: Course;
  onAddModule: (name: string, order: number) => void;
  onDeleteModule: (moduleId: number) => void;
  onAddExercise: (
    moduleId: number,
    name: string,
    repoPrefix: string,
    classroomUrl: string,
    order: number,
  ) => void;
  onDeleteExercise: (exerciseId: number) => void;
  onImportDone: () => Promise<void>;
}

function CourseDetailsPanel({
  course,
  onAddModule,
  onDeleteModule,
  onAddExercise,
  onDeleteExercise,
  onImportDone,
}: CourseDetailsPanelProps) {
  const [moduleName, setModuleName] = useState('');
  const [moduleOrder, setModuleOrder] = useState(course.modules.length + 1);

  return (
    <div style={{ marginTop: 16, borderTop: '1px solid var(--color-border)', paddingTop: 16 }}>
      <div style={{ marginBottom: 16 }}>
        <h4 style={{ marginBottom: 8 }}>Modul hozzáadása</h4>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onAddModule(moduleName.trim(), moduleOrder);
            setModuleName('');
            setModuleOrder(course.modules.length + 2);
          }}
          style={{ display: 'flex', gap: 8, alignItems: 'end', flexWrap: 'wrap' }}
        >
          <div>
            <label
              style={{
                display: 'block',
                fontSize: '0.75rem',
                color: 'var(--color-text-light)',
                marginBottom: 2,
              }}
            >
              Modul neve
            </label>
            <input
              type="text"
              placeholder="pl. Alapok"
              required
              value={moduleName}
              onChange={(e) => setModuleName(e.target.value)}
              style={{
                padding: '6px 10px',
                border: '1px solid var(--color-border)',
                borderRadius: 4,
              }}
            />
          </div>
          <div>
            <label
              style={{
                display: 'block',
                fontSize: '0.75rem',
                color: 'var(--color-text-light)',
                marginBottom: 2,
              }}
            >
              Sorrend
            </label>
            <input
              type="number"
              value={moduleOrder}
              onChange={(e) => setModuleOrder(parseInt(e.target.value) || 0)}
              style={{
                padding: '6px 10px',
                border: '1px solid var(--color-border)',
                borderRadius: 4,
                width: 70,
              }}
            />
          </div>
          <button
            type="submit"
            className="btn btn-primary"
            style={{ padding: '6px 14px', fontSize: '0.85rem' }}
          >
            Hozzáadás
          </button>
        </form>
      </div>

      {course.modules
        .sort((a, b) => a.order - b.order)
        .map((m) => (
          <ModuleBlock
            key={m.id}
            module={m}
            courseId={course.id}
            onDeleteModule={() => onDeleteModule(m.id)}
            onAddExercise={(name, repo, classroom, order) =>
              onAddExercise(m.id, name, repo, classroom, order)
            }
            onDeleteExercise={onDeleteExercise}
            onImportDone={onImportDone}
          />
        ))}
    </div>
  );
}

interface ModuleBlockProps {
  module: Course['modules'][0];
  courseId: number;
  onDeleteModule: () => void;
  onAddExercise: (name: string, repoPrefix: string, classroomUrl: string, order: number) => void;
  onDeleteExercise: (exerciseId: number) => void;
  onImportDone: () => Promise<void>;
}

function ModuleBlock({
  module: m,
  courseId,
  onDeleteModule,
  onAddExercise,
  onDeleteExercise,
  onImportDone,
}: ModuleBlockProps) {
  const [exName, setExName] = useState('');
  const [exRepo, setExRepo] = useState('');
  const [exClassroom, setExClassroom] = useState('');
  const [exOrder, setExOrder] = useState(m.exercises.length + 1);

  // Classroom import state
  const [showImport, setShowImport] = useState(false);
  const [classrooms, setClassrooms] = useState<ClassroomItem[]>([]);
  const [selectedClassroom, setSelectedClassroom] = useState<number | null>(null);
  const [assignments, setAssignments] = useState<AssignmentItem[]>([]);
  const [selectedSlugs, setSelectedSlugs] = useState<Set<string>>(new Set());
  const [importLoading, setImportLoading] = useState(false);
  const [importMsg, setImportMsg] = useState('');

  const loadClassrooms = async () => {
    setShowImport(true);
    setImportMsg('');
    const res = await fetch('/api/courses/classroom/classrooms', { credentials: 'same-origin' });
    if (res.ok) {
      const body = await res.json();
      setClassrooms(body.data);
      if (body.data.length === 0) setImportMsg('Nem található GitHub Classroom.');
    } else {
      const d = await res.json();
      setImportMsg(d.detail || 'Hiba a Classroomok lekérdezésekor.');
    }
  };

  const loadAssignments = async (classroomId: number) => {
    setSelectedClassroom(classroomId);
    setAssignments([]);
    setSelectedSlugs(new Set());
    const res = await fetch(`/api/courses/classroom/classrooms/${classroomId}/assignments`, {
      credentials: 'same-origin',
    });
    if (res.ok) {
      const body = await res.json();
      setAssignments(body.data);
      if (body.data.length === 0) setImportMsg('Nincsenek feladatok ebben a Classroomban.');
      else setImportMsg('');
    } else {
      setImportMsg('Hiba a feladatok lekérdezésekor.');
    }
  };

  const toggleAssignment = (slug: string) => {
    setSelectedSlugs((prev) => {
      const next = new Set(prev);
      if (next.has(slug)) next.delete(slug);
      else next.add(slug);
      return next;
    });
  };

  const handleImport = async () => {
    const toImport = assignments.filter((a) => selectedSlugs.has(a.slug));
    if (toImport.length === 0) return;
    setImportLoading(true);
    const res = await fetch(`/api/courses/${courseId}/modules/${m.id}/import-classroom`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({
        exercises: toImport.map((a) => ({
          title: a.title,
          slug: a.slug,
          invite_link: a.invite_link,
        })),
      }),
    });
    setImportLoading(false);
    if (res.ok) {
      const result = await res.json();
      const parts: string[] = [];
      if (result.imported.length) parts.push(`Importálva: ${result.imported.length}`);
      if (result.skipped.length) parts.push(`Kihagyva (már létezik): ${result.skipped.length}`);
      setImportMsg(parts.join(' | '));
      setSelectedSlugs(new Set());
      await onImportDone();
      // Refresh assignment list to update already_imported flags
      if (selectedClassroom) await loadAssignments(selectedClassroom);
    } else {
      const d = await res.json();
      setImportMsg(d.detail || 'Import hiba.');
    }
  };

  return (
    <div style={{ background: 'var(--color-bg)', padding: 16, borderRadius: 6, marginBottom: 12 }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 8,
        }}
      >
        <h4>
          {m.order}. {m.name}
        </h4>
        <div style={{ display: 'flex', gap: 6 }}>
          <button
            onClick={loadClassrooms}
            className="btn btn-secondary"
            style={{
              padding: '4px 10px',
              fontSize: '0.8rem',
            }}
          >
            📥 Import from Classroom
          </button>
          <button
            onClick={onDeleteModule}
            style={{
              background: '#e74c3c',
              color: '#fff',
              border: 'none',
              padding: '4px 10px',
              borderRadius: 4,
              cursor: 'pointer',
              fontSize: '0.8rem',
            }}
          >
            Modul törlése
          </button>
        </div>
      </div>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {m.exercises
          .sort((a, b) => a.order - b.order)
          .map((e) => (
            <li
              key={e.id}
              style={{
                padding: '6px 0',
                borderBottom: '1px solid var(--color-border)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <span>
                {e.order}. {e.name}{' '}
                {e.repo_prefix && (
                  <code
                    style={{
                      fontSize: '0.8rem',
                      background: '#eee',
                      padding: '2px 6px',
                      borderRadius: 3,
                    }}
                  >
                    {e.repo_prefix}
                  </code>
                )}{' '}
                {e.classroom_url && '📎'}
              </span>
              <button
                onClick={() => onDeleteExercise(e.id)}
                style={{
                  background: '#e74c3c',
                  color: '#fff',
                  border: 'none',
                  padding: '2px 8px',
                  borderRadius: 4,
                  cursor: 'pointer',
                  fontSize: '0.75rem',
                }}
              >
                ✕
              </button>
            </li>
          ))}
      </ul>
      {showImport && (
        <div
          style={{
            background: 'var(--color-bg-surface, #f8f9fa)',
            border: '1px solid var(--color-border)',
            borderRadius: 6,
            padding: 16,
            marginTop: 12,
            marginBottom: 12,
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 12,
            }}
          >
            <h5 style={{ margin: 0 }}>📥 Import from GitHub Classroom</h5>
            <button
              onClick={() => {
                setShowImport(false);
                setClassrooms([]);
                setAssignments([]);
                setSelectedClassroom(null);
                setImportMsg('');
              }}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontSize: '1rem',
              }}
            >
              ✕
            </button>
          </div>

          {classrooms.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <label
                style={{
                  display: 'block',
                  fontSize: '0.8rem',
                  color: 'var(--color-text-light)',
                  marginBottom: 4,
                }}
              >
                Classroom kiválasztása
              </label>
              <select
                value={selectedClassroom ?? ''}
                onChange={(e) => {
                  const val = parseInt(e.target.value);
                  if (val) loadAssignments(val);
                }}
                style={{
                  padding: '6px 10px',
                  border: '1px solid var(--color-border)',
                  borderRadius: 4,
                  fontSize: '0.9rem',
                  minWidth: 250,
                }}
              >
                <option value="">-- Válassz --</option>
                {classrooms.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {assignments.length > 0 && (
            <div>
              <div
                style={{
                  marginBottom: 8,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span style={{ fontSize: '0.85rem', color: 'var(--color-text-light)' }}>
                  {assignments.filter((a) => !a.already_imported).length} importálható feladat
                </span>
                <button
                  onClick={() => {
                    const importable = assignments
                      .filter((a) => !a.already_imported)
                      .map((a) => a.slug);
                    setSelectedSlugs(new Set(importable));
                  }}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--color-primary)',
                    cursor: 'pointer',
                    fontSize: '0.8rem',
                    textDecoration: 'underline',
                  }}
                >
                  Összes kijelölése
                </button>
              </div>
              <ul style={{ listStyle: 'none', padding: 0, maxHeight: 250, overflowY: 'auto' }}>
                {assignments.map((a) => (
                  <li
                    key={a.id}
                    style={{
                      padding: '6px 8px',
                      borderBottom: '1px solid var(--color-border)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      opacity: a.already_imported ? 0.5 : 1,
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={selectedSlugs.has(a.slug)}
                      disabled={a.already_imported}
                      onChange={() => toggleAssignment(a.slug)}
                    />
                    <span style={{ flex: 1 }}>
                      <strong>{a.title}</strong>
                      <code
                        style={{
                          fontSize: '0.75rem',
                          background: '#eee',
                          padding: '1px 5px',
                          borderRadius: 3,
                          marginLeft: 6,
                        }}
                      >
                        {a.slug}
                      </code>
                      {a.already_imported && (
                        <span
                          style={{
                            fontSize: '0.75rem',
                            color: 'var(--color-success, green)',
                            marginLeft: 6,
                          }}
                        >
                          ✓ már importálva
                        </span>
                      )}
                    </span>
                  </li>
                ))}
              </ul>
              <button
                onClick={handleImport}
                disabled={selectedSlugs.size === 0 || importLoading}
                className="btn btn-primary"
                style={{ marginTop: 10, padding: '6px 16px', fontSize: '0.85rem' }}
              >
                {importLoading ? 'Importálás...' : `Kijelöltek importálása (${selectedSlugs.size})`}
              </button>
            </div>
          )}

          {importMsg && (
            <p
              style={{
                marginTop: 8,
                fontSize: '0.85rem',
                color: importMsg.includes('Importálva')
                  ? 'var(--color-success, green)'
                  : 'var(--color-text-light)',
              }}
            >
              {importMsg}
            </p>
          )}
        </div>
      )}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onAddExercise(exName.trim(), exRepo.trim(), exClassroom.trim(), exOrder);
          setExName('');
          setExRepo('');
          setExClassroom('');
          setExOrder(m.exercises.length + 2);
        }}
        style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'end', marginTop: 8 }}
      >
        <div>
          <label
            style={{
              display: 'block',
              fontSize: '0.75rem',
              color: 'var(--color-text-light)',
              marginBottom: 2,
            }}
          >
            Feladat neve
          </label>
          <input
            type="text"
            placeholder="pl. Hello World"
            required
            value={exName}
            onChange={(e) => setExName(e.target.value)}
            style={{
              padding: '4px 8px',
              border: '1px solid var(--color-border)',
              borderRadius: 4,
              fontSize: '0.85rem',
            }}
          />
        </div>
        <div>
          <label
            style={{
              display: 'block',
              fontSize: '0.75rem',
              color: 'var(--color-text-light)',
              marginBottom: 2,
            }}
          >
            Repo prefix
          </label>
          <input
            type="text"
            placeholder="pl. python-hello-world"
            value={exRepo}
            onChange={(e) => setExRepo(e.target.value)}
            style={{
              padding: '4px 8px',
              border: '1px solid var(--color-border)',
              borderRadius: 4,
              fontSize: '0.85rem',
              width: 160,
            }}
          />
        </div>
        <div>
          <label
            style={{
              display: 'block',
              fontSize: '0.75rem',
              color: 'var(--color-text-light)',
              marginBottom: 2,
            }}
          >
            Classroom link
          </label>
          <input
            type="text"
            placeholder="https://classroom.github.com/a/..."
            value={exClassroom}
            onChange={(e) => setExClassroom(e.target.value)}
            style={{
              padding: '4px 8px',
              border: '1px solid var(--color-border)',
              borderRadius: 4,
              fontSize: '0.85rem',
              width: 220,
            }}
          />
        </div>
        <div>
          <label
            style={{
              display: 'block',
              fontSize: '0.75rem',
              color: 'var(--color-text-light)',
              marginBottom: 2,
            }}
          >
            Sorrend
          </label>
          <input
            type="number"
            value={exOrder}
            onChange={(e) => setExOrder(parseInt(e.target.value) || 0)}
            style={{
              padding: '4px 8px',
              border: '1px solid var(--color-border)',
              borderRadius: 4,
              width: 55,
              fontSize: '0.85rem',
            }}
          />
        </div>
        <button
          type="submit"
          className="btn btn-primary"
          style={{ padding: '4px 12px', fontSize: '0.85rem' }}
        >
          + Feladat
        </button>
      </form>
    </div>
  );
}
