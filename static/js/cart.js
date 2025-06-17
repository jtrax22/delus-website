function addToCart(productId) {
    fetch(`/add-to-cart/${productId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        // Update cart count in navbar if you have one
        updateCartCount(data.cart_total);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error adding product to cart');
    });
}

function updateCartCount(count) {
    const cartCounter = document.getElementById('cart-counter');
    if (cartCounter) {
        cartCounter.textContent = count;
    }
} 