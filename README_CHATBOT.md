# Expense Assistant Chatbot — Integration Guide

This adds a floating chatbot to your Personal Expense Tracker that guides users
around the app's features and shares finance tips. It runs entirely offline —
no API key, no internet connection, no extra cost. It's simple rule-based
keyword matching in `chatbot.py`, which is easy to explain in a demo or viva.

## What's new / changed

**New files** (copy these into your project as-is):
- `chatbot.py` — the assistant's logic (root, next to `app.py`)
- `templates/chatbot_widget.html` — the chat UI partial
- `static/css/chatbot.css` — widget styling (matches your existing green theme, dark-mode aware)
- `static/js/chatbot.js` — widget behavior (open/close, send message, show reply)

**Modified files** (replace your existing copies with these):
- `app.py` — added `from chatbot import get_bot_response` and a new `/chatbot` POST route
- `templates/dashboard.html` — added `{% include 'chatbot_widget.html' %}` before `</body>`
- `templates/add_expense.html` — same include added
- `templates/summary.html` — same include added
- `templates/profile.html` — same include added

`edit_expenses.html` was intentionally left untouched — it's a bare-bones page
without Bootstrap/theme.js loaded, so the widget isn't included there. Add the
same one-line include there too if you want it on that page.

## How it works

1. The floating button (bottom-right, on every page you added the include to) opens a chat panel.
2. Typing a message — or tapping a suggestion chip — POSTs to `/chatbot` with `{ "message": "..." }`.
3. `chatbot.py`'s `get_bot_response()` matches keywords against a list of intents
   (adding expenses, budgets, filters, exports, profile, dark mode, categories,
   finance tips, greetings, thanks) and returns the best-matching canned reply.
4. If nothing matches, it returns a helpful fallback listing what it can do.
5. The route requires an active login session, same as the rest of the app.

## Extending it later

- Add more phrases to any `keywords` list in `chatbot.py` to catch more ways of
  asking the same question.
- Add more entries to `FINANCE_TIPS` for more variety.
- To make it "smarter" later (e.g. actually query the user's own expense data —
  "how much did I spend on food?"), you'd extend `get_bot_response` to accept a
  `user_id`, run a scoped SQL query, and format the number into the reply. The
  current keyword-matching structure only needs new intents added, not a rewrite.

## Tested

Verified via Flask's test client: registration → login → dashboard/add_expense/
summary/profile all render the widget; `/chatbot` returns correct replies for
greetings, add/edit/delete expense, budget, filter, export, profile, theme,
categories, finance tips, and an unmatched fallback; and the route correctly
returns 401 when called without a logged-in session.
