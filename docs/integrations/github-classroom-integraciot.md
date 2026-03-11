# OpenSchool Platform — GitHub Classroom integráció

> 📖 **Dokumentáció:** [Főoldal](../../README.md) · [Architektúra](../getting-started/architektura.md) · [Telepítés](../getting-started/telepitesi-utmutato.md) · [Környezeti változók](../getting-started/kornyezeti-valtozok.md) · [Fejlesztői útmutató](../development/fejlesztoi-utmutato.md) · [Backend](../development/backend-fejlesztes.md) · [Frontend](../development/frontend-fejlesztes.md) · [Tesztelés](../development/tesztelesi-utmutato.md) · [API referencia](../reference/api-referencia.md) · [Adatbázis](../reference/adatbazis-sema.md) · [Karbantartás](../operations/karbantartas-utmutato.md) · [Automatizálás](../operations/automatizalas-beallitas.md) · **GitHub Classroom** · [Discord](discord-integracio.md) · [Felhasználói útmutató](../guides/felhasznaloi-utmutato.md) · [Dokumentálás](../guides/dokumentacios-utmutato.md) · [Roadmap](../jovokep-es-fejlesztesi-terv.md) · [Hozzájárulás](../../CONTRIBUTING.md)

Ez a dokumentum lépésről lépésre leírja, hogyan kell egy GitHub Classroom-ban létrehozott feladatot összekötni az OpenSchool platformmal, és hogyan működik az automatikus értékelés.

## Tartalomjegyzék

