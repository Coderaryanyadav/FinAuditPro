# FinAuditPro - Design Specification Document
**Single Source of Truth for Design System, Component Architecture, & UI/UX Standards**

---

# 1. Project Overview

### Purpose
FinAuditPro is an enterprise-grade, offline-first desktop AI financial auditing software designed specifically for Chartered Accountants (CAs), audit teams, and financial consultants. The software automates complex financial verification, anomaly detection, GST reconciliation, tax compliance monitoring, working paper generation, and audit report drafting using embedded local AI models.

### Target Users
* **Chartered Accountants (CAs)** & Senior Partners requiring audit oversight and compliance sign-offs.
* **Audit Managers & Associates** conducting day-to-day ledger verification, document reviews, and GST cross-matching.
* **Financial Risk & Compliance Analysts** inspecting enterprise risk scores, fraud indicators, and internal control gaps.

### Product Type
* **Form Factor**: Native Desktop Application Window (1440 × 900 baseline resolution) framed with standard desktop titlebar window controls (Minimize, Maximize/Restore, Close).
* **Architecture**: Hybrid Python Desktop GUI (PySide6 / Qt Designer) rendering high-performance Web-based responsive layouts.

### Major Modules
1. **Authentication & Initialization**: Splash Screen, User Login & Offline Auth.
2. **Core Workspace**: Executive Audit Dashboard, Client Portfolio Management.
3. **Document & Data Processing**: Multi-format Document Upload, OCR Data Extraction Engine.
4. **AI Audit Intelligence**: Interactive Document AI Analysis, Copilot Assistance.
5. **Compliance & Verification**: GST Verification & Matching, Statutory Compliance Monitor.
6. **Risk Assessment**: Portfolio & Client Risk Matrix Analysis.
7. **Audit Reporting**: CA-Standard Working Paper Generator, Final Audit Report Builder.
8. **System Administration**: Audit Log History, User Profile, System Settings.

### Main Pages (15 Screen Inventory)
1. `finauditpro_splash_screen.html` (System Loading & Environment Check)
2. `finauditpro_login.html` (Professional Desktop Authentication)
3. `finauditpro_dashboard.html` (Executive Summary & Portfolio Overview)
4. `finauditpro_client_management.html` (Directory & Client Profile Operations)
5. `finauditpro_document_upload.html` (File Dropzone & Category Mapper)
6. `finauditpro_ocr_processing.html` (Text Extraction & Field Parsing Workspace)
7. `finauditpro_ai_audit_analysis.html` (Split-Pane Document AI Intelligence & Evidence Inspector)
8. `finauditpro_compliance_monitoring.html` (Rule-Based Statutory & Tax Checklist)
9. `finauditpro_risk_analysis.html` (Anomaly Detection & Heatmap Dashboard)
10. `finauditpro_report_generation.html` (Audit Opinion & Executive Summary Builder)
11. `finauditpro_audit_history.html` (Immutable Action Audit Trail & Activity Logs)
12. `finauditpro_ai_assistant.html` (Embedded AI Chat & Document Query Interface)
13. `finauditpro_profile.html` (CA Practitioner Profile & Credentials)
14. `finauditpro_settings.html` (Local AI Model, Storage, & Application Preferences)
15. `finauditpro_gst_verification.html` (GSTR-2B vs 3B Reconciliation Workspace)

### Navigation Structure
* **Application Titlebar**: Top 32px frame with window icon, app title (`FinAuditPro`), and native window controls.
* **Left Fixed Sidebar (260px)**:
  * *Header*: Shield + Bar Graph Brand Logo (`FinAuditPro Smart Audit Assistant`).
  * *Main Menu Group*: Dashboard, Client Management, Upload Documents.
  * *Audit Workspace Group*: AI Audit Analysis, Financial Statements, GST Verification, Compliance Monitoring, Risk Analysis.
  * *Settings & Logs Group*: Reports, Audit History, Settings.
  * *Footer*: Active User Profile Card (`CA User`, `Chartered Accountant`).
* **Main Content Area**: Top 64px Header bar + Fluid Scrollable Body Workspace.

---

# 2. Information Architecture

