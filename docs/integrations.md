# Integrációk

Discord szerver, webhook értesítések, szerepkör szinkronizáció és GitHub Classroom integráció.

---

## Discord

**Szerver:** [discord.gg/BrKd45S6](https://discord.gg/BrKd45S6)

### Szerver felállítása

1. Discord → **+** → **Saját szerver** → **Közösség számára** → `OpenSchool`
2. **Közösségi szerver** engedélyezése (szálak, fórum, moderáció)

### Szerepkörök

| Szerepkör | Szín | Jogosultságok |
|-----------|------|---------------|
| `@Admin` | 🔴 | Administrator |
| `@Mentor` | 🟣 | Üzenetek kezelése, szálak, pinelés |
| `@Kontribútor` | 🔵 | Szálak létrehozása/kezelése |
| `@Tanuló` | 🟢 | Üzenetek, szálak használata |
| `@Bot` | 🟡 | Webhookok, üzenetek küldése |

Automatikus beállítás: `DISCORD_BOT_TOKEN="..." DISCORD_GUILD_ID="..." ./scripts/setup-discord-roles.sh`

### Csatornastruktúra

```
📋 INFORMÁCIÓK:  #szabályzat, #közlemények, #hasznos-linkek
🐍 PYTHON ALAPOK: #python-alapok-általános, #python-alapok-segítség (fórum), #python-alapok-megoldások
⚡ BACKEND FASTAPI: #backend-általános, #backend-segítség, #backend-megoldások
🤖 AUTOMATIZÁCIÓ:  #ops-alerts (webhook), #ci-cd (webhook), #github-activity
💬 KÖZÖSSÉG:       #általános, #bemutatkozás, #off-topic
```

A `#...-segítség` csatornák **Fórum** típusúak lehetnek (kérdésenként szál, tag-ek: `megoldva`, `segítségkell`).

### Webhook értesítések

Webhook létrehozása: csatorna → Integrációk → Webhookok → Új webhook → URL másolása.

**Tárolás:**
- Lokális: `.env` (`DISCORD_WEBHOOK_URL`, `DISCORD_WEBHOOK_CI`)
- GitHub Actions: repository secrets (`DISCORD_WEBHOOK_CI`)
- VPS: `/etc/openschool-maintenance.conf` (`DISCORD_WEBHOOK_URL`)

### CI/CD értesítések

A `scripts/discord-notify.sh` szkript:

```yaml
# GitHub Actions workflow végéhez:
- name: Discord notification
  if: always()
  env:
    DISCORD_WEBHOOK_CI: ${{ secrets.DISCORD_WEBHOOK_CI }}
  run: |
    ./scripts/discord-notify.sh \
      --status "${{ job.status }}" \
      --title "CI: ${{ github.event.head_commit.message }}" \
      --repo "${{ github.repository }}" \
      --commit "${{ github.sha }}" \
      --author "${{ github.actor }}" \
      --url "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
```

### VPS monitoring értesítések

A `maintenance.sh` Discord webhook-on értesít hibáknál. Beállítás: `DISCORD_WEBHOOK_URL` az `/etc/openschool-maintenance.conf`-ban.

| Esemény | Értesítés |
|---------|-----------|
| Mentés sikertelen | DB hiba |
| Health check hiba | Konténer leállt |
| Lemezhasználat ≥90% | Kritikus figyelmeztetés |
| SSL lejár ≤30 napon belül | Lejárati figyelmeztetés |

### Platform értesítések

A `backend/app/services/discord.py` automatikusan küld embed üzeneteket:

| Esemény | Szín | Leírás |
|---------|------|--------|
| 📚 Beiratkozás | 🔵 | `{username}` beiratkozott a kurzusra |
| 🎓 Tanúsítvány | 🟢 | `{username}` tanúsítványa + hitelesítési link |
| 🚀 Előléptetés | 🟣 | `{username}` előléptetve |

Beállítás: `DISCORD_WEBHOOK_URL` a `.env`-ben. Ha üres, csendben átugródik.

### Szerepkör szinkronizáció

A `backend/app/services/discord_bot.py` automatikusan szinkronizálja a platform szerepköreit Discord-ra:

1. Felhasználó megadja Discord ID-ját a dashboardon (`PATCH /api/auth/me`)
2. Validáció: snowflake formátum, egyedi, tag a szerveren
3. Szerepkör hozzáadása automatikusan (profil összekapcsolás, előléptetés, admin szerepkörváltás)

**Környezeti változók:**

```bash
DISCORD_BOT_TOKEN=your-bot-token
DISCORD_GUILD_ID=your-guild-id
DISCORD_ROLE_MAP="student:ROLE_ID,mentor:ROLE_ID,admin:ROLE_ID"
```

Bot meghívása: Developer Portal → OAuth2 → scope: `bot` → jogosultság: `Manage Roles`. A bot szerepkörnek magasabbnak kell lennie a hierarchiában.

Ha a változók nincsenek beállítva, a szinkronizáció csendben átugródik.

### Moderáció

AutoMod ajánlás: spam szűrő (max 5 mention/üzenet), link szűrő (kivéve: github.com, discord.com, stackoverflow.com), kulcsszó szűrő.

---

## GitHub Classroom

### Előfeltételek

1. GitHub Organization (pl. `OpenSchool-HU`)
2. GitHub Classroom a szervezethez (<https://classroom.github.com>)
3. OpenSchool admin hozzáférés

### Környezeti változók

```bash
GITHUB_ORG=OpenSchool-HU                    # Szervezet neve
GITHUB_ORG_ADMIN_TOKEN=ghp_xxx...           # Org owner PAT (admin:org + repo scope)
GITHUB_WEBHOOK_SECRET=valami-titkos-kulcs   # Webhook HMAC (ajánlott)
```

A `GITHUB_ORG_ADMIN_TOKEN` kötelező: ezt használja a rendszer a CI státusz lekérdezéshez és az org meghíváshoz. A tanulók OAuth tokenje nem szükséges (csak `read:user` + `user:email` scope).

### Feladat összekötés lépései

1. **Kurzus/modul létrehozása** az admin panelen
2. **Assignment létrehozása** a GitHub Classroom-ban (title, repo prefix, template repo CI workflow-val)
3. **Feladat hozzárendelése** az admin panelen:

| Mező | Leírás | Példa |
|------|--------|-------|
| `repo_prefix` | **Pontosan** a Classroom assignment prefix | `python-hello-world` |
| `classroom_url` | Assignment meghívó link (tanulóknak) | `https://classroom.github.com/a/xYz123` |
| `classroom_teacher_url` | Teacher dashboard URL (importkor automatikus) | `https://classroom.github.com/classrooms/{id}/assignments/{id}` |

### A `repo_prefix` a kulcs

```
{GITHUB_ORG}/{repo_prefix}-{tanuló GitHub username}
```

Példa: `openschool-org/python-hello-world-johndoe`

Ennek **pontosan** egyeznie kell a Classroom által generált repónévvel.

### Webhook (automatikus haladásfrissítés)

GitHub org → Settings → Webhooks → Add webhook:
- **Payload URL:** `https://{domain}/api/webhooks/github`
- **Content type:** `application/json`
- **Secret:** megegyezik a `GITHUB_WEBHOOK_SECRET`-tel
- **Events:** `Workflow runs`

Működés: `tanuló push → CI fut → sikeres → webhook → repo_prefix egyeztetés → progress = completed`

Webhook nélkül: a tanuló a dashboardon a **„Haladás szinkronizálása"** gombbal frissíti.

### Tanulói folyamat

1. Bejelentkezés (OAuth → automatikus org meghívó)
2. Kurzusra beiratkozás
3. Classroom assignment elfogadása (📎 ikon)
4. Kód megírása → push → CI
5. Haladás frissítés (webhook / sync gomb)
6. Tanúsítvány igénylése ha kész

### Mi manuális, mi automatikus

| Lépés | Ki | Hol |
|-------|-----|-----|
| Kurzus/modul létrehozás | Admin | OpenSchool |
| Assignment létrehozás | Mentor | GitHub Classroom |
| Feladat hozzárendelés (`repo_prefix`) | Admin | OpenSchool (manuális vagy Classroom import) |
| Beiratkozás | Tanuló | OpenSchool |
| Assignment elfogadás | Tanuló | GitHub Classroom |
| CI futtatás | Automatikus | GitHub Actions |
| Haladás frissítés | Automatikus (webhook) / manuális (sync) | OpenSchool |
| Mentor haladás áttekintés | Mentor | OpenSchool (Classroom teacher dashboard linkek feladatonként) |

### Classroom Import funkció

Az admin panelen a moduloknál elérhető a **„📥 Import from Classroom"** gomb, amely a GitHub Classroom API-n keresztül lekérdezi az elérhető assignment-eket és automatikusan létrehozza a megfelelő feladatokat:

1. Admin a modul mellett kattint az **Import from Classroom** gombra
2. A rendszer lekérdezi az elérhető GitHub Classroom-okat (`GET /classrooms`)
3. Admin kiválasztja a Classroom-ot, majd a listából kijelöli az importálandó assignment-eket
4. Az import automatikusan beállítja a `repo_prefix` (assignment slug), `classroom_url` (invite link) és `classroom_teacher_url` (teacher dashboard URL) mezőket
5. Már importált assignment-ek szürkén jelennek meg
6. Re-import esetén a korábban importált feladatok `classroom_teacher_url` mezője automatikusan kitöltődik (backfill). Az endpoint válasza: `{"imported": [...], "skipped": [...], "updated": [...]}` — az `updated` lista a backfill-elt feladatokat tartalmazza

> **Megjegyzés:** A Classroom API csak olvasási jogot biztosít — assignment létrehozás továbbra is a GitHub Classroom webes felületén történik.

**Szükséges:** `GITHUB_ORG_ADMIN_TOKEN` (PAT `admin:org` + `repo` scope-pal)

### Ismert korlátok

1. ~~Nincs automatikus assignment szinkronizálás Classroom → OpenSchool~~ → **Megoldva: Classroom Import funkcióval**
2. Nincs automatikus beiratkozás (külön kell a két rendszerben)
3. A `repo_prefix`-nek pontosan egyeznie kell
4. Egy org támogatott (`GITHUB_ORG`)

### Hibaelhárítás

| Probléma | Ok |
|----------|----|
| Szinkronizálás nem talál repót | `GITHUB_ORG` nincs beállítva, vagy `repo_prefix` eltérés |
| Webhook nem frissít | `GITHUB_WEBHOOK_SECRET` eltérés, vagy nem `workflow_runs` event |
| „Sync not configured" hiba | `GITHUB_ORG` / `GITHUB_ORG_ADMIN_TOKEN` hiányzik |
| Haladás 0% | CI nem fut sikeresen, vagy nincs `.github/workflows/` a template-ben |
| Nincs org meghívó | `GITHUB_ORG_ADMIN_TOKEN` hiányzik, vagy nincs `admin:org` scope |
