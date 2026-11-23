const express = require('express');
const path = require('path');
const app = express();
const port = 3000;

// Serve static files (CSS, images, etc.) from the current directory
app.use(express.static(__dirname));

// Define a route for GET requests to the root URL
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Start the server
app.listen(port, () => {
  console.log(`BlackJack is listening at http://localhost:${port}`);
});