```
FinAuditPro System Architecture
 ├── Desktop Application Chrome (Window Titlebar, Controls: Min, Max, Close)
 │
 ├── Authentication & Setup Flow
 │    ├── Splash Screen (License Check, Local DB Load, AI Model Warmup)
 │    └── Login Screen (Left: Feature Highlights & Illustration; Right: Auth Form, Remember Me)
 │
 └── Main Desktop Shell (Fixed Sidebar 260px + Header 64px + Workspace)
      │
      ├── Executive Dashboard
      │    ├── Search Bar & System Utilities (Theme, Help, Notifications, User Badge)
      │    ├── Welcome Greeting Header ("Good Morning, Auditor")
      │    ├── 4 Metric Stat Cards (Total Clients, Completed Audits, Pending Reviews, High Risk Cases)
      │    ├── AI Audit Summary Card (Portfolio Risk Score 24/100, Compliance Score 92%, Recent AI Findings)
      │    ├── Audit Progress Graph (Line Chart - Monthly Trends)
      │    ├── Risk Distribution Chart (Doughnut Chart - Low, Medium, High Risk Breakdown)
      │    └── Recent Audit Projects Table (Client, Type, Status Badge, Risk Badge, Actions)
      │
      ├── Client Management
      │    ├── Header Action Toolbar (Search, Filter by Status, Grid/Table Toggle, "Add Client" Primary Button)
      │    ├── Client Directory Grid / Table View
      │    │    └── Client Item Card (Logo/Initials, Client Name, GSTIN, Industry, Risk Level, Active Audits)
      │    └── Client Detail Drawer / Modal (Engagement History, Financial Records, Compliance Status)
      │
      ├── Upload Documents & OCR Processing
      │    ├── Drag-and-Drop Dropzone (Supports PDF, XLSX, CSV, PNG, JPG)
      │    ├── Categorization Selector (Balance Sheet, P&L, GST Returns, TDS, Bank Statements)
      │    ├── Upload Queue & Batch Processing Table
      │    └── OCR Processing Workspace (Document Image Preview + Extracted Text Fields Table + Confidence Scores)
      │
      ├── AI Audit Analysis & Copilot
      │    ├── Split View Interface
      │    │    ├── Left Panel (Document Viewer with Highlighted Bounding Boxes)
      │    │    └── Right Panel (AI Anomaly Feed, Flagged Inconsistencies, Citation Links)
      │    └── Embedded AI Assistant Chat (Quick Query Prompts, Document Q&A, Evidence Verification)
      │
      ├── Verification & Compliance
      │    ├── GST Reconciliation (GSTR-1 vs GSTR-3B Mismatch Table, Tax Difference Calculator)
      │    └── Compliance Monitoring (Statutory Due Dates, Tax Audit Checklist, Auto-Verification Badges)
      │
      ├── Risk Analysis
      │    ├── Risk Level Summary Cards (High, Medium, Low Counters)
      │    ├── Anomaly Heatmap / Breakdown
      │    └── Risk Finding Cards (Issue Title, Financial Impact Amount, Evidence Excerpt, AI Recommendation)
      │
      ├── Reporting & Working Papers
      │    ├── Working Paper Generator (CA Standard: Objective, Scope, Procedure, Observations, Conclusion)
      │    └── Report Generator (Audit Opinion Selector, Executive Summary, Export PDF / Word)
      │
      └── System & Governance
           ├── Audit History (Immutable Event Logs, User Action Records, Timestamped Diff)
           ├── CA Profile (Membership No, Firm Details, Security Keys)
           └── Settings (Local LLM Engine Selection, Ollama Host, Database Storage Path, Theme)
```

---

# 3. Layout System

### Desktop Layout Specs
* **Target Desktop Resolution**: Fixed window bounding target `1440px × 900px` (Scalable fluid flex layout `100vw × 100vh`).
* **Application Frame**: Full height `h-screen`, full width `w-screen`, `flex flex-row`, `overflow-hidden`.
* **Sidebar**:
  * Width: Fixed `260px` (`w-[260px]`, `flex-shrink-0`).
  * Height: `100vh` (`h-full`).
  * Border: `border-r border-slate-200`.
  * Background: `#FFFFFF`.
* **Header Bar**:
  * Height: Fixed `64px` (`h-16`, `flex-shrink-0`).
  * Padding: Horizontal `px-6 lg:px-8`.
  * Border: `border-b border-slate-200`.
  * Background: `#FFFFFF`.
* **Main Content Area**:
  * Flex behavior: `flex-1 flex flex-col min-w-0 overflow-hidden bg-slate-50`.
  * Scroll container: `flex-1 overflow-y-auto p-6 lg:p-8`.

