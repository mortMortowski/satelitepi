// IMPORTS

const express = require("express");
const path = require("path");
const bodyParser = require("body-parser");
const fs = require("fs");

// CONFIG

const app = express();
const imgFolder = path.join(__dirname, "public", "img");

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));

app.use(express.static(path.join(__dirname, "public")));

app.use("/img", express.static(imgFolder));

// ROUTES

app.get("/", (req, res) => {
	res.sendFile(path.join(__dirname, "views", "index.html"));
});

app.get("/about", (req, res) => {
	res.sendFile(path.join(__dirname, "views", "about.html"));
});

app.get("/api/images", async (req, res) => {
	const files = await fs.promises.readdir(imgFolder);
	const sortedFiles = files.map(fileName => ({
		name: fileName,
		time: fs.statSync(`${imgFolder}/${fileName}`).mtime.getTime(),
	})).sort((a, b) => b.time - a.time).map(file => file.name);
	res.json(sortedFiles);
});

// SERVER

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
	console.log(`Server is running on http://localhost:${PORT}`);
});
