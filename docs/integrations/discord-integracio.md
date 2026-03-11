# OpenSchool Platform — Discord integráció

> 📖 **Dokumentáció:** [Főoldal](../../README.md) · [Architektúra](../getting-started/architektura.md) · [Telepítés](../getting-started/telepitesi-utmutato.md) · [Környezeti változók](../getting-started/kornyezeti-valtozok.md) · [Fejlesztői útmutató](../development/fejlesztoi-utmutato.md) · [Backend](../development/backend-fejlesztes.md) · [Frontend](../development/frontend-fejlesztes.md) · [Tesztelés](../development/tesztelesi-utmutato.md) · [API referencia](../reference/api-referencia.md) · [Adatbázis](../reference/adatbazis-sema.md) · [Karbantartás](../operations/karbantartas-utmutato.md) · [Automatizálás](../operations/automatizalas-beallitas.md) · [GitHub Classroom](github-classroom-integraciot.md) · **Discord** · [Felhasználói útmutató](../guides/felhasznaloi-utmutato.md) · [Dokumentálás](../guides/dokumentacios-utmutato.md) · [Roadmap](../jovokep-es-fejlesztesi-terv.md) · [Hozzájárulás](../../CONTRIBUTING.md)

Ez az útmutató az OpenSchool Platform Discord szerverének felállítását, a webhook alapú értesítéseket, a CI/CD integrációt és a közösségi csatornastruktúrát írja le.

---

## Tartalomjegyzék