### Grid & Containers
* **Container Max-Widths**: `max-w-7xl` for standard pages, `w-full` for data-dense tables and split-pane views.
* **Standard Grid Columns**: 12-column grid (`grid-cols-12`) used for dashboard widgets.
  * Stat Cards: `grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6`.
  * Split Layouts: `col-span-4` (Left AI Summary) + `col-span-5` (Center Graph) + `col-span-3` (Right Chart).
  * Dual-Pane Workspaces: `w-1/2` (Document Preview) + `w-1/2` (Analysis Panel).
* **Gaps**: `gap-4` (16px) for tight controls, `gap-6` (24px) for cards, `gap-8` (32px) for major sections.

### Responsive Behavior Rules
* **Desktop (≥ 1280px)**: Full 260px sidebar visible, 4-column stat cards, 12-column dashboard layout active.
* **Laptop / Tablet Landscape (1024px - 1279px)**:
  * Stat cards break to 2 columns (`md:grid-cols-2`).
  * Dashboard split panels collapse to stacked 1-column layouts (`col-span-1 lg:col-span-12`).
* **Tablet Portrait (768px - 1023px)**:
  * Sidebar collapses to overlay or hidden mobile drawer.
  * Main header search input shrinks to icon trigger.
* **Mobile (< 768px)**:
  * Desktop window titlebar hidden.
  * 1-column stat cards (`grid-cols-1`).
  * Tables enable horizontal scrolling (`overflow-x-auto`).

---

# 4. Color System

### Primary & Brand Colors
| Token Name | HEX | RGB | Purpose & Application |
| :--- | :--- | :--- | :--- |
| `brand-50` | `#F0F9FF` | `rgb(240, 249, 255)` | Active navigation background, active row highlight, light badge background |
| `brand-100` | `#E0F2FE` | `rgb(224, 242, 254)` | Hover states on active items, avatar backgrounds, selected tags |
| `brand-200` | `#BAE6FD` | `rgb(186, 230, 253)` | Subtle borders on active cards, focus rings |
| `brand-500` | `#0EA5E9` | `rgb(14, 165, 233)` | Primary Brand Blue, active indicators, chart accent lines |
| `brand-600` | `#0284C7` / `#0B57D0` | `rgb(2, 132, 199)` | Primary actionable buttons, active navigation indicator bar, brand logo text |
| `brand-700` | `#0369A1` | `rgb(3, 105, 161)` | Button hover state, primary text on light brand backgrounds |
| `brand-900` | `#0C4A6E` | `rgb(12, 74, 110)` | Dark brand accents, high-contrast text |

### Slate Neutral Palette (Dark Navy to Pure White)
| Token Name | HEX | RGB | Purpose & Application |
| :--- | :--- | :--- | :--- |
| `slate-50` | `#F8FAFC` | `rgb(248, 250, 252)` | Main application background, table header row fill, panel footers |
| `slate-100` | `#F1F5F9` | `rgb(241, 245, 249)` | Secondary background, divider lines, progress bar tracks, scrollbar tracks |
| `slate-200` | `#E2E8F0` | `rgb(226, 232, 240)` | Card borders, input field borders, table borders, circular chart background stroke |
| `slate-300` | `#CBD5E1` | `rgb(203, 213, 225)` | Disabled element borders, scrollbar thumb color, secondary icon stroke |
| `slate-400` | `#94A3B8` | `rgb(148, 163, 184)` | Placeholder text, secondary icons, section header text in sidebar |
| `slate-500` | `#64748B` | `rgb(100, 116, 139)` | Subtitles, label text, table column headers, helper captions |
| `slate-600` | `#475569` | `rgb(71, 85, 105)` | Default navigation text, secondary text body |
| `slate-700` | `#334155` | `rgb(51, 65, 85)` | Card titles, form labels, high-contrast body text |
| `slate-800` | `#1E293B` | `rgb(30, 41, 59)` | Main content headers, active selection text, primary dark text |
| `slate-900` | `#0F172A` | `rgb(15, 23, 42)` | Main page H1 headings, brand title, dark navy accents |

