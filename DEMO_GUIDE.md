# Baladiya — AI-Powered Smart Municipality Platform
## Complete Project Documentation & Demo Guide

---

## 1. WHAT IS BALADIYA?

Baladiya (Arabic for "Municipality") is an AI-powered smart municipality platform built on Odoo 19. It replaces paper-based government services with a unified digital system where:

- **Citizens** submit service requests (building permits, road complaints, trade licenses, etc.) through a self-service web portal
- **Government officers** process requests via a Kanban workflow board with SLA tracking
- **AI makes every decision** — triage, document validation, response drafting, predictions — and **humans approve**

**The pitch:** *"We built an AI that runs a city. Humans just approve."*

**Context:** Built for Sharjah, UAE. Uses Sharjah district names, AED currency, Emirates ID.

---

## 2. SYSTEM ARCHITECTURE

```
+--------------------------------------------------+
|                  ODOO 19 SERVER                   |
|                                                   |
|  +--------------------------------------------+  |
|  |          BALADIYA MODULE                    |  |
|  |                                             |  |
|  |  Models:                                    |  |
|  |    - baladiya.department (6 departments)    |  |
|  |    - baladiya.service.category (6 services) |  |
|  |    - baladiya.service.request (core model)  |  |
|  |    - baladiya.ai.service (AI brain)         |  |
|  |    - res.partner (citizen extension)        |  |
|  |                                             |  |
|  |  Backend: Kanban + List + Form + Dashboard  |  |
|  |  Portal:  Catalog + Apply + Track + Chat    |  |
|  |  AI:      6 Brains via OpenAI API           |  |
|  +--------------------------------------------+  |
|                       |                           |
|              OpenAI API (gpt-4o-mini)             |
+--------------------------------------------------+
```

**Tech Stack:**
- Odoo 19.0 (Python 3.13, PostgreSQL)
- OpenAI API (gpt-4o-mini) via direct HTTP requests
- OWL framework (Odoo frontend)
- Vanilla JS chatbot widget
- Bootstrap 5 portal styling

---

## 3. THE 6 MUNICIPAL DEPARTMENTS

| # | Department | Code | Handles |
|---|-----------|------|---------|
| 1 | Building & Construction | BLD | Building permits, renovations, structural approvals |
| 2 | Roads & Infrastructure | RDS | Road repairs, potholes, street lighting |
| 3 | Environment & Public Health | ENV | Waste complaints, pest control, sanitation |
| 4 | Urban Planning | URB | Signage permits, zoning |
| 5 | Community Services | COM | Facility bookings, parks, event spaces |
| 6 | Commercial Licensing | LIC | Trade licenses, business permits |

## 4. THE 6 SERVICE CATEGORIES

| Service | Dept | Fee (AED) | Est. Days | Inspection? |
|---------|------|-----------|-----------|-------------|
| Building Permit | BLD | 500 | 14 | Yes |
| Road Maintenance Request | RDS | Free | 7 | No |
| Waste & Environment Complaint | ENV | Free | 3 | Yes |
| Trade License | LIC | 1,000 | 10 | No |
| Facility Booking | COM | 200 | 5 | No |
| Signage Permit | URB | 300 | 7 | Yes |

Each category has a list of required documents that AI validates against.

---

## 5. THE WORKFLOW — 5 Clear States

```
New  →  Under Review  →  In Progress  →  Completed
                                ↘ Rejected
```

Each state looks and feels **completely different** on the form — different AI panels appear, different buttons are available, and different information is shown.

| State | Who Acts | What Happens | AI Feature Visible |
|-------|----------|-------------|-------------------|
| **New** | Citizen | Request created via portal or backend. Raw request with no processing yet. | Chatbot helped citizen choose service |
| **Under Review** | Officer | Officer opens the request. **3 AI panels appear automatically**: AI Triage (priority/department suggestion), AI Insights (summary, sentiment, patterns), and AI Document Validation (completeness check). Officer clicks "Accept AI & Start Processing" or overrides. | **Brain 1 + 6 + 2** all visible at once |
| **In Progress** | Officer | Officer works the request. When ready, clicks "Complete" or "Reject" — both open the **AI Draft wizard** which writes a professional citizen message. Officer edits and sends. | **Brain 3** built into the workflow |
| **Completed** | System | Request done. Citizen can rate and leave feedback. Dashboard updates with new data. | **Brain 4** predictions update |
| **Rejected** | Manager | Rejected with AI-drafted reason. Red alert shown with rejection reason. Can reset to New. | **Brain 3** auto-drafted the rejection |

**SLA Tracking** kicks in after submission:
- **On Track** (green): More than 2 days before deadline
- **At Risk** (yellow): Within 2 days of deadline
- **Overdue** (red): Past deadline

---

## 6. THE 6 AI BRAINS

### BRAIN 1: AI Auto-Triage & Routing
**Trigger:** Automatically fires when a citizen submits any request (no button needed).

