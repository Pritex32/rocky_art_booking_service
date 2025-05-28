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

import requests

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

def upload_file_to_supabase(file, bucket_name="bookingsbucket"):
    try:
        # Read file bytes
        file_bytes = file.read()
        
        # Create unique filename to avoid overwriting, e.g. prefix with timestamp
        import time, os
        filename = f"{int(time.time())}_{file.name}"
        
        # Upload file bytes to Supabase storage bucket
        response = supabase.storage.from_(bucket_name).upload(filename, file_bytes)
        
        if response.get("error") is not None:
            st.error(f"Failed to upload file: {response['error']['message']}")
            return None
        
        # Get public URL for the uploaded file
        public_url = supabase.storage.from_(bucket_name).get_public_url(filename)
        return public_url
        
    except Exception as e:
        st.error(f"Exception during file upload: {e}")
        return None



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
st.info(f"Current USD to NGN rate: ₦{USD_TO_NGN}")  # Fixed variable name

def convert_price(price_usd, currency):
    if currency == "NGN":
        return price_usd * USD_TO_NGN
    return price_usd

def submit_booking(name, email, service, location,phone_number,deadline, details,reference_url,file_url, price, currency):
    data = {
        "name": name,
        "email": email,
        "service": service,
        'location': location,
        'phone_number': str(phone_number),
        "deadline": str(deadline),
        "details": details if details else None,
        'reference_url':reference_url if reference_url else None,
        "file_url": file_url if file_url else None,
        "price": price,
        "currency": currency  # New column, add to your supabase table!
    }

    response = supabase.table("bookings").insert(data).execute()
    if response.error is None:
        return True
    else:
        st.error(f"Failed to submit booking: {response.error.message}")
        return False
col1,col2=st.columns(2)
with col1:
    st.title("🎨 Rocky Art Company Booking System")
with col2:
    image='logo__rockyart.png'
    img=Image.open(image)
    resize_img=img.resize((100,100))
    st.write(resize_img)

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
        # File uploader for reference file
        reference_file = st.file_uploader("Upload Reference File (optional)", type=['png', 'jpg', 'jpeg', 'pdf', 'mp4', 'mov'])

        # URL input for reference link
        reference_url = st.text_input("Or enter a Reference URL (optional)")

        price = convert_price(services_usd[service], currency)
        symbol = "$" if currency == "USD" else "₦"
        st.markdown(f"**Price:** {symbol}{price:,.0f}")
        submitted = st.form_submit_button("Submit Booking")

        if submitted:
            if not name or not email:
                st.error("Please fill in all required fields.")
            else:
                file_url = ""
                uploaded_url_obj = None

                if reference_file is not None:
                    uploaded_url_obj = upload_file_to_supabase(reference_file)
                if uploaded_url_obj is not None:
                    file_url = uploaded_url_obj.get("publicUrl", "")

            
            
                data = {
                    "name": name,
                    "email": email,
                    "service": service,
                    'location': location,
                    'phone_number':str(phone_number),
                    "deadline":str(deadline),
                    "details": details if details else None,
                    'reference_url':reference_url if reference_url else None,
                    "file_url":file_url if file_url else None,
                    "price": price,
                    "currency": currency
                }
                st.write(data)
                response = supabase.table("bookings").insert(data).execute()
                if response.error is None:
                    st.success("Booking submitted!")
                else:
                    st.error(f"Error: {response.error.message}")
                    st.write(response)


elif choice == "Admin Dashboard":
    st.header("Admin Dashboard")
    password = st.text_input("Enter admin password", type="password")

    if password == "rockyadmin123":  # Change your admin password here!
        st.success("Access granted")
        # Fetch bookings
        response = supabase.table("bookings").select("*").order("created_at", desc=True).execute()
        if response.error is None:
            bookings = response.data
        else:
            st.error(f"Failed to retrieve bookings: {response.error.message}")

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
        if password:
            st.error("Incorrect password.")
