"""
============================================================
  Personal Expense Tracker  —  CLI Application
  As specified in the PDF project requirements

  Language  : Python 3
  Libraries : csv, datetime, os, matplotlib
  Storage   : expenses_data.csv (auto-load on start,
              auto-save on exit)
============================================================
"""

import csv
import os
from datetime import datetime
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from collections import defaultdict

# ──────────────────────────────────────────────
#  CONFIGURATION
# ──────────────────────────────────────────────
DATA_FILE      = "expenses_data.csv"
DATE_FORMAT    = "%Y-%m-%d"
DISPLAY_FORMAT = "%d %b %Y"          # e.g.  28 Sep 2026
VALID_CATEGORIES = [
    "Food", "Transport", "Entertainment", "Shopping",
    "Education", "Bills", "Health", "Travel", "Other"
]

CHART_COLORS = [
    "#6366f1", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981",
    "#06b6d4", "#f97316", "#84cc16", "#e11d48", "#0ea5e9"
]

# In-memory expense store
expenses: list = []


# ══════════════════════════════════════════════
#  UTILITY HELPERS
# ══════════════════════════════════════════════

def separator(char="─", width=60):
    """Print a horizontal separator line."""
    print(char * width)


def header(title, width=60):
    """Print a formatted section header."""
    print()
    separator("═", width)
    print(f"  {title}")
    separator("═", width)


