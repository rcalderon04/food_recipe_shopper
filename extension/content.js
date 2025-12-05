// Content script for Recipe to Amazon Fresh
console.log('Recipe to Amazon Fresh Extension Loaded');

// Listen for messages from popup or background
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'ping') {
        sendResponse({ status: 'alive' });
    }
});
