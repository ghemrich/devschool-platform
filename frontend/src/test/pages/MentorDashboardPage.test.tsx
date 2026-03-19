import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import MentorDashboardPage from '../../pages/MentorDashboardPage';

function mockFetch(overrides: Record<string, unknown> = {}) {
  vi.stubGlobal(
    'fetch',
    vi.fn((url: string) => {
      if (url.includes('/api/auth/me')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () =>
            Promise.resolve(
              overrides.me ?? { id: 1, username: 'mentor1', role: 'mentor', discord_id: null },
            ),
        });
      }
      if (url.includes('/api/courses') && !url.includes('students')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () =>
            Promise.resolve(
              overrides.courses ?? {
                total: 1,
                data: [{ id: 1, name: 'Python 101', description: 'Beginner' }],
              },
            ),
        });
      }
      if (url.includes('/students')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () =>
            Promise.resolve(
              overrides.students ?? {
                course_name: 'Python 101',
                students: [
                  {
                    user_id: 2,
                    username: 'student1',
                    avatar_url: null,
                    total_exercises: 10,
                    completed_exercises: 5,
                    progress_percent: 50,
                    enrolled_at: '2026-01-01T00:00:00',
                  },
                ],
              },
            ),
        });
      }
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) });
    }),
  );
}

beforeEach(() => {
  vi.restoreAllMocks();
});

describe('MentorDashboardPage', () => {
  it('renders heading for mentor', async () => {
    mockFetch();
    render(
      <MemoryRouter>
        <MentorDashboardPage />
      </MemoryRouter>,
    );
    const heading = await screen.findByText('Mentor Dashboard');
    expect(heading).toBeInTheDocument();
  });

  it('shows course list', async () => {
    mockFetch();
    render(
      <MemoryRouter>
        <MentorDashboardPage />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByText('Python 101')).toBeInTheDocument();
    });
  });

  it('shows error for student role', async () => {
    mockFetch({ me: { id: 1, username: 'student1', role: 'student' } });
    render(
      <MemoryRouter>
        <MentorDashboardPage />
      </MemoryRouter>,
    );
    const error = await screen.findByText('Csak mentorok és adminok férhetnek hozzá.');
    expect(error).toBeInTheDocument();
  });

  it('renders for admin role too', async () => {
    mockFetch({ me: { id: 1, username: 'admin1', role: 'admin' } });
    render(
      <MemoryRouter>
        <MentorDashboardPage />
      </MemoryRouter>,
    );
    const heading = await screen.findByText('Mentor Dashboard');
    expect(heading).toBeInTheDocument();
  });
});