### Semantic State Colors
| Token / State | HEX | RGB | Purpose & Application |
| :--- | :--- | :--- | :--- |
| `Success (Emerald-500)` | `#10B981` | `rgb(16, 185, 129)` | Completed audit status, low risk indicator, compliance success, positive growth badges |
| `Success Light` | `#ECFDF5` | `rgb(236, 253, 245)` | Background fill for success badges (`emerald-50`) |
| `Warning (Amber-500)` | `#F59E0B` | `rgb(245, 158, 11)` | Pending review status, medium risk indicator, warning alerts, caution banners |
| `Warning Light` | `#FFFBEB` | `rgb(255, 251, 235)` | Background fill for warning badges (`amber-50`) |
| `Danger (Red-500)` | `#EF4444` | `rgb(239, 68, 68)` | High risk cases, GST mismatch flags, error alerts, window close button hover background (`#E81123`) |
| `Danger Light` | `#FEF2F2` | `rgb(254, 242, 242)` | Background fill for high-risk badges (`red-50`) |
| `Info (Blue-500)` | `#3B82F6` | `rgb(59, 130, 246)` | General information toasts, total clients icon background, neutral system status |

---

# 5. Typography System

### Font Family & Fallbacks
* **Primary Sans Font**: `'Inter'`, `-apple-system`, `BlinkMacSystemFont`, `'Segoe UI'`, `Roboto`, `sans-serif`.
* **Monospace Font** (for GSTIN, Numbers, Financial Data, Code): `'JetBrains Mono'`, `'Fira Code'`, `'Courier New'`, `monospace`.

### Typography Scale & Hierarchy

| Usage Level | Font Size | Line Height | Weight | Tracking | CSS Class Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Window Title** | `12px (0.75rem)` | `16px` | Medium (500) | `tracking-wide` | `text-xs font-medium text-slate-700` |
| **Brand Logo** | `20px (1.25rem)` | `28px` | Bold (700) | `tracking-tight` | `text-xl font-bold text-slate-900` |
| **Page Title (H1)**| `24px (1.5rem)` | `32px` | Bold (700) | `tracking-tight` | `text-2xl font-bold text-slate-900` |
| **Section Title (H2)**| `16px (1.0rem)` | `24px` | Semibold (600) | Normal | `text-base font-semibold text-slate-800` |
| **Card Title (H3)**| `14px (0.875rem)` | `20px` | Semibold (600) | Normal | `text-sm font-semibold text-slate-800` |
| **Body Standard** | `14px (0.875rem)` | `20px` | Regular (400) | Normal | `text-sm text-slate-600` |
| **Body Small** | `13px (0.8125rem)`| `18px` | Regular (400) | Normal | `text-[13px] text-slate-500` |
| **Caption / Meta** | `12px (0.75rem)` | `16px` | Medium (500) | Normal | `text-xs font-medium text-slate-500` |
| **Sidebar Section Header**| `11px - 12px` | `16px` | Semibold (600) | `tracking-wider uppercase` | `text-xs font-semibold text-slate-400 uppercase` |
| **Table Header** | `12px (0.75rem)` | `16px` | Semibold (600) | `tracking-wider uppercase` | `text-xs font-semibold text-slate-500 uppercase` |
| **Stat Numbers** | `30px (1.875rem)`| `36px` | Bold (700) | `tracking-tight` | `text-3xl font-bold text-slate-900` |
| **Button Text** | `14px (0.875rem)` | `20px` | Medium (500) | Normal | `text-sm font-medium` |

---

# 6. Spacing System

The design enforces an 8-point baseline grid scale with 4-point micro-adjustments:

| Value | Rem Equivalent | Pixel Equivalent | System Usage & Examples |
| :--- | :--- | :--- | :--- |
| `0.5` | `0.125rem` | `2px` | Fine border widths, progress bar inner height |
| `1` | `0.25rem` | `4px` | Micro gaps, status dot rings, badge padding vertical (`py-0.5`) |
| `1.5` | `0.375rem` | `6px` | Custom scrollbar width, button icon gap |
| `2` | `0.5rem` | `8px` | Small padding (`p-2`), gap between inline tags, icon margins |
| `2.5` | `0.625rem` | `10px` | Vertical padding for nav items (`py-2.5`), search input vertical padding |
| `3` | `0.75rem` | `12px` | Medium gaps (`gap-3`), input horizontal padding (`px-3`) |
| `4` | `1.0rem` | `16px` | Standard card internal padding (`p-4`), sidebar horizontal padding (`px-4`), table cell padding |
| `5` | `1.25rem` | `20px` | Large card header/body padding (`p-5`) |
| `6` | `1.5rem` | `24px` | Main content grid gaps (`gap-6`), page padding on small screens (`p-6`) |
| `8` | `2.0rem` | `32px` | Section margins (`mb-8`), desktop main container padding (`lg:p-8`) |
| `10` | `2.5rem` | `40px` | Avatar size (`w-10 h-10`), large section spacing |
| `12` | `3.0rem` | `48px` | Login card internal padding (`p-12`) |
| `16` | `4.0rem` | `64px` | Header height (`h-16`), modal max-width margins |
| `20` | `5.0rem` | `80px` | Sidebar logo section height (`h-20`) |

