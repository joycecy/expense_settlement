**Overview:**

The Expense Settlement App is an interactive Python web application built with Streamlit to simplify group expense tracking and settlement.

It allows users to record shared expenses, assign payers and participants, calculate taxes and tips, an option to convert currencies, and generate an itemized settlement summary — all through a clean, dynamic interface.



**Features:**

Dynamic Form Inputs: Add, edit, and delete receipts with multiple items, taxes, and tips.

Participant Management: Assign shared participants and automatically calculate who owes what.

Currency Conversion: Seamlessly switch between USD and foreign currency for multi-country trips.

Smart Reset Logic: Option to reset only the form fields or the entire session (including currency).

Data Persistence: Uses Streamlit session state for consistent form control and user experience.

Interactive UI: Built with Streamlit for a lightweight, browser-based workflow.



**How It Works:**

Add participants and select the currency.

Enter receipts with details for payer, items, tax, and tip.

Track totals for each person and see who owes whom.

Reset fields or the full session as needed — without breaking the currency logic.



**Example Use Cases:**

Group trips or vacations

Shared household expenses

Event or team budget tracking

Roommate bill splitting


**Clone Repo**

git clone https://github.com/yourusername/expense-settlement.git
cd expense-settlement

**Run Streamlit app**

streamlit run app.py
