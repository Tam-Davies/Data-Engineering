# ============================================================
#  Power BI Connection Guide + DAX Measures
#  File: powerbi/POWERBI_SETUP.md
# ============================================================

# Power BI → PostgreSQL Setup Guide

## 1. Prerequisites

- Power BI Desktop (free download from Microsoft)
- PostgreSQL ODBC Driver: https://www.postgresql.org/ftp/odbc/versions/
- Your PostgreSQL server running with `ordr_db` database populated

---

## 2. Connect Power BI to PostgreSQL

1. Open **Power BI Desktop**
2. Click **Home → Get Data → More…**
3. Search for **PostgreSQL** → Connect
4. Fill in:
   - **Server:** `localhost` (or your server IP)
   - **Database:** `ordr_db`
5. Select **DirectQuery** (for live data) or **Import** (for snapshots)
6. Enter credentials: your PostgreSQL username + password
7. Click **Connect**

---

## 3. Tables to Import

Select these tables in the Navigator:

| Table | Purpose |
|-------|---------|
| `orders` | Raw order transactions |
| `order_items` | Line items per order |
| `menu_items` | Menu reference |
| `menu_categories` | Category reference |
| `staff` | Staff reference |
| `restaurant_tables` | Table reference |
| `sales_daily` | Pre-aggregated daily summaries |
| `sales_weekly` | Pre-aggregated weekly summaries |
| `sales_monthly` | Pre-aggregated monthly summaries |
| `alert_log` | Alert history |

---

## 4. Relationships (set in Model view)

```
orders.table_id        → restaurant_tables.id   (Many-to-One)
orders.staff_id        → staff.id               (Many-to-One)
order_items.order_id   → orders.id              (Many-to-One)
order_items.menu_item_id → menu_items.id        (Many-to-One)
menu_items.category_id → menu_categories.id     (Many-to-One)
```

---

## 5. DAX Measures

Paste these into **Modeling → New Measure**:

### Revenue Measures

```dax
-- Total Revenue (paid orders only)
Total Revenue = 
CALCULATE(
    SUM(orders[total]),
    orders[status] = "paid"
)

-- Today's Revenue
Revenue Today = 
CALCULATE(
    [Total Revenue],
    DATESINPERIOD(orders[created_at], TODAY(), -1, DAY)
)

-- This Week's Revenue
Revenue This Week = 
CALCULATE(
    [Total Revenue],
    DATESINPERIOD(orders[created_at], TODAY(), -7, DAY)
)

-- This Month's Revenue
Revenue This Month = 
CALCULATE(
    [Total Revenue],
    DATESMTD(orders[created_at])
)

-- Previous Day Revenue
Revenue Yesterday = 
CALCULATE(
    [Total Revenue],
    DATEADD(orders[created_at], -1, DAY)
)

-- Day-over-Day % Change
DoD Revenue Change % = 
VAR today_rev = [Revenue Today]
VAR yest_rev  = [Revenue Yesterday]
RETURN
    IF(
        yest_rev = 0, BLANK(),
        DIVIDE(today_rev - yest_rev, yest_rev) * 100
    )

-- Week-over-Week % Change
WoW Revenue Change % = 
VAR this_week = [Revenue This Week]
VAR last_week = CALCULATE([Total Revenue],
    DATEADD(DATESPERIOD(orders[created_at], 
        TODAY() - WEEKDAY(TODAY(),2), -7, DAY), -7, DAY))
RETURN
    IF(last_week = 0, BLANK(), DIVIDE(this_week - last_week, last_week) * 100)

-- Month-over-Month % Change
MoM Revenue Change % = 
VAR this_month  = [Revenue This Month]
VAR last_month  = CALCULATE([Total Revenue], DATEADD(DATESMTD(orders[created_at]), -1, MONTH))
RETURN
    IF(last_month = 0, BLANK(), DIVIDE(this_month - last_month, last_month) * 100)
```

### Order Count Measures

```dax
-- Total Orders
Total Orders = 
CALCULATE(COUNTROWS(orders), orders[status] = "paid")

-- Orders Today
Orders Today = 
CALCULATE([Total Orders], DATESINPERIOD(orders[created_at], TODAY(), -1, DAY))

-- Average Order Value
Avg Order Value = DIVIDE([Total Revenue], [Total Orders])
```

### Item Performance

```dax
-- Total Items Sold
Items Sold = SUM(order_items[qty])

-- Top Item by Revenue
Top Item Revenue = 
MAXX(
    TOPN(1, SUMMARIZE(order_items, menu_items[name],
        "rev", SUMX(order_items, order_items[price] * order_items[qty])),
    [rev], DESC),
    menu_items[name]
)
```

---

## 6. Suggested Visuals

| Visual Type | Fields | Purpose |
|-------------|--------|---------|
| Card | Revenue Today, DoD Change % | Daily snapshot |
| Card | Revenue This Month, MoM Change % | Monthly snapshot |
| Line chart | Date → Total Revenue | Revenue trend |
| Bar chart | menu_items[name] → Items Sold | Top items |
| Bar chart | staff[name] → Total Orders | Staff performance |
| Donut | menu_categories[name] → Total Revenue | Revenue by category |
| Table | orders[id], total, status, created_at | Live order feed |
| KPI visual | Revenue Today vs Revenue Yesterday | DoD comparison |
| Matrix | Year × Month → Total Revenue | Revenue calendar |

---

## 7. Auto-refresh (Power BI Service)

1. Publish your report to **Power BI Service**
2. Go to **Dataset Settings → Scheduled Refresh**
3. Set refresh to every **30 minutes** (matches pipeline cadence)
4. For DirectQuery, data is always live — no refresh needed

---

## 8. Alerts in Power BI (optional)

1. Pin a card visual (e.g. Revenue Today) to a dashboard
2. Click the bell icon → **Manage Alerts**
3. Set threshold (e.g. alert if daily revenue < ₦50,000)
4. Power BI will email you when the threshold is breached

> These work alongside the Python alert engine — use both for redundancy.
