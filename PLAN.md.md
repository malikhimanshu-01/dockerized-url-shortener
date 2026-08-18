# Build Plan: Dockerized URL Shortener + Analytics

*A multi-container project designed to demonstrate service separation, container networking, data persistence, and orchestration — the goal is depth of engineering reasoning, not a novel product idea.*

## 1. Why this project, and the choices made on your behalf

You asked for whatever domain and stack is "best," so here's the reasoning, written the way you'd defend it in an interview.

**Domain: URL shortener with a real analytics dashboard.** A plain URL shortener is the single most common "learning project" out there, which is exactly why the infrastructure has to carry the weight. To make it feel less like a tutorial clone and more like a deliberate build, this plan adds two things most tutorial versions skip: a click-analytics dashboard (referrer, device, time-of-day breakdowns) and rate limiting on link creation. Both give Redis a genuine job instead of a decorative one, and both are still explainable in ten seconds: "it's a bit.ly clone with built-in click analytics."

**Backend: Python + FastAPI.** Between Node and Python, FastAPI edges out Express here for three reasons: it's async-native, which pairs naturally with non-blocking calls to Redis and Postgres; it auto-generates OpenAPI/Swagger docs, which is a small but real README/demo differentiator ("open `/docs`, no Postman needed"); and Pydantic models force you to be explicit about request/response shapes, which reads as more deliberate than loosely-typed Express handlers. If you're materially more comfortable in Node, swap it in — the container architecture below doesn't change, only the backend Dockerfile's build steps do.

**Everything else follows the brief you pasted almost exactly**, because that advice is sound: React (or plain static JS) frontend behind Nginx, FastAPI backend, Postgres for persistence, Redis for cache + rate limiting, Nginx as the single reverse-proxy entry point.

## 2. My overall take on the idea

This is a strong pick precisely because it's boring at the product level and interesting at the infrastructure level — that's the right ratio for a resume project. The risk is entirely in execution: five services and two networks is enough rope to hang yourself with if healthchecks, env config, and volumes aren't handled deliberately. The checklist in section 8 is ordered specifically to avoid the most common failure mode, which is building all five services in parallel and then spending a weekend debugging compose networking at the end. Build and prove one vertical slice first, then add the rest.

The other risk is stopping at "it runs." The differentiator interviewers actually probe for is *why* — why two networks instead of one, why Redis caches this and not that, what broke during the build. Section 9 turns that into a concrete README section so it doesn't get lost.

## 3. Architecture

```
                        ┌─────────────────────────┐
                        │        Client            │
                        └───────────┬───────────────┘
                                    │ :80
                        ┌───────────▼───────────────┐
                        │   Nginx (reverse proxy)    │
                        │   routes / -> frontend      │
                        │   routes /api -> backend    │
                        └─────┬───────────────┬───────┘
                              │               │
                    frontend-net         frontend-net
                              │               │
                ┌─────────────▼───┐   ┌────────▼─────────┐
                │  React (static)  │   │  FastAPI backend  │
                │  served by nginx │   │  :8000             │
                └──────────────────┘   └───┬──────────┬────┘
                                            │          │
                                     backend-net   backend-net
                                            │          │
                                  ┌─────────▼──┐  ┌────▼──────┐
                                  │  Postgres   │  │   Redis    │
                                  │  :5432      │  │   :6379    │
                                  │  (volume)   │  │            │
                                  └─────────────┘  └────────────┘
```

Two Docker networks, not one:

- `frontend-net`: nginx ↔ frontend, nginx ↔ backend. The frontend container never joins `backend-net` — it has no route to Postgres or Redis at all, not even a blocked one at the app layer. This is the concrete proof of "understanding networking" the original brief calls out.
- `backend-net`: backend ↔ Postgres, backend ↔ Redis. Nothing else is attached to this network.

Only Nginx publishes a port to the host. Every other service is reachable only by service name, inside its network.

## 4. Repo structure

```
url-shortener/
├── docker-compose.yml
├── docker-compose.override.yml      # dev-only: hot reload, exposed DB port, bind mounts
├── docker-compose.prod.yml          # prod overrides: no exposed DB/Redis ports, resource limits
├── .env.example
├── README.md
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf                   # if frontend serves itself; otherwise proxy/nginx.conf below
│   └── src/...
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/ (links.py, analytics.py, health.py)
│   │   ├── models.py                # SQLAlchemy models
│   │   ├── schemas.py               # Pydantic
│   │   ├── db.py
│   │   ├── cache.py                 # Redis client + helpers
│   │   └── config.py                # settings from env vars
│   └── seed.py
├── proxy/
│   ├── Dockerfile
│   └── nginx.conf                   # routes /api -> backend, / -> frontend
└── db/
    └── init.sql                     # optional: extensions, initial schema
```

## 5. Data model (Postgres)

Two tables are enough to make the analytics feature real without turning this into a schema-design exercise:

- `links`: `id`, `short_code` (unique, indexed), `long_url`, `created_at`, `expires_at` (nullable), `owner_id` (nullable if you skip auth).
- `clicks`: `id`, `link_id` (FK), `clicked_at`, `referrer`, `user_agent`, `country` (optional, derive from IP later as a stretch goal).

