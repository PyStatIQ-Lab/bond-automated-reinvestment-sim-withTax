import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Set page config
st.set_page_config(page_title="Tax-Aware Bond Reinvestment Simulator", layout="wide")

# Custom styling
st.markdown("""
<style>
    .main {background-color: #f5f5f5;}
    .stSlider>div>div>div>div {background: #4f8bf9;}
    .reportview-container .main .block-container {padding-top: 2rem;}
    h1 {color: #2a3f5f;}
    .css-1aumxhk {background-color: #ffffff; border-radius: 10px; padding: 20px;}
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("💰 Tax-Aware Bond Reinvestment Simulator (Pvt Ltd/LLP)")
st.markdown("""
**🧠 Scenario:**  
Invest in bonds with leverage + Reinvest all interest + Calculate post-tax returns for Pvt Ltd/LLP
""")

# Sidebar controls
with st.sidebar:
    st.header("Investment Parameters")
    initial_investment = st.number_input("Initial Investment (₹)", min_value=10000, value=100000, step=10000)
    high_yield_rate = st.slider("High-Yield Bond Rate (% p.a.)", 1.0, 30.0, 14.0, 0.1)
    treasury_rate = st.slider("Treasury Bond Rate (% p.a.)", 1.0, 20.0, 12.0, 0.1)
    borrowing_rate = st.slider("Borrowing Rate (% p.a.)", 1.0, 20.0, 10.0, 0.1)
    months = st.slider("Investment Period (Months)", 1, 60, 12, 1)
    leverage_ratio = st.slider("Leverage Ratio", 1.0, 3.0, 1.0, 0.1)
    
    st.header("Tax Parameters")
    entity_type = st.selectbox("Entity Type", ["Private Limited Company", "LLP"])
    if entity_type == "Private Limited Company":
        tax_rate = st.slider("Corporate Tax Rate (%)", 15.0, 35.0, 25.0, 0.1)
    else:
        tax_rate = st.slider("LLP Tax Rate (%)", 15.0, 35.0, 31.2, 0.1)

# Calculate borrowed amount
borrowed_amount = initial_investment * leverage_ratio

# Monthly rates
monthly_high = high_yield_rate / 12 / 100
monthly_treasury = treasury_rate / 12 / 100
monthly_borrow = borrowing_rate / 12 / 100

# Initialize variables
high_yield_principal = initial_investment
treasury_principal = borrowed_amount
borrowed_balance = borrowed_amount
total_reinvested = 0
loan_interest_paid = 0
total_interest_income = 0

# Track monthly values
records = []

for month in range(1, months + 1):
    # Calculate interest from bonds
    high_yield_interest = high_yield_principal * monthly_high
    treasury_interest = treasury_principal * monthly_treasury
    
    # Track total interest income (taxable)
    total_interest_income += high_yield_interest + treasury_interest
    
    # Reinvest all interest into treasury bond
    total_reinvestment = high_yield_interest + treasury_interest
    treasury_principal += total_reinvestment
    total_reinvested += total_reinvestment
    
    # Accrue loan interest (tax-deductible)
    monthly_loan_interest = borrowed_balance * monthly_borrow
    loan_interest_paid += monthly_loan_interest
    
    # Record monthly values
    records.append({
        "Month": month,
        "High-Yield Interest": high_yield_interest,
        "Treasury Interest": treasury_interest,
        "Total Interest Income": high_yield_interest + treasury_interest,
        "Loan Interest Paid": monthly_loan_interest,
        "Taxable Income": (high_yield_interest + treasury_interest) - monthly_loan_interest,
        "Treasury Balance": treasury_principal,
        "Cumulative Loan Interest": loan_interest_paid
    })

# Create DataFrame
df = pd.DataFrame(records)

# Final calculations
final_treasury = df.iloc[-1]["Treasury Balance"]
total_loan_cost = borrowed_amount + df.iloc[-1]["Cumulative Loan Interest"]

# Tax Calculation
total_taxable_income = df["Taxable Income"].sum()
tax_paid = total_taxable_income * (tax_rate / 100)

# Investor's final position
investor_final = (high_yield_principal + final_treasury) - total_loan_cost - tax_paid
net_profit = investor_final - initial_investment
annualized_return = (net_profit / initial_investment) * (12/months) * 100

# Display summary
st.subheader("📊 Investment Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Your Investment", f"₹{initial_investment:,.0f}")
col2.metric("Borrowed Amount", f"₹{borrowed_amount:,.0f} ({leverage_ratio:,.1f}X)")
col3.metric("Total Invested", f"₹{initial_investment + borrowed_amount:,.0f}")

# Display results
st.subheader("💵 Final Results (After Tax)")
col1, col2, col3 = st.columns(3)
col1.metric("Total Interest Income", f"₹{total_interest_income:,.0f}")
col2.metric("Tax Liability (@{tax_rate}%)", f"₹{tax_paid:,.0f}")
col3.metric("Your Net Profit", f"₹{net_profit:,.0f}", f"{annualized_return:.1f}% annualized")

# Tax breakdown
st.subheader("🧾 Tax Calculation")
tax_df = pd.DataFrame({
    "Component": ["Total Interest Income", "Loan Interest Deduction", "Taxable Income", "Tax Paid"],
    "Amount (₹)": [
        total_interest_income,
        -loan_interest_paid,
        total_taxable_income,
        -tax_paid
    ]
})
st.dataframe(tax_df.style.format({"Amount (₹)": "₹{:,.0f}"}))

# Monthly breakdown
st.subheader("📅 Monthly Breakdown")
st.dataframe(df.style.format({
    "High-Yield Interest": "₹{:,.0f}",
    "Treasury Interest": "₹{:,.0f}",
    "Total Interest Income": "₹{:,.0f}",
    "Loan Interest Paid": "₹{:,.0f}",
    "Taxable Income": "₹{:,.0f}",
    "Treasury Balance": "₹{:,.0f}",
    "Cumulative Loan Interest": "₹{:,.0f}"
}))

# Visualizations
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df["Month"], df["Treasury Balance"], label="Reinvested Amount", color='#4f8bf9')
ax.plot(df["Month"], [borrowed_amount + x for x in df["Cumulative Loan Interest"]], 
        label="Loan Balance", color='#d62728', linestyle='--')
ax.plot(df["Month"], [initial_investment + x - tax_paid * (month/months) for month, x in enumerate(df["Treasury Balance"] - df["Cumulative Loan Interest"] - borrowed_amount, 1)], 
        label="Your Net Value (After Tax)", color='#2ca02c', linewidth=3)
ax.set_title("Investment Growth with Taxes", fontsize=16)
ax.set_xlabel("Months", fontsize=12)
ax.set_ylabel("Amount (₹)", fontsize=12)
ax.grid(True, alpha=0.3)
ax.legend()
st.pyplot(fig)

# Key tax notes
with st.expander("📌 Important Tax Rules for Pvt Ltd/LLP"):
    st.markdown("""
    **For Private Limited Companies:**
    - Interest income taxed as **business income** @25% (if turnover < ₹400 Cr)
    - Loan interest is **fully deductible** as business expense
    - Reinvestment gains taxed as ordinary income

    **For LLPs:**
    - Taxed at **30% + surcharge** (~31.2% effective)
    - Same treatment for interest income/expenses
    - No dividend distribution tax (unlike Pvt Ltd)

    **Key Considerations:**
    1. Maintain proper documentation of interest payments
    2. Ensure bonds are held as investments (not trading assets)
    3. Tax deducted at source (TDS) may apply on bond interest
    4. MAT (Minimum Alternate Tax) may apply for companies
    """)

# Risk disclosure
st.error("""
**⚠️ Important Risks:**
1. Higher leverage increases both potential returns and risks
2. Tax laws may change - consult a CA for exact treatment
3. Assumes all interest is reinvested immediately (may have operational delays)
4. Bond default risk not considered in calculations
""")
