const BACKEND_URL = 'http://127.0.0.1:5000/api/parse';

let selectedItems = new Map();

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('parse-btn').addEventListener('click', parseRecipe);
    document.getElementById('add-to-cart-btn').addEventListener('click', addToCart);

    // Load saved settings
    const savedHeadless = localStorage.getItem('headlessMode');
    if (savedHeadless !== null) {
        document.getElementById('headless-mode').checked = savedHeadless === 'true';
    }

    // Save settings on change
    document.getElementById('headless-mode').addEventListener('change', (e) => {
        localStorage.setItem('headlessMode', e.target.checked);
    });

    document.getElementById('ingredients-list').addEventListener('click', (e) => {
        if (e.target.classList.contains('qty-btn')) {
            handleQuantityChange(e);
        }
    });

    document.getElementById('ingredients-list').addEventListener('change', (e) => {
        if (e.target.classList.contains('qty-input')) {
            handleQuantityInputChange(e);
        }
    });
});

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <div class="toast-message">${message}</div>
        </div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

async function parseRecipe() {
    const url = document.getElementById('recipe-url').value;
    if (!url) return showToast('Please enter a URL', 'error');

    document.getElementById('results-section').classList.add('hidden');
    document.getElementById('ingredients-list').innerHTML = '';
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('parse-btn').disabled = true;
    document.getElementById('floating-cart').classList.add('hidden');
    selectedItems.clear();
    updateCartSummary();

    try {
        const response = await fetch(BACKEND_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (data.error) throw new Error(data.error);

        document.getElementById('loading').classList.add('hidden');
        document.getElementById('results-section').classList.remove('hidden');
        document.getElementById('floating-cart').classList.remove('hidden');

        data.ingredients.forEach((ing, index) => {
            createIngredientRow(ing, index);
        });

        processIngredientsSequentially(data.ingredients);

    } catch (e) {
        showToast('Error: ' + e.message, 'error');
        document.getElementById('loading').classList.add('hidden');
    } finally {
        document.getElementById('parse-btn').disabled = false;
    }
}

function createIngredientRow(ingredientText, index) {
    const template = document.getElementById('ingredient-template');
    const clone = template.content.cloneNode(true);

    const row = clone.querySelector('.ingredient-row');
    row.id = `ing-row-${index}`;

    clone.querySelector('.ingredient-name').textContent = ingredientText.split(' ').slice(0, 3).join(' ') + '...';
    clone.querySelector('.ingredient-original').textContent = ingredientText;

    document.getElementById('ingredients-list').appendChild(clone);
}

async function processIngredientsSequentially(ingredients) {
    // Switch to batch processing
    await processIngredientsBatch(ingredients);
}

async function processIngredientsBatch(ingredients) {
    const BATCH_SIZE = 4; // Process 4 items at a time
    const storefront = document.getElementById('storefront-select').value;
    const headless = document.getElementById('headless-mode').checked;

    for (let i = 0; i < ingredients.length; i += BATCH_SIZE) {
        const batch = ingredients.slice(i, i + BATCH_SIZE);

        // Scroll first item into view
        const firstRow = document.getElementById(`ing-row-${i}`);
        if (firstRow) firstRow.scrollIntoView({ behavior: 'smooth', block: 'center' });

        // Update status for batch
        batch.forEach((ing, offset) => {
            const index = i + offset;
            const row = document.getElementById(`ing-row-${index}`);
            if (row) {
                const statusIndicator = row.querySelector('.status-indicator');
                statusIndicator.textContent = 'Searching items...';
                statusIndicator.classList.remove('hidden', 'error');
                statusIndicator.classList.add('loading');
            }
        });

        const queries = batch.map((ing, offset) => ({
            ingredient: ing,
            id: i + offset,
            storefront: storefront
        }));

        try {
            const response = await fetch('http://127.0.0.1:5000/api/search-batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    queries: queries,
                    headless: headless
                })
            });

            const data = await response.json();

            if (data.results) {
                data.results.forEach((res, resIndex) => {
                    // Start index + offset in batch
                    const originalIndex = i + resIndex;
                    updateRowWithResult(res, originalIndex, ingredients[originalIndex]);
                });
            }

        } catch (e) {
            console.error("Batch error:", e);
            batch.forEach((ing, offset) => {
                const index = i + offset;
                const row = document.getElementById(`ing-row-${index}`);
                if (row) {
                    const statusIndicator = row.querySelector('.status-indicator');
                    statusIndicator.textContent = 'Error';
                    statusIndicator.classList.add('error');
                }
            });
        }

        // Small delay between batches to be nice to API
        await new Promise(r => setTimeout(r, 1000));
    }
}

function updateRowWithResult(data, index, originalIngredient) {
    const row = document.getElementById(`ing-row-${index}`);
    if (!row) return;

    const statusIndicator = row.querySelector('.status-indicator');

    if (!data.options || data.options.length === 0) {
        statusIndicator.textContent = 'No products found';
        statusIndicator.classList.remove('loading');
        statusIndicator.classList.add('error');
        return;
    }

    row.querySelector('.ingredient-name').textContent = originalIngredient;
    statusIndicator.classList.add('hidden');

    const optionsContainer = row.querySelector('.product-options');
    optionsContainer.innerHTML = ''; // Clear previous
    optionsContainer.classList.remove('hidden');

    data.options.forEach((opt, optIndex) => {
        renderProductCard(opt, optIndex, index, optionsContainer);
    });
}

async function searchAmazon(query, storefront, headless) {
    try {
        const response = await fetch('http://127.0.0.1:5000/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ingredient: query,
                storefront: storefront,
                headless: headless
            })
        });

        if (!response.ok) throw new Error(`Backend returned ${response.status}`);

        const data = await response.json();
        return data;

    } catch (e) {
        console.error('Search error:', e);
        return { error: e.message };
    }
}

