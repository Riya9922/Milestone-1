document.addEventListener('DOMContentLoaded', async () => {
    // Initialize Lucide Icons
    lucide.createIcons();

    const locationSelect = document.getElementById('location-select');
    const cuisineSearch = document.getElementById('cuisine-search');
    const cuisineDropdown = document.getElementById('cuisine-dropdown');
    const cuisinesFilterBtn = document.getElementById('cuisines-filter-btn');
    const cuisinesFilterDropdown = document.getElementById('cuisines-filter-dropdown');
    const cuisinesList = document.getElementById('cuisines-list');
    const restaurantGrid = document.getElementById('restaurant-grid');


    const aiContext = document.getElementById('ai-context');
    const aiSummaryText = document.getElementById('ai-summary-text');
    const currentLocationLabel = document.getElementById('current-location');
    const template = document.getElementById('restaurant-template');

    const BACKEND_URL = "https://milestone-1-39voagm5ffmygarhbqpk39.streamlit.app";

    // State
    let activeFilters = {
        rating: false,
        fast: false,
        veg: false
    };



    // 1. Load Metadata (Localities & Cuisines)
    let allCuisines = [];
    let restoNamesInArea = [];
    try {

        const [locResp, cuisResp] = await Promise.all([
            fetch(`${BACKEND_URL}/api/v1/localities`),
            fetch(`${BACKEND_URL}/api/v1/cuisines`)
        ]);
        
        const locData = await locResp.json();
        locationSelect.innerHTML = '<option value="">Select Location</option>';
        locData.localities.forEach(loc => {
            const opt = document.createElement('option');
            opt.value = loc;
            opt.textContent = loc;
            locationSelect.appendChild(opt);
        });

        const cuisData = await cuisResp.json();
        allCuisines = cuisData.cuisines;

        // Populate Cuisines Filter Dropdown
        cuisinesList.innerHTML = allCuisines.map(c => `
            <div class="flex items-center gap-2 px-2 py-1 hover:bg-gray-50 rounded cursor-pointer cuisine-filter-item" data-value="${c}">
                <div class="w-4 h-4 border rounded flex-shrink-0 flex items-center justify-center"></div>
                <span class="text-sm text-gray-600">${c}</span>
            </div>
        `).join('');

        // Default to first location if none selected
        if (locData.localities.length > 0) {
            locationSelect.value = locData.localities[0];
            updateLocationUI();
            fetchRestoNames(); // Initial fetch
            triggerSearch();
        }
    } catch (err) {
        console.error("Failed to load metadata", err);
    }

    async function fetchRestoNames() {
        if (!locationSelect.value) return;
        try {
            const resp = await fetch(`${BACKEND_URL}/api/v1/restaurant-names?location=${encodeURIComponent(locationSelect.value)}`);
            const data = await resp.json();
            restoNamesInArea = data.names;
        } catch (err) {
            console.error("Failed to load resto names", err);
        }
    }

    // 2. Cuisine Prediction Logic
    cuisineSearch.addEventListener('input', (e) => {
        const val = e.target.value.toLowerCase();
        if (!val) {
            cuisineDropdown.classList.add('hidden');
            return;
        }

        // Filter cuisines
        const cuisineMatches = allCuisines.filter(c => c && c.toLowerCase().includes(val)).slice(0, 5);
        // Filter restaurant names
        const restoMatches = restoNamesInArea.filter(n => n && n.toLowerCase().includes(val)).slice(0, 10);
        
        if (cuisineMatches.length > 0 || restoMatches.length > 0) {
            let html = '';
            if (restoMatches.length > 0) {
                html += '<div class="px-4 py-2 text-xs font-bold text-gray-400 bg-gray-50 uppercase tracking-widest border-t first:border-t-0">Restaurants</div>';
                html += restoMatches.map(n => `
                    <div class="px-4 py-3 hover:bg-gray-100 cursor-pointer text-sm border-b last:border-0 search-option resto-option" data-type="resto">
                        <div class="flex items-center gap-2">
                            <i data-lucide="utensils" class="w-4 h-4 text-gray-400"></i>
                            <span>${n}</span>
                        </div>
                    </div>
                `).join('');
            }
            if (cuisineMatches.length > 0) {
                html += '<div class="px-4 py-2 text-xs font-bold text-gray-400 bg-gray-50 uppercase tracking-widest border-t first:border-t-0">Cuisines</div>';
                html += cuisineMatches.map(c => `
                    <div class="px-4 py-3 hover:bg-gray-100 cursor-pointer text-sm border-b last:border-0 search-option cuisine-option" data-type="cuisine">
                        <div class="flex items-center gap-2">
                            <i data-lucide="search" class="w-4 h-4 text-gray-400"></i>
                            <span>${c}</span>
                        </div>
                    </div>
                `).join('');
            }
            
            cuisineDropdown.innerHTML = html;
            cuisineDropdown.classList.remove('hidden');
            lucide.createIcons();
        } else {
            cuisineDropdown.classList.add('hidden');
        }

    });

    // Handle clicking a prediction
    cuisineDropdown.addEventListener('click', (e) => {
        const option = e.target.closest('.search-option');
        if (option) {
            cuisineSearch.value = option.textContent.trim();
            cuisineDropdown.classList.add('hidden');
            triggerSearch();
        }
    });

    // Cuisines Filter Dropdown Logic
    cuisinesFilterBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        cuisinesFilterDropdown.classList.toggle('hidden');
    });

    cuisinesList.addEventListener('click', (e) => {
        const item = e.target.closest('.cuisine-filter-item');
        if (item) {
            const val = item.dataset.value;
            cuisineSearch.value = val;
            cuisinesFilterDropdown.classList.add('hidden');
            triggerSearch();
        }
    });

    // Close dropdowns on click outside
    document.addEventListener('click', (e) => {
        if (!cuisineSearch.contains(e.target) && !cuisineDropdown.contains(e.target)) {
            cuisineDropdown.classList.add('hidden');
        }
        if (!cuisinesFilterBtn.contains(e.target) && !cuisinesFilterDropdown.contains(e.target)) {
            cuisinesFilterDropdown.classList.add('hidden');
        }
    });

    // 3. Event Listeners
    locationSelect.addEventListener('change', () => {
        updateLocationUI();
        fetchRestoNames(); // Refresh names for new area
        triggerSearch();
    });


    cuisineSearch.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') triggerSearch();
    });

    document.querySelectorAll('.filter-chip[data-filter]').forEach(chip => {
        chip.addEventListener('click', () => {
            const filter = chip.dataset.filter;
            activeFilters[filter] = !activeFilters[filter];
            chip.classList.toggle('active', activeFilters[filter]);
            triggerSearch();
        });
    });

    function updateLocationUI() {
        currentLocationLabel.textContent = locationSelect.value || "Bangalore";
    }

    // 3. Search Orchestration
    async function triggerSearch() {
        if (!locationSelect.value) return;

        // UI: Loading state
        restaurantGrid.innerHTML = `
            <div class="col-span-full py-20 text-center">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto mb-4"></div>
                <p class="text-gray-500 font-medium">Curating your personalized list...</p>
            </div>
        `;
        aiContext.classList.add('hidden');

        const payload = {
            location: locationSelect.value,
            cuisine: cuisineSearch.value ? [cuisineSearch.value] : null,
            budget_max_inr: 5000, // Default broad budget for discovery
            min_rating: activeFilters.rating ? 4.0 : 0.0,
            extras: activeFilters.veg ? "Pure Veg" : null
        };

        try {
            const resp = await fetch(`${BACKEND_URL}/api/v1/recommend`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!resp.ok) throw new Error("Search failed");

            const data = await resp.json();
            renderResults(data);
        } catch (err) {
            restaurantGrid.innerHTML = `<div class="col-span-full py-20 text-center text-red-500">Something went wrong. Please try again.</div>`;
        }
    }

    // 4. Render Results
    function renderResults(data) {
        restaurantGrid.innerHTML = '';
        
        if (data.summary) {
            aiSummaryText.textContent = data.summary;
            aiContext.classList.remove('hidden');
        }

        if (!data.items || data.items.length === 0) {
            restaurantGrid.innerHTML = `
                <div class="col-span-full py-20 text-center">
                    <img src="https://b.zmtcdn.com/webFrontend/64d79aa393ca1b37495393160ed984631584444589.png" class="w-64 mx-auto mb-6 grayscale opacity-50">
                    <h3 class="text-xl font-bold text-gray-400">No matches found for your criteria</h3>
                </div>
            `;
            return;
        }

        data.items.forEach((item, index) => {
            const clone = template.content.cloneNode(true);
            const card = clone.querySelector('div');
            
            // Set dynamic fields
            const imgId = ['1517248135467-4c7edcad34c4', '1552566626-52f8b828add9', '1414235077428-338989a2e8c0'][index % 3];
            card.querySelector('img').src = `https://images.unsplash.com/photo-${imgId}?auto=format&fit=crop&q=80&w=600&h=400&sig=${item.id}`;
            card.querySelector('.name-text').textContent = item.name;
            card.querySelector('.rating-val').textContent = item.rating || "N/A";
            card.querySelector('.cuisine-text').textContent = Array.isArray(item.cuisines) ? item.cuisines.join(', ') : item.cuisines;
            card.querySelector('.cost-text').textContent = `₹${item.cost_for_two || '??'} for two`;
            card.querySelector('.explanation-text').textContent = item.explanation;
            
            if (index < 3) card.querySelector('.trending-label').classList.remove('hidden');
            
            restaurantGrid.appendChild(clone);
        });

        // Re-initialize icons for newly added elements
        lucide.createIcons();
    }
});
