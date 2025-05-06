// Book Store Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Star rating functionality
    initializeRatingStars();

    // Book image error handling
    handleBookImageErrors();

    // Search form functionality
    initializeSearchForm();

    // Filter form functionality
    initializeFilterForm();
});

/**
 * Initialize interactive star rating functionality
 */
function initializeRatingStars() {
    const ratingControls = document.querySelectorAll('.rating-control');
    
    ratingControls.forEach(control => {
        const stars = control.querySelectorAll('.star');
        const ratingInput = control.querySelector('input[name="rating"]');
        const ratingDisplay = control.querySelector('.rating-value');
        
        stars.forEach((star, index) => {
            // Show rating value on hover
            star.addEventListener('mouseenter', () => {
                const rating = index + 1;
                highlightStars(stars, rating);
                if (ratingDisplay) {
                    ratingDisplay.textContent = rating;
                }
            });
            
            // Reset to current value on mouseleave
            star.addEventListener('mouseleave', () => {
                const currentRating = parseInt(ratingInput.value || 0);
                highlightStars(stars, currentRating);
                if (ratingDisplay) {
                    ratingDisplay.textContent = currentRating || '';
                }
            });
            
            // Set rating on click
            star.addEventListener('click', () => {
                const rating = index + 1;
                ratingInput.value = rating;
                highlightStars(stars, rating);
                if (ratingDisplay) {
                    ratingDisplay.textContent = rating;
                }
            });
        });
        
        // Initialize with current value
        const currentRating = parseInt(ratingInput.value || 0);
        highlightStars(stars, currentRating);
        if (ratingDisplay) {
            ratingDisplay.textContent = currentRating || '';
        }
    });
}

/**
 * Highlight stars up to a given rating
 */
function highlightStars(stars, rating) {
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('active');
        } else {
            star.classList.remove('active');
        }
    });
}

/**
 * Handle book image loading errors
 */
function handleBookImageErrors() {
    const bookImages = document.querySelectorAll('.book-image');
    
    bookImages.forEach(img => {
        img.onerror = function() {
            // Replace with placeholder based on size
            const size = this.dataset.size || 'm';
            if (size === 's') {
                this.src = 'https://via.placeholder.com/60x80?text=No+Cover';
            } else if (size === 'm') {
                this.src = 'https://via.placeholder.com/100x140?text=No+Cover';
            } else {
                this.src = 'https://via.placeholder.com/200x280?text=No+Cover';
            }
            this.alt = 'Book cover not available';
            this.classList.add('missing-cover');
        };
    });
}

/**
 * Initialize search form functionality
 */
function initializeSearchForm() {
    const searchForm = document.getElementById('search-form');
    if (!searchForm) return;
    
    const searchInput = searchForm.querySelector('input[name="search"]');
    const clearSearchBtn = searchForm.querySelector('.clear-search');
    
    if (clearSearchBtn && searchInput) {
        // Show/hide clear button based on input value
        searchInput.addEventListener('input', () => {
            if (searchInput.value) {
                clearSearchBtn.style.display = 'block';
            } else {
                clearSearchBtn.style.display = 'none';
            }
        });
        
        // Clear search when button is clicked
        clearSearchBtn.addEventListener('click', () => {
            searchInput.value = '';
            clearSearchBtn.style.display = 'none';
            searchForm.submit();
        });
        
        // Initialize clear button display
        if (searchInput.value) {
            clearSearchBtn.style.display = 'block';
        }
    }
}

/**
 * Initialize filter form functionality
 */
function initializeFilterForm() {
    const filterForm = document.getElementById('filter-form');
    if (!filterForm) return;
    
    const filterSelects = filterForm.querySelectorAll('select');
    
    filterSelects.forEach(select => {
        // Submit form when a filter changes
        select.addEventListener('change', () => {
            filterForm.submit();
        });
    });
    
    const clearFiltersBtn = document.getElementById('clear-filters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Reset all filters
            filterSelects.forEach(select => {
                select.value = '';
            });
            
            // Clear search input if it exists
            const searchInput = filterForm.querySelector('input[name="search"]');
            if (searchInput) {
                searchInput.value = '';
            }
            
            // Submit the form
            filterForm.submit();
        });
    }
}

/**
 * Add a book to the user's library
 */
function addToLibrary(isbn) {
    fetch(`/add_to_library/${isbn}`)
        .then(response => {
            if (response.ok) {
                // Change the button appearance
                const addButton = document.querySelector(`.add-to-library[data-isbn="${isbn}"]`);
                if (addButton) {
                    addButton.innerHTML = '<i class="fas fa-check"></i> In Library';
                    addButton.classList.remove('btn-outline-primary');
                    addButton.classList.add('btn-success');
                    addButton.disabled = true;
                }
                
                // Show success message
                const toast = new bootstrap.Toast(document.getElementById('success-toast'));
                document.getElementById('toast-message').textContent = 'Book added to your library!';
                toast.show();
            } else {
                throw new Error('Failed to add book to library');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Show error message
            const toast = new bootstrap.Toast(document.getElementById('error-toast'));
            document.getElementById('error-toast-message').textContent = 'Failed to add book to library';
            toast.show();
        });
}
