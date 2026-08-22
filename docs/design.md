You are a senior product designer + frontend engineer specializing in premium
enterprise SaaS applications.

I am building an offline-first audit operating system called "FinAuditPro".

I have already iterated on the UI several times, but the current interface still
feels unfinished, overly sparse, and visually similar to a generic admin
dashboard.

I want you to perform a COMPLETE UI/UX refinement of the existing application.

IMPORTANT:

- Do NOT rebuild the application from scratch.
- Do NOT change the business logic.
- Do NOT remove existing functionality.
- Do NOT break routing, state management, database/storage, forms, or existing
  workflows.
- Preserve all existing features and data.
- Work directly with the existing frontend architecture and components.
- First inspect the entire project structure and understand the existing design
  system.
- Then systematically improve the UI across ALL screens, not just the dashboard.

# ================================================== PRODUCT CONTEXT

FinAuditPro is a professional audit operating system used by auditors/accounting
professionals.

The product contains:

WORKSPACE

- Dashboard
- Audit Firms
- Clients
- Engagements

FINANCIAL

- Documents
- Financial Statements
- GST Reconciliation
- Statutory Compliance

ANALYSIS

- Audit Matrix
- AI Copilot

AUDIT WORKFLOW

- Working Papers
- Reports

SYSTEM

- File Archival
- Roll-Forward
- Settings

The application should feel like a serious professional audit platform, not a
generic CRUD/admin panel.

Design references should feel closer to:

- Linear
- Stripe Dashboard
- Vercel
- Notion
- modern enterprise accounting/audit software
- premium financial SaaS products

But DO NOT blindly copy any of these products.

# ================================================== CURRENT UI PROBLEMS

The current UI has several issues visible across the application:

1. EXCESSIVE EMPTY SPACE

Pages such as:

- Audit Firms
- Clients
- Engagements

contain a huge empty area underneath the table header.

This makes the application look unfinished.

Fix this.

When there are no records:

- show a proper empty-state component
- explain what the user should do
- provide a primary CTA
- optionally show a useful illustration/icon
- visually center the empty state inside the content area
- do not leave an enormous blank white rectangle

Example:

"No audit firms yet"

"Create your first audit firm to start managing clients and engagements."

[ + Create Audit Firm ]

Do this consistently across all empty-data pages.

# ================================================== 2. TABLES FEEL EMPTY AND GENERIC

Current tables are basically:

## HEADER

## nothing

huge whitespace

Improve the table UX.

Tables should support:

- meaningful empty states
- hover states
- row interaction
- subtle separators
- proper column alignment
- consistent typography
- status badges
- risk badges
- action menus
- responsive behavior
- useful pagination when data grows

When a table is empty, DO NOT render a giant blank table.

Instead render a structured empty-state inside the table container.

When there is data, make rows feel interactive.

Example:

RELIANCE FY 2025–26 Statutory Audit Planning Low Risk Open →

Use:

- compact status badges
- consistent visual hierarchy
- subtle hover background
- clear primary action

================================================== 3. CONTENT WIDTH AND DENSITY

The application currently uses too much horizontal and vertical whitespace.

Do not make everything cramped either.

Create a professional enterprise density system.

Recommended:

Desktop:

- sidebar: approximately 220–240px
- main content: max-width around 1400–1500px
- comfortable horizontal padding
- consistent 16–24px spacing system
- cards with controlled padding
- tables that use available width efficiently

The UI should feel information-dense enough for professional users.

Auditors will spend hours inside this application.

Optimize for:

- scanning
- comparison
- data entry
- reviewing findings
- navigating between audit sections

================================================== 4. SIDEBAR

The sidebar is currently functional but visually basic.

Improve it significantly while keeping it simple.

Requirements:

- fixed/sticky sidebar
- clear active navigation state
- section grouping
- subtle section labels
- consistent icons
- better vertical rhythm
- hover states
- active indicator
- user/account area at bottom
- sidebar should feel like part of the product identity

Keep the sidebar width stable.

Do NOT turn it into a flashy navigation.

The design should communicate:

"Professional audit workstation."

Potential structure:

FinAuditPro ──────────────── WORKSPACE

Dashboard Audit Firms Clients Engagements

FINANCIAL

Documents Financial Statements GST Reconciliation Statutory Compliance

ANALYSIS

Audit Matrix AI Copilot

AUDIT WORKFLOW

Working Papers Reports

SYSTEM

File Archival Roll-Forward Settings

The active page should have:

- subtle tinted background
- clear text weight
- small accent indicator
- icon emphasis

================================================== 5. TOP BAR

The top bar currently has too much unused space.

Redesign it.

It should contain:

LEFT: global search

CENTER/RIGHT: current engagement selector

RIGHT: notifications if functionality exists user/account controls if
functionality exists primary "+ New Audit" action

The top bar should feel compact.

Global search should look like a real command/search interface.

Example:

Search clients, findings, reports... ⌘ K

The engagement selector should clearly communicate the current context.

Example:

ENGAGEMENT RELIANCE · FY 2025–26 · Statutory Audit

Do not waste huge horizontal areas on empty controls.

================================================== 6. DASHBOARD / AUDIT OVERVIEW

The Dashboard should become the strongest page in the application.

Current structure:

Audit workflow Needs attention KPI cards Audit progress Risk exposure Recent
engagements

This is conceptually correct.

Improve the hierarchy.

Top section:

AUDIT OVERVIEW

RELIANCE FY 2025–26 Statutory Audit Planning 0% complete

Then:

[Audit Workflow Progress]

Client ✓ FY ✓ Engagement ● Materiality ○ Documentation ○ Completion ○

The current step should be visually obvious.

Next action should be the dominant CTA.

Example:

NEXT ACTION Complete engagement parameters

Configure engagement details, statutory parameters, materiality and audit scope.

[ Continue Setup → ]

Make this card feel actionable instead of decorative.

================================================== 7. KPI CARDS

Current cards:

Total Clients Completed Audits Open Findings High Risk Cases

Improve them.

Each KPI should have:

- small label
- large number
- supporting text
- optional trend/change
- meaningful icon or visual accent
- clickable behavior when appropriate

Example:

TOTAL CLIENTS 1 Registered clients View clients →

Do not overuse colors.

Use color semantically:

Blue = primary/information Green = healthy/completed Amber = attention Red =
critical/high risk

Avoid rainbow-card aesthetics.

================================================== 8. RISK EXPOSURE

The risk section currently looks too empty when everything is zero.

Design a better zero state.

Instead of four lines with nothing happening, communicate:

✓ No risk exposure identified

All current anomaly scanners are clear.

Then optionally show a compact breakdown:

Critical 0 High 0 Medium 0 Low 0

Use restrained visual indicators.

When actual findings exist, the component should automatically become more
data-rich.

================================================== 9. AUDIT PROGRESS

The current "Audit Progress" section is too empty.

Create a useful empty state:

No completed audits yet

Complete your first audit engagement to begin tracking progress over time.

[ View Engagement → ]

When audit data exists, this should become a real visualization.

Design the component so it can later display:

- completion percentage
- workpaper completion
- findings trend
- engagement progress
- timeline

Do not hardcode the empty-state layout in a way that makes future charts
difficult.

================================================== 10. RECENT AUDIT ENGAGEMENTS

Improve this table substantially.

Columns:

Client Financial Year Engagement Type Status Risk Exposure Action

Example:

RELIANCE FY 2025–26 Statutory Audit Planning Low Risk Open →

Use compact badges.

Status examples:

Planning In Progress Review Completed Archived

Risk:

Low Medium High Critical

Each should have consistent semantic styling.

================================================== 11. AUDIT FIRMS PAGE

Current page is essentially:

Create Audit Firm empty table

Make this a professional management screen.

Header:

Audit Firms

Manage audit firms and practice-level information.

[ + Create Audit Firm ]

Below:

Search audit firms Filters Sort

Then table.

Columns:

Firm Name FRN / Registration No. PAN GSTIN Phone Email Actions

Empty state should appear inside the table.

================================================== 12. CLIENTS PAGE

Same improvement.

Header:

Clients

Manage your audit clients, entities, and engagement relationships.

[ + Create New Client ]

Add:

Search clients... Entity Type Industry Status

Table:

Client Legal Name Entity Type PAN GSTIN Industry Contact Person Status Actions

Empty state:

No clients yet

Create your first client to begin an audit engagement.

[ + Create Client ]

================================================== 13. ENGAGEMENTS PAGE

This should be one of the most important screens.

Header:

Audit Engagements

Manage audit engagements, financial years, teams and workflow status.

[ + Create Engagement ]

Add filters:

Search engagements Financial Year Audit Type Status Risk

Table:

Client Financial Year Audit Type Workflow Status Assigned Team Created Date Risk
Action

Use professional badges and row interactions.

================================================== 14. CREATE FORMS

Review every create/edit form.

Forms should NOT look like raw HTML forms.

Use:

- clear section headings
- field descriptions
- required indicators
- grouped fields
- logical sections
- two-column layout on desktop
- one-column layout on smaller screens
- inline validation
- helpful error messages
- sticky action footer when forms are long

Example:

CLIENT INFORMATION

Legal Name * [________________________]

Entity Type * [ Private Limited ▼ ]

PAN [________________________]

GSTIN [________________________]

INDUSTRY

Industry [________________________]

CONTACT

Contact Person [________________________]

Email [________________________]

Phone [________________________]

Footer:

Cancel Create Client

Primary action should be visually obvious.

================================================== 15. TYPOGRAPHY

Establish a real typography hierarchy.

Use a modern UI font already available in the project, or a clean system font.

Recommended hierarchy:

Page title: 24–28px / semibold

Section title: 14–16px / semibold

Body: 13–14px

Metadata: 11–12px

Large KPI: 28–36px / semibold

Avoid excessive uppercase text.

Uppercase should mainly be used for:

- section labels
- compact metadata
- category labels

Do not make entire UI feel like a spreadsheet.

================================================== 16. COLOR SYSTEM

Create a consistent design token system.

Primary: professional blue

Neutral: white very light gray border gray dark navy/charcoal text

Semantic: success green warning amber danger red info blue

Do NOT use saturated colors everywhere.

Most of the interface should remain neutral.

Color should communicate state and importance.

================================================== 17. CARDS

Current cards have too many visible borders and boxes.

Reduce visual noise.

Use:

- subtle borders
- very light shadows only when useful
- consistent radius
- consistent padding

Do not put cards inside cards inside cards.

Establish a clear hierarchy:

Page → Section → Component

not:

Page → Card → Card → Card → Card

================================================== 18. EMPTY STATES

Create a reusable EmptyState component.

It should support:

icon title description primaryAction secondaryAction

