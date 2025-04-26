mkdir -p ~/.streamlit

cat > ~/.streamlit/credentials.toml <<EOF
[general]
email = "vishruthbharath@example.com"
EOF

cat > ~/.streamlit/config.toml <<EOF
[server]
headless = true
enableCORS = false
port = $PORT

[theme]
primaryColor="#58A4B0"
backgroundColor="#FFFFFF"
secondaryBackgroundColor="#F0F2F6"
textColor="#2D3142"
font="sans serif"
EOF