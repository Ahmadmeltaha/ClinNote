# Chat

A real-time chat application built with Next.js, Hono, and PostgreSQL. The initial feature provides the foundational identity layer — email/password authentication and user profile management — that downstream features (messaging, presence, etc.) depend on.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | TypeScript |
| Frontend | Next.js (React) |
| Backend | Hono |
| Database | PostgreSQL |
| ORM | Drizzle ORM |
| Validation | Zod |
| Auth | JWT (HS256 via `hono/jwt`) |
| Password Hashing | Node `crypto.scrypt` |
| State Management | Zustand (with `persist` middleware) |

## Getting Started

### Prerequisites

- Node.js ≥ 18
- PostgreSQL ≥ 15

### Environment Variables

Create a `.env` file (or set the variables in your shell):

```bash
DATABASE_URL=postgres://user:password@localhost:5432/chat
JWT_SECRET=your-secret-key
NEXT_PUBLIC_API_URL=http://localhost:3001
```

### Installation

```bash
npm install
```

### Database Setup

The users table is created automatically on first run via `initializeDatabase()`. You can also apply the migration manually:

```bash
psql $DATABASE_URL -f src/db/migrations/0001_create_users.sql
```

### Running the App

```bash
# Start the Next.js frontend (default port 3000)
npm run dev

# Start the Hono API server (default port 3001)
npm run dev:api
```

## Features

### User Accounts & Profiles

This feature provides email/password registration and login, JWT-based session management, and a profile settings view where users can view and update their display name. Each user is assigned a deterministic, initials-based avatar with a color derived from their user ID, ensuring a consistent visual identity across sessions and devices.

**Capabilities:**
- Sign up with email, password (≥ 8 characters), and display name (1–50 characters)
- Log in / log out with JWT bearer tokens
- View profile (display name, email, avatar)
- Update display name
- Automatic redirect to login when the session expires (401 handling)

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/auth/signup` | No | Register a new account; returns user + JWT |
| `POST` | `/api/auth/login` | No | Authenticate; returns user + JWT |
| `POST` | `/api/auth/logout` | Yes | Terminate the current session |
| `GET` | `/api/users/me` | Yes | Get the authenticated user's profile |
| `PATCH` | `/api/users/me` | Yes | Update display name |

### Authentication

Protected endpoints require a `Bearer <token>` header. Tokens are issued by the signup and login endpoints and must be stored client-side (the app uses `localStorage`).

### Error Responses

| Status | Meaning |
|--------|---------|
| `401` | Unauthorized — missing/invalid token or bad credentials |
| `409` | Conflict — email already registered |
| `422` | Validation error — malformed request body |
| `404` | Not found — user does not exist |

## Project Structure

```
src/
├── app/                  # Next.js pages (login, signup, profile)
├── components/           # Shared UI components (Avatar)
├── db/                   # Drizzle schema, client, and migrations
├── lib/                  # Auth utilities, avatar utilities, API client, Zustand store
├── middleware/            # Hono auth middleware
├── routes/               # Hono route handlers (auth, users)
└── views/                # Page re-exports
```

## License

Private — internal project.