Example:

[ icon ]

No audit engagements

Create an engagement to start your audit workflow.

[ + Create Engagement ]

Use this component everywhere.

================================================== 19. STATUS BADGES

Create reusable components:

<StatusBadge status="planning" />

<RiskBadge level="low" />

Do not manually style these differently on every page.

Statuses should have consistent visual semantics.

================================================== 20. BUTTON SYSTEM

Create a consistent button hierarchy.

Primary: blue filled

Secondary: neutral outlined

Tertiary: text button

Danger: red

Do not make every button blue.

Examples:

Primary:

- Create Client

Secondary: Export

Tertiary: View details →

Danger: Delete Client

================================================== 21. RESPONSIVENESS

Make the application responsive.

Desktop should be the primary experience.

Also support:

- laptop
- tablet
- smaller desktop widths

At smaller widths:

- sidebar can collapse
- tables can horizontally scroll
- cards can stack
- two-column forms become one column

Do NOT destroy desktop density to accommodate mobile.

================================================== 22. ACCESSIBILITY

Improve:

- keyboard navigation
- visible focus states
- semantic HTML
- button labels
- accessible form labels
- contrast
- tooltips for icon-only controls
- ARIA only where actually necessary

The application should be usable without a mouse.

================================================== 23. INTERACTION DESIGN

Add subtle professional interactions:

- button hover
- row hover
- focus states
- selected states
- dropdown transitions
- modal transitions
- loading skeletons
- toast notifications
- confirmation dialogs for destructive actions

Animations should be subtle.

Avoid:

- excessive motion
- bouncing
- flashy gradients
- unnecessary animations

================================================== 24. LOADING STATES

Do not show blank screens while data loads.

Create reusable skeleton components for:

- tables
- cards
- dashboard sections
- forms

The application should feel responsive even when data is loading.

================================================== 25. ERROR STATES

Create consistent error states.

Example:

Unable to load clients

We couldn't retrieve your client records.

[ Try Again ]

Errors should never appear as raw exceptions or broken layouts.

================================================== 26. OFFLINE-FIRST DESIGN

FinAuditPro is an OFFLINE-FIRST audit operating system.

Reflect this in the UX.

Where applicable, show:

Offline Local changes saved Sync pending Synced Last synced: 2 min ago

These states should be subtle and professional.

Do not make offline status visually alarming unless there is an actual problem.

================================================== 27. AUDITOR-FIRST UX

This is extremely important.

Design for an auditor who may use the software for several hours per day.

Optimize for:

FAST NAVIGATION FAST DATA ENTRY FAST REVIEW LOW COGNITIVE LOAD CLEAR AUDIT
STATUS CLEAR NEXT ACTION EASY FINDING REVIEW EASY DOCUMENT ACCESS

Every screen should answer:

1. Where am I?
2. What audit/client/engagement am I working on?
3. What is the current status?
4. What needs my attention?
5. What should I do next?

================================================== 28. DESIGN SYSTEM

Before changing dozens of individual components, establish reusable design
tokens.

Create or improve:

colors spacing radius typography shadows borders buttons inputs badges cards
tables empty states alerts modals dropdowns tooltips

Use these primitives throughout the application.

Do not solve each page independently.

================================================== 29. VERY IMPORTANT — DO NOT
OVERDESIGN

Do NOT turn this into:

- a flashy startup landing page
- a glassmorphism dashboard
- a neon interface
- a gradient-heavy UI
- a dark-mode gaming UI
- a giant-card dashboard
- a Dribbble concept that is difficult to use

FinAuditPro should look like software professionals trust with financial and
audit data.

Think:

"Bloomberg/Linear/Stripe-level information architecture"

not:

"AI startup dashboard".

================================================== 30. FIX ALL PAGES, NOT JUST
THE DASHBOARD

After improving the dashboard, inspect every route/page.

At minimum audit:

/dashboard /audit-firms /clients /engagements /documents /financial-statements
/gst-reconciliation /statutory-compliance /audit-matrix /ai-copilot
/working-papers /reports /file-archival /roll-forward /settings

For every page ask:

- Is the page hierarchy clear?
- Is there excessive whitespace?
- Is the primary action obvious?
- Is the empty state useful?
- Are tables dense enough?
- Are forms easy to use?
- Are status indicators consistent?
- Are spacing and typography consistent?
- Does this feel like the same product?

================================================== 31. DO NOT BREAK EXISTING
FUNCTIONALITY

Before changing components:

inspect the existing implementation.

Preserve:

- routes
- event handlers
- state
- persistence
- database logic
- local storage
- API calls
- forms
- validation
- navigation
- existing business rules

If a UI component needs refactoring, refactor safely.

Do not replace working functionality with mock data.

Do not hardcode fake records just to make the UI look populated.

Empty states must remain empty when there is no data.

================================================== 32. IMPLEMENTATION PROCESS

Follow this process:

PHASE 1 — AUDIT

Inspect:

- project structure
- package.json
- routing
- global CSS
- theme
- components
- layout
- dashboard
- tables
- forms
- state management

Identify the existing design system.

PHASE 2 — DESIGN SYSTEM

Create/refine reusable primitives:

Button Input Select Badge Card Table EmptyState Alert Modal Dropdown Skeleton
PageHeader SectionHeader StatusBadge RiskBadge

PHASE 3 — GLOBAL LAYOUT

Fix:

sidebar topbar content width spacing typography responsive layout

PHASE 4 — CORE PAGES

Fix in this order:

1. Dashboard
2. Audit Firms
3. Clients
4. Engagements

PHASE 5 — REMAINING MODULES

Apply the same system to:

Documents Financial Statements GST Reconciliation Statutory Compliance Audit
Matrix AI Copilot Working Papers Reports File Archival Roll-Forward Settings

PHASE 6 — QUALITY PASS

Check:

- no visual inconsistencies
- no broken layouts
- no overflowing tables
- no dead buttons
- no console errors
- no broken routes
- no duplicate styles
- no inconsistent spacing
- no unnecessary blank areas
- no fake data
- no functionality regressions

================================================== 33. IMPORTANT VISUAL TARGET

The final product should feel approximately like:

┌──────────────────────────────────────────────────────────────┐ │ FinAuditPro
Search... Engagement + New │
├──────────────┬───────────────────────────────────────────────┤ │ │ │ │
WORKSPACE │ Audit Overview │ │ │ RELIANCE · FY 2025–26 · Statutory Audit │ │
Dashboard │ │ │ Audit Firms │ ┌──────────────────────┐ ┌─────────────────┐ │ │
Clients │ │ AUDIT WORKFLOW │ │ NEEDS ATTENTION │ │ │ Engagements │ │ ✓ Client │
│ │ │ │ │ │ ✓ FY │ │ ✓ All clear │ │ │ FINANCIAL │ │ ● Engagement │ │ │ │ │
Documents │ │ ○ Materiality │ │ │ │ │ Statements │ │ ○ Documentation │ │ │ │ │
GST │ │ ○ Completion │ │ │ │ │ Compliance │ │ │ │ │ │ │ │ │ Next action │ │ │ │
│ ANALYSIS │ │ Complete setup │ │ │ │ │ Audit Matrix │ │ [Continue Setup] │ │ │
│ │ AI Copilot │ └──────────────────────┘ └─────────────────┘ │ │ │ │ │ WORKFLOW
│ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────────┐ │ │ Working │ │Clients│ │Audits │
│Finding│ │High Risk │ │ │ Papers │ │ 1 │ │ 0 │ │ 0 │ │ 0 │ │ │ Reports │
└───────┘ └───────┘ └───────┘ └───────────┘ │ │ │ │ │ SYSTEM │
┌────────────────────┐ ┌──────────────────┐ │ │ Archive │ │ AUDIT PROGRESS │ │
RISK EXPOSURE │ │ │ Roll-forward │ │ │ │ │ │ │ Settings │ │ No completed │ │ ✓
No risk │ │ │ │ │ audits yet │ │ exposure │ │ │ │ └────────────────────┘
└──────────────────┘ │ │ │ │ │ │ RECENT AUDIT ENGAGEMENTS │ │ │
┌───────────────────────────────────────────┐ │ │ │ │ Client │ FY │ Type │
Status │ Risk │ ... │ │ │ │ │ Reliance │...│ ... │Planning│Low │Open │ │ │ │
└───────────────────────────────────────────┘ │
└──────────────┴───────────────────────────────────────────────┘

The actual implementation should be polished and modern, not literally copied
from this ASCII layout.

================================================== 34. FINAL REQUIREMENT

Do not simply tell me what you would change.

ACTUALLY IMPLEMENT THE CHANGES IN THE CODEBASE.

After implementation:

1. Run the application.
2. Inspect the resulting UI.
3. Check every major page.
4. Fix visual inconsistencies you notice.
5. Check browser console for errors.
6. Check responsive behavior.
7. Verify existing interactions still work.
8. Verify existing data still appears correctly.
9. Remove unnecessary CSS duplication.
10. Give me a concise summary of:

- what you changed
- which components were created/refactored
- which pages were updated
- any remaining issues

Most importantly:

DO NOT STOP AFTER MAKING THE DASHBOARD LOOK BETTER.

The goal is to make the ENTIRE FinAuditPro application feel like one coherent,
premium, production-ready audit platform.

PROMPT 2 : You are working on my existing FinAuditPro application.

DO NOT rebuild the application from scratch. DO NOT replace the architecture
unnecessarily. DO NOT create mock screens that only look functional.

I need you to audit the ENTIRE existing codebase and fix the application so it
behaves like a real, integrated offline-first audit operating system.

## PROJECT CONTEXT

App name: FinAuditPro Purpose: Offline-first audit operating system for Indian
statutory/GST/tax audit workflows.

Current UI modules:

WORKSPACE

- Dashboard
- Audit Firms
- Clients
- Engagements

FINANCIAL

- Documents
- Financial Statements
- GST Reconciliation
- Statutory Compliance

ANALYSIS

- Audit Matrix
- AI Copilot

AUDIT WORKFLOW

- Working Papers
- Reports

SYSTEM

- File Archival
- Roll-Forward
- Settings

The application currently has screens that look visually complete but many areas
are empty/static and the modules are not sufficiently connected.

I want you to turn this into a genuinely functional application.

==================================================

1. # FIRST: AUDIT THE EXISTING CODEBASE

Before changing anything:

1. Inspect the complete project structure.
2. Identify:
   - frontend framework
   - backend architecture
   - database/storage
   - state management
   - routing
   - models/schemas
   - services
   - file handling
   - existing business logic
   - existing mock/demo data
