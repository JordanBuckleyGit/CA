// document.addEventListener("DOMContentLoaded", function() {
//     const menuItems = document.querySelectorAll(".menu-item");
//     menuItems.forEach(item => {
//         item.addEventListener("mouseover", () => {
//             item.style.transform = "scale(1.1)";
//         });
//         item.addEventListener("mouseout", () => {
//             item.style.transform = "scale(1)";
//         });
//     });

//     // Fade in effect for movies
//     const movieCards = document.querySelectorAll(".movie-card");
//     movieCards.forEach((card, index) => {
//         setTimeout(() => {
//             card.style.opacity = 1;
//             card.style.transform = "translateY(0)";
//         }, index * 200);
//     });
// });

const navToggle = document.getElementById('nav-toggle');
const navLinks = document.getElementById('nav-links');

navToggle.addEventListener('click', () => {
    navLinks.classList.toggle('active');
});

const dnaBoxes = document.querySelectorAll('.dna-box');
dnaBoxes.forEach(box => {
    box.addEventListener('mouseenter', () => {
        box.style.transform = 'translateY(-10px)';
        box.style.boxShadow = '0 10px 20px rgba(255, 215, 0, 0.3)';
    });
    box.addEventListener('mouseleave', () => {
        box.style.transform = 'translateY(0)';
        box.style.boxShadow = 'none';
    });
});

const userIcon = document.getElementById('user-icon');
if (userIcon) {
    userIcon.addEventListener('mouseenter', () => {
        userIcon.style.transform = 'scale(1.1)';
    });
    userIcon.addEventListener('mouseleave', () => {
        userIcon.style.transform = 'scale(1)';
    });
}