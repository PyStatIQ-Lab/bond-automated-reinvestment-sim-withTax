import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Set page config
st.set_page_config(page_title="Tax-Aware Bond Reinvestment Simulator", layout="wide")

# Custom styling
st.markdown("""
<style>
    .metric {font-size: 1.2rem !important;}
    .stSlider>div>div>div>div {background: #4f8bf9;}
    .stDataFrame {font-size: 14px;}
</style>
""", unsafe_allow_html=True)

# Title
st.title("💰 Bond Reinvestment Simulator with Taxes (Pvt Ltd/LLP)")

# Input parameters
with st.sidebar:
    st.header("Investment Parameters")
    initial = st.number_input("Investor Capital (₹)", 100000, 10000000, 100000, 10000)
    bond1_rate = st.slider("Bond 1 Rate (% p.a.)", 1.0, 30.0, 14.0, 0.1)
    bond2_rate = st.slider("Bond 2 Rate (% p.a.)", 1.0, 20.0, 12.0, 0.1)
    loan_rate = st.slider("Borrowing Rate (% p.a.)", 1.0, 20.0, 10.0, 0.1)
    months = st.slider("Tenure (Months)", 1, 60, 12, 1)
    leverage = st.slider("Leverage Ratio", 1.0, 3.0, 1.0, 0.1)
    
    st.header("Tax Parameters")
    entity = st.selectbox("Entity Type", ["Private Ltd (25%)", "LLP (31.2%)", "Custom Rate"])
    if entity == "Custom Rate":
        tax_rate = st.slider("Tax Rate (%)", 0.1, 35.0, 25.0, 0.1)
    else:
        tax_rate = 25.0 if "Private" in entity else 31.2
        
    bond2_tax = st.slider("Bond 2 Tax Rate (%)", 0.0, 30.0, 0.0, 0.1)

# Calculations
borrowed = initial * leverage
monthly_bond1 = bond1_rate / 12 / 100
monthly_bond2 = bond2_rate / 12 / 100
monthly_loan = loan_rate / 12 / 100

# Initialize trackers
bond1_principal = initial
bond2_principal = borrowed
loan_balance = borrowed
cum_bond1_interest = 0
cum_bond2_interest = 0
cum_loan_interest = 0
records = []

for month in range(1, months + 1):
    # Calculate monthly interest
    bond1_interest = bond1_principal * monthly_bond1
    bond2_interest = bond2_principal * monthly_bond2
    
    # Reinvest all interest into bond 2
    total_reinvest = bond1_interest + (bond2_interest * (1 - bond2_tax/100))  # Apply tax to bond2 interest before reinvestment
    bond2_principal += total_reinvest
    
    # Track interest for tax purposes
    cum_bond1_interest += bond1_interest
    cum_bond2_interest += bond2_interest
    
    # Loan interest accrual
    loan_interest = loan_balance * monthly_loan
    cum_loan_interest += loan_interest
    loan_balance += loan_interest  # Compounding loan interest
    
    records.append({
        "Month": month,
        "Bond 1 Interest": bond1_interest,
        "Bond 2 Interest": bond2_interest,
        "After Bond 2 Tax": bond2_interest * (1 - bond2_tax/100),
        "Reinvested Amount": total_reinvest,
        "Bond 2 Balance": bond2_principal,
        "Loan Interest": loan_interest,
        "Loan Balance": loan_balance
    })

df = pd.DataFrame(records)

# Final values
final_bond2 = df.iloc[-1]["Bond 2 Balance"]
final_loan = df.iloc[-1]["Loan Balance"]

# Tax calculation (bond1 interest is taxed, bond2 interest may be partially taxed)
taxable_income = (cum_bond1_interest + (cum_bond2_interest * bond2_tax/100)) - cum_loan_interest
tax = max(0, taxable_income) * tax_rate / 100

# Net position
net_value = (bond1_principal + final_bond2) - final_loan - tax
net_return = net_value - initial
annualized = (net_return / initial) * (12 / months) * 100

# Display results
col1, col2, col3 = st.columns(3)
col1.metric("Total Bond 1 Interest", f"₹{cum_bond1_interest:,.0f}")
col2.metric("Total Bond 2 Interest", f"₹{cum_bond2_interest:,.0f}")
col3.metric("Taxable Income", f"₹{taxable_income:,.0f}", f"Tax: ₹{tax:,.0f}")

col1, col2, col3 = st.columns(3)
col1.metric("Final Bond 2 Balance", f"₹{final_bond2:,.0f}")
col2.metric("Final Loan Repayment", f"₹{final_loan:,.0f}")
col3.metric("Investor's Net Return", f"₹{net_return:,.0f}", f"{annualized:.1f}% annualized")

# Monthly breakdown
st.subheader("Monthly Cash Flows")
st.dataframe(df.style.format({
    "Bond 1 Interest": "₹{:,.0f}",
    "Bond 2 Interest": "₹{:,.0f}",
    "After Bond 2 Tax": "₹{:,.0f}",
    "Reinvested Amount": "₹{:,.0f}",
    "Bond 2 Balance": "₹{:,.0f}",
    "Loan Interest": "₹{:,.0f}",
    "Loan Balance": "₹{:,.0f}"
}))

# Visualization
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df["Month"], df["Bond 2 Balance"], label="Bond 2 Balance", color='blue')
ax.plot(df["Month"], df["Loan Balance"], label="Loan Balance", color='red', linestyle='--')

net_values = [initial + df["Bond 2 Balance"].iloc[i] - df["Loan Balance"].iloc[i] - (tax * (i+1)/months) 
              for i in range(len(df))]
ax.plot(df["Month"], net_values, label="Net Value After Tax", color='green', linewidth=2)

ax.set_title("Investment Growth with Taxes")
ax.set_xlabel("Months")
ax.set_ylabel("Amount (₹)")
ax.legend()
ax.grid(True, alpha=0.3)
st.pyplot(fig)

# Key formulas
with st.expander("🔍 Calculation Methodology"):
    st.markdown(f"""
    **Monthly Calculations:**
    1. Bond 1 Interest = ₹{initial:,.0f} × ({bond1_rate}/12)% = ₹{initial*monthly_bond1:,.0f}/month (taxable)
    2. Bond 2 Interest = (₹{borrowed:,.0f} + Reinvestments) × ({bond2_rate}/12)% (taxable at {bond2_tax}%)
    3. Loan Interest = ₹{borrowed:,.0f} × ({loan_rate}/12)% (compounding monthly)
    
    **Tax Treatment:**
    - Bond 1 Interest fully taxable
    - Bond 2 Interest taxable at {bond2_tax}%
    - Taxable Income = (Bond 1 ₹{cum_bond1_interest:,.0f} + {bond2_tax}% of Bond 2 ₹{cum_bond2_interest:,.0f}) - Loan Interest ₹{cum_loan_interest:,.0f}
    - Tax = {tax_rate}% of ₹{max(0, taxable_income):,.0f} = ₹{tax:,.0f}
    
    **Final Return:**
    - Net Value = (Initial ₹{initial:,.0f} + Bond 2 ₹{final_bond2:,.0f}) - Loan ₹{final_loan:,.0f} - Tax ₹{tax:,.0f}
    - Profit = ₹{net_return:,.0f} on ₹{initial:,.0f} investment
    """)

st.warning("""
**Note:** This assumes:
1. Bond 1 interest is fully taxable
2. Bond 2 interest is taxable at the specified rate (default 0%)
3. Loan interest can offset taxable income
4. Reinvestment happens after applying Bond 2 tax
""")