3. Find duplicated logic.
4. Find dead components.
5. Find buttons that do nothing.
6. Find pages that contain hardcoded/mock data.
7. Find forms that do not persist data.
8. Find navigation routes that do not work correctly.
9. Find state that is lost after refresh.
10. Find inconsistencies between modules.

DO NOT immediately start rewriting.

First understand how the existing application works.

Then make a concise internal implementation plan and execute it.

# ================================================== 2. CORE REQUIREMENT — ONE CONNECTED DATA MODEL

All modules must operate on the same underlying audit data.

The hierarchy should effectively be:

Audit Firm ↓ Client ↓ Financial Year ↓ Engagement ↓ Documents / Financial
Statements / GST / Compliance ↓ Audit Matrix ↓ Working Papers ↓ Findings /
Evidence ↓ Reports ↓ Archive / Roll Forward

Do not create isolated fake datasets for individual pages.

If I create a client, it must appear in Clients and be selectable when creating
an Engagement.

If I create an Engagement, it must become the active engagement.

Documents, financial data, GST reconciliation, compliance checks, audit
procedures, findings, working papers and reports must belong to the correct
engagement.

# ================================================== 3. FIX THE DASHBOARD

Dashboard must become a real audit control centre.

It should dynamically calculate:

- Total Clients
- Active Engagements
- Completed Audits
- Open Findings
- High Risk Cases
- Critical Findings
- Pending Documentation
- Pending Review
- Overall Audit Progress

The dashboard must NOT display hardcoded numbers.

The audit lifecycle should actually work:

Client → Financial Year → Engagement → Materiality → Documentation → Completion

The current engagement should be selectable.

"Continue Setup" must navigate to the correct next incomplete step.

Progress percentage must be calculated from actual workflow completion.

"Needs Attention" must dynamically detect:

- overdue items
- high-risk findings
- missing mandatory documentation
- unresolved exceptions
- pending approvals/reviews

# ================================================== 4. AUDIT FIRMS

Make Audit Firms fully functional.

Support:

- Create
- Edit
- View
- Delete/archive
- Search
- Validation

Store:

- Firm name
- FRN / Registration number
- PAN
- GSTIN
- Address
- Phone
- Email
- Partners
- Registration details
- Status

Do not allow duplicate registration identifiers where inappropriate.

# ================================================== 5. CLIENTS

Make Clients fully functional.

Create a proper client form.

Fields should include at minimum:

- Legal name
- Trade name
- Entity type
- PAN
- GSTIN
- CIN/LLP information where applicable
- Industry
- Registered address
- Contact person
- Email
- Phone
- Financial year end
- Status

Add:

- search
- filtering
- sorting
- edit
- archive
- client detail page

A client detail page should show:

- engagements
- documents
- financial statements
- GST reconciliation
- compliance
- findings
- reports

# ================================================== 6. ENGAGEMENTS

This is one of the most important modules.

Create a real engagement workflow.

Required fields:

- Client
- Financial year
- Audit type
- Engagement number
- Period
- Assigned team
- Engagement partner
- Manager
- Start date
- Due date
- Materiality
- Performance materiality
- Audit scope
- Status
- Risk classification

Engagement statuses should include something like:

Planning Fieldwork Review Completion Completed Archived

Opening an engagement must establish it as the ACTIVE ENGAGEMENT throughout the
application.

Every other module must know which engagement is currently active.

# ================================================== 7. DOCUMENT MANAGEMENT

The Documents page must actually work.

Support:

- upload documents
- drag/drop if practical
- document categories
- metadata
- file size
- page count
- SHA-256 hash
- upload timestamp
- document status
- search
- filter
- preview/open
- download/export where appropriate
- archive

Document categories could include:

- Trial Balance
- General Ledger
- Bank Statements
- GST Returns
- Purchase Register
- Sales Register
- Invoices
- Fixed Asset Register
- Payroll
- Tax Returns
- Prior Year Audit Report
- Management Representation
- Other

Documents must belong to an engagement.

Calculate real SHA-256 hashes instead of fake values.

# ================================================== 8. FINANCIAL STATEMENTS

Make the Financial Statements module functional.

Support importing financial datasets such as:

CSV XLSX JSON

Normalize imported transaction data into a consistent schema.

Example:

date voucher_number account_code account_name debit credit narration cost_center
reference

Validate:

- missing columns
- invalid dates
- invalid numeric values
- duplicate vouchers
- debit/credit inconsistencies

Show:

- dataset summary
- row count
- total debits
- total credits
- account count
- date range

The Normalized Dataset Rows Inspector must display REAL imported rows.

# ================================================== 9. DETERMINISTIC AUDIT ANALYTICS

Do NOT make audit analytics purely AI-generated.

Implement deterministic rules first.

Examples:

- duplicate transactions
- duplicate invoice numbers
- round-number transactions
- unusual journal entries
- weekend postings
- postings outside normal hours
- large transactions
- manual journal entries
- unusual account combinations
- negative balances
- credit/debit anomalies
- related-party indicators
- suspicious narration patterns
- missing supporting documents
- unusual GST amounts

Every anomaly should contain:

- rule ID
- severity
- title
- description
- implicated rows
- computed evidence
- amount
- rationale
- status

Possible severity:

Critical High Medium Low Info

Never claim an anomaly exists without actual computed evidence.

# ================================================== 10. GST RECONCILIATION

The GST Reconciliation module must be data-driven.

Support:

Purchase Register vs GSTR-2B

Compare using appropriate identifiers and fallback matching logic.

Show:

- total invoices
- matched
- mismatched
- missing in 2B
- missing in purchase register
- amount mismatch
- GST mismatch
- duplicate invoices
- ineligible ITC

For every mismatch show:

- invoice
- supplier
- GSTIN
- invoice date
- taxable value
- CGST
- SGST
- IGST
- expected value
- actual value
- variance
- reason
- status

The counters at the top must be calculated from actual reconciliation results.

# ================================================== 11. STATUTORY COMPLIANCE

Do NOT simply show a static checklist.

Build a real compliance engine.

Support at minimum:

- CARO 2020
- Tax Audit Form 3CD

Each clause should have:

- clause number
- title
- requirement
- applicability
- evidence required
- evidence attached
- auditor conclusion
- status
- reviewer
- review status
- notes
- findings

Statuses:

Not Started Applicable Not Applicable Compliant Exception Pending Evidence Under
Review

"Auto-Evaluate Compliance" must run actual deterministic checks where possible.

Never mark a clause compliant simply because the button was clicked.

If there isn't enough evidence, status should be something like:

Pending Evidence

# ================================================== 12. AUDIT MATRIX

Create a proper risk-based audit matrix.

Dimensions:

- Audit area
- Assertion
- Risk
- Inherent risk
- Control risk
- Detection risk
- Overall risk
- Materiality
- Planned procedure
- Sample size
- Evidence
- Result
- Finding
- Reviewer status

Allow users to:

- add procedures
- assign procedures
- mark procedures complete
- attach evidence
- record exceptions
- generate findings

Risk should influence audit priority.

# ================================================== 13. WORKING PAPERS

Working Papers must connect the entire audit workflow.

Each working paper should support:

- WP number
- Audit area
- Objective
- Procedure
- Population
- Sample
- Evidence
- Result
- Conclusion
- Prepared by
- Prepared date
- Reviewed by
- Review date
- Review notes
- Status

Statuses:

Draft Prepared Review Pending Reviewed Approved

Allow linking:

Working Paper → Evidence → Audit Procedure → Finding → Report

# ================================================== 14. FINDINGS MANAGEMENT

Implement a real findings system.

Each finding should contain:

- Finding ID
- Title
- Description
- Audit area
- Criteria
- Condition
- Cause
- Effect
- Risk
- Recommendation
- Management response
- Severity
- Owner
- Due date
- Status
- Evidence
- Related working paper

Statuses:

Open Management Response Remediation Resolved Closed Accepted Risk

Dashboard counts must derive from this data.

# ================================================== 15. REPORTS

Reports must be generated from actual engagement data.

Support at least:

- Audit status report
- Findings report
- GST reconciliation report
- Compliance report
- Working paper index
- Executive audit summary

Do not generate fake placeholder reports.

Report data must come from the selected engagement.

# ================================================== 16. FILE ARCHIVAL

Implement proper archival behavior.

Archived engagements should become read-only.

Do not delete audit evidence accidentally.

Support:

- archive engagement
- archive documents
- restore where appropriate
- archive metadata
- integrity verification

Preserve SHA-256 hashes for files.

# ================================================== 17. ROLL-FORWARD

Make Roll-Forward functional.

Allow previous-year engagement information to be carried into a new financial
year.

Possible roll-forward items:

- client information
- audit programs
- audit procedures
- risk assessments
- materiality settings
- recurring working paper structures
- prior findings
- compliance checklist
- document index

Clearly distinguish:

Carried Forward vs Needs Current-Year Update

Never blindly copy evidence that should be re-obtained.

# ================================================== 18. SEARCH

The global search box must actually work.

Search across:

- clients
- engagements
- documents
- findings
- working papers
- reports

Results should indicate type and allow navigation.

Support keyboard shortcut:

Cmd/Ctrl + K

# ================================================== 19. ACTIVE ENGAGEMENT

This is critical.

The top navigation contains an ACTIVE ENGAGEMENT selector.

Make it functional.

When an engagement is selected:

all modules should operate against that engagement unless explicitly browsing
global/client-level data.

The active engagement should survive navigation and refresh.

Avoid accidental cross-engagement data contamination.

# ================================================== 20. OFFLINE-FIRST REQUIREMENT

This is an OFFLINE-FIRST application.

Do not introduce unnecessary cloud dependencies.

The core application must work without internet access.

Use the existing local persistence architecture if one exists.

If persistence is currently inadequate, implement a robust local storage layer
appropriate for the existing architecture.

Data must survive:

- navigation
- page reload
- application restart

Use migrations/versioning if changing the data schema.

# ================================================== 21. UX / UI

Preserve the current FinAuditPro visual identity.

The current design is clean and professional.

Keep:

- left sidebar
- white/light audit-professional aesthetic
- blue primary actions
- compact tables
- status indicators
- cards
- workflow indicators

But improve:

- empty states
- loading states
- error states
- confirmation dialogs
- validation messages
- responsive behavior
- table readability
- action discoverability

Do NOT make the UI unnecessarily flashy.

This is professional audit software, not a marketing website.

# ================================================== 22. IMPORTANT — NO FAKE FUNCTIONALITY

This is extremely important.

DO NOT:

- hardcode dashboard metrics
- hardcode table rows
- make buttons appear functional without persistence
- fake compliance results
- fake audit findings
- fake GST results
- fabricate hashes
- fabricate financial calculations
- show "success" when an operation failed
- silently swallow errors

