# 🩺 Melo

>[!Note]
>https://devpost.com/software/melo-39fqwa

## 💡 Inspiration
We set out to empower patients with a fast, accurate way to assess the risk of melanoma on their own photos—without waiting for specialist appointments. During hackathons and research discussions, we realized that many people notice suspicious moles but hesitate to see a dermatologist due to cost, distance, or anxiety. By combining our backgrounds in machine learning, web development, and healthcare, we decided to build **Melo**: an end-to-end, patient-facing melanoma detection assistant that bridges the gap between self-monitoring and professional care.

## 🏷️ Tracks
- **Healthcare**: Automated skin-lesion risk estimation.  
- **Auth0**: Secure user authentication and session management.  
- **MongoDB Atlas**: HIPAA-compatible storage of user scans and results.  
- **Streamlit**: Rapid web UI for uploads, reporting, and history browsing.  
- **Gemini API**: AI-powered referral email drafting for dermatologists.

## 🔍 What it does
1. **User sign-up & sign-in** via Auth0 to protect personal health data.  
2. **Image upload**: Patients submit a photo of the lesion.  
3. **On-the-fly inference** with our custom EfficientNet-based model, returning a melanoma risk probability and severity category.  
4. **Contextual guidance**: We display one of ten tailored messages—ranging from “Very low risk” to “Critical risk—seek immediate attention.”  
5. **History tracking**: All scans (timestamp, body-area tag, severity) are stored in MongoDB, letting users revisit past results.  
6. **Referral package**: One-click generation of a PDF + ZIP bundle—including a professional email draft (Gemini API) and the original image—ready to send to a dermatologist.

## 🏗️ How we built it
- **Streamlit frontend**: Single-page UI with centered landing, upload widget, results panel, and a sidebar for history.  
- **Custom model**: Fine-tuned EfficientNet-B0 on a labeled dataset of 10,000+ benign vs. malignant images; wrapped in a `@st.cache_resource` loader for speed.  
- **Auth0 integration**: Embedded `streamlit-auth0-component` for secure OAuth flows; allowed callback URLs configured for localhost and Streamlit Cloud.  
- **MongoDB Atlas**: Leveraged the Python driver with SRV connection; ping checks and a “results” collection grouped by user and body-area tags.  
- **Gemini API & ReportLab**: Used Google’s generative AI to draft empathetic referral emails, then built one-page PDFs (ReportLab) and ZIP archives for download.

## ⚔️ Challenges we ran into
- **Callback URL mismatches**: Auth0 rejected our local and cloud redirects until we carefully whitelisted `/component/auth0_component.login_button/index.html` endpoints.  
- **Image embedding in PDF**: ReportLab’s `Image` flowable required converting PIL images to in-memory PNG buffers before rendering.  
- **State management**: Ensuring `st.session_state` cleared correctly on logout and PDF regeneration without unexpected reruns.  
- **Context window prompts**: Crafting concise yet complete prompts for the Gemini API, then handling streaming vs. blocking calls in Streamlit’s synchronous environment.  
- **Responsive layout**: Aligning the login button and balancing columns across desktop and mobile views without extensive CSS support.

## 🏆 Accomplishments that we’re proud of
- **Zero-to-cloud MVP** in under two days, complete with secure auth, database, ML inference, and AI-driven document generation.  
- **Custom severity messaging** for 10 risk deciles—each with its own paragraph—to guide users with actionable next steps.  
- **Seamless referral package**: Single button to save, generate, and download both PDF and original image in a ZIP, ready for tele-dermatology workflows.  
- **Reproducible environment**: Full `requirements.txt`, `.env`/`secrets.toml` configuration, and modular code (UI in `main.py`, model loader in `loader.py`, PDF logic in `pdfgen.py`).

## 📚 What we learned
- The intricacies of **Auth0’s redirect rules** and how to test them locally vs. in production.  
- Best practices for **Streamlit state** and reruns, especially when mixing blocking API calls with UI interactions.  
- Techniques for **in-memory file handling** in Python—converting images and PDFs to `BytesIO` and feeding them into download widgets or ReportLab.  
- How to **craft prompts** for a multimodal LLM (Gemini) to produce consistent, empathetic emails under strict length constraints.  
- The importance of **user-friendly feedback** (spinners, colored severity bars, footer disclaimers) in a medical-grade tool.
