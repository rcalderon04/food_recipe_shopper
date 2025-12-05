// Background Service Worker

// Open Side Panel on Action Click
chrome.action.onClicked.addListener((tab) => {
    // Open the side panel in the current window
    chrome.sidePanel.open({ windowId: tab.windowId });
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'addToCart') {
        processCartQueue(request.items, request.storefront);
    }
});

async function processCartQueue(items, storefront) {
    let tab = await findAmazonTab();
    if (!tab) {
        tab = await chrome.tabs.create({ url: 'https://www.amazon.com/' });
        await new Promise(r => setTimeout(r, 3000));
    }

    for (const item of items) {
        try {
            await addItemToCart(tab.id, item, storefront);
            await new Promise(r => setTimeout(r, 2000));
        } catch (e) {
            console.error(`Failed to add ${item.asin}:`, e);
        }
    }

    console.log('Cart processing complete');
}

async function findAmazonTab(storefront) {
    // 1. Try to find an ACTIVE Amazon tab first (best UX)
    const activeTabs = await chrome.tabs.query({ active: true, currentWindow: true });
    if (activeTabs.length > 0 && activeTabs[0].url.includes('amazon.com')) {
        return activeTabs[0];
    }

    // 2. Search for any Amazon tab
    const tabs = await chrome.tabs.query({ url: '*://*.amazon.com/*' });

    // 3. If storefront is specific, try to find a matching tab
    if (storefront === 'fresh') {
        const freshTab = tabs.find(t => t.url.includes('fresh') || t.url.includes('grocery'));
        if (freshTab) return freshTab;
    } else if (storefront === 'wholefoods') {
        const wfTab = tabs.find(t => t.url.includes('wholefoods'));
        if (wfTab) return wfTab;
    }

    // 4. Fallback to first Amazon tab found
    return tabs.length > 0 ? tabs[0] : null;
}

async function addItemToCart(tabId, item, storefront) {
    console.log(`Adding ${item.asin} (Qty: ${item.quantity})`);

    const url = item.url || `https://www.amazon.com/dp/${item.asin}`;
    await chrome.tabs.update(tabId, { url: url });

    await waitForLoad(tabId);

    await chrome.scripting.executeScript({
        target: { tabId: tabId },
        func: clickAddToCart,
        args: [item.quantity]
    });
}

function waitForLoad(tabId) {
    return new Promise(resolve => {
        chrome.tabs.onUpdated.addListener(function listener(tid, info) {
            if (tid === tabId && info.status === 'complete') {
                chrome.tabs.onUpdated.removeListener(listener);
                resolve();
            }
        });
    });
}

// This function runs IN THE TAB
async function clickAddToCart(quantity) {
    console.log(`Content Script: Attempting to add ${quantity} to cart...`);

    // Try multiple quantity selector patterns
    const qtySelectors = [
        '#quantity',  // Standard dropdown
        'select[name="quantity"]',  // Alternative dropdown
        'input[name="quantity"]'  // Input field
    ];

    let qtyElement = null;
    for (const sel of qtySelectors) {
        qtyElement = document.querySelector(sel);
        if (qtyElement) {
            console.log(`Found quantity selector: ${sel}`);
            break;
        }
    }

    if (qtyElement) {
        if (qtyElement.tagName === 'SELECT') {
            // For dropdowns, set the value
            qtyElement.value = quantity;
            qtyElement.dispatchEvent(new Event('change', { bubbles: true }));
        } else if (qtyElement.tagName === 'INPUT') {
            // For input fields, set the value
            qtyElement.value = quantity;
            qtyElement.dispatchEvent(new Event('input', { bubbles: true }));
            qtyElement.dispatchEvent(new Event('change', { bubbles: true }));
        }
        console.log(`Set quantity to ${quantity}`);

        // Wait a bit for Amazon to process the quantity change
        await new Promise(r => setTimeout(r, 500));
    } else {
        console.warn('Quantity selector not found, will add 1 item');
    }

    const selectors = [
        '#add-to-cart-button',
        '#freshAddToCartButton',
        'input[name="submit.add-to-cart"]',
        '#a-autoid-0-announce',
        'input[id^="add-to-cart-button"]'
    ];

    let btn = null;
    for (const sel of selectors) {
        btn = document.querySelector(sel);
        if (btn) {
            console.log(`Found Add to Cart button: ${sel}`);
            break;
        }
    }

    if (btn) {
        btn.click();
        console.log('Clicked Add to Cart');
    } else {
        console.error('Add to Cart button not found');
    }
}
