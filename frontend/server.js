const next = require("next");
const https = require("https");
const { parse } = require("url");
const fs = require("fs");

// Disable SSL certificate verification (only in development)
process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

const hostname = "localhost";
const port = 3000;
const dev = true;

const app = next({ dev, hostname, port });

const sslOptions = {
  key: fs.readFileSync("./certs/localhost-key.pem"),
  cert: fs.readFileSync("./certs/localhost.pem"),
};

const handle = app.getRequestHandler();

app.prepare().then(() => {
  const server = https.createServer(sslOptions, (req, res) => {
    // custom api middleware
    if (req.url.startsWith("/api")) {
      return handle(req, res);
    } else {
      // Handle Next.js routes
      return handle(req, res);
    }
  });
  server.listen(port, (err) => {
    if (err) throw err;
    console.log("> Ready on https://localhost:" + port);
  });
});