---

# 7. Component Library

### 1. Window Controls Bar (Desktop Titlebar)
* **Purpose**: Provides native desktop window management controls (Minimize, Maximize, Close).
* **Dimensions**: Height `32px` (`h-8`), Full Width (`w-full`), Background `#FFFFFF`, Bottom Border `#E2E8F0`.
* **Elements**:
  * Left: App Icon (`14px × 14px` blue rounded square with 'F') + Title text (`FinAuditPro`, `text-xs font-medium`).
  * Right: 3 Action Buttons (`h-full px-4 text-slate-500 hover:bg-slate-100`).
  * Close Button (`win-close`): `hover:bg-[#E81123] hover:text-white`.

### 2. Sidebar Navigation Item (`.nav-item`)
* **Default State**: Background transparent, Text `text-slate-600`, Icon `text-slate-400`, Border transparent.
* **Hover State**: Background `bg-slate-50`, Text `text-slate-900`, Icon `text-slate-600`.
* **Active State**: Background `bg-brand-50`, Text `text-brand-700 font-semibold`, Left Border `border-l-4 border-brand-600`, Icon `text-brand-600`.
* **Dimensions**: Padding `px-3 py-2.5`, Corner Radius `rounded-lg`.

### 3. Stat Cards (`.stat-card`)
* **Purpose**: Executive high-level KPI presentation with visual status indicators.
* **Dimensions**: Background `#FFFFFF`, Border `border border-slate-200`, Radius `rounded-xl`, Shadow `shadow-soft`.
* **Hover Effect**: `transform: translateY(-2px)`, Shadow `shadow-[0_10px_25px_-5px_rgba(0,0,0,0.05)]`.
* **Sub-elements**:
  * Top-Right Graphic: Quarter-circle background fill (`w-16 h-16 rounded-bl-full`) with embedded 24px icon.
  * Title: `text-sm font-medium text-slate-500`.
  * Value: `text-3xl font-bold text-slate-900`.
  * Growth Badge: `text-xs font-medium px-1.5 py-0.5 rounded` (e.g., `emerald-50` fill + `emerald-600` text).

### 4. Primary & Secondary Buttons
* **Primary Button**: `bg-brand-600 hover:bg-brand-700 text-white font-medium text-sm px-4 py-2 rounded-lg shadow-sm transition-all focus:ring-2 focus:ring-brand-500 focus:ring-offset-2`.
* **Secondary / Outline Button**: `bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 font-medium text-sm px-4 py-2 rounded-lg shadow-sm transition-all`.
* **Ghost / Icon Button**: `p-1.5 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors`.

### 5. Header Search Input
* **Container**: `max-w-md w-full relative group`.
* **Input Field**: `w-full pl-10 pr-3 py-2 border border-slate-200 rounded-lg leading-5 bg-slate-50 text-slate-900 placeholder-slate-400 focus:outline-none focus:bg-white focus:ring-2 focus:ring-brand-500 focus:border-brand-500 sm:text-sm transition-all`.
* **Icon Position**: Left-aligned 12px inset (`left-0 pl-3`), 20px SVG (`text-slate-400 group-focus-within:text-brand-500`).

### 6. Data Tables & Status Badges
* **Table Wrapper**: `overflow-x-auto border border-slate-200 rounded-xl bg-white shadow-soft`.
* **Header Row**: `bg-slate-50 border-b border-slate-200`, Columns: `px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider`.
* **Body Rows**: `divide-y divide-slate-200 hover:bg-slate-50/50 transition-colors`.
* **Active Selected Row (`.client-row.active`)**: `bg-[#F0F9FF] border-l-4 border-[#0284C7]`.
* **Status Badges**:
  * *In Progress / Low Risk*: `bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-0.5 rounded-full text-xs font-medium`.
  * *Pending Review / Medium Risk*: `bg-amber-50 text-amber-700 border border-amber-200 px-2.5 py-0.5 rounded-full text-xs font-medium`.
  * *High Risk / Action Req.*: `bg-red-50 text-red-700 border border-red-200 px-2.5 py-0.5 rounded-full text-xs font-medium`.

