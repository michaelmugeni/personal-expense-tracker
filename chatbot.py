"""
chatbot.py
----------
A lightweight, rule-based assistant for the Personal Expense Tracker.

It does NOT call any external API - everything runs locally with simple
keyword matching. This keeps it fast, free, and fully offline, which is
ideal for a course project (no API keys, no network dependency, no cost).

Usage (from app.py):

    from chatbot import get_bot_response
    reply = get_bot_response(user_message)
"""

import random

# ---------------------------------------------------------------------
# Finance tips shown when the user asks for advice / savings tips
# ---------------------------------------------------------------------
FINANCE_TIPS = [
    "Try the 50/30/20 rule: 50% of income to needs, 30% to wants, and 20% to savings or debt repayment.",
    "Set your monthly budget on the Profile page first - it's what powers the 'Budget Remaining' figure on your dashboard.",
    "Review your Summary page weekly, not just at month-end. Small course-corrections early are easier than big ones late.",
    "Categorize every expense, even small ones - your 'Top Category' stat is only useful if the data is complete.",
    "Before a purchase, ask: 'Would I still buy this if I had to log it right now?' Logging friction is a great impulse-spending check.",
    "Automate savings the same way you log expenses: treat 'savings' like a fixed monthly bill, not a leftover.",
    "Use the Export to Excel/CSV feature to review your last 3 months side-by-side - trends are easier to spot across months than within one.",
    "Keep an emergency fund goal separate from your monthly budget - it shouldn't compete with everyday spending categories.",
    "If one category keeps blowing past budget, don't just cut it - check if it's mis-categorized first, using Filter + Search.",
    "Round up small purchases mentally (e.g. treat 480 as 500) - it builds in a small buffer against underestimating spend.",
]

# ---------------------------------------------------------------------
# Intent -> (keywords, response) rules.
# Checked top to bottom; first matching intent wins.
# ---------------------------------------------------------------------
INTENTS = [
    {
        "name": "greeting",
        "keywords": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"],
        "response": (
            "Hi! I'm your Expense Tracker assistant. I can walk you through any "
            "feature (adding expenses, budgets, filters, exports, profile, dark mode) "
            "or share a quick finance tip. What would you like help with?"
        ),
    },
    {
        "name": "add_expense",
        "keywords": ["add expense", "log expense", "new expense", "record expense", "how do i add", "enter expense"],
        "response": (
            "To add an expense: open 'Add Expense' from the sidebar, choose a category, "
            "enter the amount, an optional description, and the date, then click "
            "'Save Expense'. It'll appear immediately on your Dashboard."
        ),
    },
    {
        "name": "edit_expense",
        "keywords": ["edit expense", "update expense", "change expense", "modify expense", "wrong amount"],
        "response": (
            "To edit an expense, go to your Dashboard's 'Recent Transactions' table and "
            "click the pencil icon on the row you want to change. Update the amount, "
            "description or date, then save."
        ),
    },
    {
        "name": "delete_expense",
        "keywords": ["delete expense", "remove expense", "delete a transaction"],
        "response": (
            "To delete an expense, find it in the Dashboard's transaction table and click "
            "the trash icon. You'll get a confirmation prompt first, since this can't be undone."
        ),
    },
    {
        "name": "budget",
        "keywords": ["budget", "monthly limit", "spending limit", "how much can i spend"],
        "response": (
            "Set your monthly budget on the Profile page, under 'Monthly Budget'. Once saved, "
            "your Dashboard automatically shows 'Budget Remaining' - your budget minus what "
            "you've spent so far this month."
        ),
    },
    {
        "name": "filter_search",
        "keywords": ["filter", "search", "sort", "find expense", "narrow down"],
        "response": (
            "On the Dashboard, use the filter bar above the transaction table: pick a category, "
            "a date range, or type a keyword to search descriptions. You can also sort results "
            "by date or amount, ascending or descending."
        ),
    },
    {
        "name": "export",
        "keywords": ["export", "download", "pdf", "excel", "csv", "report"],
        "response": (
            "You can export your expense history in three formats from the Dashboard: "
            "PDF (formatted report), Excel (.xlsx), or CSV - look for the buttons above the "
            "transaction table."
        ),
    },
    {
        "name": "profile",
        "keywords": ["profile", "picture", "photo", "avatar", "username", "email", "account settings"],
        "response": (
            "On the Profile page you can update your username and email, and upload a new "
            "profile picture (PNG, JPG, GIF or WEBP). Click 'Save Changes' when you're done."
        ),
    },
    {
        "name": "theme",
        "keywords": ["dark mode", "light mode", "theme", "night mode"],
        "response": (
            "Click the toggle switch in the top-right corner of any page to switch between "
            "light and dark mode. Your preference is remembered across visits."
        ),
    },
    {
        "name": "categories",
        "keywords": ["category", "categories", "what categories"],
        "response": (
            "The default categories are Food, Transport, Education, Entertainment, Shopping, "
            "Healthcare and Utilities. Pick the closest match when logging an expense - "
            "consistent categorization is what makes your Summary charts useful."
        ),
    },
    {
        "name": "summary",
        "keywords": ["summary", "chart", "breakdown", "pie chart", "where did my money go"],
        "response": (
            "The Summary page (sidebar link) shows a table of totals per category plus a pie "
            "chart of your spending distribution, and your all-time total spent."
        ),
    },
    {
        "name": "dashboard",
        "keywords": ["dashboard", "stats", "overview", "home page"],
        "response": (
            "The Dashboard is your home base: total expenses, this month's spending, top "
            "category, highest expense, a category pie chart, a monthly trend line chart, "
            "and your filterable transaction list - all in one place."
        ),
    },
    {
        "name": "finance_tip",
        "keywords": ["tip", "advice", "save money", "saving", "budgeting tip", "financial advice", "how to save"],
        "response": None,  # handled specially below (random tip)
    },
    {
        "name": "thanks",
        "keywords": ["thanks", "thank you", "appreciate it", "cheers"],
        "response": "You're welcome! Feel free to ask if anything else comes up.",
    },
    {
        "name": "bye",
        "keywords": ["bye", "goodbye", "see you", "later"],
        "response": "Goodbye! Good luck keeping those expenses in check.",
    },
]

FALLBACK_RESPONSE = (
    "I'm not sure about that one yet. I can help with: adding/editing/deleting expenses, "
    "setting a budget, filtering & exporting data, updating your profile, dark mode, "
    "categories, or a finance tip - just ask!"
)


def get_bot_response(message: str) -> str:
    """Return a reply string for the given user message."""
    if not message or not message.strip():
        return "I didn't catch that - could you type your question?"

    text = message.lower().strip()

    for intent in INTENTS:
        if any(keyword in text for keyword in intent["keywords"]):
            if intent["name"] == "finance_tip":
                return random.choice(FINANCE_TIPS)
            return intent["response"]

    return FALLBACK_RESPONSE
