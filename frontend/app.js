const ROLE_RANKS = {
  viewer: 10,
  member: 20,
  admin: 30,
};

const state = {
  apiBase: localStorage.getItem("convologix_api_base") || "http://127.0.0.1:8000",
  token: localStorage.getItem("convologix_auth_token") || "",
  user: readStoredUser(),
  authEnabled: true,
  currentMeetingId: null,
  pollTimer: null,
};

const pageTitles = {
  meetings: "Meetings",
  enrollment: "Enrollment",
  recognition: "Recognition",
  system: "System",
};

const authScreen = document.getElementById("auth-screen");
const appShell = document.getElementById("app-shell");
const authTitle = document.getElementById("auth-title");
const authResult = document.getElementById("auth-result");
const loginForm = document.getElementById("login-form");
const setupForm = document.getElementById("setup-form");
const logoutButton = document.getElementById("logout-button");
const userBadge = document.getElementById("user-badge");
const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".panel");
const pageTitle = document.getElementById("page-title");
const systemStatus = document.getElementById("system-status");
const apiBaseInput = document.getElementById("api-base-input");
const modelStatus = document.getElementById("model-status");
const diarizationCheckButton = document.getElementById("diarization-check-button");
const diarizationCheckResult = document.getElementById("diarization-check-result");
const galleryList = document.getElementById("gallery-list");
const processMeetingButton = document.getElementById("process-meeting-button");
const refreshMeetingsButton = document.getElementById("refresh-meetings-button");
const meetingOutput = document.getElementById("meeting-output");
const meetingList = document.getElementById("meeting-list");
const selectedMeetingStatus = document.getElementById("selected-meeting-status");
const userForm = document.getElementById("user-form");
const userList = document.getElementById("user-list");
const userResult = document.getElementById("user-result");

apiBaseInput.value = state.apiBase;

tabs.forEach((tab) => {
  tab.addEventListener("click", () => switchToTab(tab.dataset.tab));
});

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setResult(authResult, "Signing in...", "");
  const form = new FormData(event.currentTarget);

  try {
    const response = await publicRequest("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: form.get("email"),
        password: form.get("password"),
      }),
    });
    setSession(response);
    showApp();
  } catch (error) {
    setResult(authResult, error.message, "error");
  }
});

setupForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setResult(authResult, "Creating admin...", "");
  const form = new FormData(event.currentTarget);

  try {
    const response = await publicRequest("/api/auth/setup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        display_name: form.get("display_name"),
        email: form.get("email"),
        password: form.get("password"),
        role: "admin",
      }),
    });
    setSession(response);
    showApp();
  } catch (error) {
    setResult(authResult, error.message, "error");
  }
});

logoutButton.addEventListener("click", () => {
  clearSession();
  showAuth("login");
});

document.getElementById("settings-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  state.apiBase = apiBaseInput.value.replace(/\/$/, "");
  localStorage.setItem("convologix_api_base", state.apiBase);
  clearSession();
  await initialize();
});

diarizationCheckButton.addEventListener("click", async () => {
  diarizationCheckButton.disabled = true;
  setResult(diarizationCheckResult, "Checking PyAnnote model access...", "");
  try {
    const response = await request("/api/speech/diarization-check");
    setResult(
      diarizationCheckResult,
      response.message,
      response.ok && response.pipeline_loaded ? "success" : "error",
    );
    await refreshSystem();
  } catch (error) {
    setResult(diarizationCheckResult, error.message, "error");
  } finally {
    diarizationCheckButton.disabled = false;
  }
});

document.getElementById("meeting-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const result = document.getElementById("meeting-result");
  setResult(result, "Uploading meeting...", "");

  const form = new FormData(event.currentTarget);
  try {
    const response = await request("/api/meetings", { method: "POST", body: form });
    state.currentMeetingId = response.id;
    processMeetingButton.classList.remove("hidden");
    meetingOutput.innerHTML = "";
    setResult(result, `${response.title} uploaded with status: ${response.status}`, "success");
    await refreshMeetings();
  } catch (error) {
    setResult(result, error.message, "error");
  }
});

refreshMeetingsButton.addEventListener("click", refreshMeetings);

processMeetingButton.addEventListener("click", async () => {
  const result = document.getElementById("meeting-result");
  if (!state.currentMeetingId) {
    setResult(result, "Upload a meeting first.", "error");
    return;
  }

  processMeetingButton.disabled = true;
  setResult(result, "Processing speech. This can take a few minutes for longer recordings.", "");
  meetingOutput.innerHTML = "";

  try {
    const response = await request(`/api/meetings/${state.currentMeetingId}/process`, { method: "POST" });
    setResult(result, response.message, "");
    await refreshMeetings();
    startMeetingPolling(state.currentMeetingId);
    await refreshSystem();
  } catch (error) {
    setResult(result, error.message, "error");
  } finally {
    processMeetingButton.disabled = false;
  }
});