Every displayed number should have a real source.

Every action should either:

1. modify persisted application state, or
2. navigate to a real workflow.

# ================================================== 23. DATA INTEGRITY

Implement validation and defensive programming.

Handle:

- duplicate records
- invalid identifiers
- missing required fields
- invalid financial values
- malformed files
- corrupted imports
- missing active engagement
- deleted referenced entities
- orphan records

Use stable IDs.

Do not rely on display names as database identifiers.

# ================================================== 24. TESTING

After implementation, test the application end-to-end.

At minimum test:

1. Create audit firm.
2. Create client.
3. Create financial year.
4. Create engagement.
5. Set active engagement.
6. Upload document.
7. Import financial dataset.
8. Run analytics.
9. Import GST data.
10. Run GST reconciliation.
11. Evaluate compliance.
12. Create audit procedure.
13. Create working paper.
14. Create finding.
15. Generate report.
16. Complete engagement.
17. Archive engagement.
18. Refresh application.
19. Confirm data persists.
20. Confirm dashboard reflects all changes.

Fix all errors found.

# ================================================== 25. CODE QUALITY

While implementing:

- preserve existing working functionality
- avoid unnecessary rewrites
- use reusable components
- separate UI from business logic
- centralize validation
- centralize persistence
- centralize domain models
- avoid duplicated calculations
- use clear naming
- handle errors explicitly
- keep modules maintainable

Do not create one giant component.

# ================================================== 26. FINAL VERIFICATION

Before saying the task is complete:

Run the application.

Navigate through EVERY sidebar item.

Verify that every page:

- loads
- has working navigation
- has working primary actions
- persists data
- handles empty state
- handles errors
- respects active engagement
- displays real data

Check the browser/console/application logs for errors.

Fix them.

Then provide me with:

1. What was broken.
2. What you changed.
3. Files/components changed.
4. Data model changes.
5. Tests performed.
6. Remaining limitations, if any.

Do not stop after fixing only the screenshots I provided.

The goal is to make FinAuditPro function as a coherent audit operating system,
not merely make individual pages look better.

PROMPT 3 : You are a senior full-stack engineer specializing in audit software,
financial systems, AI/RAG systems, and production-grade UX.

I am building an application called “FinAuditPro — Offline-First Audit Operating
System”.

I need you to FIX and COMPLETE the existing implementation, not create a
superficial mockup.

The current AI Audit Analysis Workspace has these sections:

1. Top summary:
   - Total Findings
   - Critical / High
   - Medium Risk
   - Unresolved
   - Evidence Sources
   - “Run ICAI Audit Scan” button
   - “Rule Engine Fallback Active” indicator

2. Left panel:
   - Audit Evidence Sources
   - ICAI Audit Prompt Library
   - CARO 2020 Inventory
   - Sec 188 Related Party
   - Sec 185/186 Loans
   - SA 240 Revenue Anomaly
   - Form 3CD Clause 44
   - SA 500 Audit Evidence

3. Center:
   - AI Audit Investigation Copilot
   - Conversation/reasoning area
   - Prompt input
   - Send Prompt
   - Loading/model reasoning state

4. Right panel:
   - Audit Findings & Evidence
   - Currently “No Anomalies Flagged”

The current implementation looks visually complete but the actual functionality
is incomplete.

YOUR TASK:

Audit the existing codebase and implement the missing functionality end-to-end.

DO NOT rewrite the entire application unnecessarily. DO NOT destroy existing
working functionality. DO NOT replace real functionality with static/demo data.
DO NOT merely improve CSS. Find the actual architecture and integrate into it
properly.

==================================================

1. # FIRST: UNDERSTAND THE EXISTING CODEBASE

Before making changes:

- Inspect the entire project structure.
- Identify the framework/runtime.
- Identify the backend architecture.
- Identify database/storage.
- Identify how audit engagements are represented.
- Identify existing models/schemas.
- Identify existing document upload/storage logic.
- Identify existing financial dataset logic.
- Identify existing GST reconciliation logic.
- Identify existing statutory compliance logic.
- Identify existing audit matrix/materiality logic.
- Identify existing AI/RAG code.
- Identify existing rule-engine/fallback logic.
- Identify existing navigation/routing.
- Identify existing state management.

Do not assume anything.

Trace the real data flow from:

Document / Financial Dataset ↓ Evidence extraction ↓ Normalization ↓ Audit rules
/ analytics ↓ AI/RAG analysis ↓ Findings ↓ Evidence ↓ Copilot ↓ Reports /
Working Papers

Then fix the weakest/missing links.

# ================================================== 2. MAKE AI AUDIT COPILOT ACTUALLY FUNCTIONAL

The center AI Copilot must be a real application feature.

It should support prompts such as:

- “Analyze revenue for unusual transactions.”
- “Find transactions that may indicate fraud.”
- “Check related party transactions under Section 188.”
- “Check loans and guarantees under Sections 185/186.”
- “Analyze inventory discrepancies.”
- “Check GST 2B reconciliation exceptions.”
- “Evaluate CARO 2020 compliance.”
- “Review audit evidence under SA 500.”
- “Explain this finding.”
- “Show supporting evidence for this finding.”
- “What audit procedure should I perform next?”
- “Generate a working-paper-ready explanation.”

The Copilot should NOT hallucinate findings.

Every finding must be grounded in actual application evidence whenever evidence
exists.

Use this response structure:

Finding Risk Why it matters Applicable standard / provision Evidence Evidence
source Affected transaction/document Recommended audit procedure Suggested
auditor conclusion Confidence Status

If evidence is insufficient, explicitly say:

“Insufficient evidence — additional audit evidence required.”

Never invent financial values, invoices, transactions, documents, legal
provisions, or audit conclusions.

# ================================================== 3. CONNECT THE EVIDENCE SOURCES

The left-side evidence panel cannot be decorative.

When documents or datasets exist, display actual evidence sources.

Each evidence source should expose:

- filename
- document type
- upload date
- hash
- page count
- extracted text status
- processing status
- engagement
- relevant audit area

Clicking an evidence source should allow the AI to use that evidence.

If possible, support:

Evidence → finding traceability.

For example:

Finding: “Potential revenue recognition anomaly”

Evidence: invoice_1042.pdf page 7 ₹12,50,000 transaction date customer relevant
ledger entry

The auditor should be able to open the source.

# ================================================== 4. IMPLEMENT REAL AUDIT FINDINGS

Create a proper finding model if one does not already exist.

Minimum fields:

id engagement_id title description category severity risk_level status standard
section source_document_id source_reference affected_rows evidence
recommendation auditor_conclusion confidence created_at updated_at

Severity:

CRITICAL HIGH MEDIUM LOW INFO

Status:

OPEN UNDER_REVIEW RESOLVED DISMISSED

Every finding must have traceable evidence.

# ================================================== 5. IMPLEMENT DETERMINISTIC RULE ENGINE

The “Rule Engine Fallback Active” state must represent a real fallback.

Implement deterministic audit routines where appropriate.

Examples:

SA 240:

- unusual revenue spikes
- unusual period-end revenue
- duplicate invoices
- round-value transactions
- unusual customer concentration
- credit notes after year-end
- manual journal entries affecting revenue

Section 188:

- related-party transaction identification
- related party name matching
- transaction classification
- approval/evidence checks

Sections 185/186:

- loans
- guarantees
- securities
- investments
- directors / related entities

CARO 2020:

- inventory
- PPE
- loans
- statutory dues
- defaults
- related parties
- internal audit
- cash losses
- working capital
- etc.

GST:

- purchase register vs GSTR-2B
- missing invoices
- mismatched taxable value
- mismatched GST
- duplicate invoices
- rate differences
- ineligible ITC indicators

Do NOT blindly mark everything as non-compliant.

Rules should generate:

PASS WARNING EXCEPTION INSUFFICIENT_EVIDENCE

# ================================================== 6. FIX THE “RUN ICAI AUDIT SCAN” BUTTON

This button must actually execute the audit pipeline.

Expected flow:

User clicks: RUN ICAI AUDIT SCAN

↓

Validate active engagement

↓

Load evidence

↓

Load financial datasets

↓

Normalize available data

↓

Run deterministic audit rules

↓

Run AI/RAG analysis where configured

↓

Deduplicate findings

↓

Assign severity

↓

Attach evidence

↓

Persist findings

↓

Update dashboard counters

↓

Display findings in right panel

↓

Make findings available to Copilot

Do not show fake loading states without actually processing data.

Show meaningful progress:

Loading evidence Analyzing transactions Running audit rules Evaluating statutory
compliance Generating findings Finalizing evidence links

# ================================================== 7. FIX THE RIGHT-SIDE FINDINGS PANEL

Replace the empty:

“No Anomalies Flagged”

state with a functional findings list when findings exist.

Each finding card should show:

Severity Title Risk Short explanation Evidence count Standard / section Status

Example:

HIGH Revenue anomaly detected

3 transactions occurred unusually close to year-end and differ significantly
from historical customer patterns.

Evidence: 3 records Standard: SA 240 Status: Open

Clicking the finding should open detailed evidence.

# ================================================== 8. IMPLEMENT FINDING DETAILS

Create a detailed finding view/modal/panel.

Include:

Finding title Severity Risk explanation Audit implication Applicable standard
Evidence Affected transactions Source documents Audit procedure Management
response Auditor response Conclusion Status Confidence Created date

Allow auditor to:

- Accept finding
- Mark under review
- Resolve
- Dismiss
- Add note
- Attach evidence
- Ask Copilot about finding

# ================================================== 9. MAKE THE PROMPT LIBRARY FUNCTIONAL

Clicking:

CARO 2020 Inventory Sec 188 Related Party Sec 185/186 Loans SA 240 Revenue
Anomaly Form 3CD Clause 44 SA 500 Audit Evidence

should automatically load a structured audit prompt into the Copilot.

Do not use generic prompts.

Create specialized prompts for each audit area.

Each prompt should define:

Objective Evidence required Tests to perform Rules Relevant standard Expected
output Evidence requirements False-positive handling

# ================================================== 10. RAG / AI ARCHITECTURE

If an AI provider is configured:

Use retrieved application evidence as context.

Recommended pipeline:

User prompt ↓ Intent detection ↓ Evidence retrieval ↓ Relevant transaction
retrieval ↓ Relevant statutory/audit guidance retrieval ↓ Context assembly ↓ LLM
analysis ↓ Structured response ↓ Evidence validation ↓ Finding creation if
applicable

The model must not be allowed to invent evidence.

If no LLM/API is configured:

Use deterministic rule-engine fallback and clearly display:

“AI unavailable — deterministic audit analysis active.”

Do not crash.

# ================================================== 11. OFFLINE-FIRST REQUIREMENT

