function getToken() {
  return localStorage.getItem("access_token");
}

function requireAuth() {
  const token = getToken();
  if (!token) {
    window.location.href = "/login";
    return null;
  }
  return { Authorization: `Bearer ${token}` };
}

async function loadDashboard() {
  const container = document.getElementById("dashboard-content");
  if (!container) return;

  const headers = requireAuth();
  if (!headers) return;

  try {
    const [dashRes, certRes] = await Promise.all([
      fetch("/api/me/dashboard", { headers }),
      fetch("/api/me/certificates", { headers }),
    ]);

    if (dashRes.status === 401 || dashRes.status === 403) {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
      return;
    }

    const courses = await dashRes.json();
    const certs = certRes.ok ? await certRes.json() : [];

    if (courses.length === 0) {
      container.innerHTML = `
        <p>Még nem iratkoztál be semmilyen kurzusra.</p>
        <a href="/courses" class="btn btn-primary" style="margin-top:16px;">Kurzusok böngészése</a>
      `;
      return;
    }

    const certMap = {};
    certs.forEach((c) => {
      certMap[c.course_id] = c;
    });

    // Kurzus kártyák
    const cards = await Promise.all(
      courses.map(async (c, index) => {
        const cert = certMap[c.course_id];
        const isComplete = c.progress_percent >= 100;

        // Az adott kurzus module-ok, és ezeknek a státuszainak lekérdezése
        const [progressRes, coursesRes] = await Promise.all([
          fetch(`/api/me/courses/${c.course_id}/progress`, { headers }),
          fetch(`/api/courses/${c.course_id}`, { headers }),
        ]);

        const progressData = await progressRes.json();
        const coursesData = await coursesRes.json();

        let successfulModules = 0;
        for (const pr of progressData) {
          if (pr.exercises.every((ex) => ex.status === "completed"))
            successfulModules++;
        }

        const modulesLists = progressData
          .map((module) => {
            // A Statusok magyarosításához használt függvény
            function translateStatus(status) {
              switch (status) {
                case "in_progress":
                  return "✏️ (Folyamatban)";
                case "completed":
                  return "✅ (Teljesített)";
                default:
                  return "🔴 (Nincs elkezdve)";
              }
            }
            // Lista a moduleokról, és azoknak a feladatairól
            return `
          <div data-id="${module.module_id}" class="modulelists_info">
            <strong class="modulelists_-title">${module.module_name} - teljesítve: ${module.exercises.filter((ex) => ex.status === "completed").length} / ${module.exercises.length}</strong>
            <ul class="modulelists_dropdownlist" data-id="${module.module_id}">
              ${module.exercises
                .map((ex) => {
                  const courseModule = coursesData.modules.find(
                    (m) => m.id === module.module_id,
                  );

                  const exercise = courseModule?.exercises.find(
                    (e) => e.id === ex.id,
                  );

                  return `<li class="modulelists_dropdownlist-item">
                 ${
                   exercise?.classroom_url &&
                   ex.status !== "completed" &&
                   ex.status !== "in_progress"
                     ? `<a href="${exercise.classroom_url}">${ex.name}</a>`
                     : `<span>${ex.name}</span>`
                 }
                    <span style="color:${
                      ex.status === "completed"
                        ? "green"
                        : ex.status === "in_progress"
                          ? "orange"
                          : "gray"
                    }; font-weight:500; font-size: 10px;">
                      ${translateStatus(ex.status)}
                    </span>
                  </li>`;
                })
                .join("")}
            </ul>
          </div>
          <hr style='border: 1px solid #acacac;  width=100%;'/>`;
          })
          .join("");

        const modulesHtml = `
       ${
         progressData.length > 0
           ? `  <div>
      <div class="modulelists-container">
    <h2>Modulok - teljesítve: ${successfulModules}/${progressData.length}</h2>
       <button
            id="moduleList-toggleBtn"
            data-id="${index}"
            class="btn btn-primary"
          >
            Részletek
          </button>
          </div>
      <div id="moduleList" data-id="${index}"  class="modulelists card closed">
      ${modulesLists}
      </div>
      </div>`
           : ""
       }`;

        let certHtml = "";
        if (cert) {
          certHtml = `<button class="btn btn-secondary download-cert" data-cert-id="${cert.cert_id}" style="margin-top:8px;">PDF letöltése</button>`;
        } else if (isComplete) {
          certHtml = `<button class="btn btn-primary request-cert" data-course-id="${c.course_id}" style="margin-top:8px;">Tanúsítvány igénylése</button>`;
        }

        return `
          <div class="card" style="margin-bottom:16px;">
            <h3>${c.course_name}</h3>
            <div class="progress-wrapper">
              <div class="progress-bar">
                <div class="progress-bar-fill" style="width:${c.progress_percent}%;"></div>
              </div>
              <span style="font-weight:600;margin-left:12px;">
                ${c.completed_exercises}/${c.total_exercises} — ${c.progress_percent}%
              </span>
            </div>
            <div>
                ${modulesHtml}
            </div>
            ${certHtml}
          </div>
        `;
      }),
    );

    container.innerHTML = cards.join("");

    document.querySelectorAll(".download-cert").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const certId = e.target.dataset.certId;
        const r = await fetch(`/api/me/certificates/${certId}/pdf`, {
          headers,
        });
        if (r.ok) {
          const blob = await r.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `certificate-${certId}.pdf`;
          a.click();
          URL.revokeObjectURL(url);
        } else {
          alert("Nem sikerült letölteni a PDF-et.");
        }
      });
    });

    document.querySelectorAll(".request-cert").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const courseId = e.target.dataset.courseId;
        const r = await fetch(`/api/me/courses/${courseId}/certificate`, {
          method: "POST",
          headers,
        });
        if (r.status === 201) {
          window.location.reload();
        } else {
          const d = await r.json();
          alert(d.detail || "Hiba történt.");
        }
      });
    });

    container.querySelectorAll("#moduleList-toggleBtn").forEach((btn) => {
      if (btn) {
        btn.addEventListener("click", (e) => {
          const dataId = e.target.getAttribute("data-id");

          document.querySelectorAll("#moduleList").forEach((el) => {
            if (el.dataset.id !== dataId) {
              el.classList.add("closed");
            } else {
              el.classList.toggle("closed");
            }
          });
        });
      }
    });
  } catch {
    container.innerHTML = "<p>Hiba történt a betöltés során.</p>";
  }
}

function initSyncButton() {
  document.getElementById("sync-btn")?.addEventListener("click", async () => {
    const headers = requireAuth();
    if (!headers) return;

    const btn = document.getElementById("sync-btn");
    const msg = document.getElementById("sync-msg");
    if (btn) btn.disabled = true;
    if (btn) btn.textContent = "⏳ Szinkronizálás...";
    try {
      const r = await fetch("/api/me/sync-progress", {
        method: "POST",
        headers,
      });
      if (r.ok) {
        if (msg)
          msg.innerHTML = '<p style="color:green;">Haladás frissítve!</p>';
        setTimeout(() => window.location.reload(), 1000);
      } else {
        const d = await r.json();
        if (msg)
          msg.innerHTML = `<p style="color:red;">${d.detail || "Hiba történt."}</p>`;
      }
    } catch {
      if (msg)
        msg.innerHTML =
          '<p style="color:red;">Hiba történt a szinkronizálás során.</p>';
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = "🔄 Haladás szinkronizálása GitHub-ból";
      }
    }
  });
}

loadDashboard();
initSyncButton();
