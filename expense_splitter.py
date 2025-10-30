import streamlit as st
from collections import defaultdict
import pandas as pd
import base64

st.set_page_config(page_title="Expense Settlement", layout="centered")

# Handle scroll to form after edit
if st.session_state.get("scroll_to_form", False):
    st.session_state.scroll_to_form = False
    st.markdown("<script>window.location.href = '#receipt_form';</script>", unsafe_allow_html=True)

# ----------------------------------
# --- Full page background color
# ----------------------------------
page_bg_color = """
<style>
    .stApp { background-color: #faebe6; }
</style>
"""
st.markdown(page_bg_color, unsafe_allow_html=True)

# -----------------------
# --- App Header
# -----------------------
col1, col2 = st.columns([1, 10])
with col1:
    st.image("logo.png", width=60)
with col2:
    st.markdown("<h1 style='margin:0; padding:0; line-height:1.2;'>Expense Settlement</h1>", unsafe_allow_html=True)

# -----------------------
# Info icon helper
# -----------------------
def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()
icon_base64 = image_to_base64("info.png")

# -----------------------
# Session defaults
# -----------------------
if "receipts" not in st.session_state:
    st.session_state.receipts = []
if "form_id" not in st.session_state:
    st.session_state.form_id = 0
if "num_items" not in st.session_state:
    st.session_state.num_items = 1
if "participants" not in st.session_state:
    st.session_state.participants = []
if "currency_choice" not in st.session_state:
    st.session_state.currency_choice = "USD"

# --- Handle reset flags ---
if st.session_state.get("reset_all_now", False):
    # Reset everything, including currency
    saved_participants = st.session_state.get("participants", [])
    st.session_state.clear()
    st.session_state.receipts = []
    st.session_state.participants = saved_participants
    st.session_state.currency_choice = "USD"
    st.session_state.form_id = 0
    st.session_state.num_items = 1
    st.session_state.reset_all_now = False