This application is explicitly called:

FinAuditPro — Offline-First Audit Operating System

Therefore:

- Core audit functionality must work without internet.
- Documents should remain locally available.
- Deterministic audit rules must work offline.
- Findings must persist locally.
- Copilot should gracefully degrade when no AI provider is configured.
- Do not make the application dependent on an external API for basic auditing.

# ================================================== 12. DATA INTEGRITY

This is audit software.

Do NOT silently modify source evidence.

Preserve:

- original document
- original hash
- normalized representation
- derived analysis
- finding
- evidence relationship
- audit trail

Implement an audit log if one does not exist.

Track:

who what when old value new value reason/action

# ================================================== 13. UX IMPROVEMENTS

Keep the current FinAuditPro visual language.

Do NOT redesign the entire application.

Maintain:

- clean white interface
- blue primary actions
- restrained colors
- compact professional tables
- audit-software appearance
- clear hierarchy

Improve usability:

- loading states
- empty states
- error states
- success states
- disabled states
- tooltips
- clickable evidence
- finding drill-down
- keyboard-friendly interactions
- responsive layout

The UI should feel like professional audit software, not an AI chatbot.

# ================================================== 14. FIX THE OTHER MODULES IF NECESSARY

The screenshots show that several modules currently appear empty:

Audit Firms Clients Engagements Documents Financial Statements GST
Reconciliation Statutory Compliance Audit Matrix AI Copilot

Do not populate them with fake rows.

Instead, ensure that when real data is created/imported, it flows correctly
through the system.

Especially ensure:

Client → Engagement → Documents → Financial Dataset → Audit Matrix → Compliance
→ Findings → Working Papers → Reports

is a coherent end-to-end workflow.

# ================================================== 15. IMPORTANT: NO MOCK FUNCTIONALITY

Do not solve the problem by:

- hardcoded findings
- fake API responses
- fake loading
- static dashboard counters
- placeholder transactions
- fake AI responses
- dummy evidence
- random risk scores

If seed/demo data already exists, clearly isolate it from production data.

# ================================================== 16. TEST EVERYTHING

After implementation:

Run the application.

Test:

1. Create audit firm
2. Create client
3. Create engagement
4. Upload document
5. Import financial dataset
6. Run deterministic analytics
7. Run GST matching
8. Run statutory compliance evaluation
9. Run materiality calculation
10. Run ICAI Audit Scan
11. Generate finding
12. Open finding
13. View evidence
14. Ask Copilot about finding
15. Change finding status
16. Verify dashboard updates
17. Verify persistence after restart

Also test empty states.

Also test invalid input.

Also test missing evidence.

Also test AI unavailable.

Also test duplicate documents.

# ================================================== 17. FIX BUGS YOU DISCOVER

If you find bugs while implementing this, fix them.

Do not stop after identifying them.

Look for:

- broken routes
- missing handlers
- state synchronization problems
- database persistence problems
- incorrect calculations
- inconsistent terminology
- dead buttons
- broken forms
- missing validation
- frontend/backend mismatches
- errors hidden by try/catch
- race conditions
- stale UI state

# ================================================== 18. FINAL REQUIREMENT

I want a REAL working audit operating system, not a UI prototype.

Prioritize in this order:

1. Data integrity
2. Functional workflow
3. Evidence traceability
4. Deterministic audit logic
5. AI/RAG integration
6. Finding management
7. UX polish

Before finishing, perform a complete codebase review and verify that the AI
Audit Analysis Workspace is genuinely connected to the rest of FinAuditPro.

When finished, give me:

A. What you changed B. Files changed C. Database/schema changes D. New audit
rules E. AI/RAG changes F. Bugs fixed G. Tests performed H. Remaining
limitations

Do not just tell me what I should do.

ACTUALLY IMPLEMENT THE CHANGES IN THE EXISTING CODEBASE.

PROMPT 4 : You are working on my existing FinAuditPro application.

I need you to FIX and COMPLETE the "Working Papers" and "Reports" modules shown
in the attached screenshots.

IMPORTANT:

- Do NOT redesign the entire application.
- Preserve the existing FinAuditPro visual language, sidebar, top navigation,
  typography, spacing, colors, borders, buttons, cards, and table styling.
- Do not create a fake/static UI. These modules must actually work.
- Inspect the existing codebase first and understand the current architecture,
  data models, routing, state management, and persistence before making changes.
- Reuse existing components and utilities wherever possible.
- Do not break any existing modules.

==================================================

1. WORKING PAPERS MODULE ==================================================

Current screen contains:

"Configurable Working Paper Index Guidance"

Stats:

- Total Working Papers
- Open Review Points
- Signed Off & Locked

Table:

- Ref Code
- Title
- Audit Area
- Status
- Preparer
- Open Points
- Content Hash / Lock
- Actions

There is a "+ New Working Paper" button.

IMPLEMENT THIS AS A REAL WORKING-PAPER SYSTEM.

New Working Paper should allow the auditor to create a working paper with:

- Reference Code
- Title
- Audit Area
- Financial Year
- Engagement
- Prepared By
- Reviewer
- Objective
- Audit Assertion
- Risk
- Materiality
- Procedures
- Evidence/Documents
- Findings
- Conclusion
- Review Notes
- Status

Suggested statuses:

Draft Prepared Under Review Review Points Approved Signed Off Locked

Required functionality:

1. Create working paper.
2. Edit working paper.
3. Open/view working paper.
4. Save draft.
5. Add audit procedures.
6. Add evidence/document references.
7. Add findings.
8. Add review points.
9. Assign reviewer.
10. Mark review points as resolved.
11. Reviewer approval.
12. Sign-off workflow.
13. Lock signed-off working paper.
14. Prevent modification after locking.
15. Show audit trail/history.
16. Generate deterministic content hash when signed/locked.
17. Display lock status and hash in the table.
18. Search/filter/sort working papers.
19. Open Points counter must update automatically.
20. Signed & Locked counter must update automatically.
21. Total Working Papers must update automatically.

Working papers must be linked to: Client → Engagement → Financial Year → Audit
Area.

Evidence added to a working paper should reference actual uploaded documents
from the Documents module rather than creating duplicate files.

# ================================================== 2. WORKING PAPER DETAIL VIEW

Create a professional audit working-paper detail page.

Use a layout similar to professional audit software:

Header:

- Ref Code
- Working Paper Title
- Status badge
- Prepared By
- Reviewer
- Engagement
- Financial Year

Sections/tabs:

Overview Audit Objective Risk & Assertions Audit Procedures Evidence Findings
Review Points Conclusion Sign-Off Audit Trail

For each audit procedure provide:

- Procedure ID
- Description
- Expected Result
- Actual Result
- Evidence
- Performed By
- Performed Date
- Result: Pass / Fail / Exception / N/A

For findings provide:

- Finding ID
- Title
- Description
- Criteria
- Condition
- Cause
- Effect
- Recommendation
- Severity
- Management Response
- Status

# ================================================== 3. REPORTS MODULE

Current Reports screen contains:

"Statutory Report Text & Legal Signature Honesty"

Stats:

- Total Reports
- Draft Reports (Watermarked)
- Approved Reports

Table:

- Report Title
- Type
- Status
- Data As-Of
- Generated By
- Content Hash
- Actions

There is a "+ Generate New Report" button.

TURN THIS INTO A REAL REPORT GENERATION MODULE.

Generate New Report should support:

- Statutory Audit Report
- CARO 2020 Report
- Form 3CD / Tax Audit Report
- GST Reconciliation Report
- Audit Findings Report
- Management Letter
- Working Paper Summary
- Financial Statement Audit Summary
- Compliance Report

The report generator must pull data from the actual application.

DO NOT hardcode report values.

Data should come from:

Clients Audit Firms Engagements Documents Financial Statements GST
Reconciliation Statutory Compliance Audit Matrix AI Audit Findings Working
Papers

# ================================================== 4. REPORT GENERATION WORKFLOW

Create a proper workflow:

Select Client ↓ Select Engagement ↓ Select Financial Year ↓ Select Report Type ↓
Select Data Sources ↓ Review Data ↓ Generate Draft ↓ Validate ↓ Approve ↓ Lock ↓
Export

Before generation show:

- Client
- Engagement
- Financial Year
- Report Type
- Data As-Of date
- Number of evidence sources
- Number of findings
- Number of working papers
- Compliance status
- Materiality
- Reviewer

# ================================================== 5. REPORT DETAIL PAGE

Create a professional report viewer/editor.

Header:

- Report title
- Report type
- Client
- Financial Year
- Status
- Data As-Of
- Generated By
- Content Hash

Sections:

Executive Summary Scope Audit Approach Materiality Key Findings Risk Assessment
Statutory Compliance GST Reconciliation Financial Statement Observations CARO
2020 Form 3CD Management Recommendations Conclusion Sign-Off

Provide:

- Edit Draft
- Save
- Preview
- Validate
- Approve
- Generate PDF
- Generate DOCX
- Print
- Lock

Draft reports MUST display a clear "DRAFT" / "WATERMARKED" state.

Approved reports should be clearly distinguished from drafts.

Locked reports must become immutable.

# ================================================== 6. REPORT INTEGRITY

Implement report versioning.

Every generated report should have:

- Version
- Generated timestamp
- Generated by
- Source data version
- Content hash
- Approval status
- Lock timestamp

When a report is approved/locked:

Generate a deterministic SHA-256 hash based on the report content and relevant
source/version metadata.

If the report content changes:

- Create a new version.
- Never silently overwrite the previous approved version.

Show version history.

# ================================================== 7. LEGAL / STATUTORY SAFETY

Do NOT fabricate statutory conclusions.

Clearly distinguish:

- Application-generated analysis
- Auditor judgment
- Verified statutory information
- Unverified guidance

If statutory sources are not verified, display an appropriate warning.

Never present AI-generated text as an officially verified statutory conclusion.

Reports must preserve an audit trail of how conclusions were generated.

# ================================================== 8. PDF / DOCX EXPORT

Implement actual export functionality.

PDF should contain:

- Firm name/logo
- Client name
- Engagement
- Financial Year
- Report title
- Report content
- Findings
- Conclusions
- Sign-off
- Version
- Data As-Of
- Content Hash

DOCX should contain equivalent structured content.

Do not create empty placeholder files.

# ================================================== 9. DASHBOARD INTEGRATION

Update the Dashboard automatically.

Dashboard should reflect:

- Number of Working Papers
- Open Review Points
- Signed-Off Working Papers
- Draft Reports
- Approved Reports
- Open Findings
- High-Risk Findings
- Compliance exceptions

All numbers must come from the same underlying data source.

No duplicated hardcoded state.

