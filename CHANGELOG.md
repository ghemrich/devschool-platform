## [unreleased]

### 🚀 Features

- Add Module 3 - courses, progress tracking, and dashboard
- Add Module 4 - certificate system
- Add Module 5 - frontend with Astro
- Add Module 6 - production configuration
- Add Module 7 - open source community files
- Dynamic BASE_URL for certificate verify links, fix auth callback tests
- GitHub Classroom integration
- Add admin panel and update all documentation

### 🐛 Bug Fixes

- Ruff formatting fixes
- Alembic migration for users table, env.py model import, lint fixes
- Fix frontend tsconfig.json and add env.d.ts type reference
- Skip CD deploy when VPS secrets are not configured
- Docker testing fixes and UI improvements
- PDF download sends auth header via fetch instead of plain link
- Consistent nav button spacing for auth links
- Resolve all ruff lint errors

### 💼 Other

- Add labels and help text to admin course form fields

### 🚜 Refactor

- Deduplicate test fixtures, extract progress service, fix N+1 query
- Pagination, sorting, JS extraction, CSS dedup, Mermaid diagrams, CHANGELOG
- Project quality improvements

### 📚 Documentation

- Magyar nyelvű dokumentáció (telepítés, architektúra, jövőkép)
- Fejlesztői környezet útmutató és dev tooling
- Rewrite README as introductory page with philosophy
- Add inter-doc navigation and fix issues
- Add documentation index to README
- Add open source philosophy to README
- Refine README intro
- Add user guide, fix course detail nginx routing
- Add GitHub Classroom integration guide for teachers
- Update roadmap to reflect current project state
- Replace course list with setup guide in roadmap
- Replace inline setup guide with link to classroom doc
- Remove references to external ../testing/ scripts
- Remove grade calculator from roadmap
- Add maintenance guide and Dependabot config
- Expand staging environment guide, add staging CD job
- Add git-cliff changelog automation and update project structure
- Fix content inconsistencies across all documentation
- Restructure into separate backend/frontend guides
- Add Discord integration guide, documentation guide, and CI notify script
- Update roadmap to reflect current state
- Regenerate CHANGELOG.md
- Add API reference, database schema, testing guide, and env vars reference
- Regenerate CHANGELOG.md
- Add question and documentation issue templates
- Regenerate CHANGELOG.md
- Restructure docs/ into categorized subfolders
- Regenerate CHANGELOG.md
- Remove redundant API endpoints and project structure from README
- Remove redundant local dev section from README
- Remove redundant Makefile section from README
- Regenerate CHANGELOG.md
- Remove duplicate Discord channel structure from roadmap

### ⚙️ Miscellaneous Tasks

- Rebrand DevSchool to OpenSchool
- Update pinned dependencies to installed versions
- Update actions to Node.js 24 compatible versions
- Add git-cliff to requirements.txt
- Split requirements into prod and dev
- Add automated maintenance scripts and documentation
- Automate VPS setup and security checklist
- Add Discord notifications to CI/CD workflows

### 🛡️ Security

- Production hardening and documentation overhaul

### ◀️ Revert

- Restore previous README.md