- [Előfeltételek](#előfeltételek)
- [1. lépés: `.env` beállítása](#1-lépés-env-beállítása)
- [2. lépés: Kurzus és modulok létrehozása](#2-lépés-kurzus-és-modulok-létrehozása-az-openschool-ban)
- [3. lépés: Feladat létrehozása a GitHub Classroom-ban](#3-lépés-feladat-létrehozása-a-github-classroom-ban)
- [4. lépés: Feladat hozzárendelése az OpenSchool-ban](#4-lépés-feladat-hozzárendelése-az-openschool-ban)
- [5. lépés: Webhook beállítása](#5-lépés-webhook-beállítása-opcionális-de-ajánlott)
- [6. lépés: Tanulói folyamat](#6-lépés-tanulói-folyamat)
- [Összefoglaló](#összefoglaló-mi-manuális-és-mi-automatikus)
- [Ismert korlátok](#ismert-korlátok)
- [Hibaelhárítás](#hibaelhárítás)

---

## Előfeltételek

1. **GitHub Organization** — kell egy GitHub szervezet (org), amelyben a GitHub Classroom működik (pl. `openschool-org`)
2. **GitHub Classroom** — a szervezethez kapcsolt Classroom (<https://classroom.github.com>)
3. **OpenSchool admin hozzáférés** — admin szerepkörű felhasználó a platformon
4. **`.env` konfigurálva** — a `GITHUB_ORG` kitöltve (lásd lent)

---

## 1. lépés: `.env` beállítása

A `.env` fájlban a következő értékeket kell kitölteni:

```env
GITHUB_ORG=openschool-org          # A GitHub org neve, ahol a Classroom repókat hozza létre
GITHUB_WEBHOOK_SECRET=valami-titkos-kulcs  # Webhook HMAC ellenőrzéshez (opcionális, de ajánlott)
```

A `GITHUB_ORG` kritikus: ez mondja meg a rendszernek, hogy melyik szervezet alatt keresse a tanulók repóit. Ha üresen marad, a rendszer a bejelentkezett felhasználó saját GitHub-ját használja tulajdonosként, ami nem fog működni Classroom repókkal.

---

## 2. lépés: Kurzus és modulok létrehozása az OpenSchool-ban

1. Nyisd meg az **Admin panel** → **Kurzusok** oldalt (`/admin/courses`)
2. Hozd létre a kurzust (név + leírás)
3. A kurzus alatt hozd létre a modulokat (pl. „1. modul: Alapok")

---

## 3. lépés: Feladat létrehozása a GitHub Classroom-ban

1. Menj a <https://classroom.github.com> oldalra
2. Válaszd ki a Classroom-ot
3. Hozz létre egy új **Assignment**-et:
   - **Title:** pl. „Hello World"
   - **Repository prefix:** pl. `python-hello-world`
   - Válassz egy **template repository**-t, amely tartalmazza a feladat leírását és a CI teszteket (GitHub Actions workflow `.github/workflows/` mappában)

> **Fontos:** A repó prefix az, ami összepárosítja a GitHub Classroom-ot az OpenSchool-lal. Ha a Classroom-ban a prefix `python-hello-world`, akkor a rendszer a tanulónak `python-hello-world-{github-username}` nevű repót fog keresni.

---

## 4. lépés: Feladat hozzárendelése az OpenSchool-ban

Az admin panelen, a kurzus részleteinél add hozzá a feladatot:

| Mező | Mit írj be | Példa |
|---|---|---|
| **Feladat neve** | A feladat megjelenítési neve | `Hello World` |
| **repo_prefix** | **Pontosan** ugyanaz, mint a Classroom assignment prefix | `python-hello-world` |
| **classroom_url** | A Classroom assignment meghívó linkje | `https://classroom.github.com/a/xYz123` |
| **Sorrend** | A feladat sorrendje a modulon belül | `1` |

### A `repo_prefix` a kulcs

A rendszer a következő képlettel keresi a tanuló repóját:

```
{GITHUB_ORG}/{repo_prefix}-{tanuló GitHub username}
```

Példa:
- `GITHUB_ORG = openschool-org`
- `repo_prefix = python-hello-world`
- Tanuló GitHub username: `johndoe`
- Keresett repó: `openschool-org/python-hello-world-johndoe`

Ez **pontosan** meg kell, hogy egyezzen azzal, amit a GitHub Classroom létrehoz. A Classroom alapértelmezetten `{assignment-prefix}-{student-username}` formátumot használ, ami egyezik.

---

## 5. lépés: Webhook beállítása (opcionális, de ajánlott)

A webhook lehetővé teszi, hogy a haladás **automatikusan** frissüljön sikeres CI futás után, anélkül, hogy a tanuló megnyomná a „Haladás szinkronizálása" gombot.

### GitHub Organization webhook konfigurálása

1. Menj a GitHub org beállításaihoz: `https://github.com/organizations/{org}/settings/hooks`
2. Kattints **Add webhook**
3. Töltsd ki:
   - **Payload URL:** `https://{your-domain}/api/webhooks/github`
   - **Content type:** `application/json`
   - **Secret:** ugyanaz mint a `.env`-ben a `GITHUB_WEBHOOK_SECRET`
   - **Events:** válaszd a **Workflow runs** eseményt
4. Mentés

### Hogyan működik

```
Tanuló push-ol → CI fut → CI sikeres → GitHub küld workflow_run event
→ OpenSchool webhook fogadja → repo neve: python-hello-world-johndoe
→ megkeresi az exercise-t ahol repo_prefix = python-hello-world
→ megkeresi a user-t ahol username = johndoe
→ progress = completed
```

---

## 6. lépés: Tanulói folyamat

A tanuló szemszögéből:

1. Bejelentkezik az OpenSchool-ba GitHub OAuth-tal
2. Megnézi a kurzust → kattint a **„Beiratkozás"** gombra
3. A feladat mellett kattint a **📎** ikonra → megnyílik a GitHub Classroom assignment link
4. Elfogadja az assignment-et → GitHub Classroom létrehozza a repót
5. Megoldja a feladatot, push-ol → CI fut
6. Ha a CI sikeres:
   - **Webhook esetén:** a haladás automatikusan frissül
   - **Webhook nélkül:** a tanuló a Dashboard-on kattint a **„Haladás szinkronizálása GitHub-ból"** gombra

---

## Összefoglaló: mi manuális és mi automatikus

| Lépés | Ki csinálja | Hol |
|---|---|---|
| Kurzus/modul létrehozása | Admin | OpenSchool admin panel |
| Assignment létrehozása | Tanár | GitHub Classroom |
| Feladat hozzárendelése (`repo_prefix` + `classroom_url`) | Admin | OpenSchool admin panel |
| Beiratkozás kurzusra | Tanuló | OpenSchool frontend |
| Assignment elfogadása | Tanuló | GitHub Classroom link |
| Kód megírása és push | Tanuló | Git/GitHub |
| CI futtatás | Automatikus | GitHub Actions |
| Haladás frissítése | Automatikus (webhook) vagy manuális (sync gomb) | OpenSchool |
| Tanúsítvány igénylése | Tanuló | OpenSchool dashboard |

---

## Ismert korlátok

A jelenlegi rendszerben az alábbiak **nem** automatikusak:

1. **Nincs automatikus assignment szinkronizálás** — Ha a tanár létrehoz egy új assignment-et a GitHub Classroom-ban, azt manuálisan kell felvenni az OpenSchool admin panelen is (`repo_prefix` + `classroom_url`). A platform nem kérdezi le a Classroom API-t.

2. **Nincs automatikus beiratkozás** — Ha egy tanuló elfogad egy Classroom assignment-et, az nem jelenti, hogy az OpenSchool-ban is be van iratkozva. A két rendszerben külön kell beiratkozni.

3. **A `repo_prefix`-nek pontosan egyeznie kell** — Ha a Classroom-ban és az OpenSchool-ban eltérő a prefix, a haladás nem lesz felismerve.

4. **Egy org szükséges** — A rendszer egy GitHub org-ot támogat (`GITHUB_ORG`). Ha több Classroom különböző org-ok alatt fut, az nem működik.

---

## Hibaelhárítás

| Probléma | Lehetséges ok |
|---|---|
| Szinkronizálás nem talál repót | `GITHUB_ORG` nincs beállítva a `.env`-ben, vagy a `repo_prefix` nem egyezik a Classroom prefix-szel |
| Webhook nem frissít | `GITHUB_WEBHOOK_SECRET` nem egyezik, vagy a webhook nem a `workflow_runs` eseményre van beállítva |
| „Nincs GitHub token" hiba | A tanuló token-je lejárt — újra be kell jelentkeznie |
| Haladás 0% marad | A CI workflow nem fut sikeresen a tanuló repójában, vagy nincs `.github/workflows/` a template repóban |
