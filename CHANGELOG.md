# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Car Detail Page** — Public-facing detail view for a single vehicle, accessible at `/cars/:id`. Renders a responsive photo gallery (swipeable on mobile with pagination dots, thumbnail strip on desktop), key specifications, pricing, and description. Sold vehicles display a "Sold" badge overlay and disable action buttons while remaining accessible via direct URL. Includes a `GET /api/cars/:id` endpoint that returns full car details and a list of similar cars (matched by make or body type). Single-photo cars hide all gallery navigation controls. The "Similar Cars" section is hidden when no matches are found. 404 state displays a "Car not found." message with a link back to the catalog. (2026-09-03)