def _parse_date(date_str):
    """Try multiple date formats; return datetime or None."""
    for fmt in (DATE_FORMAT, "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            pass
    return None


def _format_date(date_str):
    """Return a human-friendly date string."""
    dt = _parse_date(date_str)
    return dt.strftime(DISPLAY_FORMAT) if dt else date_str


def _month_key(date_str):
    """Return 'YYYY-MM' key for month grouping."""
    dt = _parse_date(date_str)
    return dt.strftime("%Y-%m") if dt else "unknown"


def _week_key(date_str):
    """Return 'YYYY-W<wk>' key for ISO week grouping."""
    dt = _parse_date(date_str)
    return dt.strftime("%Y-W%V") if dt else "unknown"


def _input_amount(prompt):
    """Keep asking until a valid positive float is entered."""
    while True:
        raw = input(prompt).strip()
        try:
            value = float(raw)
            if value <= 0:
                print("  ⚠  Amount must be greater than 0. Please try again.")
            else:
                return value
        except ValueError:
            print(f"  ⚠  '{raw}' is not a valid number. Please try again.")


def _input_date(prompt):
    """Keep asking until a valid date is entered; blank = today."""
    while True:
        raw = input(prompt).strip()
        if raw == "":
            today = datetime.today().strftime(DATE_FORMAT)
            print(f"  ℹ  No date entered — using today ({_format_date(today)}).")
            return today
        dt = _parse_date(raw)
        if dt:
            return dt.strftime(DATE_FORMAT)
        print(f"  ⚠  Cannot parse '{raw}'. Use YYYY-MM-DD (e.g. 2026-09-28).")


def _input_category():
    """Display category menu and return chosen category name."""
    print()
    print("  Available categories:")
    for i, cat in enumerate(VALID_CATEGORIES, 1):
        print(f"    {i:>2}. {cat}")
    print()
    while True:
        raw = input("  Select category number (or type name): ").strip()
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(VALID_CATEGORIES):
                return VALID_CATEGORIES[idx]
            print(f"  ⚠  Enter a number between 1 and {len(VALID_CATEGORIES)}.")
        except ValueError:
            match = next((c for c in VALID_CATEGORIES if c.lower() == raw.lower()), None)
            if match:
                return match
            print("  ⚠  Invalid choice. Enter the number or category name.")


# ══════════════════════════════════════════════
#  CSV PERSISTENCE
# ══════════════════════════════════════════════

def load_expenses():
    """Load expenses from DATA_FILE into memory on startup."""
    global expenses
    expenses = []

    if not os.path.exists(DATA_FILE):
        return  # First run — no file yet

    try:
        with open(DATA_FILE, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    expenses.append({
                        "date"    : row["date"].strip(),
                        "category": row["category"].strip(),
                        "amount"  : float(row["amount"]),
                        "note"    : row.get("note", "").strip(),
                    })
                except (KeyError, ValueError):
                    pass  # Skip malformed rows
        print(f"  ✔  Loaded {len(expenses)} expense(s) from '{DATA_FILE}'.")
    except Exception as exc:
        print(f"  ⚠  Could not read '{DATA_FILE}': {exc}")
        expenses = []


def save_expenses():
    """Persist all in-memory expenses to DATA_FILE."""
    try:
        with open(DATA_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["date", "category", "amount", "note"])
            writer.writeheader()
            writer.writerows(expenses)
        print(f"  ✔  Saved {len(expenses)} expense(s) to '{DATA_FILE}'.")
    except Exception as exc:
        print(f"  ✗  Failed to save data: {exc}")


# ══════════════════════════════════════════════
#  FEATURE 1 — ADD EXPENSE
# ══════════════════════════════════════════════

def add_expense():
    """Collect expense details interactively and store them."""
    header("ADD NEW EXPENSE")

    amount   = _input_amount("  Amount (Rs.): ")
    category = _input_category()
    date_str = _input_date("  Date (YYYY-MM-DD, blank = today): ")
    note     = input("  Note / Description (optional): ").strip()

    expense = {"date": date_str, "category": category,
               "amount": amount, "note": note}
    expenses.append(expense)

    print()
    separator()
    print("  ✔  Expense added successfully!")
    print(f"       Amount   : Rs.{amount:,.2f}")
    print(f"       Category : {category}")
    print(f"       Date     : {_format_date(date_str)}")
    if note:
        print(f"       Note     : {note}")
    separator()


# ══════════════════════════════════════════════
#  FEATURE 2 — VIEW ALL EXPENSES
# ══════════════════════════════════════════════

def view_expenses():
    """Display all expenses in a formatted table."""
    header("ALL EXPENSES")

    if not expenses:
        print("  No expenses recorded yet. Use option 1 to add one.")
        return

    sorted_exp = sorted(expenses, key=lambda e: e["date"], reverse=True)
    row_fmt    = "{:<4}  {:<14}  {:<15}  {:>13}  {}"

    print(row_fmt.format("#", "Date", "Category", "Amount (Rs.)", "Note"))
    separator("-")
    for i, exp in enumerate(sorted_exp, 1):
        note = exp["note"][:20] + "..." if len(exp["note"]) > 20 else exp["note"]
        print(row_fmt.format(
            i, _format_date(exp["date"]), exp["category"],
            f"Rs.{exp['amount']:,.2f}", note or "—"
        ))

    separator()
    total = sum(e["amount"] for e in expenses)
    print(f"  Total ({len(expenses)} expense{'s' if len(expenses) != 1 else ''}):  Rs.{total:,.2f}")
    separator()


# ══════════════════════════════════════════════
#  FEATURE 3 — GENERATE REPORT
# ══════════════════════════════════════════════

def generate_report():
    """Generate a comprehensive summary report in the terminal."""
    header("EXPENSE REPORT")

    if not expenses:
        print("  No data available. Add some expenses first.")
        return

    amounts = [e["amount"] for e in expenses]
    total   = sum(amounts)
    count   = len(amounts)
    average = total / count
    highest = max(expenses, key=lambda e: e["amount"])
    lowest  = min(expenses, key=lambda e: e["amount"])

    # Overall summary
    print("  OVERALL SUMMARY")
    separator("-")
    print(f"  Total Expenses       : Rs.{total:>12,.2f}")
    print(f"  Number of Expenses   : {count:>13,}")
    print(f"  Average per Expense  : Rs.{average:>12,.2f}")
    print(f"  Highest Expense      : Rs.{highest['amount']:>12,.2f}  "
          f"({highest['category']}, {_format_date(highest['date'])})")
    print(f"  Lowest Expense       : Rs.{lowest['amount']:>12,.2f}  "
          f"({lowest['category']}, {_format_date(lowest['date'])})")

    # Category breakdown
    cat_totals = defaultdict(float)
    cat_counts = defaultdict(int)
    for e in expenses:
        cat_totals[e["category"]] += e["amount"]
        cat_counts[e["category"]] += 1

    print()
    print("  CATEGORY BREAKDOWN")
    separator("-")
    print("  {:<18}  {:>13}  {:>8}  {:>8}".format(
        "Category", "Total (Rs.)", "Count", "Share %"))
    separator("-")
    for cat, amt in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True):
        share = (amt / total * 100) if total else 0
        bar   = "|" * int(share / 2)
        print("  {:<18}  {:>13,.2f}  {:>8,}  {:>7.1f}%  {}".format(
            cat, amt, cat_counts[cat], share, bar))

    # Monthly breakdown
    month_totals = defaultdict(float)
    for e in expenses:
        month_totals[_month_key(e["date"])] += e["amount"]

    print()
    print("  MONTHLY BREAKDOWN")
    separator("-")
    max_m = max(month_totals.values()) if month_totals else 1
    for month, amt in sorted(month_totals.items()):
        dt    = datetime.strptime(month + "-01", "%Y-%m-%d")
        label = dt.strftime("%B %Y")
        bar   = "#" * int(amt / max_m * 30)
        print(f"  {label:<16}  Rs.{amt:>10,.2f}  {bar}")

    # Weekly breakdown
    week_totals = defaultdict(float)
    for e in expenses:
        week_totals[_week_key(e["date"])] += e["amount"]

    if len(week_totals) > 1:
        print()
        print("  WEEKLY BREAKDOWN")
        separator("-")
        max_w = max(week_totals.values())
        for week, amt in sorted(week_totals.items()):
            bar = "#" * int(amt / max_w * 30)
            print(f"  {week:<14}  Rs.{amt:>10,.2f}  {bar}")

    # Current month snapshot
    current_month = datetime.today().strftime("%Y-%m")
    m_expenses    = [e for e in expenses if _month_key(e["date"]) == current_month]
    if m_expenses:
        m_total = sum(e["amount"] for e in m_expenses)
        print()
        separator("-")
        print(f"  Current Month ({datetime.today().strftime('%B %Y')}): "
              f"Rs.{m_total:,.2f}  ({len(m_expenses)} transaction"
              f"{'s' if len(m_expenses) != 1 else ''})")

    separator()


# ══════════════════════════════════════════════
#  FEATURE 4 — SHOW CHARTS (matplotlib)
# ══════════════════════════════════════════════

def show_charts():
    """
    Display three matplotlib charts:
      1. Bar chart  — spending by category
      2. Pie chart  — category share distribution
      3. Line chart — monthly spending trend
    """
    header("SPENDING CHARTS")

    if not expenses:
        print("  No data to plot. Add some expenses first.")
        return

    # Build data
    cat_totals   = defaultdict(float)
    month_totals = defaultdict(float)
    for e in expenses:
        cat_totals[e["category"]] += e["amount"]
        month_totals[_month_key(e["date"])] += e["amount"]

    categories   = list(cat_totals.keys())
    cat_amounts  = [cat_totals[c] for c in categories]

    months        = sorted(month_totals.keys())
    month_labels  = [datetime.strptime(m + "-01", "%Y-%m-%d").strftime("%b %Y")
                     for m in months]
    month_amounts = [month_totals[m] for m in months]

    n_colors = max(len(categories), len(months))
    colors   = (CHART_COLORS * ((n_colors // len(CHART_COLORS)) + 1))[:len(categories)]

    # Create figure
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle("Personal Expense Tracker — Spending Analysis",
                 fontsize=14, fontweight="bold")
    fig.patch.set_facecolor("#f8fafc")
    for ax in axes:
        ax.set_facecolor("#f1f5f9")

    # Chart 1: Bar — by category
    ax1 = axes[0]
    bars = ax1.bar(categories, cat_amounts, color=colors,
                   edgecolor="white", linewidth=0.8, zorder=3)
    ax1.set_title("Spending by Category", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Category", fontsize=10)
    ax1.set_ylabel("Amount (Rs.)", fontsize=10)
    ax1.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"Rs.{x:,.0f}"))
    ax1.tick_params(axis="x", rotation=30, labelsize=9)
    ax1.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)
    ax1.set_axisbelow(True)
    for bar, amount in zip(bars, cat_amounts):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(cat_amounts) * 0.01,
            f"Rs.{amount:,.0f}",
            ha="center", va="bottom", fontsize=8, fontweight="bold"
        )

    # Chart 2: Pie — category share
    ax2 = axes[1]
    wedges, texts, autotexts = ax2.pie(
        cat_amounts, labels=categories, colors=colors,
        autopct="%1.1f%%", startangle=140,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
        pctdistance=0.8,
    )
    for t in texts:
        t.set_fontsize(9)
    for at in autotexts:
        at.set_fontsize(8)
        at.set_fontweight("bold")
    ax2.set_title("Category Distribution", fontsize=12, fontweight="bold")

    # Chart 3: Line — monthly trend
    ax3 = axes[2]
    if len(months) >= 2:
        ax3.plot(
            month_labels, month_amounts,
            marker="o", color="#6366f1", linewidth=2.5,
            markersize=8, markerfacecolor="white",
            markeredgecolor="#6366f1", markeredgewidth=2, zorder=3
        )
        ax3.fill_between(range(len(months)), month_amounts,
                         alpha=0.15, color="#6366f1")
        ax3.set_xticks(range(len(months)))
        ax3.set_xticklabels(month_labels, fontsize=9, rotation=20)
    else:
        ax3.bar(month_labels, month_amounts, color="#6366f1",
                edgecolor="white", zorder=3)
        ax3.tick_params(axis="x", rotation=20, labelsize=9)

    ax3.set_title("Monthly Spending Trend", fontsize=12, fontweight="bold")
    ax3.set_xlabel("Month", fontsize=10)
    ax3.set_ylabel("Amount (Rs.)", fontsize=10)
    ax3.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"Rs.{x:,.0f}"))
    ax3.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)
    ax3.set_axisbelow(True)
    for xi, yi in enumerate(month_amounts):
        ax3.text(xi, yi + max(month_amounts) * 0.02,
                 f"Rs.{yi:,.0f}", ha="center", va="bottom",
                 fontsize=8, fontweight="bold")

    plt.tight_layout()
    print("  Opening charts window… (close window to return to menu)")
    plt.show()
    print("  ✔  Charts closed.")


