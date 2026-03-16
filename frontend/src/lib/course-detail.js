const slug = window.location.pathname.split("/").filter(Boolean).pop();

async function loadCourse() {
  const container = document.getElementById("course-detail");
  if (!container) return;

  const token = localStorage.getItem("access_token");
  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  try {
    const [res, progressRes, coursesRes] = await Promise.all([
      await fetch(`/api/courses/${slug}`, { headers }),
      await fetch(`/api/me/courses/${slug}/progress`, { headers }),
      await fetch(`/api/me/courses`, { headers }),
    ]);
    if (!res.ok) {
      container.innerHTML = "<p>Kurzus nem található.</p>";
      return;
    }
    const course = await res.json();
    const progress = await progressRes.json();
    const courses = await coursesRes.json();

    const userEnrolled = !!courses.find((course) => {
      return String(course.course_id) === slug;
    });

    let modulesHtml = "";
    if (course.modules && course.modules.length > 0) {
      modulesHtml =
        "<h2>Modulok</h2>" +
        course.modules
          .map(
            (m) =>
              `<div class="card module-card">
          <h3>${m.name}</h3>
          <ul>${m.exercises
            .map((e) => {
              const classroomLink = e.classroom_url
                ? ` <a href="${e.classroom_url}" target="_blank" rel="noopener" class="classroom-link" title="Megnyitás GitHub Classroom-ban">📎</a>`
                : "";
              return `<li>${e.name}${classroomLink}</li>`;
            })
            .join("")}</ul>
        </div>`,
          )
          .join("");
    }

    container.innerHTML = `
      <h1>${course.name}</h1>
      <p class="course-desc">${course.description || ""}</p>
      ${
        userEnrolled
          ? ""
          : `<button id="enroll-btn" class="btn btn-primary" style="margin:20px 0;">Beiratkozás</button>
      <div id="enroll-msg"></div>`
      }
      ${modulesHtml}
    `;

    document
      .getElementById("enroll-btn")
      ?.addEventListener("click", async () => {
        const t = localStorage.getItem("access_token");
        if (!t) {
          window.location.href = "/login";
          return;
        }
        const r = await fetch(`/api/courses/${slug}/enroll`, {
          method: "POST",
          headers: { Authorization: `Bearer ${t}` },
        });
        const msg = document.getElementById("enroll-msg");
        if (r.status === 201) {
          msg &&
            (msg.innerHTML =
              '<p style="color:green;">Sikeresen beiratkoztál!</p>');
        } else if (r.status === 409) {
          msg && (msg.innerHTML = "<p>Már beiratkoztál erre a kurzusra.</p>");
        } else {
          msg && (msg.innerHTML = '<p style="color:red;">Hiba történt.</p>');
        }
      });
  } catch {
    container.innerHTML = "<p>Kurzus nem elérhető.</p>";
  }
}

loadCourse();
