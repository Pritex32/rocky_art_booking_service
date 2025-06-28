import streamlit as st
st.set_page_config(
    page_title='Rocky_art_bookings',
    page_icon='👋 ',
)
# to hide streamlit icons
hide_footer = """
    <style>
        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
    </style>
"""
st.markdown(hide_footer, unsafe_allow_html=True)

# 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
import bcrypt
import uuid

import pandas as pd
from streamlit_option_menu import option_menu
from io import BytesIO
from datetime import datetime, date
import json
import time
from streamlit_cookies_manager import EncryptedCookieManager
from PIL import Image
from postgrest.exceptions import APIError
import requests
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from twilio.rest import Client as TwilioClient
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fpdf import FPDF
import io



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
        import time
        # Read file bytes
        file_bytes = file.read()
        
        # Create unique filename
        filename = f"{int(time.time())}_{file.name}"
        
        # Upload file bytes to Supabase storage bucket
        response = supabase.storage.from_(bucket_name).upload(filename, file_bytes)
        
        # Check if upload failed
        if hasattr(response, 'error') and response.error is not None:
            st.error(f"Failed to upload file: {response.error['message']}")
            return None
        
        # Get public URL for the uploaded file
        public_url = supabase.storage.from_(bucket_name).get_public_url(filename)
        return public_url
    
    except Exception as e:
        st.error(f"Exception during file upload: {e}")
        return None

# to views files from storage
def list_files_in_bucket(bucket_name):
    data, error = supabase.storage.from_(bucket_name).list()
    if error:
        st.error(f"Error listing files: {error}")
        return []
    return data

        
# to inittialize payment with paystack
def initialize_payment(email, amount):
    paystack_secret_key = 'sk_test_2b9eaa646ab366b5a0062b70662d54fcf9494b65'
    headers = {
        "Authorization": f"Bearer {paystack_secret_key}",


        "Content-Type": "application/json",
    }
    data = {
        "email": email,
        "amount": int(amount * 100),  # Paystack expects amount in Kobo
        "reference": str(uuid.uuid4()),
        "callback_url": "https://yourdomain.com/verify_payment",  # For webhook handling
    }
    res = requests.post("https://api.paystack.co/transaction/initialize", headers=headers, json=data)
    return res.json()
# to add company logo
class PDF(FPDF):
    def footer(self):
        # Position footer 20 units from bottom
        self.set_y(-20)

        # Add logo to the left
        self.image('logo__rockyart.png', x=10, y=self.get_y(), w=20)

        # Add footer text centered
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, '© 2025 Rocky Art Company. All rights reserved.', 0, 0, 'C')
        # to ensure that this symbol # is replace everywhere in this code


# for receipt generation
def generate_receipt_pdf(data):
    pdf = FPDF()
    pdf.add_page()

    # Title - bold and larger font
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Rocky Art Booking Receipt", ln=True, align='C')

    # Date Issued
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, txt=f"Date Issued: {date.today()}", ln=True)
    pdf.ln(5)

    # Customer info - label bold, info normal
    def write_label_value(label, value):
        pdf.set_font("Arial", '', 12)
        pdf.cell(40, 10, label + ":", ln=False)
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, str(value), ln=True)

    write_label_value("Name", data['name'])
    write_label_value("Email", data['email'])
    write_label_value("Phone", data['phone_number'])
    write_label_value("Service", data['service'])
    write_label_value("Location", data['location'])
    write_label_value("Deadline", data['deadline'])
    write_label_value("Currency", data['currency'])

    # Format price with symbol
    symbol = "$" if data['currency'] == 'USD' else "NGN"
    price_str = f"{symbol} {data['price']:,.0f}"
    write_label_value("Price", price_str)

    # New fields: Payment option and payment status
    payment_option = data.get('payment_option', 'N/A')
    payment_status = data.get('payment_status', 'N/A')
    amount_paid = data.get('amount_paid', 0)
    amount_paid_str = f"{symbol}{amount_paid:,.2f}"

    write_label_value("Payment Option", payment_option)
    write_label_value("Payment Status", payment_status)
    write_label_value("Amount Paid", amount_paid_str)

    pdf.ln(5)

    # Details section (multi cell for longer text)
    if data.get("details"):
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, "Details:", ln=True)
        pdf.set_font("Arial", '', 12)
        pdf.multi_cell(0, 10, data['details'])

    # Optional: Add a footer line or thank you note
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, "Thank you for your booking!", ln=True, align='C')

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer.read()
    




