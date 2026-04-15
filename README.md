# 🪞 L611: Data Mirror and MCP — Modern Connectivity for Customer Journey Analytics

**Adobe Summit 2026 Lab** | *lab number: L611* | 🔴 Adobe Experience Platform

---

## 📖 Introduction

This lab explores two Adobe capabilities that change how data gets into Customer Journey Analytics and how you interact with it once it's there.

**Data Mirror** keeps CJA in sync with your external data warehouse — or cloud object storage that contains change data feed files — automatically, at the row level, using Change Data Capture (CDC). When a record is inserted, updated, or deleted at the source, the change propagates through the Adobe Experience Platform data lake and into CJA without any export scripts, batch jobs, or manual refresh.

**The CJA MCP Server** implements the Model Context Protocol, connecting AI coding tools like Cursor directly to your live CJA environment. Instead of navigating Analysis Workspace to build reports and segments, you describe what you want in plain language and the agent builds it.

Together, these two capabilities address the two most common friction points in analytics work: getting accurate data **in**, and getting insights **out** fast.

---

### 🎯 Goals

After completing this lab, you will walk away with the following knowledge:

- What Data Mirror is, how CDC-based ingestion works, and when to use it over batch or incremental connectors
- How to recognize the three relational schema descriptor fields required for Data Mirror
- Follow a complete Data Mirror pipeline end-to-end: source data → schema → dataflow → CJA
- How relational datasets map to CJA dataset types (event, summary, profile, lookup)
- What the Model Context Protocol (MCP) is and how it connects AI clients to live analytics data
- How to connect Cursor to the CJA MCP Server and verify the connection
- What skills are and how they enable repeatable AI workflows
- How to create CJA Analysis Workspace projects using only natural language prompts
- How to audit your CJA component library for health, waste, and duplicate segments at scale
- How to deep-dive into a dimension's cardinality and data quality
- How to identify component dependencies and plan find-and-replace migrations
- How to build simple and sequential segments through conversation — including complex THEN logic with time restrictions
- How the CJA MCP Server compares to Digital Insights Agent in CJA

---

### ✅ Prerequisites

Before starting this lab, confirm you have the following:

- Basic familiarity with CJA — you know what a data view, workspace, and segment are
- Cursor installed and running on your lab computer
- Your Adobe IMS credentials (Experience Cloud login) available
- CJA access provisioned for the lab sandbox (your lab setup confirms this)
- No coding experience required — all exercises use natural language prompts

---

### 🛍️ Customer Scenario

The lab is built around **Luma**, a fictional multi-channel retail brand selling apparel and accessories online and in stores.

Your role: you are a CJA analyst at Luma. Your team is responsible for maintaining accurate customer journey data and delivering timely insights to the marketing and e-commerce teams. You face two persistent challenges:

1. 📉 **Data freshness** — Luma's product catalog and campaign data live in external cloud systems (BigQuery, Azure Blob, S3). Every time a product price changes or a campaign window closes, someone has to manually export a file and re-upload it. Reports go stale between refreshes.
2. ⏳ **Analysis speed** — Building a workspace from scratch takes 30+ minutes. Your team spends more time assembling panels than interpreting results.

This lab shows you how to solve both.

---

### 🏗️ Technical Architecture

Two capabilities, two data flows:

![1776090399107](image/README/1776090399107.png)

> 📝 **Note:** Data Mirror requires a one-time setup in AEP (schema, dataset, source connector). Once configured, it runs continuously. The CJA MCP Server is already hosted — you connect to it in Lesson 2 with a single JSON config entry.

---

**🚦 Before you begin — confirm your setup:**

