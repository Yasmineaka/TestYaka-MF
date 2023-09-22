// slide des temoignages

const temoignages = document.querySelectorAll('.temoignage');
let currentIndex = 0;
let intervalId;

function showTemoignages(index) {
temoignages.forEach((temoignage, i) => {
    if (i >= index && i < index + 3) {
        temoignage.style.display = 'block';
        if (i === index + 1) {
            temoignage.style.transform = 'scale(1)';
            temoignage.style.border = '1px solid #007BFF';
            temoignage.style.boxShadow = 'none';
        } else {
            temoignage.style.transform = 'scale(0.8)';
            temoignage.style.border = '1px solid transparent';
            temoignage.style.boxShadow = '1px 1px 1px 15px #DDDDDD';
        }
    } else {
        temoignage.style.display = 'none';
    }
});
}

function nextTemoignage() {
currentIndex = (currentIndex + 1) % (temoignages.length - 2);
showTemoignages(currentIndex);
}

function prevTemoignage() {
currentIndex = (currentIndex - 1 + (temoignages.length - 2)) % (temoignages.length - 2);
showTemoignages(currentIndex);
}


startAutomaticScroll();

function startAutomaticScroll() {
intervalId = setInterval(() => {
    nextTemoignage();
}, 5000); 
}


showTemoignages(currentIndex);


setTimeout(() => {
startAutomaticScroll();
}, 2000);

document.getElementById('next').addEventListener('click', () => {
nextTemoignage();
clearInterval(intervalId); 
});

document.getElementById('prev').addEventListener('click', () => {
prevTemoignage();
clearInterval(intervalId); 
});