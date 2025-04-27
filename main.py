import os, streamlit as st
from dotenv import load_dotenv
from PIL import Image
from auth0_component import login_button
from loader import load_model

# ── load local .env (has no effect on Cloud) ────────────────────────
load_dotenv()

def secret(key: str) -> str:
    return st.secrets.get(key) or os.getenv(key) or st.error(f"Missing secret: {key}")

DOMAIN   = secret("AUTH0_DOMAIN")
CLIENTID = secret("AUTH0_CLIENT_ID")
RET_URL  = secret("AUTH0_LOGOUT_RETURN")

# ── page + global style ──────────────────────────────────────────────
st.set_page_config("Melo", "🩺", layout="wide")
st.markdown(
    """
    <style>
      #MainMenu, footer, .stDeployButton {visibility:hidden;}
      #stDecoration {display:none;}
    </style>
    """,
    unsafe_allow_html=True,
)

SUCCESS, WARNING, DANGER = "#33a02c", "#ffa500", "#e02d2d"

# ── nav bar ─────────────────────────────────────────────────────────
nav_left, nav_spacer, nav_right = st.columns([1, 6, 1])
with nav_left:
    st.markdown("<h2 style='margin:0'>Melo</h2>", unsafe_allow_html=True)

# ── auth flow ───────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.markdown("<h2 style='text-align:center;color:#58A4B0;margin-top:15vh;'>ML-Driven Skin Analysis</h2>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    user_info = login_button(CLIENTID, domain=DOMAIN)
    st.markdown("</div>", unsafe_allow_html=True)

    if user_info:
        st.session_state["user"] = user_info
        st.rerun()
    st.stop()

user = st.session_state["user"]

with nav_right:
    if st.button("Log out", key="logout"):
        st.session_state.pop("user", None)
        st.rerun()

    # hard redirect to Auth0 logout
    st.markdown(
        f"<script>window.location.href='https://{DOMAIN}/v2/logout?client_id={CLIENTID}&returnTo={RET_URL}';</script>",
        unsafe_allow_html=True,
    )

st.markdown(f"<h2 style='color:#58A4B0;margin-top:1em;'>Welcome, {user.get('name').split()[0]}!</h2>", unsafe_allow_html=True)

# ── model & inference helpers ───────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_model():
    return load_model()

model, labels, tfm = get_model()

# ── main UI ─────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Upload a picture of the affected area (JPG/PNG):",
    type=["jpg", "jpeg", "png"],
)

if uploaded:
    img = Image.open(uploaded).convert("RGB")
    st.image(img, caption="Uploaded image", use_container_width=True)

    with st.spinner("Analyzing …"):
        x = tfm(img).unsqueeze(0)
        prob = model(x).softmax(1)[0, labels.index("mel")].item()

    sev_txt, sev_col = (
        ("HIGH", DANGER) if prob > 0.6 else
        ("MEDIUM", WARNING) if prob > 0.3 else
        ("LOW", SUCCESS)
    )

    st.subheader("Results:")
    st.markdown(
        f"<h1 style='color:{sev_col};'>{prob*100:.1f}% ({sev_txt})</h1>",
        unsafe_allow_html=True,
    )

    if sev_txt == "HIGH":
        st.error("High risk detected — please consult a dermatologist promptly.")
    elif sev_txt == "MEDIUM":
        st.warning("Moderate risk — consider scheduling a professional skin check.")
    else:
        st.success("Low risk — continue regular self-monitoring and sun protection.")
