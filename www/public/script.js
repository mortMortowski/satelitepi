let latestContainer = document.getElementsByClassName("latest-img")[0];
let imagesContainer = document.getElementsByClassName("images-list")[0];

document.addEventListener("DOMContentLoaded", () => {
	fetch("/api/images")
	.then(response => response.json())
	.then(images => {
		latestContainer.src = "img/" + images[0];
		let imagesCount = images.length;
		for(let i=1; i < imagesCount; i++){
			let imageDiv = document.createElement("div");
			imageDiv.classList.add("image");
			let imageImg = document.createElement("img");
			imageImg.src = "img/" + images[i];
			imageImg.alt = "satellite image";
			imageDiv.appendChild(imageImg);
			imagesContainer.appendChild(imageDiv);
		}
	})
	.catch(error => console.error("Error fetching images:",error));
});