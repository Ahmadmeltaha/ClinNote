# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **User Accounts & Profiles** — foundational identity layer for the chat application (2026-09-17)
  - Email/password registration (`POST /api/auth/signup`) with Zod validation and scrypt password hashing
  - Email/password login (`POST /api/auth/login`) returning a JWT bearer token
  - Session termination (`POST /api/auth/logout`) protected by auth middleware
  - Profile retrieval (`GET /api/users/me`) returning display name, email, avatar color, and timestamps
  - Profile update (`PATCH /api/users/me`) allowing display name modification (1–50 characters)
  - PostgreSQL `users` table via Drizzle ORM with auto-initialization and migration script
  - Deterministic avatar generation: initials extracted from display name, background color chosen from an 8-color accessible palette via a hash of the user ID
  - Next.js pages for login (`/login`), sign up (`/signup`), and profile settings (`/profile`)
  - Zustand auth store with `persist` middleware for client-side session management
  - Centralized API client with automatic 401 interception and redirect to login
  - Hono auth middleware verifying JWT bearer tokens on protected routes