### 7. Circular SVG Progress Indicator (`.circular-chart`)
* **Background Track**: `circle-bg` (`stroke: #E2E8F0; stroke-width: 3.8; fill: none;`).
* **Active Arc**: `circle` (`stroke: #0EA5E9; stroke-width: 2.8; stroke-linecap: round; animation: progress 1s ease-out forwards;`).
* **Center Percentage Text**: `font-weight: 600; font-size: 0.5em; fill: #334155; text-anchor: middle;`.

### 8. Dropzone File Upload Component
* **Dashed Container**: `border-2 border-dashed border-slate-300 hover:border-brand-500 bg-slate-50/50 hover:bg-brand-50/30 rounded-xl p-8 text-center transition-all cursor-pointer`.
* **Elements**: Upload Cloud Icon (`w-12 h-12 text-slate-400 hover:text-brand-500`), Helper Text ("Drag & drop audit documents or browse"), Supported Formats Label ("Supports PDF, XLSX, CSV, ZIP up to 50MB").

---

# 8. Interaction Design

### Micro-Interactions & State Transitions
* **Navigation Transition**: `.nav-item { transition: all 0.2s ease; }`.
* **Card Lift Effect**: `.stat-card:hover { transform: translateY(-2px); box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05); }`.
* **Custom Enterprise Scrollbars**:
  ```css
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
  ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
  ```
* **Keyframe Progress Animation**:
  ```css
  @keyframes progress {
      0% { stroke-dasharray: 0 100; }
  }
  ```
* **Input Focus State**: Transition from `bg-slate-50 border-slate-200` to `bg-white border-brand-500 ring-2 ring-brand-500`.

---

# 9. Responsive Rules

| Device Breakpoint | Width Boundary | Layout Strategy & Adaptive Rules |
| :--- | :--- | :--- |
| **Desktop XL** | `≥ 1440px` | Default native resolution. Fixed 260px sidebar, full 12-col dashboard, open split-pane AI inspection. |
| **Desktop Standard**| `1280px - 1439px` | Full sidebar, stat grid `grid-cols-4`, main content auto-expands with fluid margin. |
| **Laptop / Tablet** | `1024px - 1279px` | Stat grid shifts to `grid-cols-2`. AI summary & charts stack vertically (`col-span-12`). |
| **Tablet Portrait** | `768px - 1023px` | Sidebar transitions to toggleable drawer. Table columns hide lower-priority metadata. |
| **Mobile** | `< 768px` | Stat grid shifts to `grid-cols-1`. Desktop window titlebar hidden. Mobile bottom navigation bar. |

---

# 10. Visual Language

* **Design Aesthetic**: Modern Corporate Enterprise Financial Tool (Clean, High-Trust, Data-Dense, Minimalist).
* **Avoided Styles**: No gaming neon accents, no heavy skeuomorphism, no distracting float animations, no high-saturation gradients.
* **Corner Radius System**:
  * Buttons, Inputs, Badges: `rounded-lg` (8px).
  * Cards, Tables, Modals: `rounded-xl` (12px).
  * Status Pills, Avatars, Floating Triggers: `rounded-full` (9999px).
* **Elevation & Depth**:
  * Base Canvas: Neutral `#F8FAFC` or `#F1F5F9`.
  * Cards / Panels: Pure `#FFFFFF` surface with `1px border #E2E8F0` and subtle `shadow-soft` (`0 4px 20px -2px rgba(0,0,0,0.03)`).
  * Modals / Drawers: High elevation `shadow-2xl` with dark backdrop `#0F172A` opacity 50%.

---

# 11. Accessibility (a11y) Standards

* **Color Contrast Ratio**: High contrast slate text (`#0F172A` and `#334155`) over light background (`#FFFFFF` and `#F8FAFC`) meeting WCAG 2.1 AA standards (ratio > 4.5:1).
* **Focus Visibility**: Explicit focus rings (`focus:ring-2 focus:ring-brand-500 focus:ring-offset-2`) on all interactive controls, buttons, text inputs, and table active rows.
* **Keyboard Navigation**:
  * `Tab` / `Shift+Tab`: Focus movement through sidebar navigation, header search, stat cards, and table actions.
  * `Enter` / `Space`: Trigger buttons, row selections, modal openings.
  * `Esc`: Close open drawers, modals, or context menus.
* **ARIA Standards**:
  * Navigation Landmarks: `<aside aria-label="Main Navigation">`, `<header aria-label="Top Utilities">`, `<main aria-label="Workspace">`.
  * Data Tables: `<table role="table">`, `<th scope="col">`.
  * Live Regions: `aria-live="polite"` on AI OCR extraction progress and toast messages.

