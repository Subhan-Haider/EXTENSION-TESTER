// Popup script
document.getElementById('actionBtn').addEventListener('click', () => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    chrome.tabs.sendMessage(tabs[0].id, { type: 'ACTION', data: 'button-clicked' });
  });
});
