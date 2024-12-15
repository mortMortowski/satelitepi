const img1 = document.getElementsByClassName("satellite-img")[0];
const img2 = document.getElementsByClassName("satellite-img")[1];
const img3 = document.getElementsByClassName("satellite-img")[2];
const photoBackground = document.getElementsByClassName("enlarged-photo")[0];
const bigImg = document.getElementsByClassName("enlarged-img")[0];

img1.addEventListener("click", () => {
	enlargePhoto(img1);
});

img2.addEventListener("click", () => {
	enlargePhoto(img2);
});

img3.addEventListener("click", () => {
	enlargePhoto(img3);
});

photoBackground.addEventListener("click", () => {
	hideBackground();
});

function enlargePhoto(photo){
	photoBackground.style.display = "block";
	bigImg.src = photo.src;
}

function hideBackground(){
	photoBackground.style.display = "none";
}