---

# 12. Design Tokens

### JSON Format
```json
{
  "color": {
    "brand": {
      "50": "#F0F9FF",
      "100": "#E0F2FE",
      "500": "#0EA5E9",
      "600": "#0284C7",
      "700": "#0369A1",
      "900": "#0C4A6E"
    },
    "slate": {
      "50": "#F8FAFC",
      "100": "#F1F5F9",
      "200": "#E2E8F0",
      "400": "#94A3B8",
      "500": "#64748B",
      "700": "#334155",
      "900": "#0F172A"
    },
    "state": {
      "success": "#10B981",
      "warning": "#F59E0B",
      "danger": "#EF4444"
    }
  },
  "typography": {
    "fontFamily": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    "heading1": "24px",
    "heading2": "18px",
    "body": "14px",
    "table": "13px",
    "caption": "12px"
  },
  "layout": {
    "sidebarWidth": "260px",
    "headerHeight": "64px",
    "titlebarHeight": "32px",
    "borderRadiusCard": "12px",
    "borderRadiusControl": "8px"
  },
  "shadow": {
    "soft": "0 4px 20px -2px rgba(0, 0, 0, 0.03)",
    "cardHover": "0 10px 25px -5px rgba(0, 0, 0, 0.08)"
  }
}
```

### CSS Variables (`:root`)
```css
:root {
  /* Brand Palette */
  --color-brand-50: #f0f9ff;
  --color-brand-100: #e0f2fe;
  --color-brand-500: #0ea5e9;
  --color-brand-600: #0284c7;
  --color-brand-700: #0369a1;
  --color-brand-900: #0c4a6e;

  /* Slate Neutrals */
  --color-slate-50: #f8fafc;
  --color-slate-100: #f1f5f9;
  --color-slate-200: #e2e8f0;
  --color-slate-300: #cbd5e1;
  --color-slate-400: #94a3b8;
  --color-slate-500: #64748b;
  --color-slate-600: #475569;
  --color-slate-700: #334155;
  --color-slate-800: #1e293b;
  --color-slate-900: #0f172a;

  /* Functional States */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-danger: #ef4444;

  /* Layout Metrics */
  --sidebar-width: 260px;
  --header-height: 64px;
  --titlebar-height: 32px;
  --radius-lg: 8px;
  --radius-xl: 12px;

  /* Shadows */
  --shadow-soft: 0 4px 20px -2px rgba(0, 0, 0, 0.03);
  --shadow-hover: 0 10px 25px -5px rgba(0, 0, 0, 0.08);
}
```

### Tailwind Config JavaScript Object
```javascript
module.exports = {
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        brand: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          900: '#0c4a6e',
        },
        slate: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        }
      },
      boxShadow: {
        'soft': '0 4px 20px -2px rgba(0, 0, 0, 0.03)',
        'card-hover': '0 10px 25px -5px rgba(0, 0, 0, 0.08)',
      }
    }
  }
}
```

---

# 13. UI Inventory

### Iconography (SVG Vectors)
* **Shield + Graph Logo Icon**: 28px viewBox `0 0 120 120` shield path with 3 vertical financial bar rectangles.
* **Dashboard Nav Icon**: 20px 4-grid squares icon (`M4 6a2 2 0 012-2...`).
* **Clients Nav Icon**: 20px Users group silhouette (`M17 20h5v-2...`).
* **Upload Documents Nav Icon**: 20px Cloud upload icon with arrow (`M7 16a4 4 0 01...`).
* **AI Analysis Nav Icon**: 20px Sparkle / AI lightbulb icon (`M9.663 17h4.673...`).
* **Risk Analysis Nav Icon**: 20px Alert triangle icon (`M12 9v2m0 4h.01...`).
* **GST / Compliance Icon**: 20px Checklist with checkmarks (`M9 5H7a2 2 0 00...`).
* **Window Controls**: 10px SVG Line (Minimize), 10px Square (Maximize), 10px Cross (Close).

---

# 14. UX Flow Architecture