# ================================================== 10. PERSISTENCE

Because FinAuditPro is designed as an offline-first audit operating system:

- Data must persist locally.
- Refreshing the application must not lose data.
- Closing/reopening the application must preserve data.
- Use the existing persistence layer if one already exists.
- If necessary, improve the existing local database/storage architecture.
- Maintain deterministic IDs.
- Maintain audit history.

# ================================================== 11. UX REQUIREMENTS

The application currently has too many empty states.

Replace meaningless empty tables with useful empty-state messages such as:

"No working papers yet" "Create your first working paper to begin documenting
audit evidence."

" No reports generated yet" "Generate a report from your engagement data."

Buttons should work.

Forms should validate input.

Show success/error notifications.

Use confirmation dialogs for:

- Delete
- Approve
- Sign-off
- Lock

Do not allow accidental destructive actions.

# ================================================== 12. VISUAL DESIGN

Keep the existing FinAuditPro design.

Use:

- White/light-gray workspace
- Blue primary actions
- Thin borders
- Compact professional tables
- Small audit-status badges
- Clean typography
- Consistent spacing
- Professional accounting/audit-software appearance

Do NOT introduce:

- Huge cards
- Excessive gradients
- Neon colors
- Consumer-app styling
- Unnecessary animations
- Decorative UI that reduces audit usability

The UI should feel like professional enterprise audit software.

# ================================================== 13. IMPORTANT ENGINEERING REQUIREMENTS

Before coding:

1. Inspect the entire existing project.
2. Identify the frontend framework.
3. Identify backend/data layer.
4. Identify routing.
5. Identify existing models.
6. Identify existing persistence.
7. Identify existing document upload system.
8. Identify existing report/export functionality.
9. Identify reusable components.
10. Identify existing bugs.

Then implement the features using the existing architecture.

DO NOT rewrite the application unnecessarily.

Avoid duplicated logic.

Create reusable components for:

- StatusBadge
- AuditTable
- EmptyState
- ReviewPoint
- SignOffPanel
- VersionHistory
- HashDisplay
- ReportViewer
- WorkingPaperEditor

# ================================================== 14. TEST EVERYTHING

After implementation, test the complete workflow:

Create Client → Create Engagement → Upload Document → Create Working Paper → Add
Procedure → Attach Evidence → Add Finding → Add Review Point → Resolve Review
Point → Reviewer Approval → Sign Off → Lock → Generate Report → Validate Report
→ Approve Report → Lock Report → Export PDF → Export DOCX

Also test:

- Refresh persistence
- Empty states
- Invalid forms
- Duplicate records
- Locked record editing prevention
- Hash generation
- Versioning
- Search/filter
- Navigation
- Dashboard counters

Fix all errors found during testing.

# ================================================== FINAL REQUIREMENT

Do not simply make the screens look complete.

Make Working Papers and Reports FUNCTIONAL, PERSISTENT, CONNECTED to the rest of
FinAuditPro, and suitable for a real audit workflow.

After implementation, give me:

1. What you changed
2. Files/components changed
3. Database/data-model changes
4. New workflows implemented
5. Export functionality implemented
6. Tests performed
7. Any remaining limitations

Do not stop after creating the UI. Continue until the complete workflow works
end-to-end.

PROMPT 5 : You are working on my existing FinAuditPro application.

I need you to FIX and COMPLETE the "Working Papers" and "Reports" modules shown
in the attached screenshots.

IMPORTANT:

- Do NOT redesign the entire application.
- Preserve the existing FinAuditPro visual language, sidebar, top navigation,
  typography, spacing, colors, borders, buttons, cards, and table styling.
- Do not create a fake/static UI. These modules must actually work.
- Inspect the existing codebase first and understand the current architecture,
  data models, routing, state management, and persistence before making changes.
- Reuse existing components and utilities wherever possible.
- Do not break any existing modules.

==================================================

1. WORKING PAPERS MODULE ==================================================

Current screen contains:

"Configurable Working Paper Index Guidance"

Stats:

- Total Working Papers
- Open Review Points
- Signed Off & Locked

Table:

- Ref Code
- Title
- Audit Area
- Status
- Preparer
- Open Points
- Content Hash / Lock
- Actions

There is a "+ New Working Paper" button.

IMPLEMENT THIS AS A REAL WORKING-PAPER SYSTEM.

New Working Paper should allow the auditor to create a working paper with:

- Reference Code
- Title
- Audit Area
- Financial Year
- Engagement
- Prepared By
- Reviewer
- Objective
- Audit Assertion
- Risk
- Materiality
- Procedures
- Evidence/Documents
- Findings
- Conclusion
- Review Notes
- Status

Suggested statuses:

Draft Prepared Under Review Review Points Approved Signed Off Locked

Required functionality:

1. Create working paper.
2. Edit working paper.
3. Open/view working paper.
4. Save draft.
5. Add audit procedures.
6. Add evidence/document references.
7. Add findings.
8. Add review points.
9. Assign reviewer.
10. Mark review points as resolved.
11. Reviewer approval.
12. Sign-off workflow.
13. Lock signed-off working paper.
14. Prevent modification after locking.
15. Show audit trail/history.
16. Generate deterministic content hash when signed/locked.
17. Display lock status and hash in the table.
18. Search/filter/sort working papers.
19. Open Points counter must update automatically.
20. Signed & Locked counter must update automatically.
21. Total Working Papers must update automatically.

Working papers must be linked to: Client → Engagement → Financial Year → Audit
Area.

Evidence added to a working paper should reference actual uploaded documents
from the Documents module rather than creating duplicate files.

# ================================================== 2. WORKING PAPER DETAIL VIEW

Create a professional audit working-paper detail page.

Use a layout similar to professional audit software:

Header:

- Ref Code
- Working Paper Title
- Status badge
- Prepared By
- Reviewer
- Engagement
- Financial Year

Sections/tabs:

Overview Audit Objective Risk & Assertions Audit Procedures Evidence Findings
Review Points Conclusion Sign-Off Audit Trail

For each audit procedure provide:

- Procedure ID
- Description
- Expected Result
- Actual Result
- Evidence
- Performed By
- Performed Date
- Result: Pass / Fail / Exception / N/A

For findings provide:

- Finding ID
- Title
- Description
- Criteria
- Condition
- Cause
- Effect
- Recommendation
- Severity
- Management Response
- Status

# ================================================== 3. REPORTS MODULE

Current Reports screen contains:

"Statutory Report Text & Legal Signature Honesty"

Stats:

- Total Reports
- Draft Reports (Watermarked)
- Approved Reports

Table:

- Report Title
- Type
- Status
- Data As-Of
- Generated By
- Content Hash
- Actions

There is a "+ Generate New Report" button.

TURN THIS INTO A REAL REPORT GENERATION MODULE.

Generate New Report should support:

- Statutory Audit Report
- CARO 2020 Report
- Form 3CD / Tax Audit Report
- GST Reconciliation Report
- Audit Findings Report
- Management Letter
- Working Paper Summary
- Financial Statement Audit Summary
- Compliance Report

The report generator must pull data from the actual application.

DO NOT hardcode report values.

Data should come from:

Clients Audit Firms Engagements Documents Financial Statements GST
Reconciliation Statutory Compliance Audit Matrix AI Audit Findings Working
Papers

# ================================================== 4. REPORT GENERATION WORKFLOW

Create a proper workflow:

Select Client ↓ Select Engagement ↓ Select Financial Year ↓ Select Report Type ↓
Select Data Sources ↓ Review Data ↓ Generate Draft ↓ Validate ↓ Approve ↓ Lock ↓
Export

Before generation show:

- Client
- Engagement
- Financial Year
- Report Type
- Data As-Of date
- Number of evidence sources
- Number of findings
- Number of working papers
- Compliance status
- Materiality
- Reviewer

# ================================================== 5. REPORT DETAIL PAGE

Create a professional report viewer/editor.

Header:

- Report title
- Report type
- Client
- Financial Year
- Status
- Data As-Of
- Generated By
- Content Hash

Sections:

Executive Summary Scope Audit Approach Materiality Key Findings Risk Assessment
Statutory Compliance GST Reconciliation Financial Statement Observations CARO
2020 Form 3CD Management Recommendations Conclusion Sign-Off

Provide:

- Edit Draft
- Save
- Preview
- Validate
- Approve
- Generate PDF
- Generate DOCX
- Print
- Lock

Draft reports MUST display a clear "DRAFT" / "WATERMARKED" state.

Approved reports should be clearly distinguished from drafts.

Locked reports must become immutable.

# ================================================== 6. REPORT INTEGRITY

Implement report versioning.

Every generated report should have:

- Version
- Generated timestamp
- Generated by
- Source data version
- Content hash
- Approval status
- Lock timestamp

When a report is approved/locked:

Generate a deterministic SHA-256 hash based on the report content and relevant
source/version metadata.

If the report content changes:

- Create a new version.
- Never silently overwrite the previous approved version.

Show version history.

# ================================================== 7. LEGAL / STATUTORY SAFETY

Do NOT fabricate statutory conclusions.

Clearly distinguish:

- Application-generated analysis
- Auditor judgment
- Verified statutory information
- Unverified guidance

If statutory sources are not verified, display an appropriate warning.

Never present AI-generated text as an officially verified statutory conclusion.

Reports must preserve an audit trail of how conclusions were generated.

# ================================================== 8. PDF / DOCX EXPORT

Implement actual export functionality.

PDF should contain:

- Firm name/logo
- Client name
- Engagement
- Financial Year
- Report title
- Report content
- Findings
- Conclusions
- Sign-off
- Version
- Data As-Of
- Content Hash

DOCX should contain equivalent structured content.

Do not create empty placeholder files.

# ================================================== 9. DASHBOARD INTEGRATION

Update the Dashboard automatically.

Dashboard should reflect:

- Number of Working Papers
- Open Review Points
- Signed-Off Working Papers
- Draft Reports
- Approved Reports
- Open Findings
- High-Risk Findings
- Compliance exceptions

All numbers must come from the same underlying data source.

No duplicated hardcoded state.

# ================================================== 10. PERSISTENCE

Because FinAuditPro is designed as an offline-first audit operating system:

- Data must persist locally.
- Refreshing the application must not lose data.
- Closing/reopening the application must preserve data.
- Use the existing persistence layer if one already exists.
- If necessary, improve the existing local database/storage architecture.
- Maintain deterministic IDs.
- Maintain audit history.

# ================================================== 11. UX REQUIREMENTS

The application currently has too many empty states.

Replace meaningless empty tables with useful empty-state messages such as:

"No working papers yet" "Create your first working paper to begin documenting
audit evidence."

" No reports generated yet" "Generate a report from your engagement data."

