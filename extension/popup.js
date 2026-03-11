const $ = (id) => document.getElementById(id);

let selectedType = "url";

// ── Boot ──────────────────────────────────────────────────────────────────────
chrome.storage.sync.get(["apiUrl", "token"], ({ apiUrl, token }) => {
  if (apiUrl && token) {
    showSaveScreen();
  } else {
    showSetupScreen();
  }
});

// ── Setup screen ──────────────────────────────────────────────────────────────
function showSetupScreen() {
  $("setup-screen").style.display = "block";
  $("save-screen").style.display = "none";

  chrome.storage.sync.get(["apiUrl"], ({ apiUrl }) => {
    if (apiUrl) $("api-url").value = apiUrl;
  });
}

$("login-btn").addEventListener("click", async () => {
  const apiUrl   = $("api-url").value.trim().replace(/\/$/, "");
  const username = $("username").value.trim();
  const password = $("password").value;

  if (!apiUrl || !username || !password) {
    $("setup-status").textContent = "All fields are required.";
    return;
  }

  $("login-btn").disabled = true;
  $("login-btn").textContent = "Connecting…";
  $("setup-status").textContent = "";

  try {
    const res = await fetch(`${apiUrl}/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username, password }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const { access_token } = await res.json();
    chrome.storage.sync.set({ apiUrl, token: access_token }, () => {
      showSaveScreen();
    });

  } catch (e) {
    $("setup-status").textContent = `Login failed: ${e.message}`;
  } finally {
    $("login-btn").disabled = false;
    $("login-btn").textContent = "Connect";
  }
});

// ── Save screen ───────────────────────────────────────────────────────────────
function showSaveScreen() {
  $("setup-screen").style.display = "none";
  $("save-screen").style.display = "block";

  // Load current tab info
  chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
    $("page-title").textContent = tab.title || tab.url;
    $("page-url").textContent   = tab.url;
  });
}

// Content type selector
document.querySelectorAll(".type-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".type-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    selectedType = btn.dataset.type;
  });
});

// Save button
$("save-btn").addEventListener("click", async () => {
  const status = $("status");
  status.textContent = "";
  status.className = "";

  chrome.tabs.query({ active: true, currentWindow: true }, async ([tab]) => {
    chrome.storage.sync.get(["apiUrl", "token"], async ({ apiUrl, token }) => {
      $("save-btn").disabled = true;
      $("save-btn").textContent = "Saving…";

      try {
        const body = {
          content_type: selectedType,
          url: tab.url,
          title: tab.title,
          monitoring_enabled: $("monitor-toggle").checked,
        };

        const res = await fetch(`${apiUrl}/bookmarks`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(body),
        });

        if (res.status === 401) {
          // Token expired — go back to login
          chrome.storage.sync.remove(["token"]);
          showSetupScreen();
          return;
        }

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `HTTP ${res.status}`);
        }

        status.textContent = "Saved!";
        status.className = "status-ok";

      } catch (e) {
        status.textContent = `Error: ${e.message}`;
        status.className = "status-err";
      } finally {
        $("save-btn").disabled = false;
        $("save-btn").textContent = "Save to Keepshot";
      }
    });
  });
});

// Disconnect
$("logout-link").addEventListener("click", () => {
  chrome.storage.sync.remove(["token"], () => {
    showSetupScreen();
  });
});