```
User Journey & Workflow Sequence

[Launch Desktop App]
       │
       ▼
1. Splash Screen (System initializing, local LLM warmup, license verification)
       │
       ▼
2. Login Screen (Enter CA Email & Password, option to 'Remember Me', click Login)
       │
       ▼
3. Executive Dashboard (View 4 KPI stat cards, portfolio risk score 24/100, progress charts)
       │
       ├───────────────────────────────┬───────────────────────────────┐
       ▼                               ▼                               ▼
4. Client Management            5. Document Upload & OCR       6. AI Audit Analysis
   (Add/Select Client,             (Drag-and-drop PDF/Excel,      (Inspect document side-by-side
   inspect engagement status)      parse extracted table fields)   with AI risk findings & copilot)
       │                               │                               │
       └───────────────────────────────┼───────────────────────────────┘
                                       ▼
                       7. Compliance & Risk Verification
                          (Review GST mismatch, statutory checklist,
                           flagged anomaly highlights)
                                       │
                                       ▼
                       8. Working Paper & Report Generator
                          (Auto-draft CA audit papers, review opinion,
                           export final signed PDF report)
```

---

# 15. Suggested Improvements

1. **Dark Theme Palette Specification**: Add native high-contrast dark theme tokens (`#0F172A` canvas, `#1E293B` surfaces) for late-night auditing sessions.
2. **Keyboard Shortcut Map**: Introduce native desktop hotkeys (`Cmd/Ctrl + K` for global search, `Cmd/Ctrl + U` for quick upload, `Cmd/Ctrl + Shift + A` for AI analysis trigger).
3. **Data Density Toggle**: Allow users to switch table density between "Compact" (32px row height) and "Comfortable" (48px row height) for viewing massive ledger files.
4. **Offline Sync Status Bar**: Implement a persistent 24px bottom status bar indicating local database sync state, Ollama AI model status, and offline mode confirmation.

---

# 16. AI-Ready Master Generation Prompt

```markdown
Role & Goal:
You are an expert Principal UI/UX Designer and Lead Frontend Engineer. Recreate the complete desktop UI for "FinAuditPro", an enterprise-grade AI financial auditing software designed for Chartered Accountants.

Aesthetic & Style Guidelines:
- Style: Modern Corporate Enterprise Desktop Application (Tally Prime / Microsoft Office / Modern FinTech dashboard hybrid). Clean, data-dense, highly trustworthy, zero gaming elements.
- Resolution: Target desktop window frame of 1440x900px with a 32px top desktop titlebar (app title "FinAuditPro", window controls: minimize, maximize, close).
- Color Palette:
  * Primary Brand: #0EA5E9 (Sky 500), #0284C7 (Brand 600), #0369A1 (Brand 700).
  * Backgrounds: #F8FAFC (Slate 50) canvas, #FFFFFF (Pure White) surfaces.
  * Slate Neutrals: #0F172A (Slate 900 H1 text), #334155 (Slate 700 subheaders), #64748B (Slate 500 captions), #E2E8F0 (Slate 200 borders).
  * Semantics: #10B981 (Success Emerald), #F59E0B (Warning Amber), #EF4444 (Danger Red).
- Typography: Inter font family. Title H1 (24px bold), Section H2 (16px semibold), Body (14px regular), Tables (13px medium).

Layout Architecture:
- Left Sidebar (Fixed 260px width, 100vh height): Shield + bar graph logo ("FinAuditPro Smart Audit Assistant"), categorized navigation links with left active accent bar, bottom CA User profile card.
- Header Bar (Fixed 64px height): Global search input ("Search clients, reports, documents..."), theme toggle button, help icon, notifications icon with red dot, user avatar badge.
- Main Content Area (Fluid flex scrollable):
  1. Header: "Good Morning, Auditor" + subtitle "Here is your audit overview for today."
  2. Stat Cards Grid (4 columns): Total Clients (150, +12%), Completed Audits (98), Pending Reviews (12), High Risk Cases (5).
  3. Middle Split Layout:
     - Left (4 cols): AI Audit Summary Card (Portfolio Risk Score 24/100, Compliance Score 92%, Recent AI findings list).
     - Center (5 cols): Audit Progress Line Chart (Last 6 Months filter).
     - Right (3 cols): Risk Distribution Doughnut Chart (Low/Medium/High risk breakdown with center total count).
  4. Bottom Table: Recent Audit Projects (Columns: Client Name, Audit Type, Status Badge, Risk Level Badge, Last Updated, Actions).

Interactions & Components:
- Custom subtle 6px scrollbars, 0.2s ease transitions on buttons and nav items, stat cards lift -2px on hover with shadow-soft. Responsive breakpoint rules scaling to tablet and mobile.

Output Code:
Generate clean, production-ready, semantic HTML5 with Tailwind CSS utility classes and Inter font initialization.
```