document.getElementById("enroll-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const result = document.getElementById("enroll-result");
  setResult(result, "Saving enrollment images...", "");

  const form = new FormData(event.currentTarget);
  try {
    const response = await request("/api/faces/enroll", { method: "POST", body: form });
    setResult(result, response.message, response.model.ready ? "success" : "");
    await refreshSystem();
  } catch (error) {
    setResult(result, error.message, "error");
  }
});

document.getElementById("recognize-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const output = document.getElementById("recognition-results");
  output.innerHTML = '<div class="result-band">Running recognition...</div>';

  const form = new FormData(event.currentTarget);
  try {
    const response = await request("/api/faces/recognize", { method: "POST", body: form });
    renderRecognition(response);
    await refreshSystem();
  } catch (error) {
    output.innerHTML = `<div class="result-band error">${escapeHtml(error.message)}</div>`;
  }
});

userForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setResult(userResult, "Creating user...", "");
  const form = new FormData(event.currentTarget);

  try {
    const response = await request("/api/auth/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        display_name: form.get("display_name"),
        email: form.get("email"),
        password: form.get("password"),
        role: form.get("role"),
      }),
    });
    setResult(userResult, `${response.display_name} added as ${response.role}.`, "success");
    event.currentTarget.reset();
    await refreshUsers();
  } catch (error) {
    setResult(userResult, error.message, "error");
  }
});

