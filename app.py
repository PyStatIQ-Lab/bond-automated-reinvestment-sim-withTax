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
    taxable_rate = st.slider("Taxable Bond Rate (% p.a.)", 1.0, 30.0, 14.0, 0.1)
    taxfree_rate = st.slider("Tax-Free Bond Rate (% p.a.)", 1.0, 20.0, 12.0, 0.1)
    loan_rate = st.slider("Borrowing Rate (% p.a.)", 1.0, 20.0, 10.0, 0.1)
    months = st.slider("Tenure (Months)", 1, 60, 12, 1)
    leverage = st.slider("Leverage Ratio", 1.0, 3.0, 1.0, 0.1)
    
    st.header("Tax Parameters")
    entity = st.selectbox("Entity Type", ["Private Ltd (25%)", "LLP (31.2%)", "Custom Rate"])
    if entity == "Custom Rate":
        tax_rate = st.slider("Tax Rate (%)", 0.1, 35.0, 25.0, 0.1)
    else:
        tax_rate = 25.0 if "Private" in entity else 31.2

# Calculations
borrowed = initial * leverage
monthly_taxable = taxable_rate / 12 / 100
monthly_taxfree = taxfree_rate / 12 / 100
monthly_loan = loan_rate / 12 / 100

# Initialize trackers
taxable_principal = initial
taxfree_principal = borrowed
loan_balance = borrowed
cum_taxable_interest = 0
cum_taxfree_interest = 0
cum_loan_interest = 0
records = []

for month in range(1, months + 1):
    # Calculate monthly interest
    taxable_interest = taxable_principal * monthly_taxable
    taxfree_interest = taxfree_principal * monthly_taxfree
    
    # Reinvest all interest into tax-free bond
    total_reinvest = taxable_interest + taxfree_interest
    taxfree_principal += total_reinvest
    
    # Track interest for tax purposes (only taxable interest counts)
    cum_taxable_interest += taxable_interest
    cum_taxfree_interest += taxfree_interest
    
    # Loan interest accrual
    loan_interest = loan_balance * monthly_loan
    cum_loan_interest += loan_interest
    loan_balance += loan_interest  # Compounding loan interest
    
    records.append({
        "Month": month,
        "Taxable Bond Interest": taxable_interest,
        "Tax-Free Bond Interest": taxfree_interest,
        "Reinvested Amount": total_reinvest,
        "Tax-Free Bond Balance": taxfree_principal,
        "Loan Interest": loan_interest,
        "Loan Balance": loan_balance
    })

df = pd.DataFrame(records)

# Final values
final_taxfree = df.iloc[-1]["Tax-Free Bond Balance"]
final_loan = df.iloc[-1]["Loan Balance"]

# Tax calculation (only taxable interest is taxed)
taxable_income = cum_taxable_interest - cum_loan_interest  # Only taxable interest can offset loan interest
tax = max(0, taxable_income) * tax_rate / 100  # No tax on losses

# Net position
net_value = (taxable_principal + final_taxfree) - final_loan - tax
net_return = net_value - initial
annualized = (net_return / initial) * (12 / months) * 100

# Display results
col1, col2, col3 = st.columns(3)
col1.metric("Total Taxable Interest", f"₹{cum_taxable_interest:,.0f}")
col2.metric("Total Tax-Free Interest", f"₹{cum_taxfree_interest:,.0f}")
col3.metric("Taxable Income", f"₹{taxable_income:,.0f}", f"Tax: ₹{tax:,.0f}")

col1, col2, col3 = st.columns(3)
col1.metric("Final Tax-Free Bond", f"₹{final_taxfree:,.0f}")
col2.metric("Final Loan Repayment", f"₹{final_loan:,.0f}")
col3.metric("Investor's Net Return", f"₹{net_return:,.0f}", f"{annualized:.1f}% annualized")

# Monthly breakdown
st.subheader("Monthly Cash Flows")
st.dataframe(df.style.format({
    "Taxable Bond Interest": "₹{:,.0f}",
    "Tax-Free Bond Interest": "₹{:,.0f}",
    "Reinvested Amount": "₹{:,.0f}",
    "Tax-Free Bond Balance": "₹{:,.0f}",
    "Loan Interest": "₹{:,.0f}",
    "Loan Balance": "₹{:,.0f}"
}))

# Visualization
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df["Month"], df["Tax-Free Bond Balance"], label="Tax-Free Bond Balance", color='blue')
ax.plot(df["Month"], df["Loan Balance"], label="Loan Balance", color='red', linestyle='--')

# Corrected line with proper parentheses and pandas access
net_values = [initial + df["Tax-Free Bond Balance"].iloc[i] - df["Loan Balance"].iloc[i] - (tax * (i+1)/months) 
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
    1. Taxable Bond Interest = ₹{initial:,.0f} × ({taxable_rate}/12)% = ₹{initial*monthly_taxable:,.0f}/month (taxable)
    2. Tax-Free Bond Interest = (₹{borrowed:,.0f} + Reinvestments) × ({taxfree_rate}/12)% (tax-free)
    3. Loan Interest = ₹{borrowed:,.0f} × ({loan_rate}/12)% (compounding monthly)
    
    **Tax Treatment:**
    - Only taxable interest is subject to tax
    - Taxable Income = Taxable Interest (₹{cum_taxable_interest:,.0f}) - Loan Interest (₹{cum_loan_interest:,.0f})
    - Tax = {tax_rate}% of ₹{max(0, taxable_income):,.0f} = ₹{tax:,.0f}
    
    **Final Return:**
    - Net Value = (Initial ₹{initial:,.0f} + Tax-Free Bond ₹{final_taxfree:,.0f}) - Loan ₹{final_loan:,.0f} - Tax ₹{tax:,.0f}
    - Profit = ₹{net_return:,.0f} on ₹{initial:,.0f} investment
    """)

st.warning("""
**Note:** This assumes:
1. Only the taxable bond interest is subject to tax (14% in this case)
2. The tax-free bond interest (12%) is completely tax exempt
3. Loan interest can only offset taxable income
4. Reinvestment happens immediately each month
""")
