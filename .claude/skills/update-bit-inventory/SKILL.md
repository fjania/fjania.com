---
name: update-bit-inventory
description: Check email for router bit order updates and sync the inventory YAML files — update statuses, flag new bits, clear delivered items.
allowed-tools: Read, Edit, Bash, Grep, Glob, mcp__claude_ai_Gmail__gmail_search_messages, mcp__claude_ai_Gmail__gmail_read_message, WebFetch, Skill
---

# Update Router Bit Inventory from Email

Scan email for recent router bit orders and shipping notifications, then update the inventory YAML files to reflect current order statuses.

## Overview

The inventory is stored as individual YAML files in `workshop/src/content/bits/`. Each file has `status` and `status_date` fields:
- `status: in-stock` — owned, in inventory
- `status: backorder` with `status_date: ~DATE` — ordered but not yet shipped
- `status: shipped` with `status_date: DATE` — shipped, in transit
- `status: ordered` with `status_date: DATE` — ordered, being processed

## Step 1: Search email for recent orders

Search Gmail for order confirmations and shipping notifications from approved vendors:

```
mcp__claude_ai_Gmail__gmail_search_messages
q: "from:woodpeck.com OR from:bitsandbits.com OR from:whitesiderouterbits.com (order OR shipping OR backorder OR delivered OR tracking)"
maxResults: 30
```

## Step 2: Read the relevant emails

Read each order confirmation and shipping email. Extract:

**From order confirmations:**
- SKU(s) ordered
- Product name(s)
- Whether the item is backordered (look for `backorder-message` div or "Sold Out! Reserve Yours" text)
- Estimated ship date if backordered
- Order number (Web/PO number maps to the shipping email's order number)

**From shipping emails:**
- Order number (in subject line: "Order XXXXXXXXXX Shipped")
- Web/PO number (in the body, maps to order confirmation number)
- SKU(s) shipped
- Back-ordered quantity (column in the item table — if >0, that SKU is still pending)
- Ship date

**Key patterns in Woodpeckers emails:**
- Order confirmations: Subject "Your Woodpeckers LLC order confirmation", from `mailroom@woodpeck.com`. SKUs are in `<p class="sku">SKU: XXXXX</p>`. Backorder messages are in `<div class="backorder-message">`.
- Shipping emails: Subject "Order XXXXXXXXXX Shipped", from `mailroom@woodpeck.com`. Items are in an HTML table with columns: Item, Description, Quantity Ordered, Back Ordered, Quantity Shipped.
- Sets (e.g. US57BD-3PC) contain individual SKUs listed with `..` prefix (e.g. `..US57125BD`).

## Step 3: Build the status map

Cross-reference orders with shipments to determine current status of each SKU:

| Scenario | Status |
|---|---|
| Ordered, no shipping email yet, has backorder message | **backorder** with estimated date |
| Ordered, no shipping email yet, no backorder message | **ordered** (processing) |
| Shipping email exists, back-ordered qty = 0 | **shipped** with ship date |
| Shipping email exists, back-ordered qty > 0 | Partially shipped — the backordered portion is still **backorder** |
| Shipped and enough time has passed (>7 days) | Likely **delivered** — clear the status |

Only flag bits that are in the inventory (have a YAML file in `workshop/src/content/bits/`). Report any ordered SKUs not in the inventory so the user can decide whether to add them.

## Step 4: Update the YAML files

For each bit that needs a status change, edit the YAML file in `workshop/src/content/bits/`:

**To set backorder:**
Change `status: in-stock` to `status: backorder` and `status_date: null` to `status_date: ~DATE`

**To set shipped:**
Change status to `status: shipped` and set `status_date: DATE`

**To set ordered:**
Change status to `status: ordered` and set `status_date: DATE`

**To clear a status (delivered):**
Change status to `status: in-stock` and set `status_date: null`

**To add a new bit** that isn't in the inventory yet:
Invoke `/add-bit {SKU} --status backorder --status-date {date}` (or `--status shipped --status-date {date}`) for each new SKU found in orders. The add-bit skill handles vendor resolution, image fetching, and YAML creation automatically.

## Step 5: Summarize changes

Report to the user:
- Which YAML files were updated (and to what status)
- Which statuses were cleared (delivered)
- Which ordered SKUs are not yet in the inventory
- Any ambiguous cases (e.g. couldn't match a SKU, partial shipment)

Do NOT commit, push, or deploy — let the user review and decide.