This is enough to build a "top links" and "clicks over time" view without needing a data warehouse.

## 6. What Redis actually does here (not decoration)

1. **Redirect cache**: on `GET /{short_code}`, check Redis first for `short_code -> long_url`. On a miss, read Postgres, write-through to Redis with a TTL (e.g. 24h), then redirect. This is the textbook reason real URL shorteners use a cache — reads massively outnumber writes, and a redirect should never wait on a full DB round trip if it can help it.
2. **Rate limiting**: a simple fixed-window or token-bucket counter in Redis (`INCR` + `EXPIRE` on a key like `ratelimit:{ip}:{minute}`) on the link-creation endpoint. This gives you a second, unrelated use of the same dependency, which heads off the "I added Redis because the list said so" criticism.
3. Click events themselves stay a straight write to Postgres for now — don't over-engineer with a queue unless you want that as an explicit stretch goal (see section 10).

## 7. Docker specifics that separate this from a tutorial clone

- **Multi-stage builds** for both frontend and backend: build stage compiles/installs, final stage copies only the runtime artifact onto a minimal base (`python:3.12-slim`, `node:20-alpine` for the build stage, `nginx:alpine` to serve).
- **Non-root user** in every custom image (`USER app` after creating the user in the Dockerfile) — a genuinely common thing tutorials skip.
- **Healthchecks** in compose for Postgres and Redis, and `depends_on: condition: service_healthy` on the backend, so the backend never crash-loops waiting on a DB that isn't accepting connections yet. Add a `/health` endpoint on the backend that checks both Postgres and Redis connectivity, and give the backend its own healthcheck so nginx doesn't route to a backend that's up but not ready.
- **Named volume** for Postgres data (`pgdata:/var/lib/postgresql/data`) so `docker compose down` doesn't wipe your data — only `docker compose down -v` should.
- **Env-based config**: `.env` for secrets/config, `.env.example` committed with placeholder values, nothing hardcoded in the compose file or Dockerfiles. `docker-compose.override.yml` for dev conveniences (bind-mounted source for hot reload, exposed Postgres port for local psql access); a separate prod compose file that removes those exposures and adds resource limits.
- **Seed script**: a `seed.py` (or a `make seed` target) that inserts a handful of sample links and synthetic click events, run once via `docker compose exec backend python seed.py` or as an init container step, so a fresh clone shows a populated dashboard immediately instead of an empty state.

## 8. Build order (do this in phases, not all five services at once)

1. **Backend + Postgres only.** Get FastAPI talking to Postgres via SQLAlchemy, with Alembic (or a plain init.sql) for schema. Prove CRUD on `links` with curl before anything else exists.
2. **Add Redis** to that same slice. Wire the redirect cache and the rate limiter. Verify cache hits with logging before moving on.
3. **Add the frontend**, talking directly to the backend's exposed port (no nginx yet). A create-link form and a basic analytics table/chart is enough.
4. **Introduce Nginx** as the reverse proxy in front of both, and only then split into the two networks — this is the point where you actually remove the DB/Redis ports from the host and confirm the frontend container genuinely cannot reach Postgres.
5. **Healthchecks, volumes, env split, seed script** — harden what already works rather than debugging orchestration and business logic at the same time.
6. **README + architecture diagram + design-decisions writeup.**
7. **Basic tests + CI** (see section 10).

## 9. What actually gets read: the README

- One command works: `docker compose up --build` (or `up -d` after first build) brings up all five services correctly ordered, healthchecks passing.
- An architecture diagram — even the ASCII one in section 3 is fine, or render it as a simple Mermaid diagram in the README.
- A **design decisions** section, written as prose, covering: why Postgres over Mongo/SQLite here (relational data with a link → clicks relationship, and it's the more resume-relevant choice for showing you understand real persistence); why Redis is used specifically for redirect caching and rate limiting, not just "added"; why two networks instead of one; and one concrete thing that broke during the build and how you diagnosed it (this is the single most interview-relevant sentence in the whole README — keep a running note of real problems as you hit them, don't reconstruct one after the fact).
- Env var reference table (`.env.example` documented).

## 10. Stretch goals, roughly in order of effort-to-payoff

1. GitHub Actions CI: spin up the compose stack (or just backend + Postgres + Redis) in the runner, run pytest against it. This directly extends the same setup into a "CI/CD project" story if you want to pair it with another resume item.
2. QR code generation per short link (cheap to add, nice demo visual).
3. Auth (JWT) so links belong to a user — only worth it if you want to demonstrate auth patterns; it adds real complexity, so treat it as optional rather than default scope.
4. Swap the direct-write click logging for a small Redis-backed queue (list or Streams) consumed by a worker, if you want to show async processing — but be honest in the README that this is deliberately over-engineered relative to the traffic the app actually sees, which is itself a mature thing to say.

## 11. Common pitfall (repeating this because it matters most)

The tell of a copied `docker-compose.yml` is a repo where every service is on one flat default network, there's no healthcheck, and the README doesn't mention a single tradeoff. Building in the phased order above naturally avoids that, because each phase forces you to actually observe something (a cache hit, a healthcheck failing, a network boundary working) rather than assembling all the pieces from a reference and hoping.
