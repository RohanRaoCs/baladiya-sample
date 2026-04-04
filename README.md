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

## 5. THE 10-STATE WORKFLOW

```
Draft → Submitted → Under Review → In Progress → Inspection* → Pending Approval → Approved → Completed
                                                                                        ↘ Rejected
                                                                          ↘ Cancelled
```
*Inspection is optional — only for categories that require it.

| State | Who Acts | What Happens |
|-------|----------|-------------|
| **Draft** | Citizen | Request created, not yet submitted |
| **Submitted** | System | Submission date set, tracking code generated, email sent, **AI Triage auto-fires** |
| **Under Review** | Officer | Officer reviews request completeness |
| **In Progress** | Officer | Active work being done |
| **Inspection** | Inspector | On-site visit (building permits, signage, waste) |
| **Pending Approval** | Officer → Manager | Escalated for manager sign-off |
| **Approved** | Manager | Manager approved, approval email sent |
| **Completed** | Officer | Service delivered, completion email sent, citizen can rate |
| **Rejected** | Manager | Rejected with reason via wizard, citizen notified |
| **Cancelled** | Anyone | Withdrawn before completion |

**SLA Tracking** kicks in after submission:
- **On Track** (green): More than 2 days before deadline
- **At Risk** (yellow): Within 2 days of deadline
- **Overdue** (red): Past deadline

---

## 6. THE 6 AI BRAINS

### BRAIN 1: AI Auto-Triage & Routing
**Trigger:** Automatically fires when a citizen submits any request.

**What AI does:**
- Reads the description and assigns priority (Normal / High / Urgent)
- Suggests the correct department (even if citizen picked wrong category)
- Suggests the best officer to assign
- Detects duplicate requests
- Provides a confidence score (0-100%) and reasoning

**Human in the loop:** Officer sees a blue panel on the form with AI recommendations. Two buttons: "Accept AI Suggestions" or "Dismiss".

**Demo example:** Citizen submits "sewage flooding the street near a park where children play" under Road Maintenance → AI sets priority to Urgent, re-routes to Environment & Public Health department, 95% confidence.

---

### BRAIN 2: AI Document Validator
**Trigger:** Officer clicks "Validate Documents with AI" button in the Documents tab.

**What AI does:**
- Compares uploaded filenames against the category's required documents list
- Identifies what each uploaded file likely is
- Flags missing documents
- Calculates a completeness score (0-100%)
- Provides an assessment summary

**Human in the loop:** Officer sees completeness percentage, identified docs, missing docs list, and assessment. Can request missing docs from citizen.

**Demo example:** Citizen applies for Building Permit, uploads 4 files → AI says "Completeness: 80%. Missing: NOC from Civil Defense. Assessment: 4 of 5 required documents provided."

---

### BRAIN 3: AI Response Drafter
**Trigger:** Officer clicks the yellow "AI Draft Response" button in the form header.

**What AI does:**
- Opens a wizard dialog
- Officer selects message type (Review Started, Work Started, Inspection Scheduled, Approved, Rejected, Completed, General Update)
- AI generates a professional, formal email with subject line and body
- Uses real data: citizen name, request number, tracking code, department, service type

**Human in the loop:** Officer reads the AI-drafted message, can edit any part, then clicks "Send to Citizen". Message posts to chatter and sends email. **AI never auto-sends.**

**Demo example:** Officer selects "Request Approved" → AI writes: "Dear Admin, We are pleased to inform you that your Building Permit request (SR-2026-00004) for the Al Khan district has been approved by the Building & Construction department manager. Your tracking code is BLD-2026-PL6T..."

---

### BRAIN 4: AI Predictive Dashboard
**Trigger:** Click "AI Dashboard" in the Baladiya menu, then "Refresh AI Predictions".

**What AI does:**
- Analyzes ALL active requests, deadlines, and department workload data
- Predicts which requests will miss their SLA deadline
- Identifies the bottleneck department (where requests pile up)
- Identifies the busiest department
- Generates 5 actionable management recommendations
- Assesses overall system health (Good / Warning / Critical)