# ══════════════════════════════════════════════
#  FEATURE 5 — SEARCH / FILTER
# ══════════════════════════════════════════════

def search_expenses():
    """Search expenses by category, keyword, or month."""
    header("SEARCH / FILTER EXPENSES")

    print("  Search by:")
    print("    1. Category")
    print("    2. Keyword (in note or category)")
    print("    3. Month (YYYY-MM)")
    print()
    choice = input("  Enter choice (1-3): ").strip()

    results = []

    if choice == "1":
        print()
        for i, cat in enumerate(VALID_CATEGORIES, 1):
            print(f"    {i:>2}. {cat}")
        raw = input("\n  Select category number: ").strip()
        try:
            cat = VALID_CATEGORIES[int(raw) - 1]
            results = [e for e in expenses if e["category"] == cat]
            filter_label = f"Category: {cat}"
        except (ValueError, IndexError):
            print("  ⚠  Invalid choice.")
            return

    elif choice == "2":
        keyword = input("  Enter keyword: ").strip().lower()
        results = [e for e in expenses
                   if keyword in e["note"].lower() or keyword in e["category"].lower()]
        filter_label = f"Keyword: '{keyword}'"

    elif choice == "3":
        month = input("  Enter month (YYYY-MM): ").strip()
        try:
            datetime.strptime(month, "%Y-%m")
            results = [e for e in expenses if _month_key(e["date"]) == month]
            dt_label = datetime.strptime(month + "-01", "%Y-%m-%d").strftime("%B %Y")
            filter_label = f"Month: {dt_label}"
        except ValueError:
            print("  ⚠  Invalid month format. Use YYYY-MM.")
            return
    else:
        print("  ⚠  Invalid choice.")
        return

    print(f"\n  Filter: {filter_label}")
    if not results:
        print("  No matching expenses found.")
        return

    separator("-")
    row_fmt = "{:<4}  {:<14}  {:<15}  {:>13}  {}"
    print(row_fmt.format("#", "Date", "Category", "Amount (Rs.)", "Note"))
    separator("-")
    for i, exp in enumerate(sorted(results, key=lambda e: e["date"], reverse=True), 1):
        note = exp["note"][:20] + "..." if len(exp["note"]) > 20 else exp["note"]
        print(row_fmt.format(
            i, _format_date(exp["date"]), exp["category"],
            f"Rs.{exp['amount']:,.2f}", note or "—"
        ))
    separator()
    total = sum(e["amount"] for e in results)
    print(f"  {len(results)} result(s)  |  Total: Rs.{total:,.2f}")
    separator()


