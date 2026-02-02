import streamlit as st
import json
import os
import glob
from ddgs import DDGS
from core.schemas import FullScript

st.set_page_config(page_title="Evidence-First Director", layout="wide")

# --- SMART FILE LOADER ---
def get_available_scripts():
    # Look for script_*.json in root and output/ folders
    files = glob.glob("script_*.json") + glob.glob("output/script_*.json")
    # Sort by newest first
    files.sort(key=os.path.getmtime, reverse=True)
    return files

# --- SIDEBAR SELECTOR ---
st.sidebar.title("🗄️ Project Loader")
script_files = get_available_scripts()

if not script_files:
    st.error("❌ No 'script_*.json' files found in root or output/ folders.")
    st.stop()

selected_file = st.sidebar.selectbox("Select a Script:", script_files)

# Auto-detect corresponding Visual Plan
# Assumes format: script_TOPIC.json -> visual_plan_TOPIC.json
# works for output/script_TOPIC.json -> output/visual_plan_TOPIC.json
visual_plan_file = selected_file.replace("script_", "visual_plan_")

st.sidebar.info(f"📂 Loaded: {selected_file}")
if os.path.exists(visual_plan_file):
    st.sidebar.success(f"🎨 Visual Plan found!")
else:
    st.sidebar.warning(f"⚠️ Visual Plan missing\n(Expected: {visual_plan_file})")

# --- LOADERS ---
def load_data(script_path, plan_path):
    """Loads the script and visual plan with encoding fallback."""
    script = None
    visual_plan = []

    # 1. Load Script
    try:
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script = FullScript(**json.load(f))
        except UnicodeDecodeError:
            with open(script_path, 'r', encoding='cp1252') as f:
                script = FullScript(**json.load(f))
    except Exception as e:
        st.error(f"Failed to load script: {e}")
        return None, None

    # 2. Load Visual Plan (if exists)
    if os.path.exists(plan_path):
        try:
            try:
                with open(plan_path, 'r', encoding='utf-8') as f:
                    visual_plan = json.load(f)
            except UnicodeDecodeError:
                with open(plan_path, 'r', encoding='cp1252') as f:
                    visual_plan = json.load(f)
        except Exception as e:
            st.warning(f"Failed to parse visual plan: {e}")

    return script, visual_plan

def save_data(script, visual_plan, script_path, plan_path):
    """Saves the modified data back to JSON."""
    try:
        # Save Script
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script.model_dump_json(indent=2))
        
        # Save Visual Plan
        if visual_plan:
            with open(plan_path, 'w', encoding='utf-8') as f:
                json.dump(visual_plan, f, indent=2)
        
        st.toast(f"✅ Saved to {script_path}")
    except Exception as e:
        st.error(f"Save failed: {e}")

# --- UTILS ---
def search_preview(query):
    """Performs a live DuckDuckGo image search."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=3))
            return [r['thumbnail'] for r in results]
    except Exception:
        return []

# --- MAIN UI ---
st.title("🎬 Evidence-First: Director's Desk")

# Initialize Session State when File Changes
if "current_file" not in st.session_state or st.session_state["current_file"] != selected_file:
    script, v_plan = load_data(selected_file, visual_plan_file)
    if script:
        st.session_state["script"] = script
        st.session_state["visual_plan"] = v_plan
        st.session_state["current_file"] = selected_file
    else:
        st.stop()

script = st.session_state["script"]
visual_plan = st.session_state["visual_plan"]

# Global Script Metadata
with st.expander("📄 Script Metadata (Title, Sources)", expanded=False):
    new_title = st.text_input("Video Title", value=script.title)
    script.title = new_title
    st.write("Sources Bibliography:")
    st.json(script.sources_bibliography)

st.markdown("---")

# Iterate through Segments
for i, segment in enumerate(script.segments):
    
    # Match Visual Plan Segment
    # Handle case where visual_plan is empty or None
    seg_plan = None
    if visual_plan:
        seg_plan = next((p for p in visual_plan if p.get("segment_order") == segment.segment_order), None)

    with st.container():
        col1, col2 = st.columns([1, 1])
        
        # LEFT: Narration
        with col1:
            st.subheader(f"Segment {segment.segment_order}")
            st.caption(f"Evidence IDs: {segment.evidence_refs}")
            
            new_text = st.text_area(
                f"Narration", 
                value=segment.narration_text,
                height=150,
                key=f"text_{i}",
                label_visibility="collapsed"
            )
            segment.narration_text = new_text

        # RIGHT: Visual Plan
        with col2:
            st.subheader("Visual Queries")
            if seg_plan:
                shots = seg_plan.get("shots", [])
                for j, shot in enumerate(shots):
                    cols = st.columns([3, 1])
                    with cols[0]:
                        new_query = st.text_input(
                            f"Shot {j+1}", 
                            value=shot["visual_query"],
                            key=f"q_{i}_{j}",
                            label_visibility="collapsed"
                        )
                        shot["visual_query"] = new_query
                    
                    with cols[1]:
                        if st.button("👁️", key=f"btn_{i}_{j}"):
                            st.session_state[f"preview_{i}_{j}"] = search_preview(new_query)

                    # Preview area
                    if f"preview_{i}_{j}" in st.session_state:
                        thumbnails = st.session_state[f"preview_{i}_{j}"]
                        if thumbnails:
                            st.image(thumbnails, width=150)
                        else:
                            st.caption("No images found.")
            else:
                st.info("No visual plan for this segment.")

    st.markdown("---")

# Save Button
if st.button("💾 Save All Changes", type="primary", use_container_width=True):
    save_data(script, visual_plan, selected_file, visual_plan_file)