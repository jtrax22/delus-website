document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        // Only process if href is not just "#" and starts with #
        if (href && href !== '#') {
            e.preventDefault();
            try {
                const targetId = href.split('#')[1]; // Get the ID without the #
                const target = document.getElementById(targetId);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth'
                    });
                }
            } catch (error) {
                console.log('Smooth scroll error:', error);
            }
        }
    });
}); 