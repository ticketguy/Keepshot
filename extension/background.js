// Background service worker
// Currently minimal — handles token refresh or future push notifications here.

chrome.runtime.onInstalled.addListener(() => {
  console.log("Keepshot extension installed.");
});