elif st.session_state.get("keep_currency", False):
    # Preserve current currency only for 'Reset items'
    current_currency = st.session_state.currency_choice
    # clear only relevant fields, not currency
    for key in ["payer", "tax", "tip"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.keep_currency = False
    st.session_state.currency_choice = current_currency

# -----------------------
# Determine edit receipt safely
# -----------------------
edit_receipt = None
edit_idx = st.session_state.get("edit_receipt", None)
if edit_idx is not None and 0 <= edit_idx < len(st.session_state.receipts):
    edit_receipt = st.session_state.receipts[edit_idx]

# -----------------------
# Determine default number of items
# -----------------------
if edit_receipt is not None:
    temp_num_items = len(edit_receipt.get("items", []))
else:
    temp_num_items = st.session_state.get("num_items", 1)

# -----------------------
# Determine form defaults safely
# -----------------------
if edit_receipt is not None:
    default_payer = edit_receipt.get("payer", "")
    default_currency = edit_receipt["items"][0].get("currency", "USD") if edit_receipt.get("items") else "USD"
    # Use foreign tax/tip if non-USD
    default_tax = edit_receipt.get("tax_foreign" if default_currency != "USD" else "tax", 0.0)
    default_tip = edit_receipt.get("tip_foreign" if default_currency != "USD" else "tip", 0.0)
    # Persist this currency choice for the session
    st.session_state.currency_choice = default_currency
else:
    default_payer = ""
    default_currency = st.session_state.currency_choice
    default_tax = 0.0
    default_tip = 0.0

# -----------------------
# Step 0: Currency Settings
# -----------------------
st.subheader("Currency Conversion")

st.markdown(
    f"""
    <div style="display:flex; align-items:center; gap:8px; color:blue;">
        <img src="data:image/png;base64,{icon_base64}" width="15">
        <span style="font-size:12px;"><i>"Enter currency code if need to convert amounts to USD. Otherwise, leave blank. Amounts are in USD by default.</i></span>
    </div>
    """, unsafe_allow_html=True
)

foreign_currency = st.text_input("Foreign currency code (e.g., EUR, JPY)", value=" ")
conversion_rate = st.number_input(
    f"Conversion rate (1 USD = ? {foreign_currency})",
    min_value=0.0001,
    format="%.4f",
    value=1.0
)

st.caption(f"💡 All amounts entered in {foreign_currency} will be converted using this rate.")

st.divider()


# -----------------------
# Step 1: Participants input
# -----------------------
participants_input = st.text_input(
    "Enter all participant names (comma-separated):",
    value=", ".join(st.session_state.participants)
)
st.session_state.participants = [p.strip() for p in participants_input.split(",") if p.strip()]

# -----------------------
# Determine temp_num_items safely after participants input
# -----------------------
if edit_receipt is not None:
    # If editing a receipt, set temp_num_items based on the receipt
    temp_num_items = len(edit_receipt.get("items", []))
else:
    # If not editing, use existing session value or default to 1
    temp_num_items = st.session_state.get("num_items", 1)

# # Handle 'Reset all' (clears everything) — keeps currency handled elsewhere
# if st.session_state.get("reset_all_now", False):
#     st.session_state.form_id += 1
#     st.session_state.reset_all_now = False
#     temp_num_items = 1
#     # Clear only the relevant fields
#     for key in ["payer", "tax", "tip"]:
#         if key in st.session_state:
#             del st.session_state[key] 

# -----------------------
# Controls: number of items + reset buttons
# -----------------------
col1, col2 = st.columns([3, 3])

# Number of items input (uses temp_num_items, never assign st.session_state.num_items yet)
with col1:
    num_items = st.number_input(
        "How many items?",
        min_value=1,
        value=temp_num_items,
        key="num_items"
    )

with col2:
    st.markdown("<div style='margin-top:23px'></div>", unsafe_allow_html=True)
    if st.button("🔄 Reset to clear items"):
        form_prefix = f"f{st.session_state.form_id}_"
        st.session_state.form_id += 1

        # Clear dynamic item fields from old form
        keys_to_clear = [k for k in list(st.session_state.keys()) if k.startswith(form_prefix)]
        for k in keys_to_clear:
            del st.session_state[k]

        # ✅ Do NOT clear currency_choice — keeps last selected value
        st.session_state.keep_currency = True
        st.rerun()

# Reset all (clears everything, including num_items)
# with col3:
#     if st.button("🔁 Reset all (clear fields AND reset count)"):
#         st.session_state.reset_all_now = True
#         st.rerun()

# -----------------------
# Add Receipt form
# -----------------------
form_prefix = f"f{st.session_state.form_id}_"

# Get default values from session_state (reset clears these)
default_payer = st.session_state.get("payer", "")
default_tax = st.session_state.get("tax", 0.0)
default_tip = st.session_state.get("tip", 0.0)
default_currency = st.session_state.get("currency_choice", "USD")

# Anchor for jumping to the form
st.markdown("<a name='receipt_form'></a>", unsafe_allow_html=True)

with st.form("add_receipt_form", clear_on_submit=False):

    # Pre-fill if editing
    if edit_receipt is not None:
        
        st.markdown(
            "<div style='background-color:#fff3cd; border:1px solid #ffeeba; "
            "padding:10px; border-radius:8px; margin-bottom:10px;'>"
            "✏️ <strong>Editing existing receipt...</strong> "
            "Make changes and click <em>'Save Changes'</em> to save."
            "</div>",
            unsafe_allow_html=True
        )

        default_payer = edit_receipt.get("payer", "")
        default_currency = (
            edit_receipt["items"][0]["currency"]
            if edit_receipt.get("items")
            else st.session_state.currency_choice
        )
        # Tax & tip in the same currency as receipt
        if default_currency == "USD":
            default_tax = edit_receipt.get("tax", 0.0)
            default_tip = edit_receipt.get("tip", 0.0)
        else:
            default_tax = edit_receipt.get("tax_foreign", 0.0)
            default_tip = edit_receipt.get("tip_foreign", 0.0)

        # Force form currency choice to match receipt
        currency_choice = default_currency
    else:
        default_payer = ""
        default_currency = st.session_state.get("currency_choice", "USD")
        default_tax = 0.0
        default_tip = 0.0

    st.markdown("<span style='font-size:0.875rem; font-weight:400;'>Payer Name <span style='color:red;'>*</span></span>", unsafe_allow_html=True)
    payer_options = ["(Choose a Participant)"] + st.session_state.participants

    # Determine default index (so reset can show placeholder)
    if default_payer in st.session_state.participants:
        default_index = payer_options.index(default_payer)
    else:
        default_index = 0  # 0 = "Choose an option"

    payer = st.selectbox(
        label="Payer Name",
        options=payer_options,
        index=default_index,
        key=f"{form_prefix}payer",
        label_visibility="collapsed"
    )

    # Treat placeholder as empty (for validation)
    if payer == "Choose an option":
        payer = ""

    # Use a manual default index based on session
    default_currency_choice = st.session_state.get("currency_choice", "USD")

    # Render radio WITHOUT using key="currency_choice" — avoids auto-reset on rerun
    currency_choice = st.radio(
        "Currency for this receipt",
        ["USD", foreign_currency],
        index=0 if default_currency_choice == "USD" else 1,
        horizontal=True
    )

    # Manually persist selected currency
    st.session_state.currency_choice = currency_choice

    # --- Tax and Tip inputs ---
    tax_val = st.number_input("Tax Amount", min_value=0.0, format="%.2f", value=default_tax, key=f"{form_prefix}tax")
    tip_val = st.number_input("Tip Amount", min_value=0.0, format="%.2f", value=default_tip, key=f"{form_prefix}tip")

    # Convert to USD if foreign
    if currency_choice == "USD":
        tax_usd, tax_foreign = tax_val, tax_val * conversion_rate
        tip_usd, tip_foreign = tip_val, tip_val * conversion_rate
    else:
        tax_foreign, tax_usd = tax_val, tax_val / conversion_rate if conversion_rate > 0 else 0
        tip_foreign, tip_usd = tip_val, tip_val / conversion_rate if conversion_rate > 0 else 0

    # --- Item inputs ---
    items = []
    for i in range(num_items):
        st.markdown(f"**Item #{i+1}**")
        if edit_receipt is not None and i < len(edit_receipt["items"]):
            existing_item = edit_receipt["items"][i]
            default_name = existing_item["name"]
            default_shared = existing_item["shared_with"]

            # ✅ Detect whether the form currency matches the item currency
            if currency_choice == "USD":
                default_price = existing_item["price_usd"]
            else:
                default_price = existing_item["price_foreign"]

        else:
            default_name = ""
            default_price = 0.0
            default_shared = []

        st.markdown(f"<span style='font-size:0.875rem; font-weight:400;'>Item #{i+1} name <span style='color:red'>*</span></span>", unsafe_allow_html=True)
        name = st.text_input("", key=f"{form_prefix}name_{i}", value=default_name, label_visibility="collapsed")

        st.markdown(f"<span style='font-size:0.875rem; font-weight:400;'>Item #{i+1} amount <span style='color:red'>*</span></span>", unsafe_allow_html=True)
        price = st.number_input("", min_value=0.0, format="%.2f",
                                key=f"{form_prefix}price_{i}", value=default_price, label_visibility="collapsed")
        
        if currency_choice == "USD":
            price_usd = price
            price_foreign = price * conversion_rate
        else:
            price_foreign = price
            price_usd = price / conversion_rate if conversion_rate > 0 else 0

        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:8px; color:blue;">
                <img src="data:image/png;base64,{icon_base64}" width="15">
                <span style="font-size:12px;"><i>"Shared with" field needs to include "payer" if the item is also split with payer.</i></span>
            </div>
            """, unsafe_allow_html=True
        ) 

        st.markdown(f"<span style='font-size:0.875rem; font-weight:400;'>Item #{i+1} Shared with <span style='color:red'>*</span></span>", unsafe_allow_html=True)
        shared_list = st.multiselect("", options=st.session_state.participants,
                                     default=default_shared, key=f"{form_prefix}shared_{i}", label_visibility="collapsed")

        items.append({
            "name": name,
            "price_usd": price_usd,
            "price_foreign": price_foreign,
            "currency": currency_choice,
            "shared_with": shared_list
        })

    submitted = st.form_submit_button("Save Changes" if edit_receipt is not None else "Add Receipt")


# -----------------------
# On submit with required field validation
# -----------------------
if submitted:
    errors = []

    # Validate payer
    if not payer.strip():
        errors.append("Payer name is required.")

    # Validate items
    for i, item in enumerate(items, start=1):
        if not item["name"].strip():
            errors.append(f"Item #{i} name is required.")
        if item["price_usd"] <= 0:
            errors.append(f"Item #{i} amount must be greater than 0.")
        if not item["shared_with"]:
            errors.append(f"Item #{i} 'Shared with' must include at least one person.")

    # If there are any validation errors, show them
    if errors:
        st.error("🚫 Please fix the following before saving:")
        for e in errors:
            st.write(f"- {e}")
    else:
        # ✅ All required fields filled — proceed to save
        if "edit_receipt" in st.session_state:
            idx = st.session_state.pop("edit_receipt")
            st.session_state.receipts[idx] = {
                "payer": payer,
                "items": items,
                "tax": tax_usd,
                "tip": tip_usd,
                "tax_foreign": tax_foreign,
                "tip_foreign": tip_foreign,
            }
            st.success("✅ Changes saved!")
        else:
            st.session_state.receipts.append({
                "payer": payer,
                "items": items,
                "tax": tax_usd,
                "tip": tip_usd,
                "tax_foreign": tax_foreign,
                "tip_foreign": tip_foreign,
            })
            st.success("✅ Receipt added!")

        # Clear some temporary fields
        for key in ["payer", "tax", "tip"]:
            if key in st.session_state:
                del st.session_state[key]

        st.session_state.form_id += 1
        st.rerun()

# -----------------------
# Settlement calculation
# -----------------------
def calculate_settlements(receipts):
    balances = defaultdict(float)
    total_paid = defaultdict(float)
    total_owed = defaultdict(float)

    for receipt in receipts:
        payer = receipt["payer"]
        tax = receipt["tax"]
        tip = receipt["tip"]
        items = receipt["items"]

        total_item_cost = sum(item["price_usd"] for item in items)
        if total_item_cost == 0:
            continue

        for item in items:
            ratio = item["price_usd"] / total_item_cost
            item["price_with_tax_tip"] = item["price_usd"] + ratio * tax + ratio * tip

        for item in items:
            if item["shared_with"]:
                split = round(item["price_with_tax_tip"] / len(item["shared_with"]), 2)
                for person in item["shared_with"]:
                    total_owed[person] += split
                    balances[person] -= split

        total_paid[payer] += total_item_cost + tax + tip
        balances[payer] += total_item_cost + tax + tip

    balances = {p: round(v,2) for p,v in balances.items()}
    total_paid = {p: round(v,2) for p,v in total_paid.items()}
    total_owed = {p: round(v,2) for p,v in total_owed.items()}

    creditors = [(p, amt) for p, amt in balances.items() if amt > 0]
    debtors = [(p, -amt) for p, amt in balances.items() if amt < 0]

    i = j = 0
    txns = []
    while i < len(debtors) and j < len(creditors):
        debtor, debt = debtors[i]
        creditor, credit = creditors[j]
        payment = min(debt, credit)
        txns.append(f"{debtor} pays {creditor} ${payment:.2f}")
        debtors[i] = (debtor, debt - payment)
        creditors[j] = (creditor, credit - payment)
        if debtors[i][1] == 0: i += 1
        if creditors[j][1] == 0: j += 1

    return txns, total_paid, total_owed, balances

# -----------------------
# Display receipts + summary
# -----------------------
if st.session_state.receipts:
    st.subheader("📋 Receipts Entered")
    
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:8px; color:blue; margin-bottom:15px; margin-left:13px;">
            <img src="data:image/png;base64,{icon_base64}" width="15">
            <span style="font-size:12px;"><i>Tax and tip are applied to every item on that receipt.</i></span><br>
        </div>
        """, unsafe_allow_html=True
    )
    
    # Ensure old receipts have foreign amounts
    for r in st.session_state.receipts:
        if "tax_foreign" not in r:
            r["tax_foreign"] = r.get("tax", 0.0) * conversion_rate
        if "tip_foreign" not in r:
            r["tip_foreign"] = r.get("tip", 0.0) * conversion_rate

    for idx, r in enumerate(st.session_state.receipts):
        receipt_currency = r["items"][0]["currency"] if r["items"] else "USD"
    
        # Dynamically calculate foreign values
        for it in r["items"]:
            if receipt_currency == "USD":
                it["price_foreign_display"] = it["price_usd"] * conversion_rate
            else:
                it["price_foreign_display"] = it["price_foreign"] 
        
        if receipt_currency == "USD":
            tax_foreign_display = r["tax"] * conversion_rate
            tip_foreign_display = r["tip"] * conversion_rate
        else:
            tax_foreign_display = r["tax_foreign"]
            tip_foreign_display = r["tip_foreign"]
        
        # Use price_foreign_display, tax_foreign_display, tip_foreign_display in the table

        # Determine whether to show foreign column
        show_foreign = foreign_currency.strip() != ""

        # --- Generate items table ---
        items_html = '<table style="width:100%; border-collapse: collapse;">'
        items_html += (
            f'<tr>'
            f'<th style="text-align:left; padding:4px;">Item</th>'
        )

        if show_foreign:
            items_html += f'<th style="text-align:right; padding:4px;">Price ({foreign_currency})</th>'

        items_html += (
            f'<th style="text-align:right; padding:4px;">Price (USD)</th>'
            f'<th style="text-align:left; padding:4px;">Shared With</th>'
            f'</tr>'
        )

        for it in r["items"]:
            items_html += (
                f'<tr>'
                f'<td style="padding:4px;">{it["name"]}</td>'
            )

            if show_foreign:
                items_html += f'<td style="padding:4px; text-align:right;">{it["price_foreign_display"]:.2f} {foreign_currency}</td>'

            items_html += (
                f'<td style="padding:4px; text-align:right;">${it["price_usd"]:.2f}</td>'
                f'<td style="padding:4px;">{", ".join(it["shared_with"])}</td>'
                f'</tr>'
            )

        # --- Tax and Tip rows ---
        items_html += (
            f'<tr>'
            f'<td style="padding:4px; font-style:italic;">Tax</td>'
        )

        if show_foreign:
            items_html += f'<td style="padding:4px; text-align:right;">{tax_foreign_display:.2f} {foreign_currency}</td>'
        
        items_html += (
            f'<td style="padding:4px; text-align:right;">${r["tax"]:.2f}</td>'
            f'<td></td>'
            f'</tr>'
        )

        items_html += (
            f'<tr>'
            f'<td style="padding:4px; font-style:italic;">Tip</td>'
        )

        if show_foreign:
            items_html += f'<td style="padding:4px; text-align:right;">{tip_foreign_display:.2f} {foreign_currency}</td>'
        
        items_html += (
            f'<td style="padding:4px; text-align:right;">${r["tip"]:.2f}</td>'
            f'<td></td>'
            f'</tr>'
        )

        # --- Total row ---
        receipt_total_foreign = sum(it["price_foreign_display"] for it in r["items"]) + tax_foreign_display + tip_foreign_display
        receipt_total_usd = sum(it["price_usd"] for it in r["items"]) + r["tax"] + r["tip"]

        items_html += (
            f'<tr style="font-weight:bold; border-top:2px solid #ccc;">'
            f'<td>Total</td>'
        )
        if show_foreign:
            items_html += f'<td style="text-align:right;">{receipt_total_foreign:.2f} {foreign_currency}</td>'
        
        items_html += (
            f'<td style="text-align:right;">${receipt_total_usd:.2f}</td>'
            f'<td></td>'
            f'</tr>'
        )

        items_html += '</table>'

        # --- Render card with table ---
        st.markdown(
            f'<div style="border: 2px solid #ccc; border-radius: 10px; padding: 12px; margin-bottom:10px; background-color: transparent; box-shadow:1px 1px 5px rgba(0,0,0,0.05); position: relative;">'
            f'<strong>Receipt #{idx+1}</strong> — Paid by <code>{r["payer"]}</code><br>'
            f'{items_html}'
            f'</div>',
            unsafe_allow_html=True
        )

        # --- Buttons aligned bottom-right ---
        col1, col2, col3 = st.columns([5,1,1])
        with col2:
            if st.button("🗑 Delete", key=f"delete_{idx}"):
                st.session_state.receipts.pop(idx)
                st.rerun()
        with col3:
            if st.button("✏️ Edit", key=f"edit_{idx}"):
                st.session_state.form_id += 1
                st.session_state.edit_receipt = idx
                st.session_state.scroll_to_form = True  # 👈 flag for scroll
                st.rerun()


    st.subheader("📊 Per-Person Summary")
    
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:8px; color:blue; margin-left:13px;">
            <img src="data:image/png;base64,{icon_base64}" width="15">
            <span style="font-size:12px;"><i>Amounts are shown in USD.</i></span>
        </div>
        """, unsafe_allow_html=True
    )
    
    settlements, total_paid, total_owed, balances = calculate_settlements(st.session_state.receipts)
    people = sorted(set(list(total_paid.keys()) + list(total_owed.keys())))
    df = pd.DataFrame([{
        "Name": p,
        "Paid": total_paid.get(p,0),
        "Owes": total_owed.get(p,0),
        "Net Balance": balances.get(p,0)
    } for p in people])
    def highlight_net(v):
        return "color: green; font-weight:bold;" if v>0 else ("color: red; font-weight:bold;" if v<0 else "")
    st.dataframe(df.style.applymap(highlight_net, subset=["Net Balance"])
                 .format({"Paid":"${:.2f}","Owes":"${:.2f}","Net Balance":"${:.2f}"}), use_container_width=True)

    st.subheader("💸 Settlement Summary")
    
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:8px; color:blue; margin-left:13px;">
            <img src="data:image/png;base64,{icon_base64}" width="15">
            <span style="font-size:12px;"><i>Amounts are shown in USD.</i></span>
        </div>
        """, unsafe_allow_html=True
    )
    
    if settlements:
        for s in settlements:
            st.success(s)
    else:
        st.info("Everyone is settled. No payments needed.")
else:
    st.info("No receipts added yet.")