# for rediction to admin dashbooard
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""
if "menu_page" not in st.session_state:
    st.session_state.menu_page = "Book a Service"

from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()



def send_email(to, subject, body):
    sender_email = 'oluomachiukanwa32@gmail.com'         # <- Your Gmail
    sender_password = 'priscaukanwa'
    # <- App password from Gmail

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to, msg.as_string())
        server.quit()
        print(f"✅ Email sent to {to}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email to {to}. Error: {e}")
        return False



# get booking table
def get_all_bookings():
    response = supabase.table("bookings").select("*").execute()
    if response.data:
        return pd.DataFrame(response.data)
    else:
        return pd.DataFrame()  # Return empty DataFrame if no data





# To send automatic mail and WhatsApp messages
def send_notifications(bookings):
    name = bookings.get('name')
    email = bookings.get('email')
   
    service = bookings.get('service')
    
    if not email or not name or not service:
        print("Missing required booking info.")
        return False  # Don’t send anything if critical info is missing

    # Send Email
    email_subject = f"🎉 {name}, your {service} service is complete — Action Required"
    email_body = f"""Hi {name},

We're happy to inform you that your booking for **{service}** has been successfully completed.

If you have any outstanding payment, we kindly ask that you complete it as soon as possible to finalize the process.

We appreciate your trust in our service and look forward to serving you again.

If you have any questions or need assistance, feel free to reach out.

Warm regards,  
**Rocky Art**  
Customer Service Team
"""

   
    # Send notifications
    email_sent=send_email(to=email, subject=email_subject, body=email_body)
    if email_sent:
        print("Email sent successfully!")
    else:
        print("Email failed to send.")
    return email_sent

@st.cache_data(ttl=7200) 
def get_usd_to_ngn_rate():
    API_KEY = "d25a9a667870cb6fe7c611ba"  # Put your actual API key here or store as env var
    url=f"https://v6.exchangerate-api.com/v6/d25a9a667870cb6fe7c611ba/latest/USD"
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
st.info(f"Current USD to NGN rate: NGN{USD_TO_NGN}")  # Fixed variable name

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
        "currency": currency,  # New column, add to your supabase table!
        "payment_status": "Pending",
        "payment_reference": reference,
        "payment_option": payment_option,
        "amount_paid": amount_to_pay
    }

    response = supabase.table("bookings").insert(data).execute()
    if response.error is None:
        return True
    else:
        st.error(f"Failed to submit booking: {response.error.message}")
        return False



import hashlib

# Simple in-memory "database"
if "admins" not in st.session_state:
    st.session_state.admins = {}  # store {username: hashed_password}
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register(username, password):
    if username in st.session_state.admins:
        st.error("User already exists!")
    else:
        st.session_state.admins[username] = hash_password(password)
        st.success("Admin registered successfully!")

def login(username, password):
    hashed = hash_password(password)
    if st.session_state.admins.get(username) == hashed:
        st.session_state.logged_in = True
        st.session_state.current_user = username
        st.success(f"Welcome {username}!")
    else:
        st.error("Invalid username or password")

def logout():
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.success("Logged out successfully")

if "booking_data" not in st.session_state:
    st.session_state.booking_data = {}
   
if "show_receipt_button" not in st.session_state:
    st.session_state.show_receipt_button = False


col1,col2=st.columns([3,1])
with col1:
    st.title("🎨 Rocky Art Booking System")
with col2:
    image='logo__rockyart.png'
    img=Image.open(image)
    resize_img=img.resize((100,100))
    st.write(resize_img,width=100)

menu = ["Book a Service","Admin Login/Register", "Admin Dashboard"]
# Show dropdown only if not logged in or if not on admin dashboard



if not st.session_state.logged_in:
    choice = st.selectbox("Menu", menu, index=0)
    st.session_state.menu_page = choice
else:
    st.session_state.menu_page = "Admin Dashboard"
choice = st.session_state.menu_page