**What AI does:**
- Reads the description and assigns priority (Normal / High / Urgent)
- Suggests the correct department (even if citizen picked wrong category)
- Suggests the best officer to assign
- Provides a confidence score (0-100%) and reasoning

**Visible on form:** Blue panel at the top of the form in "Under Review" state. Officer sees suggestions with "Accept AI & Start Processing" button.

**Demo example:** Citizen submits "sewage flooding the street near a park where children play" under Road Maintenance → AI sets priority to Urgent, re-routes to Environment & Public Health department, 95% confidence.

---

### BRAIN 2: AI Document Validator
**Trigger:** Automatically fires on submission (if documents are attached).

**What AI does:**
- Compares uploaded filenames against the category's required documents list
- Identifies what each uploaded file likely is
- Flags missing documents with a completeness score (0-100%)

**Visible on form:** Grey panel below the documents section showing completeness %, identified docs, missing docs.

---

### BRAIN 3: AI Response Drafter
**Trigger:** Built into the workflow — opens automatically when officer clicks "Complete" or "Reject".

**What AI does:**
- Generates a professional email with subject line and body
- Uses real data: citizen name, request number, tracking code, department
- Pre-set to "completion" or "rejection" based on which button was clicked

**Visible on form:** Wizard dialog where officer reviews AI-drafted message, can edit, then clicks "Send & Apply" — message sends AND state changes in one action.

**Demo example:** Officer clicks "Complete" → AI writes: "Dear Admin, We are pleased to inform you that your Building Permit request (SR-2026-00004) has been approved..."

---

### BRAIN 4: AI Predictive Dashboard
**Trigger:** Click "AI Dashboard" in the Baladiya menu → "Refresh AI Predictions".

**What AI does:**
- Predicts which requests will miss their SLA deadline
- Identifies bottleneck and busiest departments
- Generates 5 actionable management recommendations
- Assesses overall system health (Good / Warning / Critical)

**Visible as:** Full-page dashboard with stat cards, risk tables, and recommendations.

---

### BRAIN 5: AI Citizen Chatbot
**Trigger:** Always visible as a blue chat bubble on bottom-right of ALL portal pages.

**What AI does:**
- Lists all services with real fees and processing times
- Tracks requests by code — looks up live status from database
- Guides citizens through the application process
- Responds in English or Arabic

**Strictly read-only** — cannot create, modify, or delete any data.

---

### BRAIN 6: AI Request Summarizer & Insights
**Trigger:** Automatically fires on submission (alongside triage).

**What AI does:**
- One-line executive summary
- Sentiment analysis (Frustrated / Neutral / Urgent)
- Pattern detection across the district
- Recommended next action for the officer

**Visible on form:** Yellow panel below the description showing all insights inline.

---

## 7. CITIZEN PORTAL PAGES

| URL | Auth | Description |
|-----|------|-------------|
| `/my/services` | Login required | Service catalog — 6 cards with icons, fees, estimated days, "Apply Now" buttons |
| `/my/services/apply/<id>` | Login required | Application form — citizen info, description, district, address, file upload |
| `/my/requests` | Login required | My requests list — tracking codes, status badges, dates |
| `/my/requests/<id>` | Login required | Request detail — 4-step progress stepper, all info, feedback form |
| `/track` | **Public** (no login) | Tracking page — enter tracking code |
| `/track/result?code=XXX` | **Public** | Tracking result — progress stepper, department, SLA |

The chatbot widget appears on ALL portal pages.

---

## 8. BACKEND VIEWS

| View | Description |
|------|-------------|
| **Kanban** | 5 columns (New, Under Review, In Progress, Completed, Rejected). SLA progressbar, AI summary on cards, sentiment badges |
| **List** | Color-coded rows (red=overdue, yellow=at risk). AI sentiment column |
| **Form** | Single scrollable page — no tabs. AI panels show/hide based on state. Workflow buttons change per state |
| **Dashboard** | Graph views — bar (by department), pie (by status), line (trend) |
| **AI Dashboard** | Predictive analytics — stat cards, SLA risks, bottleneck analysis, AI recommendations |

---

## 9. SECURITY MODEL

| Group | Access | Who |
|-------|--------|-----|
| **Citizen** | Create + read own requests only | Portal users |
| **Service Officer** | Read + write all requests, process workflows | Municipal staff |
| **Department Manager** | All officer permissions + reject | Department heads |
| **Municipality Admin** | Full access to everything | IT admin, Mayor |

---

## 10. DEMO SCRIPT (Step-by-Step, ~8 minutes)

### Opening (30 seconds)
> "Baladiya is an AI-powered municipality platform. Citizens submit requests through a portal. AI does the thinking — triage, validation, drafting, predictions. Humans just approve. Let me show you the complete flow."

### Act 1: Citizen Portal (2 minutes)