# ══════════════════════════════════════════════
#  FEATURE 6 — DELETE AN EXPENSE
# ══════════════════════════════════════════════

def delete_expense():
    """Show numbered list; delete the selected entry after confirmation."""
    header("DELETE AN EXPENSE")

    if not expenses:
        print("  No expenses to delete.")
        return

    view_expenses()

    print()
    raw = input("  Enter the # to delete (0 = cancel): ").strip()
    try:
        idx = int(raw)
        if idx == 0:
            print("  ℹ  Deletion cancelled.")
            return
        sorted_exp = sorted(expenses, key=lambda e: e["date"], reverse=True)
        if not (1 <= idx <= len(sorted_exp)):
            print("  ⚠  Invalid number.")
            return
        target  = sorted_exp[idx - 1]
        confirm = input(
            f"  Delete Rs.{target['amount']:,.2f} — {target['category']} "
            f"on {_format_date(target['date'])}? (y/n): "
        ).strip().lower()
        if confirm == "y":
            expenses.remove(target)
            print("  ✔  Expense deleted.")
        else:
            print("  ℹ  Deletion cancelled.")
    except (ValueError, IndexError):
        print("  ⚠  Invalid input.")


# ══════════════════════════════════════════════
#  MAIN MENU — Interactive loop
# ══════════════════════════════════════════════

