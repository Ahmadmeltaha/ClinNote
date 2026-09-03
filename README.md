# Car Dealership

A web application for browsing and exploring a dealership's vehicle inventory. Customers can filter and sort available cars, view detailed listings with photo galleries and specifications, and take actions such as booking test drives or sending inquiries.

## Tech Stack

- **Language:** TypeScript
- **Frontend:** React (with React Router, Tailwind CSS)
- **Backend:** Hono
- **Database:** PostgreSQL (managed via Drizzle ORM)
- **Validation:** Zod

## Getting Started

```bash
# Install dependencies
npm install

# Run database migrations
npx drizzle-kit migrate

# Start the development server
npm run dev
```

## Features

- **Car Catalog:** Browse, filter, and sort the vehicle inventory with pagination support.
- **Car Detail Page:** View a comprehensive detail page for any single vehicle. The page renders a responsive photo gallery (swipeable on mobile, thumbnail-based on desktop), key specifications (make, model, year, mileage, fuel, transmission, color), pricing, and a full description. Sold vehicles are clearly marked with a "Sold" badge overlay and disabled action buttons, while still remaining accessible via direct URL to preserve shared links. A "Similar Cars" row at the bottom surfaces related vehicles based on make or body type.

## API Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/cars` | List cars with filtering, sorting, and pagination. |
| `POST` | `/api/cars` | Create a new car listing. |
| `GET` | `/api/cars/:id` | Fetch full car details including photos, specs, and similar cars. |

### `GET /api/cars/:id`

Fetches the complete detail for a single vehicle, including its photo gallery, specifications, pricing, description, availability status, and a list of similar cars.

**Path Parameters:**

| Name | Type | Description |
| :--- | :--- | :--- |
| `id` | `string` (UUID) | The unique identifier of the car. |

**Success Response (`200`):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "make": "Toyota",
  "model": "Camry",
  "year": 2023,
  "mileage": 15000,
  "fuel": "Gasoline",
  "transmission": "Automatic",
  "color": "Silver",
  "bodyType": "sedan",
  "price": 28500,
  "description": "Well-maintained sedan with low mileage.",
  "photos": [
    { "url": "https://example.com/photo1.jpg", "altText": "Front view" }
  ],
  "status": "available",
  "similarCars": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "make": "Honda",
      "model": "Accord",
      "year": 2022,
      "price": 26000,
      "mainPhotoUrl": "https://example.com/similar1.jpg"
    }
  ]
}
```

**Error Responses:**

| Status | Description |
| :--- | :--- |
| `400` | Invalid car ID (malformed UUID). |
| `404` | Car not found. |

## Project Structure

```
src/
├── api/
│   ├── routes/         # Hono route handlers
│   ├── services/       # Business logic and database queries
│   └── validators/     # Zod schemas for request/response validation
├── db/
│   └── schema.ts       # Drizzle ORM table definitions
└── frontend/
    ├── components/     # Reusable React components
    ├── hooks/          # Custom React hooks
    └── pages/          # Route-level page components
```