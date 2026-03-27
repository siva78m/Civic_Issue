# AI-Empowered Urban Governance System — Complete Project Explanation

## 1. Project Overview

The **AI-Empowered Urban Governance System** is a full-stack smart civic complaint platform. Citizens can report urban problems — potholes, garbage, water leakage, damaged infrastructure — using images, text, and GPS location. The system uses AI (Google Gemini) to automatically classify, prioritize, and route these complaints to the right authorities.

### Core Problem It Solves

Traditional complaint portals are manual, slow, and subjective. This system:

- Removes human bias from complaint classification
- Ensures high-priority/dangerous issues are surfaced first
- Prevents duplicate reports from flooding the system
- Gives citizens full transparency on complaint resolution

---

## 2. Tech Stack

| Layer                  | Technology              | Purpose                                                                    |
| ---------------------- | ----------------------- | -------------------------------------------------------------------------- |
| **Frontend Framework** | Next.js 15 (App Router) | Full-stack React framework with server components, routing, and API routes |
| **Language**           | TypeScript              | Type-safe code across frontend and backend                                 |
| **Styling**            | Tailwind CSS            | Utility-first CSS framework for rapid UI development                       |
| **UI Components**      | ShadcnUI + Radix UI     | Accessible, headless component primitives                                  |
| **Authentication**     | Clerk                   | Managed auth with social logins, JWT, and webhook sync                     |
| **ORM**                | Prisma                  | Type-safe database client with schema-first development                    |
| **Database**           | NeonDB (PostgreSQL)     | Serverless, scalable PostgreSQL with connection pooling                    |
| **AI Model**           | Google Gemini 1.5 Flash | Free-tier multimodal AI for text + image analysis                          |
| **AI SDK (JS)**        | @google/generative-ai   | Official Google Gemini SDK for Node.js                                     |
| **AI Service**         | Python + FastAPI        | Dedicated microservice for advanced AI processing                          |
| **Forms**              | React Hook Form + Zod   | Performant forms with schema-based validation                              |
| **Charts**             | Recharts                | Analytics charts in admin dashboard                                        |
| **Webhook Validation** | Svix                    | Verifies Clerk webhook signatures                                          |

## 3. How Each Feature Works (Step by Step)

### Feature 1: User Registration & Authentication (Clerk)

**Step 1** — User visits `/sign-up` and registers with email/password or social login.

**Step 2** — Clerk handles auth internally and issues a JWT session token.

**Step 3** — Clerk fires a `user.created` webhook to `/api/webhooks/clerk`.

**Step 4** — The webhook handler verifies the Svix signature (to prevent spoofing), extracts user data, and creates a matching record in NeonDB via Prisma.

**Step 5** — If the email matches `ADMIN_EMAIL` environment variable, the user is assigned `ADMIN` role.

**Step 6** — `src/middleware.ts` uses `clerkMiddleware()` to protect all non-public routes. Every page request checks for a valid Clerk session.

---

### Feature 2: Multimodal Complaint Reporting

**Step 1** — Citizen navigates to `/citizen/report`.

**Step 2** — The `ReportForm` component renders a 2-step form:

- Step 1: Title, description, image upload, location picker
- Step 2: Review summary before submission

**Step 3 — Image Upload** (`ImageUpload` component):

- User drags/drops or selects images
- File is sent to `/api/upload` via FormData POST
- Server validates type (JPEG/PNG/WebP) and size (max 5MB)
- Saved to `public/uploads/` with a unique timestamped filename
- URL returned to frontend and stored in state
- First image is also converted to base64 for AI analysis

**Step 4 — Location Detection** (`LocationPicker` component):

- User clicks "Detect My Location" → browser's `navigator.geolocation.getCurrentPosition()`
- Coordinates sent to OpenStreetMap Nominatim API for free reverse geocoding
- Human-readable address displayed for confirmation
- Or user can enter lat/lng coordinates manually

**Step 5** — User submits the form → POST to `/api/issues`

---

### Feature 3: AI-Based Issue Classification (Gemini)

**Step 1** — `/api/issues` POST handler receives the issue data.

**Step 2** — Fetches all nearby active issues from DB (within ~0.5° lat/lng bounding box) for duplicate checking.

**Step 3** — Calls `analyzeIssue()` from `src/lib/gemini.ts`.

**Step 4** — Gemini prompt is constructed:

```
"You are an AI assistant for an Urban Governance System. Analyze this civic issue:
Title: [title]
Description: [description]
Location: Lat X, Long Y
[Image attached if provided]

Return JSON: { category, severity, urgency, confidence, analysisText, tags }"
```

**Step 5** — If an image was uploaded, it is included as `inlineData` (base64 + mimeType) in the Gemini API call — this is the **multimodal** part.

**Step 6** — Gemini returns a JSON response with:

- `category` — one of 10 civic categories
- `severity` — LOW/MEDIUM/HIGH/CRITICAL
- `urgency` — LOW/MEDIUM/HIGH/IMMEDIATE
- `confidence` — 0.0 to 1.0
- `analysisText` — professional 2–3 sentence assessment
- `tags` — 2–5 descriptive tags

**Step 7** — Response is validated and sanitized (invalid values fall back to defaults).

---

### Feature 4: Duplicate Detection (Geospatial)

**Step 1** — After AI classifies the category, the `analyzeIssue()` function iterates over `existingIssues` fetched from DB.

**Step 2** — For each existing issue of the same category with non-terminal status (not RESOLVED/REJECTED):

- Computes Haversine distance between GPS coordinates
- Formula: `d = 2R × arctan2(√a, √(1-a))` where `a = sin²(Δφ/2) + cos φ₁ × cos φ₂ × sin²(Δλ/2)`

**Step 3** — If distance ≤ 500 meters AND same category → duplicate detected.

**Step 4** — The new issue is created with:

- `status: "DUPLICATE"`
- `duplicateOfId: [original issue ID]`
- `aiAnalysis.isDuplicate: true`

**Step 5** — Citizen sees a notice: "Duplicate report found — merged with existing issue."

---

### Feature 5: MCIA Priority Scoring

**Step 1** — After AI analysis, `calculatePriorityScore()` runs with:

- severity, urgency (from AI)
- upvoteCount = 0 (new issue)
- createdAt = now

**Step 2** — MCIA formula executes (see Section 7 for full breakdown).

**Step 3** — Priority score stored in `issue.priorityScore` and `aiAnalysis.priorityScore`.

**Step 4** — When a citizen upvotes an issue, the priority score is **recalculated** with the new upvote count, ensuring community engagement updates rankings in real time.

---

### Feature 6: Real-Time Status Tracking

**Step 1** — Issue is created with `status: "PENDING"`.

**Step 2** — Admin reviews and changes to `UNDER_REVIEW`.

**Step 3** — Admin assigns to a department and changes to `IN_PROGRESS`, adds optional admin notes.

**Step 4** — Work is completed → Admin marks `RESOLVED`. `resolvedAt` timestamp is saved.

**Step 5** — Citizen views `/citizen/issues/[id]` and sees current status, admin notes, and resolution time.

**Step 6** — Status badges are color-coded: Gray (Pending) → Blue (Under Review) → Yellow (In Progress) → Green (Resolved) → Red (Rejected) → Purple (Duplicate).

---

### Feature 7: Administrative Dashboard

**Step 1** — Admin logs in → `(admin)/layout.tsx` checks `user.role === "ADMIN"`. Non-admins are redirected to citizen dashboard.

**Step 2** — `/admin` dashboard shows:

- 6 stat cards: Total, Pending, In Progress, Resolved, Critical, Citizens
- Resolution rate progress bar
- Priority Queue (top 5 issues ranked by MCIA score)
- Category breakdown bar chart
- Recent issues table with all fields

**Step 3** — `/admin/issues` shows paginated table of ALL issues with filtering by status, category, severity, and sorting by priority/upvotes/date.

**Step 4** — `/admin/issues/[id]` shows full issue details + `AdminStatusUpdate` sidebar component to:

- Change status via dropdown
- Add admin notes
- Assign to department/officer
- Mark resolved in one click

---

### Feature 8: Community Upvoting

**Step 1** — Citizen clicks upvote on any issue card or issue detail page.

**Step 2** — POST to `/api/issues/[id]/upvote`:

- Checks `Upvote` table for `issueId + userId` unique pair
- If not exists → creates upvote, increments `upvoteCount`
- If exists → deletes upvote (toggle), decrements `upvoteCount`

**Step 3** — New `priorityScore` recalculated with updated `upvoteCount`:

- More upvotes = higher community score = higher priority
- Community weight is 20% of total MCIA score

**Step 4** — Updated `upvoteCount` and `priorityScore` saved back to DB.

**Step 5** — Frontend updates UI immediately (optimistic-style with useState).

## 7. MCIA Algorithm Deep Dive

**MCIA (Multimodal Civic Intelligence Algorithm)** is the custom priority scoring system.

### Formula

```
PriorityScore = (Severity × 0.40) + (Urgency × 0.30) + (Community × 0.20) + (Recency × 0.10)
```

### Component Breakdown

| Component     | Weight | Calculation                                      |
| ------------- | ------ | ------------------------------------------------ |
| **Severity**  | 40%    | LOW=2.5, MEDIUM=5, HIGH=7.5, CRITICAL=10         |
| **Urgency**   | 30%    | LOW=2.5, MEDIUM=5, HIGH=7.5, IMMEDIATE=10        |
| **Community** | 20%    | `min(upvoteCount × 0.5, 10)` — capped at 10      |
| **Recency**   | 10%    | `10 × e^(-age_in_days / 30)` — exponential decay |

### Why These Weights?

- **Severity (40%)** — The most important factor. A critical pothole or open manhole must rank highest regardless of age or popularity.
- **Urgency (30%)** — Time sensitivity matters. An immediate threat needs faster response than a low-urgency issue.
- **Community (20%)** — Democratic weighting. Popular issues affect more citizens and deserve higher priority.
- **Recency (10%)** — Prevents old issues from being permanently buried. Fresh reports get a small recency boost that decays over 30 days.

### Example Calculation

```
Issue: Large pothole causing accidents (CRITICAL severity, HIGH urgency)
Upvotes: 15, Age: 2 days

Severity Score  = 10.0
Urgency Score   = 7.5
Community Score = min(15 × 0.5, 10) = min(7.5, 10) = 7.5
Recency Score   = 10 × e^(-2/30) = 10 × 0.935 = 9.35

Priority = (10.0 × 0.40) + (7.5 × 0.30) + (7.5 × 0.20) + (9.35 × 0.10)
         = 4.00 + 2.25 + 1.50 + 0.935
         = 8.69  ← Critical Priority (≥8)
```

### Priority Labels

| Score Range | Label             |
| ----------- | ----------------- |
| 8.0 – 10.0  | Critical Priority |
| 6.0 – 7.9   | High Priority     |
| 4.0 – 5.9   | Medium Priority   |
| 0.0 – 3.9   | Low Priority      |

---

## 8. Duplicate Detection — Geospatial Analysis

### Haversine Formula

The Haversine formula calculates the great-circle distance between two points on Earth given their GPS coordinates:

```
a = sin²(Δφ/2) + cos(φ₁) × cos(φ₂) × sin²(Δλ/2)
c = 2 × arctan2(√a, √(1−a))
d = R × c
```

Where:

- φ = latitude in radians
- λ = longitude in radians
- R = 6,371,000 meters (Earth's radius)
- d = distance in meters

### Duplicate Detection Logic

```
For each new issue submission:
  1. Query DB for all issues within ±0.005° bounding box (roughly 500m)
  2. Filter: same category + non-terminal status (not RESOLVED/REJECTED)
  3. For each match:
     - Calculate Haversine distance
     - If distance ≤ 500m → DUPLICATE DETECTED
  4. Mark new issue as DUPLICATE, link to original via duplicateOfId
```

### Why 500 Meters?

500m is a practical urban block radius. Issues beyond 500m are likely genuinely different locations even if same category.

---

## 9. User Flows

### Citizen Flow

```
Landing Page → Sign Up → Citizen Dashboard
     ↓
Report Issue (report page)
  → Fill title + description
  → Upload photo(s)
  → Detect/enter GPS location
  → Submit
     ↓
AI Analysis (Gemini)
  → Category classified
  → Severity/urgency assessed
  → Duplicate check performed
  → MCIA score calculated
     ↓
Issue Created in DB
  → Citizen sees AI analysis results
  → Issue appears in /citizen/issues
     ↓
Browse Issues → Upvote others' issues
     ↓
Track own issues → View status updates + admin notes
```

### Admin Flow

```
Login (admin email) → Admin Dashboard
  → See stats, priority queue, category breakdown
     ↓
/admin/issues → View all issues (sortable by priority)
  → Filter by status/category/severity
     ↓
Click issue → Full detail view
  → See AI analysis (category, confidence, tags)
  → See MCIA breakdown
  → Update status via sidebar
  → Add admin notes / assign department
  → Mark resolved
     ↓
/admin/analytics → View charts
  → Monthly trends line chart
  → Category bar chart
  → Status pie chart
  → Severity distribution
```

## Folder Structure Explained

```
urban-governance/
│
├── prisma/
│   └── schema.prisma          ← Database schema (4 models, 4 enums)
│
├── python/                    ← FastAPI AI Microservice
│   ├── main.py                ← FastAPI app, API routes
│   ├── ai_analyzer.py         ← Gemini API integration, image processing
│   ├── duplicate_detector.py  ← Haversine geospatial duplicate detection
│   ├── priority_calculator.py ← MCIA algorithm implementation
│   ├── models.py              ← Pydantic request/response models
│   ├── requirements.txt       ← Python dependencies
│   └── Dockerfile             ← Containerization
│
├── src/
│   ├── app/                   ← Next.js App Router
│   │   ├── (auth)/            ← Public auth routes (no layout)
│   │   │   ├── sign-in/       ← Clerk sign-in page
│   │   │   └── sign-up/       ← Clerk sign-up page
│   │   │
│   │   ├── (citizen)/         ← Citizen-only routes (protected)
│   │   │   ├── layout.tsx     ← Citizen layout with navbar
│   │   │   ├── dashboard/     ← Citizen dashboard
│   │   │   ├── report/        ← Report new issue page
│   │   │   └── issues/        ← Browse all issues + detail page
│   │   │
│   │   ├── (admin)/           ← Admin-only routes (role protected)
│   │   │   ├── layout.tsx     ← Admin layout (redirects citizens)
│   │   │   └── admin/
│   │   │       ├── page.tsx   ← Admin dashboard
│   │   │       ├── issues/    ← Issue management table + detail
│   │   │       └── analytics/ ← Charts and trends
│   │   │
│   │   ├── api/               ← Next.js API Routes
│   │   │   ├── issues/        ← CRUD + upvote + status routes
│   │   │   ├── upload/        ← Image upload handler
│   │   │   └── webhooks/clerk ← Clerk user sync webhook
│   │   │
│   │   ├── layout.tsx         ← Root layout (ClerkProvider + Toaster)
│   │   ├── page.tsx           ← Public landing page
│   │   └── globals.css        ← Global styles + CSS variables
│   │
│   ├── components/
│   │   ├── ui/                ← ShadcnUI components (button, card, etc.)
│   │   ├── admin/             ← Admin-specific components
│   │   │   ├── AdminStatusUpdate.tsx   ← Status management sidebar
│   │   │   ├── AdminIssueFilters.tsx   ← Filter bar for issues table
│   │   │   └── AnalyticsCharts.tsx     ← Recharts analytics
│   │   ├── forms/             ← Form components
│   │   │   ├── ReportForm.tsx          ← Multi-step issue report form
│   │   │   ├── ImageUpload.tsx         ← Drag-drop image uploader
│   │   │   └── LocationPicker.tsx      ← GPS + manual location input
│   │   ├── issues/            ← Issue display components
│   │   │   ├── IssueCard.tsx           ← Issue card with upvote
│   │   │   └── UpvoteButton.tsx        ← Standalone upvote button
│   │   ├── dashboard/
│   │   │   └── StatsCard.tsx           ← Stat display card
│   │   └── layout/
│   │       └── Navbar.tsx              ← Responsive navigation bar
│   │
│   ├── lib/
│   │   ├── prisma.ts          ← Prisma client singleton
│   │   ├── gemini.ts          ← Gemini AI analysis function
│   │   └── utils.ts           ← MCIA algorithm, Haversine, formatters
│   │
│   ├── types/
│   │   └── index.ts           ← All TypeScript interfaces and enums
│   │
│   └── middleware.ts           ← Clerk auth middleware (route protection)
│
├── public/uploads/             ← Uploaded issue images (gitignored)
├── .env.example                ← Environment variable template
├── package.json                ← Node.js dependencies
├── prisma/schema.prisma        ← DB schema
├── tailwind.config.ts          ← Tailwind + dark mode config
├── next.config.ts              ← Next.js config
├── tsconfig.json               ← TypeScript config
```