function renderProductCard(opt, optIndex, index, container) {
    const cardTemplate = document.getElementById('product-card-template');
    const cardClone = cardTemplate.content.cloneNode(true);
    const cardRoot = cardClone.querySelector('.product-card');

    const radio = cardClone.querySelector('input');
    radio.name = `ing-${index}`;
    radio.value = opt.asin;
    radio.checked = optIndex === 0;

    const itemData = {
        ...opt,
        ingredient_index: index,
        quantity: opt.quantity_recommendation || 1
    };

    const img = cardClone.querySelector('.product-img');
    img.src = opt.image || 'https://via.placeholder.com/80?text=No+Img';

    cardClone.querySelector('.product-title').textContent = opt.title;

    const productLink = cardClone.querySelector('.product-link');
    productLink.href = opt.url || `https://www.amazon.com/dp/${opt.asin}`;

    const badge = cardClone.querySelector('.confidence-badge');
    badge.textContent = `Match`;
    badge.classList.add('medium');

    // Add department badge
    const deptBadge = cardClone.querySelector('.department-badge');
    if (deptBadge && opt.department) {
        deptBadge.textContent = opt.department;
        deptBadge.classList.remove('hidden');

        if (opt.department.toLowerCase().includes('fresh')) {
            deptBadge.classList.add('fresh');
        } else if (opt.department.toLowerCase().includes('whole')) {
            deptBadge.classList.add('wholefoods');
        }
    }

    const priceEl = cardClone.querySelector('.price');
    const qtyInput = cardClone.querySelector('.qty-input');

    // Set initial quantity from recommendation
    qtyInput.value = itemData.quantity;

    itemData.elements = { priceEl, qtyInput, cardRoot };

    updateItemPriceDisplay(itemData);

    // Set up event handlers AFTER price is calculated
    radio.onchange = () => {
        selectedItems.set(index, itemData);
        updateCartSummary();
    };

    if (optIndex === 0) {
        selectedItems.set(index, itemData);
        updateCartSummary();
    }

    container.appendChild(cardClone);
}

function handleQuantityChange(e) {
    const btn = e.target.closest('.qty-btn');
    const card = btn.closest('.product-card');
    const input = card.querySelector('.qty-input');
    let val = parseInt(input.value);

    if (btn.classList.contains('plus')) val++;
    else if (btn.classList.contains('minus')) val--;

    if (val < 0) val = 0;
    input.value = val;

    updateModelFromDOM(card, val);
}

function handleQuantityInputChange(e) {
    const input = e.target;
    const card = input.closest('.product-card');
    let val = parseInt(input.value);
    if (val < 0) val = 0;

    updateModelFromDOM(card, val);
}

function updateModelFromDOM(card, qty) {
    const radio = card.querySelector('input[type="radio"]');

    if (radio.checked) {
        const index = parseInt(radio.name.split('-')[1]);
        const item = selectedItems.get(index);
        if (item && item.asin === radio.value) {
            item.quantity = qty;
            updateItemPriceDisplay(item);
            updateCartSummary();
        }
    } else {
        radio.click();
        const index = parseInt(radio.name.split('-')[1]);
        const item = selectedItems.get(index);
        if (item) {
            item.quantity = qty;
            card.querySelector('.qty-input').value = qty;
            updateItemPriceDisplay(item);
            updateCartSummary();
        }
    }
}

function updateItemPriceDisplay(item) {
    const { priceEl, cardRoot } = item.elements;

    console.log('updateItemPriceDisplay called:', {
        title: item.title,
        quantity: item.quantity,
        price: item.price
    });

    if (item.quantity === 0) {
        priceEl.textContent = 'Skipped';
        cardRoot.classList.add('skipped');
        item.total_price = 0;
    } else {
        cardRoot.classList.remove('skipped');
        let unitPrice = item.price;
        if (typeof unitPrice === 'string') {
            unitPrice = parseFloat(unitPrice.replace('$', '').replace(',', ''));
        }

        if (isNaN(unitPrice)) {
            priceEl.textContent = item.price;
            item.total_price = 0;
        } else {
            const total = (unitPrice * item.quantity).toFixed(2);
            priceEl.textContent = `$${unitPrice} ea (Total: $${total})`;
            item.total_price = parseFloat(total);
            console.log('Calculated total_price:', item.total_price);
        }
    }
}

function updateCartSummary() {
    let count = 0;
    let total = 0;

    console.log('updateCartSummary called, selectedItems:', selectedItems);

    selectedItems.forEach(item => {
        console.log('Processing item:', {
            title: item.title,
            quantity: item.quantity,
            total_price: item.total_price
        });

        if (item.quantity > 0) {
            count++;
            if (typeof item.total_price === 'number') {
                total += item.total_price;
            }
        }
    });

    console.log('Final cart summary:', { count, total });

    document.getElementById('selected-count').textContent = count;
    document.getElementById('total-cost').textContent = `($${total.toFixed(2)})`;
    document.getElementById('float-count').textContent = count;
    document.getElementById('float-total').textContent = `($${total.toFixed(2)})`;
}

function addToCart() {
    const items = Array.from(selectedItems.values())
        .filter(item => item.quantity > 0)
        .map(item => ({
            asin: item.asin,
            quantity: item.quantity,
            url: item.url
        }));

    if (items.length === 0) return showToast('No items to add', 'error');

    chrome.runtime.sendMessage({
        action: 'addToCart',
        items: items,
        storefront: document.getElementById('storefront-select').value
    });

    showToast('Started adding to cart! Check your Amazon tab.', 'success');
}
