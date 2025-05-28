import streamlit as st
st.set_page_config(
    page_title='Rocky_art_bookings',
    page_icon='👋 ',

)


import bcrypt
import pandas as pd
from streamlit_option_menu import option_menu
from datetime import datetime
import json
import time
from streamlit_cookies_manager import EncryptedCookieManager
from PIL import Image



from streamlit_cookies_manager import EncryptedCookieManager

# Initialize Cookie Manager

cookies = EncryptedCookieManager(prefix="inventory_app_", password="your_secret_key_here")

if not cookies.ready():
    st.stop()





from supabase import create_client
# supabase configurations
def get_supabase_client():
    supabase_url = 'https://bpxzfdxxidlfzvgdmwgk.supabase.co' # Your Supabase project URL
    supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJweHpmZHh4aWRsZnp2Z2Rtd2drIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI3NjM0MTQsImV4cCI6MjA1ODMzOTQxNH0.vQq2-VYCJyTQDq3QN2mJprmmBR2w7HMorqBuzz43HRU'
    supabase = create_client(supabase_url, supabase_key)
    return supabase  # Make sure to return the client

# Initialize Supabase client
supabase = get_supabase_client() # use this to call the supabase database




def get_usd_to_ngn_rate():
    API_KEY = "d25a9a667870cb6fe7c611ba"  # Put your actual API key here or store as env var
    url=f" https://v6.exchangerate-api.com/v6/d25a9a667870cb6fe7c611ba/latest/USD"
    try:
        response = requests.get(url)
        data = response.json()
        if data["result"] == "success":
            rate = data["conversion_rates"]["NGN"]
            return rate
        else:
            st.warning("Failed to fetch exchange rate, using default rate.")
            return 1000 # fallback default
    except Exception as e:
        st.error(f"Error fetching exchange rate: {e}")
        return 1000  # fallback default





services_usd = {
    'Digital Art portrait': 10,
    'Video animation (60 secs)': 100,
    'Motion graphics (60 secs)': 100,
    'Animated music video (60 secs)': 133,
    'Logo and brand identity': 33,
    'E-flier design': 10,
    'Social media monthly package': 167,
    'Crypto meme ar': 13,
    'Crypto meme animation (<30 secs)': 53
}

# Currency conversion rate
USD_TO_NGN = get_usd_to_ngn_rate()
st.metric(f"Current USD to NGN rate: ₦{USD_TO_NGN}")  # Fixed variable name

def convert_price(price_usd, currency):
    if currency == "NGN":
        return price_usd * USD_TO_NGN
    return price_usd

def submit_booking(name, email, service, deadline, details, price, currency):
    data = {
        "name": name,
        "email": email,
        "service": service,
        'location': location,
        'phone_number': phone_number,
        "deadline": deadline,
        "details": details,
        "file_url": "",
        "price": price,
        "currency": currency  # New column, add to your supabase table!
    }

    response = supabase.table("bookings").insert(data).execute()
    if response.error is None:
        return True
    else:
        st.error(f"Failed to submit booking: {response.error.message}")
        return False

st.title("🎨 Rocky Art Company Booking System")

menu = ["Book a Service", "Admin Dashboard"]
choice = st.selectbox("Menu", menu)

if choice == "Book a Service":
    st.header("Submit a Booking")

    with st.form("booking_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        phone_number = st.number_input('Phone_number', value=0)
        currency = st.selectbox("Select Currency", ["USD", "NGN"])
        location = st.text_input('Location', value='London')

        # Show services with price in selected currency
        def format_service(service_name):
            price = convert_price(services_usd[service_name], currency)
            symbol = "$" if currency == "USD" else "₦"
            return f"{service_name} - {symbol}{price:,.0f}"

        service = st.selectbox("Select Service", options=list(services_usd.keys()), format_func=format_service)

        deadline = st.date_input("Deadline")
        details = st.text_area("Project Details / Description")

        price = convert_price(services_usd[service], currency)
        symbol = "$" if currency == "USD" else "₦"
        st.markdown(f"**Price:** {symbol}{price:,.0f}")
        submitted = st.form_submit_button("Submit Booking")

        if submitted:
            if not name or not email:
                st.error("Please fill in all required fields.")
            else:
                data = {
                    "name": name,
                    "email": email,
                    "service": service,
                    'location': location,
                    'phone_number': phone_number,
                    "deadline": deadline,
                    "details": details,
                    "file_url": "",
                    "price": price,
                    "currency": currency
                }
                response = supabase.table("bookings").insert(data).execute()
                if response.error is None:
                    st.success("Booking submitted!")
                else:
                    st.error(f"Error: {response.error.message}")

elif choice == "Admin Dashboard":
    st.header("Admin Dashboard")
    password = st.text_input("Enter admin password", type="password")

    if password == "rockyadmin123":  # Change your admin password here!
        st.success("Access granted")
        # Fetch bookings
        response = supabase.table("bookings").select("*").order("created_at", desc=True).execute()
        if response.status_code == 200:
            bookings = response.data
            if bookings:
                for b in bookings:
                    st.markdown(f"**Name:** {b['name']}")
                    st.markdown(f"**Email:** {b['email']}")
                    st.markdown(f"**Service:** {b['service']}")
                    st.markdown(f"**Deadline:** {b['deadline']}")
                    st.markdown(f"**Details:** {b['details']}")
                    st.markdown(f"**Submitted At:** {b['created_at']}")
                    st.markdown("---")
            else:
                st.info("No bookings found.")
        else:
            st.error("Failed to fetch bookings.")
    else:
        if password:
            st.error("Incorrect password.")
