import os, io, zipfile
from datetime import datetime

import streamlit as st
from PIL import Image
from dotenv import load_dotenv
from auth0_component import login_button
from loader import load_model
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from google import genai
from pdfgen import create_referral_pdf

load_dotenv()

def secret(key: str) -> str:
    if os.getenv(key):
        return os.getenv(key)
    try:
        return st.secrets[key]
    except:
        st.error(f"Missing secret: {key}")
        st.stop()

# ── Secrets & clients ─────────────────────────────────────────────────────
DOMAIN        = secret("AUTH0_DOMAIN")
CLIENTID      = secret("AUTH0_CLIENT_ID")
RET_URL       = secret("AUTH0_LOGOUT_RETURN")
MONGO_URI     = secret("MONGO_URI")
GEMINI_API_KEY= secret("GEMINI_API_KEY")

genai_client = genai.Client(api_key=GEMINI_API_KEY)
SUCCESS, WARNING, DANGER = "#33a02c", "#ffa500", "#e02d2d"

# ── Streamlit page setup ─────────────────────────────────────────────────
st.set_page_config(page_title="Melo.", page_icon="🩺", layout="centered")

if "user" not in st.session_state:
    # a centered container for all of our intro text
    st.markdown(
        """
        <div style="max-width:600px; margin:2rem auto; text-align:center;">
          <h1 style="font-size: 100px";>🩺 Melo</h1>
          <p style="font-size:40px; line-height:1.4;">
            An ML-based Melanoma detection algorithm.
          </p>
          <ul style="font-size: 30px; list-style:none; padding:0; text-align:left; display:inline-block;">
            <li>✅ Save past image uploads and review history, assign labels, etc.</li>
            <li>✉️ Automatically generate referral emails & PDFs to your healthcare provider(s)</li>
            <li>🔒 Secure and compliant patient data hosting with Auth0 & MongoDB Atlas</li>
            <li>🧠 ...and most importantly, a custom-trained model for high-confidence melanoma detection.</li>
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # now center the login button beneath it
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        user = login_button(CLIENTID, domain=DOMAIN)

    if user:
        st.session_state["user"] = user
        st.experimental_rerun()
    else:
        st.stop()

# — now the rest of your app runs, with `user = st.session_state["user"]` available
user = st.session_state["user"]

# ── Top-right controls ────────────────────────────────────────────────────
ctrl, _ = st.columns([9,1])
with ctrl:
    st.markdown(f"<h2 style='color:#58A4B0;'>Welcome, {user.get('name','').split()[0]}!</h2>",
                unsafe_allow_html=True)
with _:
    if "last_pdf" in st.session_state:
        st.download_button(
            "📄 PDF",
            st.session_state["last_pdf"],
            file_name="Melo_referral.pdf",
            mime="application/pdf"
        )
    if st.button("&larr;"):
        st.session_state.clear()
        st.experimental_rerun()
        st.markdown(
            f"<script>window.location.href='https://{DOMAIN}/v2/logout?"
            f"client_id={CLIENTID}&returnTo={RET_URL}';</script>",
            unsafe_allow_html=True
        )

# ── Mongo + history sidebar ──────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_db():
    client = MongoClient(MONGO_URI, server_api=ServerApi("1"))
    client.admin.command("ping")
    return client["melo"]

db  = get_db()
col = db["results"]

with st.sidebar.expander("📜 Past Results"):
    st.write(f"User: {user.get('email')}")
    for doc in col.find({"user_id": user["sub"]}).sort("ts",-1).limit(10):
        ts = doc["ts"].strftime("%Y-%m-%d %H:%M")
        st.write(f"{ts} — {doc['tag']} — {doc['severity']} "
                 f"({doc['prob_melanoma']*100:.1f}%)")
    if col.count_documents({"user_id":user["sub"]}) == 0:
        st.caption("No scans yet.")

# ── Load model ───────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_all():
    return load_model()
model, labels, tfm = load_all()

# ── Decile messages ──────────────────────────────────────────────────────
decile_msgs = [
    "Your risk is very low. Continue regular self-checks and sun protection.",
    "Low risk. Monitor the area and protect your skin daily.",
    "Low, but consider a routine skin exam if concerned.",
    "Moderate-low risk. Scheduling a dermatologist visit is wise.",
    "Mid-range risk. Professional evaluation recommended.",
    "Moderate-high risk. Please arrange a skin check soon.",
    "High risk. Seek a dermatologist promptly.",
    "Very high risk. Immediate professional evaluation advised.",
    "Extreme risk. Urgent medical attention recommended.",
    "Critical risk. Contact a dermatologist without delay.",
]

# ── Main upload & analysis ───────────────────────────────────────────────
uploaded = st.file_uploader("Upload lesion image (JPG/PNG)", type=["jpg","jpeg","png"])
if uploaded:
    img = Image.open(uploaded).convert("RGB")
    st.image(img, use_column_width=True)

    # inference
    with st.spinner("Analyzing…"):
        x    = tfm(img).unsqueeze(0)
        prob = model(x).softmax(1)[0, labels.index("mel")].item()

    decile = min(int(prob*10), 9)
    sev, colr = (
        ("HIGH", DANGER)   if prob > 0.6 else
        ("MEDIUM", WARNING) if prob > 0.3 else
        ("LOW", SUCCESS)
    )

    st.markdown(
        f"<div style='border-left:4px solid {colr};"
        f"padding:0.5em;margin:1em 0;'>"
        f"<strong>Probability:</strong> {prob*100:.1f}% → {sev}<br/><br/>"
        f"{decile_msgs[decile]}"
        f"</div>",
        unsafe_allow_html=True
    )

    tag = st.selectbox(
        "Body area for this scan",
        ["Face","Scalp","Neck","Chest","Back","Arm","Leg","Hand/Foot","Other"],
        index=0
    )

    if st.button("📦 Save"):
        # persist
        col.insert_one({
            "user_id":     user["sub"],
            "filename":    uploaded.name or f"scan_{datetime.utcnow().timestamp()}.jpg",
            "prob_melanoma": prob,
            "severity":    sev,
            "tag":         tag,
            "ts":          datetime.utcnow(),
        })
        # create PDF
        pdf_bytes = create_referral_pdf(img, prob, sev, tag,
                                        user.get("name","Patient"),
                                        genai_client)
        # zip + download
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr(f"referral_{tag}.pdf", pdf_bytes)
            imgio = io.BytesIO()
            img.save(imgio, format="PNG")
            zf.writestr(uploaded.name, imgio.getvalue())
        buf.seek(0)
        st.download_button(
            "⬇️ Download files to send to healthcare provider",
            buf,
            file_name=f"melo_{tag}_package.zip",
            mime="application/zip"
        )
        st.success("Downloaded successfully.")

    st.caption("Disclaimer: This tool is for educational purposes and not a substitute for professional medical advice.")