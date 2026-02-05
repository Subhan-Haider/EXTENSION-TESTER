// Content script for injecting functionality into web pages
console.log('Content script loaded');

// Example: Send message to background
chrome.runtime.sendMessage({ type: 'ACTION', data: 'page-loaded' }, (response) => {
  console.log('Response from background:', response);
});

// Example: Highlight specific elements
document.querySelectorAll('a').forEach(link => {
  if (link.textContent.includes('example')) {
    link.classList.add('extension-highlight');
  }
});