- You can log in to CJA at [experience.adobe.com](https://experience.adobe.com)
- Cursor is installed and open on your lab computer
- You have your Adobe IMS credentials ready

---

## ⚙️ Environment setup

To prepare our environment today using *Cursor* we have a few setup steps to follow. Begin these steps as soon as you arrive in the lab.

### 🖥️ Setup 1: Open Cursor

Cursor is the sdk platform we will use today with the CJA MCP server. Open it from your application list.

<img width="168" height="38" alt="Screenshot 2026-04-03 141758" src="https://github.com/user-attachments/assets/7761c37c-bf73-475e-984a-a61a7b206a16" />

### 📦 Setup 2: Clone our Git repository

This step is a simple way to download files we need. In Github, the terminology is that we are cloning a public repository.

1. Cursor will open to a black window like this. Click on the *Clone repo* option.

<img width="448" height="179" alt="Screenshot 2026-04-03 142109" src="https://github.com/user-attachments/assets/d31260ff-eccf-459f-b4e8-739c534224a2" />

2. In the text bar that has appeared, paste the following URL and click *Clone from URL*.

```
https://github.com/Adobe-Experience-Cloud/adobe-analytics-mcp-lab
```

<img width="529" height="84" alt="AdobeExpressPhotos_26e57926bbcc47c58cfd164169b25eb8_CopyEdited" src="https://github.com/user-attachments/assets/e95c2f8d-bd7b-494b-87a5-e32dd30d68d4" />

3. Select any location, such as the desktop, for the repo to be saved.

*IMAGE:mac finder type window*

Your screen should look similar to this, afterward:

*IMAGE:cursor window*

### 🔧 Setup 3: Config Cursor

Now, we just need to tell Cursor how to reach CJA and help us connect.

1. Open an agent chat via ______.

*IMAGE:agent chat open button*

2. Paste this prompt into chat so Cursor use the CJA MCP server info from our download.

```
Add my cja mcp server to the global Cursor settings.
```

<img width="479" height="89" alt="AdobeExpressPhotos_dfbdba47b8514d9b95b3c51d9ed23ac6_CopyEdited" src="https://github.com/user-attachments/assets/d7b14b05-938c-41d3-8dc9-1bb864527f9d" />

This should process quickly, taking only a few seconds. Instead of clicking through Settings menus, we are using the downloaded files and the Composer agent in Cursor to automate setup.

3. Submit this prompt to open web authentication for CJA.

```
Authenticate to CJA using mcp_auth.
```

As before, this should only take a few seconds. Cursor will hopefully make a call and produce this interactive result for you. Click *Authenticate*:

<img width="478" height="207" alt="AdobeExpressPhotos_b0c2b17aff54421b87bf69f9a614765a_CopyEdited" src="https://github.com/user-attachments/assets/27aa4344-1714-4cff-9b5d-7c368e90c9b3" />

4. On web auth, select *Experience Showcase* (if asked) and click OK.

*IMAGE: org choice*

5. On the following screen, click *Allow access*:

<img width="415" height="581" alt="AdobeExpressPhotos_c07022c6ea14438bb535f87a152922c5_CopyEdited" src="https://github.com/user-attachments/assets/6c0bc68d-edd8-4f7e-978a-3978d95b79f5" />

Now, Cursor should say some positive comments about being connected. If so, you can confirm the connection to CJA is active with a prompt like this:

```
What data views can I access?
```

If Cursor returns a small list including the L611 data view, then you are ready! *Leave the Cursor app alone until we get to the MCP tasks in a few minutes.*

<img width="461" height="151" alt="AdobeExpressPhotos_bfd296436c9d4730b877c53442b6d399_CopyEdited" src="https://github.com/user-attachments/assets/e4ff7d01-62d5-4630-9813-55ce9d40e013" />

### 🛠️ Manual setup instructions

**⚠️ Problems connecting?**
If any of the steps above didn't work, here are the manual click instructions to ensure you are setup for Cursor.

1. In Cursor, go to **Settings → Tools & MCP → Add New MCP Server**.
2. An editor opens with `mcp.json`. Paste the following configuration and save:

   ```json
   {
     "mcpServers": {
       "cja": {
         "type": "streamable-http",
         "url": "https://mcp-gateway.adobe.io/cja/mcp"
       }
     }
   }
   ```
3. Back in **Settings → Tools & MCP**, find the **cja** server entry and click **Connect**.
4. A dialog asks for permission to open the authentication page — click **Open**.
5. Your browser opens the Adobe Experience Platform login. Sign in with your credentials, select your organization when prompted, and click **Allow access**.
6. After authentication, the browser shows a dialog asking to open Cursor — click **Open Cursor.app**.
7. The CJA server should now show as connected, with tools listed below it.

> 🔧 **Troubleshoot:** If CJA tools don't appear after authentication, go back to **Settings → Tools & MCP**, click **Disable** on the CJA server, then click **Enable**. The tools will be available in your next Agent chat.

To verify the connection, open a new Agent chat and type:

```
Are my CJA tools connected?
```

The agent should respond with a list of available tools. If it does, you're all set.

---

## 🪞 Lesson 1 of 4 — Data Mirror

⏱️ Est. completion: 10 min *(No Cursor needed for this lesson)*

---

### 🎯 1.1 Objectives

By the end of this lesson you will be able to:

- Explain what Data Mirror does and the problem it solves
- Identify the descriptor fields a relational schema requires for CDC
- Follow a complete Data Mirror pipeline: source data → schema → dataflow → CJA

### 🔄 1.2 What is Data Mirror?

Most analytics teams have the same problem: data in CJA goes stale. A product price changes in the warehouse, a campaign ends, a customer profile updates — but CJA doesn't know until someone runs an export script and re-uploads a file. By then the data is hours or days old.

**Data Mirror** is an Adobe Experience Platform capability that solves this by enabling row-level change ingestion from external databases into the AEP data lake using **relational schemas** and **Change Data Capture (CDC)** [1]. When a record is inserted, updated, or deleted at the source, that change flows through to AEP — and from there to CJA — without any manual intervention.

Let's see a change data feed in action. In the example below, we start with three rows in **state 1**. Between state 1 and state 2, two things happen: Razvan's row is **deleted** and Rene's role is **updated** from Engineer to Architect. The change feed on the right captures exactly these two operations — a `delete` for row 2 and an `update` for row 3 — along with a version timestamp so the system knows the order. **State 2** reflects the result: Razvan is gone and Rene's role has changed. This is the core mechanic behind Data Mirror — only the changes move, not the entire table.

<img src="assets/lesson-1/00-change-feed-example.png" alt="Change feed example — before and after states with change operations" height="300" />

| Method                        | Best For                                   | Supports Updates/Deletes                   |
| ----------------------------- | ------------------------------------------ | ------------------------------------------ |
| Flat file / CSV upload        | One-time or ad-hoc loads                   | No                                         |
| Incremental source connectors | Append-only data streams                   | Inserts only                               |
| **Data Mirror (CDC)**   | **Live sync with mutation tracking** | **Yes — inserts, updates, deletes** |

A complete Data Mirror pipeline has been set up for this lab. This lesson walks through each layer so you can see how the pieces connect.

### 🗄️ 1.3 The Source Data

The lab dataset is built around **Luma**, a fictional retail brand. Four tables across three cloud sources:

| Table                 | Type                  | Source             | Records | Purpose                                                  |
| --------------------- | --------------------- | ------------------ | ------- | -------------------------------------------------------- |
| `web_traffic`       | Time Series / Event   | Google BigQuery    | 1,000   | Clickstream events (page views, purchases, cart actions) |
| `customer_profiles` | Record / Profile      | Google BigQuery    | 200     | Customer identity, loyalty tier, region                  |
| `products`          | Record / Lookup       | Azure Blob Storage | 50      | Product catalog with category and price                  |
| `campaigns`         | Time Series / Summary | Amazon S3          | 5       | Campaign windows, Jan–Feb 2026                          |

**Entity Relationship Diagram:**

```
┌──────────────────────────────────────┐
│         customer_profiles            │
│  (Record/Profile — BigQuery)         │
├──────────────────────────────────────┤
│ PK  person_id         VARCHAR        │
│     first_name        VARCHAR        │
│     last_name         VARCHAR        │
│     email             VARCHAR        │
│     loyalty_tier      VARCHAR        │
│     region            VARCHAR        │
│     signup_date       DATE           │
│  V  version_time      DATETIME       │
└───────────────▲──────────────────────┘
                │
                │ person_id (N:1)
                │
┌───────────────┴──────────────────────┐                ┌───────────────────────────────────────┐
│           web_traffic                │                │          products                     │
│  (Time Series/Event — BigQuery)      │                │  (Record/Lookup — Blob Storage)       │
├──────────────────────────────────────┤                ├───────────────────────────────────────┤
│ PK  event_id          VARCHAR        │  product_id    │ PK  product_id        VARCHAR         │
│  V  version_no        INT            │   (N:1)        │     product_name      VARCHAR         │
│  T  event_timestamp   DATETIME       ├───────────────►│     category          VARCHAR         │
│ FK  person_id         VARCHAR        │                │     price             DECIMAL         │
│     event_type        VARCHAR        │                │     description       VARCHAR         │
│ FK  product_id        VARCHAR        │                │  V  last_modified_time DATETIME       │
│     page_url          VARCHAR        │                └───────────────────────────────────────┘
│     device_type       VARCHAR        │
│     browser           VARCHAR        │
│ FK  campaign_id       VARCHAR        │
└───────────────┬──────────────────────┘
                │
                │ campaign_id (N:1, nullable)
                │
┌───────────────▼──────────────────────┐
│           campaigns                  │                ╔═══════════════════════════════════════╗
│  (Time Series/Summary — S3)          │                ║  LEGEND                               ║
├──────────────────────────────────────┤                ║  PK  Primary Key                      ║
│ PK  campaign_id       VARCHAR        │                ║  V   Record Version                   ║
│  V  campaign_version  DATETIME       │                ║  T   Record Timestamp (time series)   ║
│  T  timestamp         DATETIME       │                ║  FK  Foreign Key                      ║
│     campaign_name     VARCHAR        │                ╚═══════════════════════════════════════╝
│     campaign_description VARCHAR     │
│     start_time        DATETIME       │
│     end_time          DATETIME       │
└──────────────────────────────────────┘
```

| Relationship | From | To | Cardinality | Join Key |
|---|---|---|---|---|
| Event → Person | `web_traffic` | `customer_profiles` | N : 1 | `person_id` |
| Event → Product | `web_traffic` | `products` | N : 1 | `product_id` |
| Event → Campaign | `web_traffic` | `campaigns` | N : 1 (nullable) | `campaign_id` |

### 📋 1.4 The Source Tables

Each source table contains fields that Data Mirror uses as descriptors.

Descriptor fields per table:

| Table                 | Primary Key     | Version Descriptor                           | Timestamp Descriptor      | Notes                                               |
| --------------------- | --------------- | -------------------------------------------- | ------------------------- | --------------------------------------------------- |
| `web_traffic`       | `event_id`    | `version_no` (integer, increments 0→1→2) | `event_timestamp`       | BigQuery native CDC                                 |
| `customer_profiles` | `person_id`   | `version_time` (datetime)                  | —                        | BigQuery native CDC                                 |
| `products`          | `product_id`  | `last_modified_time` (datetime)            | —                        | Cloud storage: uses `_change_request_type` column |
| `campaigns`         | `campaign_id` | `campaign_version` (datetime)              | `timestamp`             | Cloud storage: uses `_change_request_type` column |

Two versioning patterns are in use:
- **Integer** — `web_traffic` uses `version_no` (0→1→2)
- **DateTime** — `customer_profiles` uses `version_time`, `products` uses `last_modified_time`, `campaigns` uses `campaign_version`

Both patterns are supported by Data Mirror.

### 📐 1.5 The Relational Schemas

Standard XDM schemas in AEP are append-only. The schemas for this lab use **relational schemas**, which enable mutation tracking through descriptors [1]:

- **Primary key** — unique row identifier
- **Version descriptor** — integer or timestamp used to reconcile out-of-order changes
- **Timestamp descriptor** — required for time-series schemas

Each relational schema is created with a behavior type — **Record** or **Time series**:

<img src="assets/lesson-1/30-aep-relational-xdm-behaviour-types.png" alt="AEP — Create relational schema with behavior type selection" height="410" />

**Time series example: `web_traffic`** — uses all three descriptors.

BigQuery source schema:

<img src="assets/lesson-1/20-gbq-table-schema.png" alt="BigQuery — web_traffic table schema" height="300" />

AEP relational schema:

- **Primary key** — `event_id`
- **Version descriptor** — `version_no`
- **Timestamp descriptor** — `event_timestamp`

<img src="assets/lesson-1/31-aep-relational-xdm-web-traffic-schema.png" alt="AEP — Relational schema for web_traffic showing primary key, version descriptor, and timestamp descriptor" height="430" />

**Record example: `products`** — uses only two descriptors (no timestamp descriptor needed):

- **Primary key** — `product_id`
- **Version descriptor** — `last_modified_time`

<img src="assets/lesson-1/32-aep-relational-xdm-products-schema.png" alt="AEP — Relational schema for products showing primary key and version descriptor" height="520" />

### 🔀 1.6 The CDC Dataflows

With schemas in place, source connectors move the data. All four dataflows are configured from the three source accounts for this lab in AEP:

<img src="assets/lesson-1/10-aep-sources-accounts.png" alt="AEP Sources — Accounts tab showing BigQuery, Azure Blob Storage, and S3 source accounts" height="250" />

Each dataflow has **Enable change data capture** toggled on. This requires a relational schema with primary key and version descriptor on the target dataset:

<img src="assets/lesson-1/41-aep-sources-cdc-enable.png" alt="AEP — Dataflow detail showing the Enable change data capture toggle and CDC requirements" height="490" />

**CDC behavior by source type:**

- **Database sources** (BigQuery, Snowflake, Delta Lake) — CDC is handled natively. Change history was enabled once per table:

  ```sql
  ALTER TABLE `<gcp_project>.adobesummit26lab611.web_traffic`
    SET OPTIONS (enable_change_history = true);
  ALTER TABLE `<gcp_project>.adobesummit26lab611.customer_profiles`
    SET OPTIONS (enable_change_history = true);
  ```

  > 📝 **Other databases:** The concept is the same — enable change tracking at the table level. Here's what it looks like in Snowflake and Databricks:
  >
  > **Snowflake:**
  > ```sql
  > ALTER TABLE web_traffic SET CHANGE_TRACKING = TRUE;
  > ```
  >
  > **Databricks (Delta):**
  > ```sql
  > ALTER TABLE web_traffic SET TBLPROPERTIES (delta.enableChangeDataFeed = true);
  > ```

- **Cloud storage sources** (Azure Blob, S3) — signal operations via a `_change_request_type` column: `"u"` for upsert (insert or update), `"d"` for delete. Evaluated during ingestion only; not stored or mapped to XDM fields [2].

Once configured, the dataflows run continuously. Here are the active flows for this lab:

<img src="assets/lesson-1/40-aep-sources-cdc-flows.png" alt="AEP Sources — Dataflows tab showing active CDC dataflows for all sources" height="250" />

### ✏️ 1.7 The Changes

With the dataflows running, the following changes were applied at the source for this lab session.

**Database changes (BigQuery):**

```sql
-- 1. DELETE all events on March 15
DELETE FROM `<gcp_project>.adobesummit26lab611.web_traffic`
WHERE CAST(event_timestamp AS DATE) = '2026-03-15';

-- 2. INSERT 3 new events on March 18
INSERT INTO `<gcp_project>.adobesummit26lab611.web_traffic`
  (event_id, version_no, person_id, event_timestamp, event_type,
   product_id, page_url, device_type, browser, campaign_id)
VALUES
  ('EVT-200001', 0, 'daniel.thompson10001@example.com', '2026-03-18T09:15:00Z',
   'page_view', 'PROD-1005', 'https://luma.retail.example.com/', 'desktop', 'Chrome', ''),
  ('EVT-200002', 0, 'paul.davis10002@example.com', '2026-03-18T09:32:00Z',
   'product_view', 'PROD-1012', 'https://luma.retail.example.com/shop/footwear', 'mobile', 'Safari', ''),
  ('EVT-200003', 0, NULL, '2026-03-18T10:05:00Z',
   'search', 'PROD-1023', 'https://luma.retail.example.com/search', 'desktop', 'Firefox', '');

-- 3. Rename Anthony Harris → Anthony Harris Jr.
UPDATE `<gcp_project>.adobesummit26lab611.customer_profiles`
SET last_name = 'Harris Jr.',
    version_time = CURRENT_TIMESTAMP()
WHERE person_id = 'PER-10091';
```

BigQuery's [change history](https://docs.cloud.google.com/bigquery/docs/change-history) captures these automatically — no `_change_request_type` column needed.

**Cloud storage changes (Azure Blob)** — A CDC file `products_changes.json` was uploaded:

```json
[{
  "product_id": "PROD-1001",
  "product_name": "Classic Cotton T-Shirt",
  "category": "Apparel",
  "price": 24.99,
  "description": "Soft 100% cotton crew-neck tee in assorted colors",
  "last_modified_time": "2026-03-24T12:00:00Z",
  "_change_request_type": "u"
},
{
  "product_id": "PROD-1003",
  "product_name": "Lightweight Running Jacket",
  "category": "Apparel",
  "price": 119.99,
  "description": "Water-resistant jacket with reflective trim",
  "last_modified_time": "2026-03-24T12:00:00Z",
  "_change_request_type": "d"
}]
```

Data Mirror matches on `product_id` and reads `_change_request_type`:
- `"u"` — upsert (insert or update): the newer `last_modified_time` replaces the existing record
- `"d"` — delete: the row is removed

Across both sources, these operations exercise every CDC mutation type: **delete**, **insert**, **update**.

### 🔗 1.8 Adding Data Mirror Datasets to CJA

Once the datasets land in the AEP data lake, the next step is adding them to a CJA connection. When you add a relational XDM dataset, CJA asks you to classify it based on the schema's behavior type:

| Schema Behavior | CJA Dataset Type | Use Case |
|---|---|---|
| **Time Series** | **Event** dataset | Clickstream, transactions — rows with a timestamp per interaction |
| **Time Series** | **Summary** dataset | Aggregated data — campaign-level totals, daily rollups |
| **Record** | **Profile** dataset | Person-level attributes — identity, loyalty tier, region |
| **Record** | **Lookup** dataset | Reference tables — product catalog, campaign metadata |

In this lab, the four datasets map as follows:
- `web_traffic` → **Event** (time series — individual clickstream hits)
- `campaigns` → **Summary** (time series — campaign-level aggregates)
- `customer_profiles` → **Profile** (record — one row per person)
- `products` → **Lookup** (record — one row per product)

<img src="assets/lesson-1/50-cja-connection.png" alt="CJA — Connection showing Data Mirror datasets added with their dataset types" height="400" />

Once the connection is saved, CJA ingests the datasets and respects the CDC operations — inserts, updates, and deletes all carry through into your data views and reports.

### 👀 1.9 See the Results in CJA

Two setups are running during this session:
- **Live setup** — changes are being applied now
- **Pre-run setup** — same changes applied earlier, already fully propagated

Open CJA on your lab computer and find the pre-run freeform table. Observe:

- **March 15** shows **0 events** — the delete propagated
- **PROD-1001 (Classic Cotton T-Shirt)** shows **$24.99** — the price update propagated
- **PROD-1003 (Lightweight Running Jacket)** no longer appears — the product delete took effect
- **PER-10091** shows **Harris Jr.** — the customer profile update propagated

<img src="assets/lesson-1/60-cja-changes-propagated.png" alt="CJA — Freeform table showing propagated Data Mirror changes" height="400" />

This is the end state the live setup will reach once its propagation completes.

### 💡 1.10 Checkpoint

Before moving on, consider:

- What happens in CJA when a record is **deleted** at the source? Does it disappear from reports?
- What are the three descriptor fields a relational schema must define for CDC to work?
- Name a data scenario in your own work where Data Mirror would be more useful than a batch connector.

---

---

## 🤖 2 — Intro to CJA MCP Server and project builder

⏱️ Est. completion: 10 min

---

### 🎯 2.1 Objectives

By the end of this lesson you will be able to:

- Explain what MCP is and how it enables AI-to-CJA connectivity
- Connect Cursor to the CJA MCP Server
- Verify that CJA tools are available in an Agent chat
- Create simple and advanced CJA projects using natural language

### 🔌 2.2 What is MCP?

**MCP (Model Context Protocol)** is an open standard for connecting AI applications to external data sources and tools. It provides a universal interface so AI clients — Cursor, Claude.ai, ChatGPT — can securely access live data and take actions on your behalf, without requiring a custom integration for each platform.

MCP is like an API for AI/LLM agents. You chat conversationally with AI tool like normal but now that AI platform can connect to CJA to pull data, build a dashboard, check components, etc.

**What the CJA MCP Server exposes:**

| Category      | What you can do                                                                   |
| ------------- | --------------------------------------------------------------------------------- |
| Discovery     | Find data views, dimensions, metrics, segments, date ranges, projects             |
| Reporting     | Run freeform reports, search dimension items                                      |
| Creation      | Create and update workspaces, segments, calculated metrics                        |
| Governance    | List component usage, find similar components, find frequently co-used components |
| Configuration | Set session defaults (data view, context)                                         |

Instead of navigating Analysis Workspace manually, you describe what you want: *"Show me mobile revenue by product category for the last 30 days"* — the agent runs the query and returns results directly.

**How it differs from Data Insights Agent in CJA/AEP**

In the CJA UI, there is a feature called Data Insights Agent or AI Assistant. It will answer simple information requests, report updates, etc. but only within your CJA/AEP context. The MCP server facilitates those too, but it is the power of the chat agent you use which takes it farther. You can give an AI like ChatGPT a complex prompt, with external references, instructing it to generate a unique CJA report app for you. This lab will explore the possibilities.

AI Assistant and Data Insights Agent in CJA:
`<img width="858" height="736" alt="AI Assistant and Data Insights Agent" src="https://github.com/user-attachments/assets/0bdd9adf-0ae1-46de-a34d-c8c0471e85fc" />`

### 🧠 2.3 What are **skills**?

**Skills** represents the way you can share task or context knowledge across instances of an AI chat. After wrestling an AI to doing something just the way you want it, you can ask it to save the capability as a skill, in hopes that it will be repeatable and shareable when you or another opens a brand new AI conversation.

Skills are the sheet of notes that you give to an AI to help it replicate a scenario it doesn't know.

### 🏗️ 2.4 Project builder skill

With the MCP server connected, you can describe what you want to analyze and let the agent build it. The server provides a minimal framework to the LLM that connects to it: pull reports like this, update projects like that, etc. No additional context is needed - yet there are nuances that experienced analysts know that AI might miss.

So, to aid repeatability and demonstrations in our lab, we have defined the `cja-project-builder` **skill**. It guides the agent through a structured workflow: it discovers your available components, assembles a complete project definition, and calls `upsertProject` to create the workspace in CJA. For advanced, specific, repeatable tasks, skills can give us helpful guardrails and *repeatability* (usually). To show cool things and keep attendees' instances on the same track, we will use skills.

> 📝 **Note:** For our lab today, we suggest using the prompts listed and following along. If you want to try something additional, use a separate agent chat so that you can still explore the prepared skills and ideas we have. The lab goal is to show a breadth of possibilities with *reasonably consistent* exercises, but in practice, iterations are typically required.

1. Open a new agent chat.

<img width="155" height="152" alt="AdobeExpressPhotos_a9aeb23ad3c14d3c85fd6ebfcc3cdfd5_CopyEdited" src="https://github.com/user-attachments/assets/584a0ad2-38ca-4131-9264-afab80fd42ed" />

2. Specify the data view for our session with this prompt:

```
Set L611 as my default data view for this session.
```

<img width="1070" height="174" alt="AdobeExpressPhotos_8155baefdfad4ad09ecaae450a2e324a_CopyEdited" src="https://github.com/user-attachments/assets/7cfcd234-9748-42d3-bb4a-b157c81aa441" />

The agent calls `setDefaultSessionDataViewId` — now every subsequent tool call uses this data view by default. This is a proactive call, as the AI would have asked us directly as needed.

3. Create a basic CJA project with this prompt:

```
Make a simple CJA project.
```

<img width="786" height="199" alt="AdobeExpressPhotos_6539e90f9a394454ab16297ae7b557b9_CopyEdited" src="https://github.com/user-attachments/assets/24e931ab-94e4-4650-80f6-5a0f9feefd28" />

> 📝 **Note:** This will use our project builder skill. They are naturally identified by the AI based on their definition (or you may invoke it explicitly by skillname). In our Cursor environment, if we use phrases like *make/build a CJA project* or reference `@cja-project-builder`, the agent will follow the skill to address the prompt.

The agent uses a basic definition framework to create a project and return its link.

4. Let's ask a data question:

```
How many people saw each azb product in March?
```

This is a followup from our data mirror example. We are a little vague, intentionally, to demonstrate how the system processes and infers context. The LLM can respond with CJA data directly in our chat.

<img width="668" height="178" alt="AdobeExpressPhotos_1a34beef47cd40d68255a522bf65b6eb_CopyEdited" src="https://github.com/user-attachments/assets/62d5a583-af0b-4661-a37e-240148af1ac1" />

Your results will likely include a text representation of the product names and people counts.

<img width="855" height="305" alt="image" src="https://github.com/user-attachments/assets/85817e12-394d-4428-a969-104aa8ec0349" />

5. Save that report into a new project:

```
Save this in a project and give me the link.
```

<img width="1074" height="565" alt="AdobeExpressPhotos_0f2f44fbabe24d8bbf8614199feaa187_CopyEdited" src="https://github.com/user-attachments/assets/f1643179-05a4-4a97-b35f-effc14b5d836" />

6. Let it create a more interesting CJA project:

```
Create an e-commerce performance dashboard for the Luma retail data. Show revenue, orders, and conversion rate for the last 30 days, broken down by product category. Include a line chart for the daily revenue trend.
```

The agent responds with a proposed structure and builds it. It uses context from your skills, chat, common reporting and ecommerce knowledge, and existing components in CJA. Panels, visualizations, dimensions, metrics are all driven through that lens.

Hopefully, your result takes only a minute or two. The timing and result will vary with AI. If something looks wrong or your want a change, you would continue the conversation. Most often, even skill-based results require iterations to reach your exact goal.

> 💡 **Tip:** Be specific in your prompts. Whenever possible, use clear time ranges ("last 30 days"), metric names ("orders", "revenue"), and dimensions ("product category") when you know them.

7. Prepare a component survey project:

> 📝 **Note:** This will take a few minutes to run. We will continue into the lab, so you may open a new agent chat while this runs.

```
Build a survey for the top 15 dimensions in L611.
```

This will use a skill we named *dimension survey*. It addresses a common use case: working with a connection or data view I know little about. It finds the most used components and prepares a compact and organized view of them. The directions tell it to ignore the generic time or out-of-the-box dimensions. It can also pull only fields with at least two elements (not No Value).

I always wanted to build something like this. However, the volume of manual and tedious duplication activity in the UI prevented it - not to mention sorting by usage! It has been successful for approximately 60 dimensions and many panels.

It may take a few minutes but when running in the background it feels fast. This skill was the product of *many* iterative conversations, as is common.

> 💡 **Tip:** What manual or tedious tasks could this system build for you? Don't force a use case onto the feature, but dream big when scale and manual tasks are a blocker.

### 💡 2.5 Checkpoint

Discuss or reflect:

- Building that workspace manually would take 20–30 minutes. What would you build first for your own team using this approach?
- The agent called several MCP tools in sequence: `findDataViews`, `setDefaultSessionDataViewId`, `findMetrics`, `findDimensions`, `upsertProject`. You didn't need to know any of those tool names. What does that tell you about how MCP changes the analyst workflow?
- What's one thing you'd want to add to the workspace you just created?

---

## 🔍 Lesson 3 of 4 — Component Management

⏱️ Est. completion: 15 min *(Hands-on in Cursor — three skills)*

All operations in this lesson are **read-only** — the skills report and recommend but never modify anything without your explicit confirmation.

---

### 🎯 3.1 Objectives

By the end of this lesson you will be able to:

- Run a full component audit across segments and calculated metrics
- Interpret health scores, usage classifications, and duplicate flags
- Deep-dive into a dimension's cardinality and data quality
- Identify all projects using a specific component in preparation for a replacement

### 🩺 3.2 Exercise: Run a Component Audit

Over time, every CJA org accumulates component debt: segments nobody uses, calculated metrics that are near-identical copies of each other, components owned by people who left the team two years ago. The `cja-component-audit` skill scans your entire library and produces an actionable report — without touching a single thing.

1. Open a new Agent chat
2. Load the skill:

```
   @cja-component-audit
```

3. **Prompt:**

```
   Audit all my components on the [Data View Name] data view.
   Include segments and calculated metrics.
```

4. The agent works through seven phases:

| Phase             | What happens                                                          |
| ----------------- | --------------------------------------------------------------------- |
| 0 — Setup        | Confirms data view and component types                                |
| 1 — Inventory    | Pulls full component lists with metadata, definitions, and timestamps |
| 2 — Usage        | Classifies each component as Active, Stale, or Unused                 |
| 3 — Duplicates   | Compares definitions; flags near-identical formulas and names         |
| 4 — Dependencies | Maps which calculated metrics reference which segments                |
| 5 — Ownership    | Identifies who owns what and flags high concentrations                |
| 6 — Health       | Calculates a health score (0–100) per component type                 |
| 7 — Report       | Generates an HTML dashboard or markdown report                        |

5. When the report is ready, review:

- **Active / Stale / Unused** counts for segments and calculated metrics
- **Duplicate flags** — pairs with identical or near-identical definitions
- **Top recommendations** — what to delete, merge, rename, or archive

> 📝 **Note:** The audit is strictly read-only. It inventories and reports. It never deletes, modifies, or archives components.

> 💡 **Tip:** If the report is large, ask the agent to focus: *"Show me only the unused segments"* or *"Give me the top 5 consolidation recommendations."*

### 📊 3.3 Exercise: Analyze a Dimension

The `cja-dimension-analysis` skill gives you a deep view into a single dimension — how many unique values it has, how skewed the distribution is, whether there are anomalies, and whether there are data quality issues like unexpected gaps or high-cardinality spikes.

1. In the same or a new Agent chat:

```
   @cja-dimension-analysis
```

2. **Prompt:**

```
   Analyze the Product Category dimension.
   Show me cardinality, the top values by event count, and any data quality issues.
```

3. The agent returns:

- **Cardinality** — how many distinct values exist
- **Top-N distribution** — which values dominate and by how much
- **Skew** — Gini coefficient and top-N concentration
- **Data quality flags** — unexpected gaps, anomalous spikes, new/disappeared values

> 💡 **Tip:** You can ask follow-up questions: *"Which product categories have the most purchases?"* or *"Are there any category values that appeared recently and might be data quality issues?"*

### 🔎 3.4 Exercise: Find and Replace a Component

Before you can safely retire or replace a segment or calculated metric, you need to know which projects use it. The `cja-component-find-replace` skill finds every project that references a specific component, so you have a complete picture before making any changes.

1. Open a new Agent chat:

```
   @cja-component-find-replace
```

2. **Prompt — find affected projects:**

```
   Find all projects that use the segment "[Segment Name]"
```

   Use a segment name from your audit report in Exercise 3.2 — ideally one flagged as stale or a duplicate.
3. Review the list of affected projects. Note how many projects would be impacted.
4. **Prompt — plan the replacement:**

```
   What would I need to change if I wanted to replace it
   with the segment "[Better Segment Name]"?
```

   The agent describes the replacement plan: which projects to update and what the component swap looks like. Actual replacement happens only after your explicit confirmation.

> 💡 **Tip:** Combine with the audit: use the health report to identify a consolidation candidate (two near-duplicate segments), find all projects using the weaker one, then plan the migration to the better one.

### 💡 3.5 Checkpoint

- What health score did your component library receive? What was the most common issue?
- How would you incorporate a component audit into a regular governance cadence — monthly, quarterly, before a major analysis project?
- If you found that 40% of your segments were unused, what would be your first step before deleting them?

---

---

## 🧩 Lesson 4 of 4 — Segment Builder

⏱️ Est. completion: 15 min *(Hands-on in Cursor — deep dive on segmentation)*

You'll build a simple segment, a sequential segment, and attempt a challenge segment on your own. The `cja-segment-builder` skill handles the full workflow — finding existing duplicates, clarifying your intent, validating the definition, and creating — all with your confirmation before anything is saved.

---

### 🎯 4.1 Objectives

By the end of this lesson you will be able to:

- Build a general segment (AND/OR logic) from a plain-language description
- Build a sequential segment using THEN logic with a time restriction
- Understand the five key sequential pattern types in CJA
- Read and interpret the plain-language segment summary the agent produces before creation
- Apply the duplicate-check workflow to avoid segment bloat

### 🔨 4.2 Exercise: Build a Simple Segment

A general segment uses AND/OR logic to filter visitors, visits, or hits based on dimensions and metrics. This is the most common segment type.

1. Open a new Agent chat:

```
   @cja-segment-builder
```

2. **Prompt:**

```
   Create a segment for mobile visitors who viewed a product
   but didn't complete a purchase in the same session.
```

3. The agent first **checks for similar existing segments** using `findSegments` and `listSimilarTo`. Review what it finds — if a suitable segment already exists, you may not need to create a new one.
4. The agent then proposes the segment. It will show you:

- **Name** — a suggested name based on your description
- **Scope** — Visitor, Visit, or Hit level
- **Plain-language rules summary** — *"Visitor where: Device Type = Mobile AND visits containing at least one product view event AND no purchase events"*
- **Components referenced** — a table of dimensions and metrics with their IDs and how they're used

5. Review the proposal carefully. Ask for changes if needed: *"Change the scope to Visit level"* or *"Exclude cases where they removed the item from cart."*
6. When it looks right, confirm:

```
   Looks good, create it.
```

7. Note the segment ID the agent returns. You'll need it if you want to use this segment in a report or workspace.

> 💡 **Tip:** The more specific you are, the less the agent needs to ask. Include scope ("visit-level"), time windows ("within 7 days"), and explicit exclusions ("but not if they also completed a purchase later").

> 📝 **Note:** The agent never creates a segment without your explicit confirmation. It always shows you the plain-language summary and the components table first — treat this as your validation step.

### ⛓️ 4.3 Exercise: Build a Sequential Segment

Sequential segments use THEN logic — *"first X happened, then Y happened."* They are the most powerful segmentation capability in CJA and also the hardest to build manually. The JSON structure is complex and easy to get wrong. The segment builder handles it automatically.

1. In the same or a new Agent chat (the skill is already loaded):
2. **Prompt:**

```
   Create a segment for visitors who viewed the Collections page
   and then made a purchase within 2 days.
```

3. The agent identifies this as a sequential segment. It proposes:

- **Scope:** Visitor level
- **Sequence:** Checkpoint 1 → Page Name contains "collections" → THEN within 2 days → Checkpoint 2 → Event Type = purchase
- The underlying API structure uses `sequence` with a `time-restriction` element between checkpoints

4. Review the logic, then confirm:

```
   Yes, create it.
```

5. **Optional — test the segment:**

```
   Run a quick report with this segment to see how many visitors qualify over the last 30 days.
```

   The agent calls `runReport` with the new segment applied.

> 📖 **Sequential pattern reference:**
>
> | Pattern                       | What it means                                                    |
> | ----------------------------- | ---------------------------------------------------------------- |
> | **THEN**                | `sequence` — checkpoint A happened, then checkpoint B         |
> | **THEN within X days**  | `time-restriction` element between checkpoints in the sequence |
> | **Everything before X** | `sequence-suffix` — "only before X occurred"                  |
> | **Everything after X**  | `sequence-prefix` — "only after X occurred"                   |
> | **A not followed by B** | `sequence` with `exclude-next-checkpoint` — A then "not B"  |

### 🏆 4.4 Exercise: Complex Segment Challenge

Try building this segment on your own. It combines multiple concepts: a distinct count condition, scope nesting, and a date-based exclusion.

**Prompt to try:**

```
Build a segment for hits during sessions where the visitor
viewed at least 3 different product categories,
but exclude sessions that happened on December 27, 2025.
```

What the agent will need to do:

- Apply a **distinct count modifier** (3 distinct values of Product Category) at the visit level
- Apply a **visitor-level exclusion** for a specific date (Day = Dec 27, 2025, using its item ID)
- Nest the conditions correctly: visit-level condition AND visitor-level exclusion

Watch how the agent breaks down the problem and what clarifying questions it asks.

> 📝 **Note:** Building this segment manually in the CJA UI requires knowing about Distinct Count operators, correct container nesting, and how date dimensions are stored as item IDs. The agent handles all of this — your job is to describe the intent clearly.

### 💡 4.5 Checkpoint

Reflect on what you built:

- You just created three segments in 15 minutes — from plain language to live CJA segments. What would the same work look like without the MCP server?
- Look at the sequential segment. The underlying JSON for a `sequence` with a `time-restriction` is about 40 lines of nested objects. How does the agent's plain-language summary help you verify correctness without reading the JSON?
- Where else outside CJA could you use segment logic? *(Think: the same filtering logic you just described could describe a SQL WHERE clause or a BigQuery filter.)*

---

---

## 🎁 Bonus — Explore More

⏱️ Est. completion: 10 min *(Optional — try what interests you)*

---

### 🎯 B.1 Objectives

- See what else is possible with 25 CJA MCP tools
- Experience ad-hoc analysis and app generation through conversation
- Understand where the CJA MCP Server fits relative to Digital Insights Agent

### 🧪 B.2 Exercise: Try One of These

**⚖️ Option A — Comparative Analysis**

Compare two segments or two time periods side by side:

```
Compare revenue and conversion rate between mobile and desktop visitors
for the last 30 days. Then show me how this compares to the same period last month.
```

**🗺️ Option B — Metric Dependency Mapper**

Find out which of your calculated metrics depend on a specific base metric:

```
Show me which calculated metrics use the Orders metric as a component.
If you can, create a simple text map showing their dependencies.
```

**🚀 Option C — Build a Single-Page Dashboard App**

Go beyond the CJA UI entirely:

```
Using the Luma data, build a single-page HTML app that shows
the top 10 products by revenue with a bar chart.
Pull the data live through the CJA MCP tools and render it in the browser.
```

> 📝 **Note:** These prompts go beyond the structured exercises. They're meant to show what's possible when an agent has free access to 25 live CJA tools. Some may require follow-up clarifications.

### 🆚 B.3 MCP vs. Digital Insights Agent

The CJA MCP Server and Adobe's Digital Insights Agent (DIA) are complementary — not competing.

|                         | Digital Insights Agent (DIA)                                   | CJA MCP Server                                                               |
| ----------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| **What it is**    | Pre-built AI-guided analysis workflows within Experience Cloud | Open protocol layer that connects any MCP-capable AI client to live CJA data |
| **Best for**      | Guided, repeatable analysis flows for business users           | Custom, programmatic, and agentic workflows for analysts and developers      |
| **Client**        | Adobe Experience Cloud UI                                      | Cursor, Claude.ai, ChatGPT, or any MCP-compatible client                     |
| **Extensibility** | Adobe-managed                                                  | Scriptable, skill-based, fully extensible                                    |

Use DIA for structured guided analysis within Adobe's UI. Use the MCP Server when you want to write your own skills, combine CJA with other data sources, or drive workflows from an AI coding environment.

---

---

## 🏁 Wrap-up and Q&A

⏱️ Est. completion: 10 min

---

### 🔑 Key Takeaways

1. **Data Mirror** eliminates the export-schedule-import cycle. CDC keeps your CJA data in sync with your warehouse source of truth — inserts, updates, and deletes propagate automatically.
2. **The CJA MCP Server** makes your analytics conversational. Describe what you want; the agent builds it. Workspace creation, segment building, and component governance all work through natural language.
3. **Component governance at scale** is now manageable. A 7-phase audit across hundreds of segments and calculated metrics takes a few minutes of agent work, not a week of manual review.
4. **Segmentation is accessible to everyone.** From a simple AND/OR filter to a multi-step sequential segment with time restrictions — the segment builder handles the JSON complexity so you can focus on the logic.

### 🚀 Next Steps

**To connect the CJA MCP Server to your own org:**
See the *Remote MCPs for Analytics and CJA — Getting Started Guide* in the lab materials. It covers Cursor, Claude.ai, ChatGPT, and non-OAuth (server-to-server) clients.

**To set up Data Mirror for your warehouse:**
See the Data Mirror setup walkthrough in `1 data mirror/` — it covers BigQuery, Azure Blob Storage, and Amazon S3, including schema creation, CDC enablement, and the AEP source connector configuration.

**To explore more skills:**
Open `.cursor/skills/` in this repository. Skills available include: `cja-project-builder`, `cja-segment-builder`, `cja-segment-audit`, `cja-component-audit`, `cja-dimension-analysis`, `cja-component-find-replace`, and `cja-mcp-connectivity`.

**Both capabilities are currently in beta.** Your feedback matters 🙏 — share it with your Adobe team contact or submit it through the lab feedback form.

---

*🔴 Adobe Summit 2026 — Lab L611 — Data Mirror and MCP: Modern Connectivity for Customer Journey Analytics*

---

**References**

[1]: [Data Mirror Overview — Adobe Experience Platform XDM](https://experienceleague.adobe.com/en/docs/experience-platform/xdm/data-mirror/overview)
[2]: [Change Data Capture — Adobe Experience Platform Sources](https://experienceleague.adobe.com/en/docs/experience-platform/sources/api-tutorials/change-data-capture#data-mirror-with-relational-schemas)
