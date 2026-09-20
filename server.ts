import express, { Request, Response, NextFunction } from "express";
import path from "path";
import fs from "fs";
import { createServer as createViteServer } from "vite";
import { apiRouter, MEDICAL_DISCLAIMER } from "./src/server/api";

const PORT = 3000;

// Rate limiting state: IP -> timestamps[]
const rateLimitMap = new Map<string, number[]>();
const RATE_LIMIT_WINDOW_MS = 60 * 1000;
const MAX_REQUESTS_PER_WINDOW = 120;

function rateLimitMiddleware(req: Request, res: Response, next: NextFunction) {
  // Only rate limit API calls
  if (!req.path.startsWith("/v1")) {
    return next();
  }

  const clientIp =
    (req.headers["x-forwarded-for"] as string)?.split(",")[0].trim() ||
    req.socket.remoteAddress ||
    "unknown-client";

  const now = Date.now();
  const windowStart = now - RATE_LIMIT_WINDOW_MS;

  let timestamps = rateLimitMap.get(clientIp) || [];
  timestamps = timestamps.filter((t) => t > windowStart);

  if (timestamps.length >= MAX_REQUESTS_PER_WINDOW) {
    const oldest = timestamps[0];
    const resetTimeSec = Math.ceil((oldest + RATE_LIMIT_WINDOW_MS - now) / 1000);
    res.setHeader("X-RateLimit-Limit", MAX_REQUESTS_PER_WINDOW.toString());
    res.setHeader("X-RateLimit-Remaining", "0");
    res.setHeader("X-RateLimit-Reset", resetTimeSec.toString());
    res.setHeader("Retry-After", resetTimeSec.toString());

    return res.status(429).json({
      error: {
        code: "RATE_LIMIT_EXCEEDED",
        message: `Rate limit of ${MAX_REQUESTS_PER_WINDOW} requests per minute exceeded. Please slow down.`,
        retry_after_seconds: resetTimeSec,
      },
    });
  }

  timestamps.push(now);
  rateLimitMap.set(clientIp, timestamps);

  const remaining = MAX_REQUESTS_PER_WINDOW - timestamps.length;
  res.setHeader("X-RateLimit-Limit", MAX_REQUESTS_PER_WINDOW.toString());
  res.setHeader("X-RateLimit-Remaining", remaining.toString());
  res.setHeader("X-RateLimit-Reset", "60");

  next();
}

async function startServer() {
  const app = express();

  // JSON parser
  app.use(express.json());

  // Global Metadata and CORS middleware
  app.use((req: Request, res: Response, next: NextFunction) => {
    const start = Date.now();
    const requestId = `req_${Math.random().toString(36).substring(2, 11)}_${Date.now()}`;

    res.setHeader("X-Request-ID", requestId);
    res.setHeader("X-CancerInfo-API-Version", "1.0.0");
    res.setHeader("X-Medical-Disclaimer", "Informational only; not medical advice");
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With, X-RapidAPI-Key, X-RapidAPI-Host");

    const originalSend = res.send;
    res.send = function (body) {
      try {
        if (!res.headersSent) {
          const duration = Date.now() - start;
          res.setHeader("X-Response-Time-MS", duration.toString());
        }
      } catch {
        // ignore if headers already sent
      }
      return originalSend.call(this, body);
    };

    if (req.method === "OPTIONS") {
      return res.sendStatus(204);
    }

    next();
  });

  // Standard health check routes for platform and dev server monitors
  app.get("/api/health", (req: Request, res: Response) => {
    res.json({ status: "ok" });
  });
  app.get("/health", (req: Request, res: Response) => {
    res.json({ status: "ok" });
  });

  // Apply rate limiter to API
  app.use(rateLimitMiddleware);

  // Serve OpenAPI specification
  app.get("/openapi.json", (req: Request, res: Response) => {
    const openApiPath = path.join(process.cwd(), "rapidapi/rapidapi-openapi.json");
    if (fs.existsSync(openApiPath)) {
      const spec = fs.readFileSync(openApiPath, "utf-8");
      res.setHeader("Content-Type", "application/json");
      res.send(spec);
    } else {
      res.status(404).json({ error: "OpenAPI specification not found" });
    }
  });

  // Serve Interactive Swagger UI
  app.get("/docs", (req: Request, res: Response) => {
    res.setHeader("Content-Type", "text/html");
    res.send(`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CancerInfo API - Interactive Swagger Docs</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
  <style>
    body { margin: 0; background: #0f172a; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .topbar { display: none !important; }
    .swagger-ui { background: #ffffff; padding: 24px 32px; border-radius: 12px; margin: 24px auto; max-width: 1280px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); }
    .header-banner { background: #0284c7; color: white; padding: 18px 24px; text-align: center; font-size: 15px; font-weight: 500; }
    .header-banner a { color: #ffffff; text-decoration: underline; font-weight: 600; }
  </style>
</head>
<body>
  <div class="header-banner">
    CancerInfo API &bull; Open-Access Verified Clinical Oncology Data &bull; <a href="/">Return to Developer Portal</a>
  </div>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.onload = () => {
      window.ui = SwaggerUIBundle({
        url: '/openapi.json',
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [SwaggerUIBundle.presets.apis],
        layout: "BaseLayout"
      });
    };
  </script>
</body>
</html>`);
  });

  // Serve ReDoc UI
  app.get("/redoc", (req: Request, res: Response) => {
    res.setHeader("Content-Type", "text/html");
    res.send(`<!DOCTYPE html>
<html>
  <head>
    <title>CancerInfo API - ReDoc Documentation</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <style>body { margin: 0; padding: 0; }</style>
  </head>
  <body>
    <redoc spec-url='/openapi.json'></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"> </script>
  </body>
</html>`);
  });

  // Mount API Router under /v1
  app.use("/v1", apiRouter);

  // Vite middleware for dev or static for prod
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req: Request, res: Response) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  const server = app.listen(PORT, "0.0.0.0", () => {
    console.log(`[CancerInfo API] Server running at http://0.0.0.0:${PORT}`);
    console.log(`[CancerInfo API] Live API Endpoints: http://0.0.0.0:${PORT}/v1/health`);
    console.log(`[CancerInfo API] Interactive Swagger Docs: http://0.0.0.0:${PORT}/docs`);
    console.log(`[CancerInfo API] ReDoc Specification: http://0.0.0.0:${PORT}/redoc`);
  });

  process.on("SIGTERM", () => {
    server.close(() => process.exit(0));
  });
  process.on("SIGINT", () => {
    server.close(() => process.exit(0));
  });
}

process.on("uncaughtException", (err) => {
  console.error("[CancerInfo API] Uncaught exception:", err);
});

process.on("unhandledRejection", (reason) => {
  console.error("[CancerInfo API] Unhandled rejection:", reason);
});

startServer().catch((err) => {
  console.error("Failed to start server:", err);
});
