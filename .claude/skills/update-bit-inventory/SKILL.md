---
name: update-bit-inventory
description: Check email for router bit order updates and sync the inventory page — update statuses, flag new bits, clear delivered items.
allowed-tools: Read, Edit, Bash, Grep, Glob, mcp__claude_ai_Gmail__gmail_search_messages, mcp__claude_ai_Gmail__gmail_read_message, WebFetch, Skill
---

# Update Router Bit Inventory from Email

Scan email for recent router bit orders and shipping notifications, then update the inventory page to reflect current order statuses.

## Overview

The inventory lives at `workshop/router-bits/index.html`. Each bit is a `.card` inside a `.card-link` wrapper. Cards can have status classes:
- `.card.backorder` + `<span class="order-stamp">Backorder ~DATE</span>` — ordered but not yet shipped
- `.card.shipped` + `<span class="order-stamp">Shipped DATE</span>` — shipped, in transit
- No status class = in inventory (delivered/owned)

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

Only flag bits that are in the inventory (have a card in index.html). Report any ordered SKUs not in the inventory so the user can decide whether to add them.

## Step 4: Update the HTML

Read `workshop/router-bits/index.html` and for each bit that needs a status change:

**To add a backorder stamp:**
Change `<div class="card"` to `<div class="card backorder"` and add `<span class="order-stamp">Backorder ~DATE</span>` as the first child inside the card div (before the brand badge).

**To add a shipped stamp:**
Change `<div class="card"` to `<div class="card shipped"` and add `<span class="order-stamp">Shipped DATE</span>` as the first child.

**To clear a status** (delivered / no longer pending):
Remove `backorder` or `shipped` from the card's class list, and remove the `<span class="order-stamp">...</span>` element.

**To add a new bit** that isn't in the inventory yet:
Invoke `/add-bit {SKU} --status backorder --status-date {date}` (or `--status shipped --status-date {date}`) for each new SKU found in orders. The add-bit skill handles vendor resolution, image fetching, and card insertion automatically.

## Step 5: Summarize changes

Report to the user:
- Which cards were updated (and to what status)
- Which statuses were cleared (delivered)
- Which ordered SKUs are not yet in the inventory
- Any ambiguous cases (e.g. couldn't match a SKU, partial shipment)

Do NOT commit, push, or deploy — let the user review and decide.
