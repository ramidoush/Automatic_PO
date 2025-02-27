import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import urllib.parse
import base64

# ------------------- DATABASE SETUP -------------------
def create_connection():
    try:
        conn = sqlite3.connect('purchase_orders.db')
        return conn
    except sqlite3.Error as e:
        st.error(f"Database Connection Error: {e}")
        return None

def create_table():
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS purchase_orders (
                    po_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_date TEXT NOT NULL,
                    transaction_name TEXT NOT NULL,
                    amount REAL NOT NULL,
                    user_name TEXT NOT NULL,
                    notes TEXT,
                    payment_method TEXT DEFAULT 'Other',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
        except sqlite3.Error as e:
            st.error(f"Error Creating Table: {e}")
        finally:
            conn.close()

def add_po(transaction_date, transaction_name, amount, user_name, notes, payment_method):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO purchase_orders (transaction_date, transaction_name, amount, user_name, notes, payment_method, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (transaction_date, transaction_name, amount, user_name, notes, payment_method, datetime.now()))
            conn.commit()
        except sqlite3.Error as e:
            st.error(f"Error Adding PO: {e}")
        finally:
            conn.close()

def delete_po(po_id):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM purchase_orders WHERE po_id = ?", (po_id,))
            conn.commit()
        except sqlite3.Error as e:
            st.error(f"Error Deleting PO: {e}")
        finally:
            conn.close()

# ------------------- STREAMLIT APP -------------------
def main():
    st.set_page_config(page_title="Happy Sweep PO Generator", layout="wide")

    st.title("Happy Sweep PO Generator")

    # Ensure table exists
    create_table()

    # PO Form in Sidebar
    st.sidebar.header("Add New Purchase Order")
    transaction_date = st.sidebar.date_input("Transaction Date", datetime.now())
    transaction_name = st.sidebar.text_input("Transaction Name")
    amount = st.sidebar.number_input("Amount (AED)", min_value=0.0, step=0.01)
    user_name = st.sidebar.selectbox("User Name", ["Rami", "Tariq", "Ricky", "New Admin"])
    notes = st.sidebar.text_area("Notes")
    payment_method = st.sidebar.selectbox("Payment Method", ["Transfer", "Cash", "Card", "Payback", "Other"])

    if st.sidebar.button("Add Purchase Order"):
        if transaction_name and amount > 0:
            add_po(transaction_date, transaction_name, amount, user_name, notes, payment_method)
            st.success("Purchase Order Added Successfully!")
            st.rerun()
        else:
            st.error("Please enter a valid transaction name and amount.")

    # Fetch existing POs
    conn = create_connection()
    df = pd.read_sql_query("SELECT * FROM purchase_orders", conn)
    conn.close()

    if not df.empty:
        # Rearranging columns to have transaction_date first
        columns_order = ['transaction_date', 'po_id', 'transaction_name', 'amount', 'user_name', 'payment_method', 'notes', 'created_at']
        df = df[columns_order]

        st.subheader("Purchase Orders")

        # Use columns() to align buttons on the same row
        col1, col2 = st.columns([1, 1])

        # Send PO Email Button (Left)
        with col1:
            last_po = df.iloc[-1]
            subject = f"PO-{last_po['po_id']:04d}: {last_po['transaction_name']} - AED {last_po['amount']:,.2f}"
            body = f"""
Purchase Order (PO-{last_po['po_id']:04d})

Transaction Date: {last_po['transaction_date']}
Transaction Name: {last_po['transaction_name']}
Amount: AED {last_po['amount']}
User: {last_po['user_name']}
Payment Method: {last_po['payment_method']}
Notes: {last_po['notes']}
Created At: {last_po['created_at']}
            """
            recipients = ['rssd78@gmail.com', 'happysweep.cleaning@gmail.com', 'tarekalkafery@gmail.com']
            recipient_str = ','.join(recipients)  # Convert list to comma-separated string
            mailto_link = f"mailto:{recipient_str}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"

            st.markdown(f'<a href="{mailto_link}" target="_blank" style="display: block; text-align: center; padding: 10px; background-color: #0a214c; color: white; text-decoration: none; border-radius: 4px;">Send PO Email</a>', unsafe_allow_html=True)

        # Download CSV Button (Right)
        with col2:
            csv = df.to_csv(index=False).encode()
            b64 = base64.b64encode(csv).decode()  # Convert to Base64
            st.markdown(f'<a href="data:file/csv;base64,{b64}" download="purchase_orders.csv" style="display: block; text-align: center; padding: 10px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px;">Download CSV</a>', unsafe_allow_html=True)

        # Display DataFrame as a table
        st.dataframe(df, use_container_width=True)

        # Delete Functionality with Selectbox
        st.write("### Delete a Purchase Order")
        po_ids = df['po_id'].tolist()
        selected_po_id = st.selectbox("Select PO ID to Delete", po_ids)

        if st.button("Delete Selected PO"):
            delete_po(selected_po_id)
            st.success(f"Deleted PO ID: {selected_po_id}")
            st.rerun()

    else:
        st.info("No purchase orders available.")

if __name__ == '__main__':
    main()