1. [Szerver felállítása](#1-szerver-felállítása)
2. [Csatornastruktúra](#2-csatornastruktúra)
3. [Webhook értesítések](#3-webhook-értesítések)
4. [CI/CD Discord értesítések](#4-cicd-discord-értesítések)
5. [Ops monitoring (VPS)](#5-ops-monitoring-vps)
6. [Discord bot (jövőbeli)](#6-discord-bot-jövőbeli)
7. [Moderáció és szabályok](#7-moderáció-és-szabályok)
8. [Hibaelhárítás](#8-hibaelhárítás)

---

## 1. Szerver felállítása

### Új szerver létrehozása

1. Discord → **+** (Szerver hozzáadása) → **Saját szerver** → **Közösség számára**
2. Adj nevet: `OpenSchool`
3. Állítsd be a szerver ikont (opcionális)

### Közösségi szerver engedélyezése

A közösségi funkciók szálakat (threads), fórumokat és moderációs eszközöket biztosítanak:

1. **Szerver beállítások → Közösség engedélyezése**
2. Állítsd be a szabályzat csatornát (`#szabályzat`)
3. Állítsd be a frissítések csatornát (`#közlemények`)

### Szerepkörök (roles) beállítása

| Szerepkör | Szín | Jogosultságok |
|-----------|------|---------------|
| `@Admin` | Piros | Minden jogosultság |
| `@Tanár` | Kék | Üzenetek kezelése, szálak létrehozása, pinelés |
| `@Mentor` | Zöld | Szálak létrehozása, reakciók kezelése |
| `@Diák` | Szürke | Üzenetek küldése, szálak használata |
| `@Bot` | Sárga | Webhookok, üzenetek küldése |

Beállítás: **Szerver beállítások → Szerepkörök → Új szerepkör**

---

## 2. Csatornastruktúra

Az ajánlott csatornastruktúra kurzusonként bővíthető:

```
📋 INFORMÁCIÓK
  #szabályzat          — szerver szabályok, magatartási kódex
  #közlemények          — fontos értesítések (csak admin/tanár írhat)
  #hasznos-linkek      — dokumentáció, repó, eszközök linkjei

🐍 PYTHON 10  (példa kurzus)
  #python10-általános  — általános kérdések, beszélgetés
  #python10-segítség   — heti szálak a kérdésekhez
  #python10-megoldások — elfogadott megoldások, tippek

⚡ BACKEND 13  (példa kurzus)
  #backend13-általános
  #backend13-segítség
  #backend13-megoldások

🤖 AUTOMATIZÁCIÓ
  #ops-alerts          — VPS monitoring értesítések (webhook)
  #ci-cd               — CI/CD pipeline értesítések (webhook)
  #github-activity     — GitHub push/PR/issue értesítések

💬 KÖZÖSSÉG
  #általános           — szabadtéma
  #bemutatkozás        — új tagok bemutatkozása
  #off-topic           — programozáson kívüli témák
```

### Csatorna létrehozása

```
Szerver → Jobb klikk a kategóriára → Csatorna létrehozása → Szöveges csatorna
```

### Fórum csatorna a segítséghez

A `#...-segítség` csatornák **Fórum** típusúak lehetnek — minden kérdés saját szálat kap:

1. Csatorna létrehozása → **Fórum** típus
2. Tag-ek beállítása: `megoldva`, `segítség-kell`, `modulN`
3. Alapértelmezett rendezés: **Legújabb aktivitás**

---

## 3. Webhook értesítések

A webhookok egyirányú értesítéseket küldenek a Discordra szkriptek, CI/CD vagy a platform nevében.

### Webhook létrehozása

1. Navigálj a célcsatornára (pl. `#ops-alerts`)
2. **Csatorna beállítások → Integrációk → Webhookok → Új webhook**
3. Adj nevet (pl. `OpenSchool CI`, `OpenSchool Monitoring`)
4. Kattints a **Webhook URL másolása** gombra
5. Mentsd el biztonságosan — ez a URL ne kerüljön Git-be!

### Webhook tesztelése

```bash
# Egyszerű teszt üzenet
curl -s -X POST "https://discord.com/api/webhooks/ID/TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"content": "**[OpenSchool]** Teszt értesítés — a webhook működik! ✅"}'

# Embed formátumú üzenet (szebb megjelenés)
curl -s -X POST "https://discord.com/api/webhooks/ID/TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "embeds": [{
      "title": "✅ Deploy sikeres",
      "description": "A main branch sikeresen deployolva a VPS-re.",
      "color": 3066993,
      "fields": [
        {"name": "Commit", "value": "`abc1234`", "inline": true},
        {"name": "Szerző", "value": "felhasználó", "inline": true}
      ],
      "timestamp": "2026-03-11T12:00:00.000Z"
    }]
  }'
```

### Webhook URL biztonságos tárolása

**Lokális fejlesztés:** `.env` fájlban (gitignore-ban van):

```bash
DISCORD_WEBHOOK_OPS=https://discord.com/api/webhooks/...
DISCORD_WEBHOOK_CI=https://discord.com/api/webhooks/...
```

**GitHub Actions:** Repository secrets-ben:

```
Settings → Secrets and variables → Actions → New repository secret
  Name: DISCORD_WEBHOOK_CI
  Value: https://discord.com/api/webhooks/...
```

**VPS:** `/etc/openschool-maintenance.conf` fájlban:

```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

---

## 4. CI/CD Discord értesítések

A `scripts/discord-notify.sh` szkript egységes értesítéseket küld a CI/CD pipeline eredményéről.

### Használat GitHub Actions-ben

Add hozzá a CI/CD workflow végéhez:

```yaml
# .github/workflows/ci.yml — a jobs.test végéhez:
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

```yaml
# .github/workflows/cd.yml — a deploy job végéhez:
      - name: Discord notification
        if: always()
        env:
          DISCORD_WEBHOOK_CI: ${{ secrets.DISCORD_WEBHOOK_CI }}
        run: |
          ./scripts/discord-notify.sh \
            --status "${{ job.status }}" \
            --title "Deploy: main → VPS" \
            --repo "${{ github.repository }}" \
            --commit "${{ github.sha }}" \
            --author "${{ github.actor }}" \
            --url "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
```

### Szkript paraméterek

| Paraméter | Leírás | Példa |
|-----------|--------|-------|
| `--status` | Job eredmény | `success`, `failure`, `cancelled` |
| `--title` | Értesítés címe | `CI: feat: add login` |
| `--repo` | Repó neve | `ghemrich/openschool-platform` |
| `--commit` | Commit SHA | `abc1234def5678` |
| `--author` | Commit szerzője | `ghemrich` |
| `--url` | Actions run link | `https://github.com/.../runs/123` |

---

## 5. Ops monitoring (VPS)

A `scripts/maintenance.sh` automatikusan küld Discord értesítéseket a VPS állapotáról, ha a `DISCORD_WEBHOOK_URL` be van állítva.

### Beállítás

Lásd: [Automatizálás — 5. lépés](../operations/automatizalas-beallitas.md#5-lépés--discord-értesítések-beállítása)

### Milyen eseményre küld értesítést?

| Esemény | Webhook üzenet |
|---------|---------------|
| Mentés sikertelen | DB nem elérhető, backup hiba |
| Health check hiba | Konténer leállt, `/health` nem válaszol |
| Lemezhasználat ≥90% | Kritikus lemezhasználat figyelmeztetés |
| SSL lejár ≤30 napon belül | Tanúsítvány lejárati figyelmeztetés |
| SSL lejárt | Azonnali riasztás |
| Biztonsági audit figyelmeztetés | pip-audit sérülékenységet talált |

### Kézi teszt

```bash
# A health check küld értesítést, ha baj van
./scripts/maintenance.sh health

# Direkt webhook teszt
source /etc/openschool-maintenance.conf
curl -s -X POST "$DISCORD_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{"content": "**[OpenSchool]** Kézi teszt — monitoring OK!"}'
```

---

## 6. Discord bot (jövőbeli)

> 🔴 **Tervezett** — jelenleg webhook alapú értesítések vannak. A bot fejlesztése a roadmap 1. fázisának része.

A jövőben egy Discord bot biztosíthatja a kétirányú integrációt:

| Funkció | Leírás |
|---------|--------|
| Beiratkozás értesítés | Diák beiratkozott → üzenet a kurzus csatornán |
| Tanúsítvány értesítés | Diák elvégezte a kurzust → gratulálás |
| Kurzus létrehozás | Új kurzus → automatikus csatornák létrehozása |
| Heti szálak | Automatikus heti Q&A szál indítása |
| `/status` parancs | Bot parancs a szerver/platform állapotának lekérdezéséhez |

### Előkészítés a bot fejlesztéséhez

1. [Discord Developer Portal](https://discord.com/developers/applications) → **New Application**
2. **Bot** fül → **Add Bot**
3. Jogosultságok: Send Messages, Create Public Threads, Embed Links, Read Message History
4. **OAuth2 → URL Generator** → `bot` scope → generált URL-lel meghívni a szerverbe
5. A bot token-t GitHub Secrets-ben tárolni: `DISCORD_BOT_TOKEN`

---

## 7. Moderáció és szabályok

### Szerver szabályzat minta (`#szabályzat` csatornához)

```markdown
# OpenSchool Discord szerver szabályzat

1. **Légy kedves és segítőkész** — konstruktív kommunikáció
2. **Kérdezz bátran** — nincs buta kérdés
3. **Ne oszd meg a megoldásokat** a segítség csatornán — adj tippet inkább
4. **Használd a megfelelő csatornát** — kurzus-specifikus kérdések a kurzus csatornán
5. **Angol és magyar** nyelv egyaránt elfogadott
6. **Spam, reklám és sértő tartalom** tiltott
```

### AutoMod beállítása

A Discord beépített AutoMod rendszere automatikusan moderál:

1. **Szerver beállítások → AutoMod**
2. Ajánlott szabályok:
   - **Spam szűrő:** mentionok korlátozása (max 5/üzenet)
   - **Link szűrő:** ismeretlen domain-ek blokkolása (kivéve: github.com, discord.com, stackoverflow.com)
   - **Kulcsszó szűrő:** sértő kifejezések tiltása

---

## 8. Hibaelhárítás

### Webhook nem küld üzenetet

```bash
# 1. Ellenőrizd a webhook URL-t
curl -s -o /dev/null -w "%{http_code}" -X POST "$DISCORD_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{"content": "teszt"}'
# Várt válasz: 204

# 2. Ellenőrizd, hogy a webhook nem lett törölve a Discord-ban
# (törölt webhook 404-et ad)

# 3. Rate limiting — Discord max 30 üzenet/perc/webhook
# Ha 429-es státuszt kapsz, várj a Retry-After header-ben jelzett ideig
```

### GitHub Actions secret nem érhető el

```yaml
# Ellenőrizd, hogy a secret neve pontosan megegyezik:
env:
  DISCORD_WEBHOOK_CI: ${{ secrets.DISCORD_WEBHOOK_CI }}
# A forked repókból induló PR-eknél a secrets NEM elérhető (biztonsági okokból)
```

### Embed formátum nem jelenik meg

- A `color` mező decimális szám (nem hex): `3066993` = `#2ecc71` zöld
- Embed limitek: title max 256 karakter, description max 4096, max 25 field

---

> **Kapcsolódó dokumentáció:**
> - [Automatizálás](../operations/automatizalas-beallitas.md) — VPS monitoring, cron jobok, Discord webhook beállítás
> - [Fejlesztői útmutató](../development/fejlesztoi-utmutato.md) — CI/CD pipeline, Git workflow
> - [Roadmap](../jovokep-es-fejlesztesi-terv.md) — Discord bot és platform értesítések terve