1. Open **http://localhost:8069/my/services**
2. Show the **service catalog** — 6 cards with icons, fees, estimated days
3. Click the **chatbot bubble** → ask "What services do you offer?" → AI responds with real data from the database
4. Ask the chatbot to track a code → it returns live status
5. Click **"Apply Now"** on Building Permit
6. Fill the form: description about a villa renovation, select Al Khan district
7. Click **Submit** → show confirmation page with tracking code
8. Open **http://localhost:8069/track** → enter tracking code → show 4-step progress stepper

### Act 2: AI Does the Thinking (2 minutes)

9. Switch to **backend** (http://localhost:8069/odoo/baladiya)
10. Open the request from Kanban → it's in "Under Review"
11. Point out **3 AI panels visible at once**:
    - **Blue panel (Triage)**: "AI suggests High priority, Building & Construction department, 95% confidence"
    - **Yellow panel (Insights)**: "Summary: Villa renovation with structural changes. Sentiment: Urgent. Pattern: No similar requests in Al Khan."
    - **Grey panel (Documents)**: "Completeness: 80%. Missing: NOC from Civil Defense"
12. Say: *"Three AI brains analyzed this request the moment it was submitted. The officer sees everything at a glance."*
13. Click **"Accept AI & Start Processing"** → state changes to In Progress, priority and department updated

### Act 3: AI Drafts the Response (2 minutes)

14. Click **"Complete (AI Draft)"**
15. The AI Draft wizard opens with type pre-set to "completion"
16. Click **"Generate AI Draft"** → AI writes professional email with citizen name, request number, tracking code
17. Show the editable message → officer can tweak any line
18. Click **"Send & Apply"** → message posts to chatter AND request completes in one click
19. Say: *"AI wrote the email. The officer just approved it. One click."*

### Act 4: AI Predictive Dashboard (1 minute)

20. Click **"AI Dashboard"** in menu → **"Refresh AI Predictions"**
21. Show: stat cards, bottleneck analysis, busiest department, 5 AI recommendations
22. Say: *"This isn't reporting what happened — it's predicting what WILL happen. AI identifies bottlenecks and recommends resource reallocation."*

### Act 5: Citizen Sees Result (30 seconds)

23. Go to portal tracking page with the tracking code
24. Show all 4 steps checked off → "Completed" badge
25. Say: *"The citizen tracked their request in real-time. No phone calls, no office visits."*

### Closing (30 seconds)
> "Every single workflow step had AI making a decision and a human approving it. 6 AI brains. 5 clear workflow stages. One platform. AI runs the city."

---

## 11. KEY DEMO TALKING POINTS

- **"Human in the loop everywhere"** — AI never auto-applies anything. Officers see suggestions and choose to accept or override.
- **"AI is visible, not hidden"** — Three AI panels appear on the form the moment a request is submitted. No tabs to click, no buttons to find.
- **"Each step feels different"** — New (raw request), Under Review (AI panels visible), In Progress (AI drafts responses), Completed (citizen feedback).
- **"Real data, not mockups"** — The chatbot queries the actual database. The dashboard analyzes real requests. The triage reads the real description.
- **"Built on Odoo"** — Full Odoo module with ORM, security, portal, chatter, email templates. Enterprise-grade.

---

## 12. TECHNICAL SETUP

### Prerequisites
- Odoo 19.0 running on localhost:8069
- PostgreSQL database: `odoo_erp`
- OpenAI API key

### Setting the API Key
1. Log in as admin
2. Go to **Settings** → **Technical** → **System Parameters**
3. Find `baladiya.openai_api_key` → set your OpenAI API key
4. Optionally change `baladiya.openai_model` (default: `gpt-4o-mini`)

### Installing/Upgrading
```bash
# First install
python odoo-bin -c odoo.conf -d odoo_erp -i baladiya --stop-after-init

# Upgrade after changes
python odoo-bin -c odoo.conf -d odoo_erp -u baladiya --stop-after-init

# Start server
python odoo-bin -c odoo.conf
```

### Module Structure
```
addons/baladiya/
├── models/          (5 Python models + AI service)
├── views/           (8 XML view files)
├── controllers/     (portal + chatbot endpoints)
├── wizard/          (reject wizard + AI draft wizard)
├── security/        (groups + access rules + record rules)
├── data/            (seed data + email templates + AI config)
└── static/          (CSS + JS chatbot + module icon)
```

---

## 13. URLS QUICK REFERENCE

| URL | What It Shows |
|-----|--------------|
| `localhost:8069/odoo/baladiya` | Backend — Service Requests Kanban |
| `localhost:8069/my/services` | Portal — Service Catalog |
| `localhost:8069/my/services/apply/1` | Portal — Apply for Building Permit |
| `localhost:8069/my/requests` | Portal — My Requests List |
| `localhost:8069/track` | Public — Track by Code |
| `localhost:8069/baladiya/ai-dashboard` | AI Predictive Dashboard |

---

*Built for the Public & Institutional ERP Hackathon — Sharjah, UAE*
*Powered by Odoo 19 + OpenAI*
