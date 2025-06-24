import streamlit as st
import pandas as pd
import requests
import io

st.set_page_config(page_title="LinkedIn Bulk Extractor", layout="wide")
st.title("📄 LinkedIn Bulk Data Extractor")

st.markdown("Upload a CSV file with a column named `username`.")

# Initialize session state
if "all_results" not in st.session_state:
    st.session_state.all_results = []

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

extract_comments = st.selectbox("Extract Comments?", ["yes", "no"])
count = st.number_input("Number of Comments per Post", min_value=0, max_value=50, value=2)

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if "username" not in df.columns:
        st.error("CSV must contain a 'username' column.")
    else:
        usernames = df["username"].dropna().unique().tolist()

        if st.button("Start Extraction"):
            results = []
            flat_rows = []

            for username in usernames:
                with st.spinner(f"Fetching data for {username}..."):
                    try:
                        url = "https://linkedin-extractor-v7yv.onrender.com/extract-all"
                        params = {
                            "username": username,
                            "extract_comments": extract_comments,
                            "count": count
                        }
                        res = requests.get(url, params=params)
                        res.raise_for_status()
                        data = res.json()

                        credits_used = data.get("credits_used", "N/A")

                        result = {"username": username, "data": data, "credits_used": credits_used}
                        results.append(result)
                        st.session_state.all_results.append(result)

                        st.success(f"✅ Fetched for: {username} (Credits Used: {credits_used})")

                    except Exception as e:
                        st.error(f"❌ Failed for {username}: {e}")

# Button to show all session results
if st.button("Show All Extracted Results"):
    if not st.session_state.all_results:
        st.info("No results yet in session.")
    else:
        flat_rows = []
        st.subheader("✅ All Session Extracted Data Summary")

        for result in st.session_state.all_results:
            username = result["username"]
            data = result["data"]
            credits_used = result["credits_used"]
            profile = data.get("profile", {})

            st.markdown(f"### 👤 {username} — Credits Used: **{credits_used}**")

            for post in data.get("posts", []):
                flat_rows.append({
                    "username": username,
                    "type": "post",
                    **profile,
                    **post,
                    "comments": ", ".join(post.get("comments", [])) if "comments" in post else ""
                })

            for repost in data.get("reposts", []):
                flat_rows.append({
                    "username": username,
                    "type": "repost",
                    **profile,
                    **repost
                })

            for comment in data.get("commented_posts", []):
                flat_rows.append({
                    "username": username,
                    "type": "commented_post",
                    **profile,
                    **comment
                })

            for like in data.get("reacted_posts", []):
                flat_rows.append({
                    "username": username,
                    "type": "reacted_post",
                    **profile,
                    **like
                })

        final_df = pd.DataFrame(flat_rows)

        if not final_df.empty:
            st.dataframe(final_df)

            csv_buffer = io.StringIO()
            final_df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()

            st.download_button(
                label="📥 Download Full Session CSV",
                data=csv_data,
                file_name="linkedin_full_session_data.csv",
                mime="text/csv"
            )
