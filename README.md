# OrchState

Gas cylinder ordering and delivery management system built with a Flutter mobile frontend and TypeScript/Hono backend.

## Tech Stack

- **Frontend**: Flutter (Dart)
- **Backend**: TypeScript with Hono framework
- **Database**: PostgreSQL with Drizzle ORM
- **Validation**: Zod schemas

## Features

### Cylinder Catalog

The Cylinder Catalog provides a digital shelf for browsing available gas cylinders. Users can view a scrollable list of products displaying physical specifications, gas type, pricing, and real-time stock status. Out-of-stock items remain visible but are disabled to maintain catalog transparency, serving as the primary entry point for the ordering flow.

## Setup

### Backend

```bash
cd backend
npm install
npm run dev
```

The backend runs on `http://localhost:3000` by default.

### Database

Ensure PostgreSQL is running and configure the database connection in your environment variables. The schema will be automatically migrated on first run.

### Frontend

```bash
flutter pub get
flutter run
```

Configure the API base URL via the `API_BASE_URL` environment variable (defaults to `http://localhost:3000`).

## API Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/catalog` | Fetch complete cylinder list with stock status | Required |

### GET /api/v1/catalog

Returns an array of all available cylinders with their specifications and current stock status.

**Response Schema:**

```json
[
  {
    "id": "uuid",
    "name": "string",
    "sizeKg": "number",
    "gasType": "butane | propane",
    "price": "number",
    "imageUrl": "string",
    "inStock": "boolean"
  }
]
```

**Error Responses:**

- `500 Internal Server Error`: `{ "error": "Failed to fetch catalog" }`