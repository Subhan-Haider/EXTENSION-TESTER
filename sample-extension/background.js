// Service Worker for background tasks
console.log('Service worker loaded');

// Example: Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'ACTION') {
    console.log('Action received:', request.data);
    sendResponse({ success: true });
  }
});