Buttons should work.

Forms should validate input.

Show success/error notifications.

Use confirmation dialogs for:

- Delete
- Approve
- Sign-off
- Lock

Do not allow accidental destructive actions.

# ================================================== 12. VISUAL DESIGN

Keep the existing FinAuditPro design.

Use:

- White/light-gray workspace
- Blue primary actions
- Thin borders
- Compact professional tables
- Small audit-status badges
- Clean typography
- Consistent spacing
- Professional accounting/audit-software appearance

Do NOT introduce:

- Huge cards
- Excessive gradients
- Neon colors
- Consumer-app styling
- Unnecessary animations
- Decorative UI that reduces audit usability

The UI should feel like professional enterprise audit software.

# ================================================== 13. IMPORTANT ENGINEERING REQUIREMENTS

Before coding:

1. Inspect the entire existing project.
2. Identify the frontend framework.
3. Identify backend/data layer.
4. Identify routing.
5. Identify existing models.
6. Identify existing persistence.
7. Identify existing document upload system.
8. Identify existing report/export functionality.
9. Identify reusable components.
10. Identify existing bugs.

Then implement the features using the existing architecture.

DO NOT rewrite the application unnecessarily.

Avoid duplicated logic.

Create reusable components for:

- StatusBadge
- AuditTable
- EmptyState
- ReviewPoint
- SignOffPanel
- VersionHistory
- HashDisplay
- ReportViewer
- WorkingPaperEditor

# ================================================== 14. TEST EVERYTHING

After implementation, test the complete workflow:

Create Client → Create Engagement → Upload Document → Create Working Paper → Add
Procedure → Attach Evidence → Add Finding → Add Review Point → Resolve Review
Point → Reviewer Approval → Sign Off → Lock → Generate Report → Validate Report
→ Approve Report → Lock Report → Export PDF → Export DOCX

Also test:

- Refresh persistence
- Empty states
- Invalid forms
- Duplicate records
- Locked record editing prevention
- Hash generation
- Versioning
- Search/filter
- Navigation
- Dashboard counters

Fix all errors found during testing.

# ================================================== FINAL REQUIREMENT

Do not simply make the screens look complete.

Make Working Papers and Reports FUNCTIONAL, PERSISTENT, CONNECTED to the rest of
FinAuditPro, and suitable for a real audit workflow.

After implementation, give me:

1. What you changed
2. Files/components changed
3. Database/data-model changes
4. New workflows implemented
5. Export functionality implemented
6. Tests performed
7. Any remaining limitations

Do not stop after creating the UI. Continue until the complete workflow works
end-to-end.

PROMPT 6 : You are a senior full-stack architect, product engineer, UI/UX
designer, audit-domain systems engineer, and QA engineer.

I am building an application called:

FINAUDITPRO “Offline-First Audit Operating System”

The current application is a Python desktop application running on macOS ARM64.
The UI already exists, but many screens are empty/static and several workflows
are incomplete.

I want you to inspect the existing codebase FIRST and then implement the
application properly.

IMPORTANT: DO NOT rebuild the application blindly. DO NOT remove existing
functionality. DO NOT create fake/demo-only buttons. DO NOT replace working
modules unnecessarily. DO NOT use placeholder data where real application state
should be used. Preserve the existing architecture where practical, but refactor
it when necessary for reliability and maintainability.

==================================================

1. CURRENT APPLICATION ==================================================

The application currently contains these major modules:

WORKSPACE

- Dashboard
- Audit Firms
- Clients
- Engagements

FINANCIAL

- Documents
- Financial Statements
- GST Reconciliation
- Statutory Compliance

ANALYSIS

- Audit Matrix
- AI Copilot

AUDIT WORKFLOW

- Working Papers
- Reports

SYSTEM

- File Archival
- Roll-Forward
- Settings

The application also has:

- Offline-first architecture
- Local AI/LLM integration
- Evidence/document processing
- Audit findings
- Working papers
- Reports
- Engagement management
- Audit materiality
- SA 510 opening balance tie-out
- File archival
- Roll-forward
- AI audit analysis

# ================================================== 2. MAIN PROBLEM

The current UI looks like a prototype.

Several pages show:

- 0 records
- empty tables
- buttons without meaningful workflows
- configuration displayed as static text
- empty evidence panels
- empty findings panels
- incomplete audit workflows
- no realistic seeded engagement
- weak connections between modules

I want you to transform this into a cohesive, production-style application where
the modules actually communicate with each other.

The application must behave like a real audit engagement management and audit
execution system.

# ================================================== 3. CORE PRINCIPLE

Everything should revolve around:

FIRM → CLIENT → ENGAGEMENT → PERIOD → DOCUMENTS → FINANCIAL DATA → AUDIT AREAS →
PROCEDURES → EVIDENCE → FINDINGS → WORKING PAPERS → REVIEW → REPORT → ARCHIVE

Create a proper relational/domain model around this lifecycle.

No isolated screens.

Every relevant screen must consume and update shared application state.

# ================================================== 4. DATABASE / PERSISTENCE

Implement proper local persistence.

Prefer SQLite for structured data.

Create a clean database layer/repository layer.

At minimum model:

- users
- audit_firms
- clients
- engagements
- engagement_periods
- financial_statements
- accounts
- trial_balance
- documents
- document_versions
- evidence
- audit_areas
- audit_procedures
- audit_programs
- working_papers
- findings
- finding_evidence
- materiality_calculations
- review_points
- reports
- report_versions
- archive_records
- roll_forward_records
- statutory_compliance_items
- gst_reconciliations
- ai_analysis_runs
- audit_logs
- application_settings

Every important object needs:

- UUID/unique ID
- created_at
- updated_at
- status where applicable
- audit trail where appropriate

Use migrations/versioning for the database schema.

# ================================================== 5. SEED A REALISTIC DEMO ENGAGEMENT

The application should NOT open to an entirely empty system.

Create a clearly marked DEMO engagement that demonstrates the entire workflow.

Example:

Client: “ABC Manufacturing Private Limited”

Financial Year: FY 2025-26

Currency: INR

Industry: Manufacturing

Populate realistic but clearly synthetic data:

- Trial balance
- Revenue
- Purchases
- Inventory
- Fixed assets
- Receivables
- Payables
- Cash/bank
- Loans
- Related parties
- GST data
- statutory compliance items
- audit documents
- evidence
- audit findings
- review points
- working papers

Make it obvious that this is synthetic/demo data.

Provide a way to reset/delete demo data.

# ================================================== 6. DASHBOARD

Build a real engagement dashboard.

Show:

- Active engagements
- Current client
- Financial year
- Audit status
- Overall materiality
- Performance materiality
- Clearly trivial threshold
- Total audit areas
- Completed procedures
- Pending procedures
- Evidence collected
- Findings
- High/Critical findings
- Open review points
- Working papers pending review
- Report status
- Archival status

Add useful visual indicators.

Clicking a metric should navigate to the relevant module.

# ================================================== 7. ENGAGEMENT MANAGEMENT

Implement:

Create Engagement Edit Engagement Open Engagement Close Engagement Reopen
Engagement Archive Engagement

Engagement fields should include:

- Client
- Financial year
- Engagement type
- Audit period
- Partner
- Manager
- Senior
- Team
- Status
- Reporting framework
- Applicable standards
- Materiality status

Implement proper lifecycle:

PLANNING → FIELDWORK → REVIEW → REPORTING → COMPLETED → ARCHIVED

Prevent invalid transitions.

Require confirmation for destructive operations.

# ================================================== 8. AUDIT MATERIALITY

The SA 320 Materiality screen must become functional.

Allow selection of benchmark:

- Revenue
- Profit Before Tax
- Total Assets
- Net Assets
- Expenses
- User-defined benchmark

Allow benchmark amount input.

Allow percentage selection/input.

Calculate:

Overall Materiality Performance Materiality Clearly Trivial Threshold

Default calculations may use:

OM = Benchmark × Selected %

PM = OM × 75%

CTT = OM × 5%

BUT:

Do not represent these percentages as mandatory statutory rules.

Clearly label them as configurable auditor judgments / suggested defaults.

Allow users to override the percentages.

Store every materiality version.

Display:

Version Benchmark Amount Percentage OM PM CTT Prepared By Date Reason for
Revision

Keep a complete revision history.

# ================================================== 9. AI AUDIT COPILOT

The AI Copilot should become one of the strongest features.

The application already indicates local AI:

LM Studio: http://localhost:1234

Model: qwen-based local model

Embedding: nomic-embed-text

Maintain offline-first behavior.

AI should NEVER silently send audit evidence to external cloud APIs.

Cloud AI must remain opt-in.

Implement:

Document ingestion Text extraction Chunking Embedding Local vector search RAG
Prompt templates Evidence citations Finding generation Risk analysis Anomaly
detection

The AI must distinguish:

FACT INFERENCE RECOMMENDATION MISSING EVIDENCE

Never fabricate audit evidence.

Every AI-generated finding must reference source evidence.

# ================================================== 10. AI PROMPT LIBRARY

Implement functional audit prompts such as:

CARO 2020 Inventory SA 188 Related Party SA 185/186 Loans SA 240 Revenue Anomaly
Form 3CD Clause 44 SA 500 Audit Evidence

Add more:

SA 315 Risk Assessment SA 330 Responses to Assessed Risks SA 450 Misstatements
SA 505 External Confirmations SA 520 Analytical Procedures SA 530 Sampling SA
550 Related Parties SA 560 Subsequent Events SA 570 Going Concern SA 580 Written
Representations SA 700 Reporting

Each prompt should:

1. Identify relevant evidence
2. Analyze evidence
3. Identify exceptions
4. Assign risk
5. Explain reasoning
6. Cite evidence
7. Suggest audit procedures
8. Identify missing evidence
9. Create a structured finding when appropriate

# ================================================== 11. AUDIT FINDINGS

Create a unified findings system.

Finding fields:

- Finding ID
- Engagement
- Audit area
- Title
- Description
- Condition
- Criteria
- Cause
- Effect
- Recommendation
- Risk
- Severity
- Financial impact
- Evidence
- Management response
- Auditor conclusion
- Status
- Owner
- Due date

Severity:

LOW MEDIUM HIGH CRITICAL

Status:

OPEN IN_PROGRESS RESOLVED ACCEPTED CLOSED

The AI Copilot should be able to create a finding draft, but a human must
approve it.

# ================================================== 12. AUDIT MATRIX

Create a real audit matrix.

Columns:

Audit Area Risk Assertion Risk Rating Control Procedure Sample Size Evidence
Status Finding Reviewer Conclusion

Allow filtering by:

- Risk
- Status
- Audit area
- Assertion
- Reviewer

