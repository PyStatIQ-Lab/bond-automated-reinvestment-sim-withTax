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
    bond1_rate = st.slider("Primary Bond Rate (% p.a.)", 1.0, 30.0, 14.0, 0.1)
    bond2_rate = st.slider("Secondary Bond Rate (% p.a.)", 1.0, 20.0, 12.0, 0.1)
    loan_rate = st.slider("Borrowing Rate (% p.a.)", 1.0, 20.0, 10.0, 0.1)
    months = st.slider("Tenure (Months)", 1, 60, 12, 1)
    leverage = st.slider("Leverage Ratio", 1.0, 3.0, 1.0, 0.1)
    
    st.header("Tax Parameters")
    entity = st.selectbox("Entity Type", ["Private Ltd (25%)", "LLP (31.2%)", "Custom Rate"])
    if entity == "Custom Rate":
        tax_rate = st.slider("Tax Rate (%)", 15.0, 35.0, 25.0, 0.1)
    else:
        tax_rate = 25.0 if "Private" in entity else 31.2

# Calculations
borrowed = initial * leverage
monthly_b1 = bond1_rate / 12 / 100
monthly_b2 = bond2_rate / 12 / 100
monthly_loan = loan_rate / 12 / 100

# Initialize trackers
b1_principal = initial
b2_principal = borrowed
loan_balance = borrowed
cum_interest_income = 0
cum_loan_interest = 0
records = []

for month in range(1, months + 1):
    # Calculate monthly interest
    b1_interest = b1_principal * monthly_b1
    b2_interest = b2_principal * monthly_b2
    
    # Reinvest all interest into secondary bond
    total_reinvest = b1_interest + b2_interest
    b2_principal += total_reinvest
    
    # Track interest for tax purposes
    cum_interest_income += b1_interest + b2_interest
    
    # Loan interest accrual
    loan_interest = loan_balance * monthly_loan
    cum_loan_interest += loan_interest
    loan_balance += loan_interest  # Compounding loan interest
    
    records.append({
        "Month": month,
        "Primary Bond Interest": b1_interest,
        "Secondary Bond Interest": b2_interest,
        "Reinvested Amount": total_reinvest,
        "Secondary Bond Balance": b2_principal,
        "Loan Interest": loan_interest,
        "Loan Balance": loan_balance
    })

df = pd.DataFrame(records)

# Final values
final_b2 = df.iloc[-1]["Secondary Bond Balance"]
final_loan = df.iloc[-1]["Loan Balance"]

# Tax calculation
taxable_income = cum_interest_income - cum_loan_interest
tax = max(0, taxable_income) * tax_rate / 100  # No tax on losses

# Net position
net_value = (b1_principal + final_b2) - final_loan - tax
net_return = net_value - initial
annualized = (net_return / initial) * (12 / months) * 100

# Display results
col1, col2, col3 = st.columns(3)
col1.metric("Total Interest Earned", f"₹{cum_interest_income:,.0f}")
col2.metric("Total Loan Interest", f"₹{cum_loan_interest:,.0f}")
col3.metric("Taxable Income", f"₹{taxable_income:,.0f}", f"Tax: ₹{tax:,.0f}")

col1, col2, col3 = st.columns(3)
col1.metric("Final Secondary Bond", f"₹{final_b2:,.0f}")
col2.metric("Final Loan Repayment", f"₹{final_loan:,.0f}")
col3.metric("Investor's Net Return", f"₹{net_return:,.0f}", f"{annualized:.1f}% annualized")

# Monthly breakdown
st.subheader("Monthly Cash Flows")
st.dataframe(df.style.format({
    "Primary Bond Interest": "₹{:,.0f}",
    "Secondary Bond Interest": "₹{:,.0f}",
    "Reinvested Amount": "₹{:,.0f}",
    "Secondary Bond Balance": "₹{:,.0f}",
    "Loan Interest": "₹{:,.0f}",
    "Loan Balance": "₹{:,.0f}"
}))

# Visualization - CORRECTED SECTION
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df["Month"], df["Secondary Bond Balance"], label="Reinvested Amount", color='blue')
ax.plot(df["Month"], df["Loan Balance"], label="Loan Balance", color='red', linestyle='--')

# Corrected line with proper parentheses
net_values = [initial + df["Secondary Bond Balance"][i] - df["Loan Balance"][i] - (tax * (i+1)/months) 
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
    1. Primary Bond Interest = ₹{initial:,.0f} × ({bond1_rate}/12)% = ₹{initial*monthly_b1:,.0f}/month
    2. Secondary Bond Interest = (₹{borrowed:,.0f} + Reinvestments) × ({bond2_rate}/12)%
    3. Loan Interest = ₹{borrowed:,.0f} × ({loan_rate}/12)% (compounding monthly)
    
    **Tax Treatment:**
    - Taxable Income = Total Interest (₹{cum_interest_income:,.0f}) - Loan Interest (₹{cum_loan_interest:,.0f})
    - Tax = {tax_rate}% of ₹{taxable_income:,.0f} = ₹{tax:,.0f}
    
    **Final Return:**
    - Net Value = (Primary ₹{initial:,.0f} + Secondary ₹{final_b2:,.0f}) - Loan ₹{final_loan:,.0f} - Tax ₹{tax:,.0f}
    - Profit = ₹{net_return:,.0f} on ₹{initial:,.0f} investment
    """)

st.warning("""
**Note:** This assumes:
1. Interest income taxed as business income
2. Loan interest fully deductible
3. No TDS or surcharges beyond base rate
4. Reinvestment happens immediately each month
""")