MENU = """
  ╔══════════════════════════════════════════╗
  ║       PERSONAL EXPENSE TRACKER  v1.0    ║
  ╠══════════════════════════════════════════╣
  ║  1.  Add Expense                         ║
  ║  2.  View All Expenses                   ║
  ║  3.  Generate Report                     ║
  ║  4.  Show Charts  (matplotlib)           ║
  ║  5.  Search / Filter Expenses            ║
  ║  6.  Delete an Expense                   ║
  ║  7.  Save & Exit                         ║
  ╚══════════════════════════════════════════╝
"""

ACTIONS = {
    "1": add_expense,
    "2": view_expenses,
    "3": generate_report,
    "4": show_charts,
    "5": search_expenses,
    "6": delete_expense,
}


def main():
    """Entry point — load data, then run the interactive menu loop."""
    print()
    separator("═")
    print("  Welcome to Personal Expense Tracker")
    separator("═")
    load_expenses()

    while True:
        print(MENU)
        choice = input("  Select an option (1-7): ").strip()

        if choice == "7":
            save_expenses()
            print()
            separator("═")
            print("  Goodbye! Your expenses have been saved.")
            separator("═")
            print()
            break
        elif choice in ACTIONS:
            try:
                ACTIONS[choice]()
            except KeyboardInterrupt:
                print("\n  ℹ  Operation cancelled. Returning to menu…")
            except Exception as exc:
                print(f"\n  ✗  Unexpected error: {exc}")
        else:
            print("  ⚠  Invalid option. Please enter a number from 1 to 7.")

        input("\n  Press Enter to continue…")


if __name__ == "__main__":
    main()
