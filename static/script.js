document.addEventListener("DOMContentLoaded", function() {
    const menuItems = document.querySelectorAll(".menu-item");
    menuItems.forEach(item => {
        item.addEventListener("mouseover", () => {
            item.style.transform = "scale(1.1)";
        });
        item.addEventListener("mouseout", () => {
            item.style.transform = "scale(1)";
        });
    });

    // Fade in effect for movies
    const movieCards = document.querySelectorAll(".movie-card");
    movieCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = 1;
            card.style.transform = "translateY(0)";
        }, index * 200);
    });
});