**Human in the loop:** Manager/Mayor sees predictions and recommendations on a dashboard with stat cards. Clicks "Apply Recommendation" or dismisses.

**Demo example:** Dashboard shows "Bottleneck: Roads & Infrastructure — 1 pending request with zero processing days, indicating potential delay. Suggestion: Allocate additional resources. Recommendation: Monitor the pending request closely."

---

### BRAIN 5: AI Citizen Chatbot
**Trigger:** Always visible as a blue chat bubble on the bottom-right of ALL portal pages.

**What AI does:**
- Answers questions about available services, fees, required documents, processing times
- Tracks requests by code — if citizen types a tracking code (e.g., "BLD-2026-PL6T"), AI looks it up in the real database and returns live status, deadline, department
- Guides citizens through the application process
- Responds in English or Arabic (matches citizen's language)

**Human in the loop:** Chatbot is strictly **read-only** — it cannot create, modify, or delete any data. Complex cases are directed to visit the municipality office.

**Demo example:** Citizen asks "What services do you offer?" → AI lists all 6 services with fees. Citizen asks "Track RDS-2026-IIP2" → AI responds "Your Road Maintenance Request was submitted on 2026-04-04 and is currently on track. Expected completion: 2026-04-11."

---

### BRAIN 6: AI Request Summarizer & Insights
**Trigger:** Officer clicks "Generate AI Insights" button in the AI Insights tab.

**What AI does:**
- Generates a one-line executive summary of the request
- Analyzes citizen sentiment (Frustrated / Neutral / Urgent)
- Detects patterns ("This is the 5th road complaint from Al Nahda this month")
- Recommends a specific next action for the officer

**Human in the loop:** Summary and insights appear on the form. Officer reads AI's analysis, then decides what to do.

**Demo example:** Officer opens a sewage complaint → AI panel shows: Summary: "Urgent sewage flooding near Al Majaz Waterfront Park". Sentiment: Urgent. Patterns: "No similar requests in this district — new escalating issue." Recommendation: "Dispatch specialized sanitation team immediately."

---

## 7. CITIZEN PORTAL PAGES

| URL | Auth | Description |
|-----|------|-------------|
| `/my/services` | Login required | Service catalog — 6 cards with icons, fees, estimated days, "Apply Now" buttons |
| `/my/services/apply/<id>` | Login required | Application form — auto-filled citizen info, description, district, address, file upload |
| `/my/requests` | Login required | My requests list — table with tracking codes, status badges, dates |
| `/my/requests/<id>` | Login required | Request detail — visual progress stepper, all info, feedback form when completed |
| `/track` | **Public** (no login) | Tracking page — enter tracking code to check status |
| `/track/result?code=XXX` | **Public** | Tracking result — progress stepper, department, SLA, dates |

The chatbot widget appears on ALL portal pages.

---

## 8. BACKEND VIEWS

| View | Description |
|------|-------------|
| **Kanban** | Main officer view — requests grouped by state columns, SLA progressbar, priority stars, citizen avatar, department badge |
| **List** | Table view — color-coded rows (red=overdue, yellow=at risk), all key columns |
| **Form** | Full request detail — statusbar, workflow buttons, AI triage panel, notebook tabs (Details, Documents + AI Validator, Internal Notes, AI Insights, Feedback, Rejection) |
| **Search** | Filters: My Assigned, Overdue, At Risk, by state. Group by: Department, Service Type, District, Priority |
| **Dashboard** | Graph views — bar (by department), pie (by status), line (trend over time), pivot table |
| **AI Dashboard** | Predictive analytics page — stat cards, SLA risks, bottleneck analysis, AI recommendations |

---

## 9. SECURITY MODEL

| Group | Access | Who |
|-------|--------|-----|
| **Citizen** | Create + read own requests only | Portal users |
| **Service Officer** | Read + write all requests, process workflows | Municipal staff |
| **Department Manager** | All officer permissions + approve/reject | Department heads |
| **Municipality Admin** | Full access to everything | IT admin, Mayor |

Citizens can only see their own requests (record rule enforced). Officers see all.

---

## 10. DEMO SCRIPT (Step-by-Step)

### Opening (30 seconds)
> "Baladiya is an AI-powered municipality platform. Citizens submit service requests through a portal. AI does the thinking — triage, validation, drafting, predictions. Humans just approve. Let me show you."

### Act 1: Citizen Submits (2 minutes)

1. Open **http://localhost:8069/my/services**
2. Show the **service catalog** — 6 cards with icons, fees, estimated days
3. Point out the **chatbot bubble** in the bottom-right — click it, ask "What services do you offer?" — show AI responding with real data
4. Click **"Apply Now"** on Building Permit
5. Fill the form: description about a villa renovation, select Al Khan district
6. Click **Submit** — show the confirmation page with the tracking code
7. Open **http://localhost:8069/track** — enter the tracking code — show the public tracking page with progress stepper

### Act 2: AI Triage (2 minutes)

8. Switch to the **backend** (http://localhost:8069/odoo/baladiya)
9. Open the submitted request from the Kanban board
10. Show the **AI Triage panel** — "Look, the AI already analyzed this. It suggests High priority for the Building & Construction department with 95% confidence. Here's the reasoning..."
11. Click **"Accept AI Suggestions"** — priority and department update instantly
12. Say: *"The citizen didn't even choose the right department — AI corrected it automatically."*

### Act 3: AI Insights (1 minute)

13. Click the **"AI Insights"** tab
14. Click **"Generate AI Insights"**
15. Show the result: summary, sentiment badge (Urgent), detected patterns, recommended action
16. Say: *"Before the officer even reads the full request, AI has already summarized it, detected the urgency, and recommended the next step."*

### Act 4: Officer Processes (1 minute)

17. Click **Start Review** → **Start Processing** → **Request Approval** → **Approve**
18. Show the statusbar progressing through each stage
19. Say: *"Every transition is tracked in the chatter with timestamps."*

### Act 5: AI Drafts the Response (2 minutes)

20. Click the yellow **"AI Draft Response"** button
21. Select "Request Approved" as message type
22. Click **"Generate AI Draft"**
23. Show the AI-written professional email — subject line, formal body with request details, tracking code, department
24. Say: *"The AI wrote this. The officer can edit anything before sending. AI never sends automatically."*
25. Click **"Send to Citizen"**
26. Click **Mark Complete**

### Act 6: AI Dashboard (1 minute)

27. Click **"AI Dashboard"** in the menu
28. Click **"Refresh AI Predictions"**
29. Show: stat cards (active, overdue, completed, system health), bottleneck analysis, busiest department, 5 AI recommendations
30. Say: *"This isn't just reporting what happened — it's predicting what WILL happen. The AI identifies bottlenecks and recommends resource reallocation."*

### Act 7: Chatbot Tracking (30 seconds)

31. Go back to the portal, open the chatbot
32. Type the tracking code from the completed request
33. Show the AI responding with live status from the database
34. Say: *"Citizens can track their requests 24/7 through the chatbot without logging in or calling anyone."*

### Closing (30 seconds)
> "Every single workflow in this system has AI making a decision and a human approving it. That's 6 AI brains — triage, document validation, response drafting, predictive dashboard, citizen chatbot, and request summarizer. One module. One platform. AI runs the city."

---

## 11. KEY DEMO TALKING POINTS

- **"Human in the loop everywhere"** — AI never auto-applies anything. Officers see suggestions with confidence scores and choose to accept or override.
- **"Real data, not mockups"** — The chatbot queries the actual database. The dashboard analyzes real requests. The triage reads the real description.
- **"6 AI decision points"** — Every interaction in the system touches at least one AI brain.
- **"Built on Odoo"** — Not a standalone app. It's a full Odoo module with ORM, security, portal, chatter, email templates. Enterprise-grade.
- **"Sharjah context"** — District names, AED currency, Emirates ID, UAE government communication standards.

---

## 12. TECHNICAL SETUP

### Prerequisites
- Odoo 19.0 running on localhost:8069
- PostgreSQL database: `odoo_erp`
- OpenAI API key configured

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

### Module Location
```
addons/baladiya/
├── __init__.py, __manifest__.py
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