Show completion percentage.

# ================================================== 13. WORKING PAPERS

Working papers must become functional.

Allow:

Create Edit Attach evidence Add procedures Add conclusions Add review notes
Submit for review Review Return for modification Approve Lock

Working paper status:

DRAFT PREPARED UNDER_REVIEW REVIEW_NOTES APPROVED LOCKED

Once locked, prevent unauthorized modification.

Show:

Ref Code Title Audit Area Status Preparer Reviewer Open Points Content Hash Lock
Status

# ================================================== 14. REPORTING

The Reports screen should generate real reports from engagement data.

Report types:

- Audit Summary
- Findings Report
- Management Letter
- Working Paper Completion Report
- Evidence Summary
- Statutory Compliance Report
- GST Reconciliation Report
- CARO Report
- Audit Completion Report

Reports should contain:

- Client
- Financial year
- Report date
- Scope
- Significant findings
- Materiality
- Audit completion status
- Open issues
- Conclusions

Implement report versioning.

Draft reports must clearly show:

DRAFT / WATERMARKED

Approved reports should be immutable/versioned.

Do not falsely claim statutory approval.

# ================================================== 15. WORKING PAPER → REPORT CONNECTION

Reports must pull information from:

- Working papers
- Findings
- Evidence
- Materiality
- Audit matrix
- Compliance modules

Do not make report data manually duplicated.

If a finding changes, the next report version should reflect it.

# ================================================== 16. FILE ARCHIVAL

Implement real archival behavior.

When an engagement is completed:

1. Verify required working papers
2. Verify unresolved review points
3. Verify report status
4. Calculate content hashes
5. Create immutable archive record
6. Encrypt archive where appropriate
7. Record archive timestamp
8. Record retention date
9. Prevent normal modification

Display:

Archive ID Report Date Assembly Deadline Retain Until Encrypted Content Hash

Use configurable retention settings.

Do not hard-code retention periods as statutory law.

Clearly identify guidance/configuration vs legal requirements.

# ================================================== 17. ROLL-FORWARD

Make SA 510 opening balance tie-out functional.

Compare:

Prior Closing DR Prior Closing CR

against:

Current Opening DR Current Opening CR

For every account.

Show:

Account Code Account Name Opening DR Opening CR Prior Closing DR Prior Closing
CR Difference Tie-Out Status

Statuses:

MATCHED MISMATCH MISSING_PRIOR MISSING_CURRENT REVIEW_REQUIRED

Require auditor confirmation before finalizing.

Provide:

“Confirm Tie-Out (Auditor)”

Record:

User Timestamp Confirmation status Comments

# ================================================== 18. GST RECONCILIATION

Implement:

Books GST GSTR data Input Tax Credit Output Tax Differences Potential mismatches

Show:

Taxable Value CGST SGST IGST Cess Books Amount Return Amount Difference Status

Automatically identify anomalies.

# ================================================== 19. STATUTORY COMPLIANCE

Create a configurable compliance checklist.

Do NOT present configurable guidance as guaranteed statutory law.

Each compliance item should have:

- Requirement
- Applicability
- Evidence
- Due date
- Status
- Responsible person
- Reviewer
- Notes
- Source/reference
- Verification status

Support:

Applicable Not Applicable Pending Completed Exception

# ================================================== 20. DOCUMENT MANAGEMENT

Documents should be first-class objects.

Allow:

Upload Import Preview Rename Version Tag Categorize Attach to audit area Attach
to working paper Attach to finding Search Archive

Document categories:

Bank GST Tax Ledger Trial Balance Invoices Payroll Loans Related Parties
Inventory Fixed Assets Legal Contracts Board Minutes Other

Generate hashes for document integrity.

# ================================================== 21. SEARCH

The global search bar should actually work.

Search across:

Clients Engagements Documents Evidence Working Papers Findings Reports Audit
Procedures

Provide keyboard shortcut:

⌘K

Search should return categorized results.

# ================================================== 22. SETTINGS

Turn the Settings page into a real configuration page.

Sections:

Application Database Local AI LLM Embeddings Security Encryption Cloud AI Audit
Defaults Materiality Defaults Retention Compliance Backup

For Local AI:

Base URL Model Embedding Model Connection Test

Add:

“Test Local AI Connection”

Show:

CONNECTED DISCONNECTED ERROR

Do not expose secrets in plaintext.

# ================================================== 23. SYSTEM DIAGNOSTICS

Implement the “Run System Diagnostics” button.

Check:

- Database
- File storage
- Permissions
- Encryption
- Local AI endpoint
- Embedding model
- Vector index
- Disk space
- Configuration
- Migration status

Return a clear diagnostic report.

# ================================================== 24. SECURITY

Implement strong local security architecture.

Include:

- Role-based access
- Audit logs
- Secure configuration
- File hashing
- Immutable records where required
- Confirmation dialogs
- Safe deletion
- Backup/restore
- Encryption support

Roles:

ADMIN PARTNER MANAGER SENIOR ASSOCIATE REVIEWER

Enforce permissions in the backend/domain layer, not only in UI.

# ================================================== 25. AUDIT TRAIL

Every sensitive action should create an audit log.

Examples:

Created engagement Changed materiality Uploaded document Created finding
Modified finding Approved working paper Reviewed working paper Generated report
Approved report Closed engagement Archived engagement Reopened engagement

Log:

Timestamp User Action Object Previous Value New Value Reason where applicable

# ================================================== 26. UI/UX

Keep the existing clean FinAuditPro visual identity.

Maintain:

- White/light background
- Blue primary accent
- Dark navy text
- Compact professional layout
- Sidebar navigation
- Cards
- Tables
- Status badges

Improve:

- Empty states
- Loading states
- Error states
- Success notifications
- Confirmation dialogs
- Breadcrumbs
- Filters
- Pagination
- Tooltips
- Responsive layouts

Avoid excessive rounded cards.

Avoid unnecessary decorative UI.

The application should look like professional audit software, not a generic AI
dashboard.

# ================================================== 27. EMPTY STATES

Never leave important screens as giant blank white areas.

Instead show meaningful empty states.

Example:

“No engagements yet”

[Create Engagement]

or:

“No audit findings”

“Run an audit analysis or create a finding manually.”

Every empty screen should explain:

- what is missing
- why it matters
- what action the user can take

# ================================================== 28. ERROR HANDLING

Every operation must have proper error handling.

Never silently fail.

Show actionable errors.

Example:

“Unable to connect to local LLM at localhost:1234.

Check that LM Studio is running and the configured model is loaded.”

Do not expose Python stack traces to normal users.

Log detailed errors internally.

# ================================================== 29. OFFLINE-FIRST

The application must work without internet.

Core functionality must NOT require cloud services.

Offline functionality:

- Database
- Documents
- Evidence
- Audit procedures
- Findings
- Working papers
- Reports
- Archival
- Roll-forward
- GST reconciliation
- AI when local model is available

Cloud AI should be an explicit opt-in feature.

# ================================================== 30. DATA INTEGRITY

Use transactions for multi-step operations.

Prevent orphan records.

Use foreign keys.

Validate input.

Use deterministic calculations.

Never let UI state become the source of truth.

Database/domain state must be authoritative.

# ================================================== 31. TESTING

Create automated tests.

At minimum test:

- Materiality calculation
- Materiality revisions
- SA 510 tie-out
- Finding lifecycle
- Working paper lifecycle
- Report generation
- Engagement lifecycle
- Archive creation
- Roll-forward
- GST reconciliation
- Permissions
- Database migrations
- AI evidence citation
- Search

Also test invalid states.

# ================================================== 32. DEMO WORKFLOW

After implementation, I should be able to demonstrate this complete workflow:

1. Open FinAuditPro
2. Select demo client
3. Open FY 2025-26 engagement
4. View dashboard
5. Review materiality
6. Review trial balance
7. Review audit matrix
8. Review documents
9. Run AI audit analysis
10. Detect an anomaly
11. Create finding
12. Attach evidence
13. Create working paper
14. Submit working paper
15. Add reviewer note
16. Resolve review point
17. Approve working paper
18. Generate audit report
19. Review report
20. Approve report
21. Close engagement
22. Run SA 510 tie-out
23. Archive engagement
24. View archive hash
25. Roll-forward engagement into next period

Every step should use real persisted data.

# ================================================== 33. IMPORTANT ACCOUNTING/AUDIT SAFETY

This software is an audit workflow and decision-support system.

It must NOT pretend that software-generated judgments are automatically
compliant with auditing standards.

Clearly distinguish:

- statutory requirement
- professional guidance
- configurable firm policy
- auditor judgment
- AI recommendation

AI must never claim:

“Compliant”

unless the application has an explicit verified rule/evidence basis.

Use wording such as:

“Potential exception identified” “Suggested procedure” “Requires auditor
judgment” “Evidence insufficient” “Not independently verified”

# ================================================== 34. CODE QUALITY

Use clean architecture.

Separate:

UI Application services Domain models Repositories Database AI services Document
processing Reporting Security Configuration

Avoid huge monolithic files.

Avoid duplicated business logic.

Use typed models where practical.

Use dependency injection where useful.

Keep UI event handlers thin.

Business logic belongs in services/domain modules.

# ================================================== 35. IMPORTANT IMPLEMENTATION PROCESS

Before changing anything:

1. Inspect the entire repository.
2. Identify the framework.
3. Identify the entry point.
4. Identify database implementation.
5. Identify existing models.
6. Identify existing navigation.
7. Identify existing AI integration.
8. Identify incomplete/TODO functionality.
9. Identify duplicate code.
10. Identify current persistence behavior.

Then create a short implementation plan.

Then implement in logical phases.

Do not merely describe what should be done.

Actually modify the application.

After implementation:

- Run the application
- Run tests
- Fix runtime errors
- Fix UI errors
- Verify navigation
- Verify database persistence
- Verify demo workflow
- Verify local AI configuration
- Verify all buttons
- Verify empty states
- Verify destructive-action confirmations

# ================================================== 36. FINAL ACCEPTANCE CRITERIA

The project is NOT finished if:

- pages only look good but don't work
- buttons are fake
- data disappears after restart
- modules don't share data
- AI findings have no evidence
- reports contain hard-coded data
- archive records are fake
- materiality is static
- roll-forward is static
- working papers are static
- settings are static
- search does nothing
- diagnostics do nothing

The project IS finished when FinAuditPro behaves like a coherent offline-first
audit operating system with a complete end-to-end engagement lifecycle.

Prioritize FUNCTIONALITY + DATA INTEGRITY + AUDIT TRACEABILITY first, then
polish the UI.

Start by inspecting the existing project and provide the implementation plan
before making changes.