document.addEventListener("submit", async (event) => {
  const formElement = event.target;
  if (!(formElement instanceof HTMLFormElement) || !formElement.classList.contains("email-form")) {
    return;
  }

  event.preventDefault();
  const meetingId = formElement.dataset.meetingId;
  const resultElement = formElement.querySelector(".email-result");
  const emailInput = formElement.querySelector("input[name='receiver_email']");
  resultElement.textContent = "Sending...";

  try {
    const response = await request(`/api/meetings/${meetingId}/email-report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ receiver_email: emailInput.value }),
    });
    resultElement.textContent = response.message;
  } catch (error) {
    resultElement.textContent = error.message;
  }
});

document.addEventListener("click", async (event) => {
  if (!(event.target instanceof Element)) {
    return;
  }
  const button = event.target.closest(".report-download");
  if (!button) {
    return;
  }

  button.disabled = true;
  try {
    await downloadReport(button.dataset.meetingId, button.dataset.reportType);
  } catch (error) {
    setResult(document.getElementById("meeting-result"), error.message, "error");
  } finally {
    button.disabled = false;
  }
});

async function initialize() {
  try {
    const status = await publicRequest("/api/auth/status");
    state.authEnabled = status.enabled;
    if (!status.enabled) {
      state.user = {
        id: "auth-disabled",
        email: "auth-disabled@local",
        display_name: "Local Admin",
        role: "admin",
      };
      showApp();
      return;
    }

    if (status.setup_required) {
      clearSession();
      showAuth("setup");
      return;
    }

    if (!state.token) {
      showAuth("login");
      return;
    }

    state.user = await request("/api/auth/me");
    persistUser();
    showApp();
  } catch (error) {
    showAuth("login");
    setResult(authResult, error.message, "error");
  }
}

function setSession(response) {
  state.token = response.access_token;
  state.user = response.user;
  localStorage.setItem("convologix_auth_token", state.token);
  persistUser();
}

function persistUser() {
  if (state.user) {
    localStorage.setItem("convologix_auth_user", JSON.stringify(state.user));
  }
}

function clearSession() {
  state.token = "";
  state.user = null;
  localStorage.removeItem("convologix_auth_token");
  localStorage.removeItem("convologix_auth_user");
  clearMeetingPolling();
}

function showAuth(mode) {
  authScreen.classList.remove("hidden");
  appShell.classList.add("hidden");
  authResult.classList.add("hidden");
  loginForm.classList.toggle("hidden", mode !== "login");
  setupForm.classList.toggle("hidden", mode !== "setup");
  authTitle.textContent = mode === "setup" ? "Create Admin" : "Sign in";
}

function showApp() {
  authScreen.classList.add("hidden");
  appShell.classList.remove("hidden");
  const userName = state.user?.display_name || "User";
  const role = state.user?.role || "viewer";
  userBadge.textContent = `${userName} · ${role}`;
  logoutButton.classList.toggle("hidden", !state.authEnabled);
  applyRoleUi();
  refreshSystem();
}

function switchToTab(tabName) {
  const targetTab = Array.from(tabs).find((tab) => tab.dataset.tab === tabName && !tab.classList.contains("hidden"));
  if (!targetTab) {
    return;
  }
  tabs.forEach((item) => item.classList.toggle("active", item === targetTab));
  panels.forEach((panel) => panel.classList.toggle("active", panel.id === tabName));
  pageTitle.textContent = pageTitles[tabName] || "ConvoLogix";
}

function applyRoleUi() {
  document.querySelectorAll("[data-min-role]").forEach((element) => {
    element.classList.toggle("hidden", !hasRole(element.dataset.minRole));
  });

  const activeTab = document.querySelector(".tab.active");
  if (activeTab?.classList.contains("hidden")) {
    const firstVisibleTab = Array.from(tabs).find((tab) => !tab.classList.contains("hidden"));
    if (firstVisibleTab) {
      switchToTab(firstVisibleTab.dataset.tab);
    }
  }
}

function hasRole(role) {
  const actual = ROLE_RANKS[state.user?.role] || 0;
  const required = ROLE_RANKS[role] || 0;
  return actual >= required;
}

async function refreshSystem() {
  try {
    const health = await publicRequest("/api/health");
    systemStatus.textContent = health.model.ready ? "Model ready" : "API online";
    systemStatus.className = health.model.ready ? "status-pill ready" : "status-pill";
    renderModelStatus(health.model, health.speech);

    if (hasRole("viewer")) {
      const gallery = await request("/api/faces/gallery");
      renderGallery(gallery.people);
      await refreshMeetings();
    }
    if (hasRole("admin")) {
      await refreshUsers();
    }
  } catch (error) {
    systemStatus.textContent = "API offline";
    systemStatus.className = "status-pill error";
    modelStatus.innerHTML = `<div class="result-band error">${escapeHtml(error.message)}</div>`;
    galleryList.innerHTML = '<div class="result-band">No gallery loaded.</div>';
  }
}

async function refreshUsers() {
  try {
    const users = await request("/api/auth/users");
    renderUsers(users);
  } catch (error) {
    userList.innerHTML = `<div class="result-band error">${escapeHtml(error.message)}</div>`;
  }
}

async function refreshMeetings() {
  try {
    const meetings = await request("/api/meetings");
    renderMeetingList(meetings);
    if (state.currentMeetingId) {
      const selected = meetings.find((meeting) => meeting.id === state.currentMeetingId);
      if (selected) {
        renderMeetingDetail(selected);
        return;
      }
    }
    if (meetings.length) {
      state.currentMeetingId = meetings[0].id;
      renderMeetingDetail(meetings[0]);
    } else {
      selectedMeetingStatus.innerHTML = '<div class="result-band">No meeting selected.</div>';
      meetingOutput.innerHTML = "";
    }
  } catch (error) {
    meetingList.innerHTML = `<div class="result-band error">${escapeHtml(error.message)}</div>`;
  }
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (state.authEnabled && state.token) {
    headers.set("Authorization", `Bearer ${state.token}`);
  }
  return handleResponse(path, await fetch(`${state.apiBase}${path}`, { ...options, headers }), true);
}

async function publicRequest(path, options = {}) {
  return handleResponse(path, await fetch(`${state.apiBase}${path}`, options), false);
}

async function handleResponse(path, response, authenticated) {
  const payload = await readPayload(response);
  if (authenticated && response.status === 401) {
    clearSession();
    showAuth("login");
  }
  if (!response.ok) {
    throw new Error(payload.detail || `Request failed with ${response.status}`);
  }
  return payload;
}

async function readPayload(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  const text = await response.text();
  return { detail: text };
}

function renderGallery(people) {
  if (!people.length) {
    galleryList.innerHTML = '<div class="result-band">No attendees enrolled yet.</div>';
    return;
  }

  galleryList.innerHTML = people
    .map(
      (person) => `
        <div class="gallery-item">
          <strong>${escapeHtml(person.display_name)}</strong>
          <span>${person.image_count} images</span>
        </div>
      `,
    )
    .join("");
}

function renderUsers(users) {
  if (!users.length) {
    userList.innerHTML = '<div class="result-band">No users created yet.</div>';
    return;
  }

  userList.innerHTML = users
    .map(
      (user) => `
        <div class="user-item">
          <div>
            <strong>${escapeHtml(user.display_name)}</strong>
            <span>${escapeHtml(user.email)}</span>
          </div>
          <span class="role-badge">${escapeHtml(user.role)}</span>
        </div>
      `,
    )
    .join("");
}

function renderRecognition(response) {
  const output = document.getElementById("recognition-results");
  if (!response.faces.length) {
    output.innerHTML = '<div class="result-band">No faces detected in this image.</div>';
    return;
  }

  output.innerHTML = response.faces
    .map(
      (face) => `
        <div class="match-item">
          <div>
            <strong>${escapeHtml(face.identity)}</strong>
            <span>Box ${face.bbox.join(", ")}</span>
          </div>
          <span>${Math.round(face.confidence * 100)}%</span>
        </div>
      `,
    )
    .join("");
}

function renderMeetingList(meetings) {
  if (!meetings.length) {
    meetingList.innerHTML = '<div class="result-band">No meetings uploaded yet.</div>';
    return;
  }

  meetingList.innerHTML = meetings
    .map(
      (meeting) => `
        <button class="meeting-card ${meeting.id === state.currentMeetingId ? "active" : ""}" data-meeting-id="${meeting.id}" type="button">
          <div>
            <strong>${escapeHtml(meeting.title)}</strong>
            <span>${escapeHtml(meeting.file_name)}</span>
          </div>
          <span class="status-chip ${escapeHtml(meeting.status)}">${escapeHtml(meeting.status)}</span>
        </button>
      `,
    )
    .join("");

  meetingList.querySelectorAll(".meeting-card").forEach((card) => {
    card.addEventListener("click", async () => {
      try {
        state.currentMeetingId = card.dataset.meetingId;
        await loadMeetingDetail(state.currentMeetingId);
        renderMeetingList(await request("/api/meetings"));
      } catch (error) {
        meetingList.innerHTML = `<div class="result-band error">${escapeHtml(error.message)}</div>`;
      }
    });
  });
}

async function loadMeetingDetail(meetingId) {
  const detail = await request(`/api/meetings/${meetingId}`);
  renderMeetingDetail(detail);
}

function renderMeetingDetail(detail) {
  state.currentMeetingId = detail.id;
  const canProcess =
    hasRole("member") && ["uploaded", "failed", "processed_without_diarization", "processed"].includes(detail.status);
  processMeetingButton.classList.toggle("hidden", !canProcess);

  selectedMeetingStatus.innerHTML = `
    <div>
      <strong>${escapeHtml(detail.title)}</strong>
      <span>${escapeHtml(detail.file_name)}</span>
      ${detail.owner_email ? `<span>${escapeHtml(detail.owner_email)}</span>` : ""}
    </div>
    <span class="status-chip ${escapeHtml(detail.status)}">${escapeHtml(detail.status)}</span>
    ${detail.error_message ? `<div class="result-band error">${escapeHtml(detail.error_message)}</div>` : ""}
    ${detail.result ? reportLinks(detail.id) : ""}
  `;

  if (detail.result) {
    renderMeetingResult(detail.result);
  } else {
    meetingOutput.innerHTML =
      detail.status === "queued" || detail.status === "processing"
        ? '<div class="result-band">Processing is running. Results will appear here automatically.</div>'
        : '<div class="result-band">Process this meeting to generate transcript, speaker summary, attendance, and reports.</div>';
  }
}

function renderMeetingResult(response) {
  const summary = response.summary_by_speaker.length
    ? response.summary_by_speaker
        .map(
          (item) => `
            <div class="speaker-card">
              <strong>${escapeHtml(item.speaker)}</strong>
              <p>${escapeHtml(item.summary || "No summary available.")}</p>
            </div>
          `,
        )
        .join("")
    : '<div class="result-band">No speaker summary generated.</div>';

  const attendance = response.attendance.length
    ? response.attendance
        .map(
          (item) => `
            <div class="speaker-card">
              <strong>${escapeHtml(item.person)}</strong>
              <p>${item.detections} detections, first seen ${formatTime(item.first_seen)}, last seen ${formatTime(item.last_seen)}, best confidence ${Math.round(item.best_confidence * 100)}%</p>
            </div>
          `,
        )
        .join("")
    : `<div class="result-band">${escapeHtml(response.attendance_message)}</div>`;

  const turns = response.speaker_turns.length
    ? response.speaker_turns
        .map(
          (turn) => `
            <div class="transcript-item">
              <span>${formatTime(turn.start)} - ${formatTime(turn.end)}</span>
              <strong>${escapeHtml(turn.speaker)}</strong>
              <p>${escapeHtml(turn.text)}</p>
            </div>
          `,
        )
        .join("")
    : '<div class="result-band">No transcript turns generated.</div>';

  meetingOutput.innerHTML = `
    <div class="output-section">
      <h4>Reports</h4>
      ${reportLinks(response.id)}
      ${emailReportForm(response.id)}
    </div>
    <div class="output-section">
      <h4>Who Said What</h4>
      <div class="summary-list">${summary}</div>
    </div>
    <div class="output-section">
      <h4>Attendance</h4>
      <div class="attendance-list">${attendance}</div>
    </div>
    <div class="output-section">
      <h4>Speaker Turns</h4>
      <div class="speaker-turns">${turns}</div>
    </div>
  `;
}

function emailReportForm(meetingId) {
  if (!hasRole("member")) {
    return "";
  }
  return `
    <form class="email-form" data-meeting-id="${meetingId}">
      <label>
        Email report
        <input name="receiver_email" type="email" placeholder="recipient@example.com" required />
      </label>
      <button class="secondary-action" type="submit">Send</button>
      <span class="email-result"></span>
    </form>
  `;
}

function reportLinks(meetingId) {
  return `
    <div class="report-links">
      <button class="report-download" data-meeting-id="${meetingId}" data-report-type="md" type="button">Markdown Report</button>
      <button class="report-download" data-meeting-id="${meetingId}" data-report-type="txt" type="button">Text Report</button>
    </div>
  `;
}

async function downloadReport(meetingId, reportType) {
  const headers = new Headers();
  if (state.authEnabled && state.token) {
    headers.set("Authorization", `Bearer ${state.token}`);
  }
  const response = await fetch(`${state.apiBase}/api/meetings/${meetingId}/report.${reportType}`, { headers });
  if (response.status === 401) {
    clearSession();
    showAuth("login");
  }
  if (!response.ok) {
    const payload = await readPayload(response);
    throw new Error(payload.detail || `Report download failed with ${response.status}`);
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `convologix-${meetingId}.${reportType}`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function startMeetingPolling(meetingId) {
  clearMeetingPolling();
  state.pollTimer = window.setInterval(async () => {
    try {
      const detail = await request(`/api/meetings/${meetingId}`);
      renderMeetingDetail(detail);
      await refreshMeetings();
      if (["processed", "processed_without_diarization", "failed"].includes(detail.status)) {
        clearMeetingPolling();
      }
    } catch (error) {
      setResult(document.getElementById("meeting-result"), error.message, "error");
      clearMeetingPolling();
    }
  }, 3000);
}

function clearMeetingPolling() {
  if (state.pollTimer) {
    window.clearInterval(state.pollTimer);
    state.pollTimer = null;
  }
}

function renderModelStatus(model, speech) {
  const values = [
    ["Detector", model.detector_exists ? "Ready" : "Missing"],
    ["Recognizer", model.recognizer_exists ? "Ready" : "Missing"],
    ["Gallery", model.gallery_exists ? "Built" : "Empty"],
    ["Threshold", String(model.threshold)],
  ];

  const speechValues = speech
    ? [
        ["FFmpeg", speech.ffmpeg_available ? "Ready" : "Missing"],
        ["ASR", speech.ready_for_transcription ? speech.asr_model : "Missing"],
        ["Diarization", speech.ready_for_diarization ? "Configured" : "Needs token/package"],
        ["Model access", speech.diarization_model_access || "not_checked"],
      ]
    : [];

  modelStatus.innerHTML = `
    <div class="result-band ${model.ready ? "success" : ""}">${escapeHtml(model.message)}</div>
    ${speech ? `<div class="result-band ${speech.ready_for_diarization ? "success" : ""}">${escapeHtml(speech.message)}</div>` : ""}
    ${values
      .map(
        ([label, value]) => `
          <div class="model-item">
            <strong>${label}</strong>
            <span>${value}</span>
          </div>
        `,
      )
      .join("")}
    ${speechValues
      .map(
        ([label, value]) => `
          <div class="model-item">
            <strong>${label}</strong>
            <span>${value}</span>
          </div>
        `,
      )
      .join("")}
  `;
}

function setResult(element, message, tone) {
  element.className = `result-band ${tone || ""}`.trim();
  element.textContent = message;
}

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem("convologix_auth_user") || "null");
  } catch {
    localStorage.removeItem("convologix_auth_user");
    return null;
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatTime(seconds) {
  const totalSeconds = Math.max(0, Math.round(seconds));
  const minutes = Math.floor(totalSeconds / 60);
  const remainder = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${remainder}`;
}

initialize();
