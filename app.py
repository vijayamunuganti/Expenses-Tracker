import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer, Paragraph
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io
import tempfile

st.title("💰 Personal Expense Tracker")

# Create tabs
tab1, tab2 = st.tabs(["Add Expense", "Dashboard"])

# ---------------- TAB 1 : ADD EXPENSE ----------------

with tab1:

    st.subheader("Add New Expense")

    date = st.date_input("Select Date")

    category = st.selectbox(
        "Select Category",
        ["Food","Travel","Shopping","Bills","Entertainment","Other"]
    )

    amount = st.number_input("Enter Amount", min_value=0.0)

    payment = st.selectbox(
        "Payment Method",
        ["Cash","UPI","Credit Card","Debit Card"]
    )

    location = st.text_input("Location")
    description = st.text_input("Description")

    if st.button("Add Expense"):

        new_data = pd.DataFrame(
            [[date, category, amount, payment, location, description]],
            columns=["Date","Category","Amount","Payment","Location","Description"]
        )

        if os.path.exists("expenses.csv"):
            new_data.to_csv("expenses.csv", mode="a", header=False, index=False)
        else:
            new_data.to_csv("expenses.csv", index=False)

        st.success("Expense Added Successfully!")

# ---------------- TAB 2 : DASHBOARD ----------------

with tab2:

    st.subheader("📊 Expense Dashboard")

    if os.path.exists("expenses.csv"):

        df = pd.read_csv("expenses.csv")

        expected_columns = ["Date","Category","Amount","Payment","Location","Description"]

        for col in expected_columns:
            if col not in df.columns:
                df[col] = None

        df = df[expected_columns]

        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
        df = df.dropna(subset=["Amount"])

        if df.empty:
            st.warning("No expense data available yet.")

        else:

            # -------- EDITABLE TABLE --------
            st.subheader("All Expenses (Editable)")

            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="dynamic"
            )

            if st.button("Save Edited Data"):
                edited_df.to_csv("expenses.csv", index=False)
                st.success("Expenses updated successfully!")
                st.rerun()

            # -------- TOTAL EXPENSE --------
            st.subheader("💰 Total Expense")
            st.write("₹", edited_df["Amount"].sum())

            # -------- MONTHLY SUMMARY --------
            edited_df["Date"] = pd.to_datetime(edited_df["Date"], errors="coerce")
            edited_df = edited_df.dropna(subset=["Date"])
            edited_df["Month"] = edited_df["Date"].dt.month_name()

            monthly_expense = edited_df.groupby("Month")["Amount"].sum()

            st.subheader("📅 Monthly Expense Summary")
            st.dataframe(monthly_expense)

            # -------- PIE CHART --------
            st.subheader("🥧 Expense Distribution by Category")

            category_expense = edited_df.groupby("Category")["Amount"].sum()

            if not category_expense.empty:

                col1, col2, col3 = st.columns([1,2,1])

                with col2:

                    fig, ax = plt.subplots(figsize=(6,6))  # FIXED SIZE

                    ax.pie(
                        category_expense,
                        labels=category_expense.index,
                        autopct="%1.1f%%",
                        startangle=90,
                        labeldistance=1.1  # FIXED LABEL CUT
                    )

                    ax.axis("equal")
                    plt.tight_layout()  # FIXED SPACING

                    st.pyplot(fig, use_container_width=False)

            else:
                st.info("No data available for pie chart.")

            # -------- PDF REPORT --------

            def create_pdf(monthly_data, chart):

                buffer = io.BytesIO()
                pdf = SimpleDocTemplate(buffer, pagesize=letter)

                styles = getSampleStyleSheet()
                elements = []

                # Title
                elements.append(Paragraph("Personal Expense Report", styles['Title']))
                elements.append(Spacer(1,20))

                # Monthly Table
                elements.append(Paragraph("Monthly Expense Summary", styles['Heading2']))
                elements.append(Spacer(1,10))

                monthly_table_data = [["Month", "Total Expense"]]

                for month, amount in monthly_data.items():
                    monthly_table_data.append([month, amount])

                table = Table(monthly_table_data)

                table.setStyle(TableStyle([
                    ("BACKGROUND",(0,0),(-1,0),colors.grey),
                    ("TEXTCOLOR",(0,0),(-1,0),colors.whitesmoke),
                    ("GRID",(0,0),(-1,-1),1,colors.black),
                    ("ALIGN",(0,0),(-1,-1),"CENTER")
                ]))

                elements.append(table)
                elements.append(Spacer(1,30))

                # Pie Chart
                elements.append(Paragraph("Expense Distribution by Category", styles['Heading2']))
                elements.append(Spacer(1,10))

                temp_chart = tempfile.NamedTemporaryFile(delete=False, suffix=".png")

                # ✅ FIXED SAVE (NO CUT LABELS)
                chart.savefig(temp_chart.name, bbox_inches='tight')

                elements.append(Image(temp_chart.name, width=350, height=350))

                pdf.build(elements)

                buffer.seek(0)
                return buffer

            st.subheader("📄 Download Report")

            pdf = create_pdf(monthly_expense, fig)

            st.download_button(
                label="Download PDF Report",
                data=pdf,
                file_name="expense_report.pdf",
                mime="application/pdf"
            )

    else:
        st.info("No expenses added yet.")