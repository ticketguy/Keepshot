/**
 * Keepshot Bookmarklet
 *
 * Minify this and prefix with "javascript:" to create a one-click
 * drag-to-toolbar bookmarklet. The user is prompted for their JWT on first use,
 * then it's stored in localStorage for subsequent saves.
 *
 * Usage:
 *   1. Paste the minified version into a new bookmark's URL field.
 *   2. Drag it to the browser toolbar.
 *   3. Click it on any page to save to Keepshot.
 */

(function () {
  const API_URL = "https://api.keepshot.xyz"; // Change to your API URL

  let token = localStorage.getItem("keepshot_token");
  if (!token) {
    token = prompt("Paste your Keepshot API token:");
    if (!token) return;
    localStorage.setItem("keepshot_token", token);
  }

  const body = JSON.stringify({
    content_type: "url",
    url: location.href,
    title: document.title,
    monitoring_enabled: false,
  });

  fetch(`${API_URL}/bookmarks`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body,
  })
    .then((r) => {
      if (r.status === 401) {
        localStorage.removeItem("keepshot_token");
        alert("Token expired. Click the bookmarklet again to re-enter.");
        return;
      }
      if (!r.ok) return r.json().then((e) => { throw new Error(e.detail || r.status); });
      alert("Saved to Keepshot!");
    })
    .catch((e) => alert("Keepshot error: " + e.message));
})();