if choice == "Book a Service":
    st.header("Submit a Booking")

    with st.form("booking_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        phone_number = st.text_input('Phone_number', value="")  # Changed default from 0 to empty string
        currency = st.selectbox("Select Currency", ["USD", "NGN"])
        location = st.text_input('Location', value='London')

        # Set symbol before it's used in format_service
        symbol = "$" if currency == "USD" else "NGN"

        # Show services with price in selected currency
        def format_service(service_name):
            price = convert_price(services_usd[service_name], currency)
            price_str = f"{service_name} - {symbol}{price:,.0f}"
            return price_str

        service = st.selectbox("Select Service", options=list(services_usd.keys()), format_func=format_service)

        deadline = st.date_input("Deadline")
        details = st.text_area("Project Details / Description")

        # File uploader for reference file
        reference_file = st.file_uploader("Upload Reference File (optional)", type=['png', 'jpg', 'jpeg', 'pdf', 'mp4', 'mov'])

        # URL input for reference link
        reference_url = st.text_input("Or enter a Reference URL (optional)")

        # Price calculations
        price = convert_price(services_usd[service], currency)
        symbol = "$" if currency == "USD" else "NGN"

        payment_option = st.radio("Payment Option", ["Full Payment", "50% Deposit"])
        if payment_option == "50% Deposit":
            amount_to_pay = price / 2
            payment_status = "Partial"
        else:
            amount_to_pay = price
            payment_status = "Paid"

        # Format display strings
        amount_to_pay_str = f"{symbol} {amount_to_pay:,.0f}"
        total_price_str = f"{symbol} {price:,.0f}"
        price_str = f"{symbol} {price:,.0f}"

        # Display on screen
        st.markdown(f"**Amount to Pay Now:** {amount_to_pay_str}")
        st.markdown(f"**Total Price:** {total_price_str}")
        st.markdown(f"**Price:** {price_str}")

        submitted = st.form_submit_button("Submit Booking")

        if submitted:
            if not name or not email:
                st.error("Please fill in all required fields.")
            else:
                if currency == "USD":
                    amount_to_pay_in_naira = convert_price(amount_to_pay, "NGN")
                else:
                    amount_to_pay_in_naira = amount_to_pay

                init_response = initialize_payment(email, amount_to_pay_in_naira)
                if init_response["status"]:
                    payment_link = init_response["data"]["authorization_url"]
                    reference = init_response["data"]["reference"]
                    file_url = ""
                    uploaded_url_obj = None

                    if reference_file is not None:
                        uploaded_url_obj = upload_file_to_supabase(reference_file)
                    if uploaded_url_obj is not None:
                        file_url = uploaded_url_obj

                    data = {
                        "name": name,
                        "email": email,
                        "service": service,
                        "location": location,
                        "phone_number": str(phone_number),
                        "deadline": str(deadline),
                        "details": details if details else None,
                        "reference_url": reference_url if reference_url else None,
                        "file_url": file_url if file_url else None,
                        "price": price,
                        "currency": currency,
                        "payment_status": "Pending",
                        "payment_reference": reference,
                        "payment_option": payment_option,
                        "amount_paid": amount_to_pay
                    }

                    response = supabase.table("bookings").insert(data).execute()
                    st.success("Redirecting to payment...")
                else:
                    st.error("Payment initialization failed. Try again.")

                # Safe error access:
                error = getattr(response, "error", None)
                if error is None:
                    st.success("Booking submitted!")
                    st.session_state.booking_data = data
                    st.session_state.booking_submitted = True
                    st.markdown(f"[Click here to Pay]({payment_link})")
                else:
                    st.session_state.booking_submitted = False
                    error_message = getattr(error, "message", str(error))
                   
                
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.get("booking_submitted", False):  # ✅ only if submitted
            data = st.session_state.get("booking_data", {})
            data = st.session_state.booking_data
            required_keys = ["name", "email", "service", "location", "phone_number", "deadline", "price", "currency"]
            missing_keys = [key for key in required_keys if key not in data]

            if missing_keys:
                st.error(f"Missing data fields in booking_data: {', '.join(missing_keys)}")
            else:
                receipt_pdf = generate_receipt_pdf(data)
                st.download_button(
                label="Download Receipt",
                data=receipt_pdf,
                file_name=f"rocky_art_receipt_{data['name'].replace(' ', '_')}.pdf",
                mime="application/pdf" )
        else:
            st.warning("No booking data available yet. Please submit the form first.")

    
    

    with col2:
        if st.button('View My Work', key='view_work_button'):
            st.write('[View my Works on Instagram](https://www.instagram.com/rocky__art?igsh=MXJkaTZxa2o2YXcwaA==)')







from postgrest.exceptions import APIError

if choice == "Admin Login/Register":
    st.header("Admin Login")
    with st.form("login_form"):
        login_username = st.text_input("Username")
        login_password = st.text_input("Password", type="password")
        login_submitted = st.form_submit_button("Login")
        if login_submitted:
            # Call login logic
            response = supabase.table("admins").select("*").eq("username", login_username).eq("password_hash", login_password).execute()
            if response.data:
                st.session_state.logged_in = True
                st.session_state.current_user = login_username
                st.session_state.menu_page = "Admin Dashboard"
                st.success("Login successful! Redirecting to Admin Dashboard...")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    st.markdown("---")

    st.header("Admin Registration")
    with st.form("register_form"):
        reg_username = st.text_input("New Username")
        reg_password = st.text_input("New Password", type="password")
        reg_submit = st.form_submit_button("Register")

        if reg_submit:
            try:
                response = supabase.table("admins").insert({
                    "username": reg_username,
                    "password_hash": reg_password  # In real apps, hash this!
                }).execute()

                if response.data:
                    st.success("Admin registered successfully!")

            except APIError as e:
                if e.code == '23505':  # Unique constraint violation
                    st.error("Username already exists. Please choose a different one.")
                else:
                    st.error(f"Registration failed: {e.message}")


elif choice == "Admin Dashboard":
    st.header("Admin Dashboard")
    password = st.text_input("Enter admin password", type="password")

    if password == "rockyadmin123":  # Change your admin password here!
        st.success("Access granted")
        # Fetch bookings
        with st.expander("📋 View All Bookings"):
            df=get_all_bookings()
            if not df.empty:
                st.dataframe(df)
            else:
                st.write("Booking not found.")

        with st.expander("📁 Files in Storage Bucket"):
            bucket_name = "bookingsbucket"
            files = list_files_in_bucket(bucket_name)  
            if files:
                # Convert list of dicts to DataFrame to show as a table
                df = pd.DataFrame(files)
                st.dataframe(df)
            else:
                st.write("No files found in bucket.")

                                                 
            

       
        response = supabase.table("bookings").select("*").order("created_at", desc=True).execute()
        if response.data:
            bookings = response.data
            if bookings:
                # Filter out completed bookings
                pending_bookings = [b for b in bookings if b.get("status") != "Completed"]
                for b in pending_bookings:
                    st.markdown(f"**Name:** {b['name']}")
                    st.markdown(f"**Email:** {b['email']}")
                    st.markdown(f"**Service:** {b['service']}")
                    st.markdown(f"**Deadline:** {b['deadline']}")
                    st.markdown(f"**Details:** {b['details']}")
                    st.markdown(f"**Status:** {b.get('status', 'Pending')}")
                    st.markdown(f"**Payment_Status:** {b.get('payment_status', 'Unknown')}")

                    st.markdown(f"**Price:** {b.get('price', 'N/A')}")
                    file_url = b.get("file_url")
                    if file_url:
                        st.markdown(f"[📎 View Uploaded File]({file_url})", unsafe_allow_html=True)
                        try:
                            response = requests.get(file_url)
                            response.raise_for_status()
                            st.download_button(
                                "Download File",
                                data=response.content,
                                file_name="reference_file",
                                mime="application/octet-stream")
                            st.download_button("Download File", data=requests.get(bookings['file_url']).content, file_name="reference_file", mime="application/octet-stream")
                        except Exception as e:
                            st.error("Could not download the file.")
                    else:
                        st.write("No file uploaded.")      


                    st.markdown(f"**Submitted At:** {b['created_at']}")
                    st.markdown("---")
                    # Unique key per booking to avoid Streamlit warning
                    button_key = f"complete_{b['id']}"

                    if b.get('status', 'Pending') != "Completed":
                        if st.button("Mark as Completed", key=button_key):
                            # Update status in Supabase
                            update_response = supabase.table("bookings").update( {"status": "Completed"}).eq("id", b['id']).execute()

                            if 'error' not in update_response or update_response['error'] is None:
                                email_sent=send_notifications(b)
                                st.success("Booking marked as completed.")
                                if email_sent:
                                    st.success("Booking marked as completed and email sent successfully.")
                                else:
                                    st.error("Booking marked as completed but email failed to send.")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(f"Update failed: {update_response.error.message}")


                     
            else:
                st.info("No bookings found.")
        else:
            st.error(f"Failed to retrieve bookings: {response.error.message}")
    else:
        if password:
            st.error("Incorrect password.")
