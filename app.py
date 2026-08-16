import streamlit as st
import pandas as pd
import os
import subprocess
import plotly.express as px
from google import genai

st.set_page_config(page_title="InstaSave Search Engine", page_icon="🔍", layout="wide")
st.title("🔍 Instagram Saved Posts Semantic Search Engine")

CSV_FILE = "my_instagram_links_vault.csv"

if not os.path.exists(CSV_FILE):
    st.error(f"Missing local file '{CSV_FILE}'!")
    st.stop()

df = pd.read_csv(CSV_FILE)
df["AI_Semantic_Tags"] = df["AI_Semantic_Tags"].fillna("")
df["Date_Parsed"] = pd.to_datetime(df["Date_Interacted"], errors='coerce')

def parse_metadata_string(tags_raw):
    if not tags_raw or " | " not in tags_raw:
        return {"TOPIC": "Uncategorized", "DETAILS": "None", "SUMMARY": tags_raw}
    try:
        return dict(item.split(": ", 1) for item in tags_raw.split(" | "))
    except Exception:
        return {"TOPIC": "Uncategorized", "DETAILS": "None", "SUMMARY": tags_raw}

parsed_tags_list = [parse_metadata_string(x) for x in df["AI_Semantic_Tags"]]
df["Category_Tag"] = [p.get("TOPIC", "Uncategorized").strip() for p in parsed_tags_list]

# ─── BROWSER BOOKMARKLET MOBILE INGESTION ENDPOINT ───
if "add_url" in st.query_params:
    incoming_url = st.query_params["add_url"]
    if incoming_url and incoming_url not in df["Post_URL"].values:
        with st.status("📥 Mobile Sync: Running AI pipeline...", expanded=True) as status:
            try:
                client = genai.Client()
                prompt = f"Analyze this Instagram URL: {incoming_url}.\nFormat as: TOPIC: X | DETAILS: Y | SUMMARY: Z"
                response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                ai_tags = response.text.strip()
                current_date = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                
                new_row = pd.DataFrame([{"Post_URL": incoming_url, "Date_Interacted": current_date, "AI_Semantic_Tags": ai_tags}])
                new_row.to_csv(CSV_FILE, mode='a', header=False, index=False, encoding="utf-8")
                
                os.system("git config --global user.email 'streamlittobot@example.com'")
                os.system("git config --global user.name 'Streamlit Cloud Automation'")
                os.system("git add my_instagram_links_vault.csv")
                os.system(f"git commit -m 'Mobile Bookmarklet Sync: {current_date}'")
                
                github_token = st.secrets["MY_GITHUB_TOKEN"]
                repo_url = f"https://{github_token}@://github.com{st.secrets['GITHUB_USER']}/{st.secrets['GITHUB_REPO']}.git"
                subprocess.run(["git", "push", repo_url, "main"])
                
                status.update(label="🎉 Saved successfully! Closing window...", state="complete")
                st.components.v1.html("<script>window.close();</script>", height=0)
                st.stop()
            except Exception as e:
                st.error(f"Mobile sync error: {e}")

# ─── SIDEBAR OPTIONS & FILTERS ───
with st.sidebar:
    st.header("📥 Sync New Instagram Post")
    new_url = st.text_input("Paste Instagram URL:", placeholder="https://instagram.com...")
    
    if st.button("🚀 Process & Save Post"):
        if "instagram.com" in new_url:
            with st.spinner("🤖 Processing post metadata..."):
                try:
                    client = genai.Client()
                    prompt = f"Analyze this Instagram URL: {new_url}.\nFormat as: TOPIC: X | DETAILS: Y | SUMMARY: Z"
                    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                    ai_tags = response.text.strip()
                    current_date = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    new_row = pd.DataFrame([{"Post_URL": new_url, "Date_Interacted": current_date, "AI_Semantic_Tags": ai_tags}])
                    new_row.to_csv(CSV_FILE, mode='a', header=False, index=False, encoding="utf-8")
                    
                    os.system("git config --global user.email 'streamlittobot@example.com'")
                    os.system("git config --global user.name 'Streamlit Cloud Automation'")
                    os.system("git add my_instagram_links_vault.csv")
                    os.system(f"git commit -m 'Dashboard Appended Sync: {current_date}'")
                    
                    github_token = st.secrets["MY_GITHUB_TOKEN"]
                    repo_url = f"https://{github_token}@://github.com{st.secrets['GITHUB_USER']}/{st.secrets['GITHUB_REPO']}.git"
                    subprocess.run(["git", "push", repo_url, "main"])
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    st.markdown("---")
    st.header("🎛️ Filter & Refine Options")
    unique_categories = ["All Categories"] + sorted(list(df["Category_Tag"].unique()))
    selected_category = st.selectbox("Select Content Topic:", unique_categories)
    sort_order = st.radio("Chronological Order Sorting:", ["Newest First", "Oldest First"])

# ─── VISUAL DATA ANALYTICS METRICS ───
st.markdown("### 📊 Your Collection Insights")
col1, col2 = st.columns()
with col1:
    st.metric(label="Total Saved Items Archived", value=len(df))
    top_cat = df["Category_Tag"].value_counts().idxmax() if not df.empty else "None"
    st.metric(label="Most Saved Collection", value=top_cat)

with col2:
    if not df.empty:
        cat_counts = df["Category_Tag"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Count"]
        fig = px.bar(cat_counts, x="Count", y="Category", orientation='h', title="Distribution of Your Saved Categories", color="Count", color_continuous_scale="Viridis")
        fig.update_layout(height=220, margin=dict(l=20, r=20, t=35, b=20), showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ─── MAIN APPS GRID SEARCH QUERY RENDERER ───
filtered_df = df.copy()
if selected_category != "All Categories":
    filtered_df = filtered_df[filtered_df["Category_Tag"] == selected_category]

filtered_df = filtered_df.sort_values(by="Date_Parsed", ascending=(sort_order != "Newest First"))

search_query = st.text_input("What saved post text or topic are you looking for?", placeholder="e.g., pasta recipe...")
if search_query:
    query = search_query.lower()
    filtered_df = filtered_df[filtered_df["AI_Semantic_Tags"].str.lower().str.contains(query) | filtered_df["Post_URL"].str.lower().str.contains(query)]

st.subheader(f"📊 Results ({len(filtered_df)} matches)")
for index, row in filtered_df.iterrows():
    with st.container():
        st.markdown(f"### 📍 Post Match #{index + 1}")
        st.write(f"**📅 Date Logged:** {row['Date_Interacted']}")
        parsed_data = parse_metadata_string(row['AI_Semantic_Tags'])
        st.markdown(f"**🏷️ Category:** `{parsed_data.get('TOPIC', 'General')}`")
        st.markdown(f"**📦 Extracted Details:** *{parsed_data.get('DETAILS', 'None')}*")
        st.markdown(f"**... Summary:** {parsed_data.get('SUMMARY', 'No descriptive data.')}")
        st.link_button("Open Original Instagram Link ↗️", row["Post_URL"])
        st.markdown("---")
              
