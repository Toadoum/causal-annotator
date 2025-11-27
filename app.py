"""
CausaFr Annotation Tool
=======================
Enhanced annotation app with:
- User authentication (from users.json)
- Persistent progress tracking per user
- View/download annotated files
- Inter-annotator agreement analysis

Run with: streamlit run causafr_annotation_app.py
"""

import streamlit as st
import json
import os
import hashlib
from datetime import datetime
from pathlib import Path

# =========================
# Configuration
# =========================

DATA_DIR = "data"
OUT_DIR = "output"
USERS_FILE = "users.json"
PROGRESS_FILE = "annotation_progress.json"

os.makedirs(OUT_DIR, exist_ok=True)

# =========================
# Utils
# =========================

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def hash_password(password):
    """Simple password hashing."""
    return hashlib.sha256(password.encode()).hexdigest()

# =========================
# Authentication
# =========================

def load_users():
    """Load users from users.json."""
    if os.path.exists(USERS_FILE):
        return load_json(USERS_FILE)
    return {}

def verify_user(username, password):
    """Verify username and password."""
    users = load_users()
    if username in users:
        stored_password = users[username]
        # Support both hashed and plain text passwords
        if len(stored_password) == 64:  # SHA256 hash length
            return stored_password == hash_password(password)
        else:
            return stored_password == password
    return False

def login_page():
    """Display login page."""
    st.title("🔐 CausaFr Annotation Tool")
    st.markdown("Please log in to continue.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                if verify_user(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.login_time = datetime.now().isoformat()
                    st.success(f"Welcome, {username}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")

def logout():
    """Log out the current user."""
    for key in ['authenticated', 'username', 'login_time', 'pair_index', 'current_dataset']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# =========================
# Progress Management
# =========================

def load_progress():
    """Load annotation progress for all users."""
    if os.path.exists(PROGRESS_FILE):
        return load_json(PROGRESS_FILE)
    return {}

def save_progress(username, dataset, index, total_annotated):
    """Save user's annotation progress."""
    progress = load_progress()
    
    if username not in progress:
        progress[username] = {}
    
    progress[username][dataset] = {
        "current_index": index,
        "total_annotated": total_annotated,
        "last_updated": datetime.now().isoformat()
    }
    
    save_json(PROGRESS_FILE, progress)

def get_user_progress(username, dataset):
    """Get user's progress for a specific dataset."""
    progress = load_progress()
    if username in progress and dataset in progress[username]:
        return progress[username][dataset]
    return {"current_index": 0, "total_annotated": 0}

def get_annotated_file_path(username, dataset):
    """Get the path to user's annotated file."""
    base_name = dataset.replace(".json", "")
    return os.path.join(OUT_DIR, f"{base_name}_{username}_annotated.json")

# =========================
# Statistics
# =========================

def compute_annotation_stats(pairs):
    """Compute statistics for annotated pairs."""
    total = len(pairs)
    if total == 0:
        return {"total": 0, "annotated": 0, "causal": 0, "non_causal": 0, 
                "with_cue1": 0, "with_cue2": 0, "causal_rate": 0}
    
    annotated = sum(1 for p in pairs if p.get("annotated_by"))
    causal = sum(1 for p in pairs if p.get("label") == 1)
    non_causal = sum(1 for p in pairs if p.get("label") == 0)
    with_cue1 = sum(1 for p in pairs if p.get("cue1"))
    with_cue2 = sum(1 for p in pairs if p.get("cue2"))
    
    return {
        "total": total,
        "annotated": annotated,
        "causal": causal,
        "non_causal": non_causal,
        "with_cue1": with_cue1,
        "with_cue2": with_cue2,
        "causal_rate": causal / total * 100 if total > 0 else 0
    }

# =========================
# Pair Annotation
# =========================

def annotate_pairs(username, file_name):
    """Main annotation interface."""
    path = os.path.join(DATA_DIR, file_name)
    out_path = get_annotated_file_path(username, file_name)
    
    # Check if source file exists
    if not os.path.exists(path):
        st.error(f"Dataset file not found: {path}")
        return
    
    # Load existing annotations or original data
    if os.path.exists(out_path):
        pairs = load_json(out_path)
        if isinstance(pairs, dict):
            pairs = pairs.get("pairs", [])
        st.sidebar.success("📂 Loaded your previous annotations")
    else:
        pairs = load_json(path)
        if isinstance(pairs, dict):
            pairs = pairs.get("pairs", [])
    
    if not pairs:
        st.error("No pairs found in dataset")
        return
    
    # Get user's progress and restore position
    user_progress = get_user_progress(username, file_name)
    
    # Handle dataset switch - reset index if dataset changed
    if st.session_state.get("current_dataset") != file_name:
        st.session_state.current_dataset = file_name
        st.session_state.pair_index = user_progress["current_index"]
    
    # Initialize pair_index if not present
    if "pair_index" not in st.session_state:
        st.session_state.pair_index = user_progress["current_index"]
    
    total_pairs = len(pairs)
    
    # Clamp index to valid range
    if st.session_state.pair_index >= total_pairs:
        st.session_state.pair_index = total_pairs - 1
    if st.session_state.pair_index < 0:
        st.session_state.pair_index = 0
    
    # Sidebar stats
    stats = compute_annotation_stats(pairs)
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Statistics")
    st.sidebar.metric("Total Pairs", stats["total"])
    annotated_pct = stats['annotated']/stats['total']*100 if stats['total'] > 0 else 0
    st.sidebar.metric("Annotated", f"{stats['annotated']} ({annotated_pct:.1f}%)")
    st.sidebar.metric("Causal Rate", f"{stats['causal_rate']:.1f}%")
    
    # Progress bar
    progress_pct = (st.session_state.pair_index + 1) / total_pairs if total_pairs > 0 else 0
    st.sidebar.progress(progress_pct)
    st.sidebar.caption(f"Position: {st.session_state.pair_index + 1} / {total_pairs}")
    
    # Navigation
    st.sidebar.markdown("---")
    st.sidebar.subheader("🧭 Navigation")
    
    jump_to = st.sidebar.number_input(
        "Jump to pair #",
        min_value=1,
        max_value=total_pairs,
        value=st.session_state.pair_index + 1
    )
    if st.sidebar.button("Go", key="jump_btn"):
        st.session_state.pair_index = jump_to - 1
        st.rerun()
    
    # Filter options
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Quick Jump")
    
    col_f1, col_f2 = st.sidebar.columns(2)
    with col_f1:
        if st.button("First unannotated", key="first_unannotated"):
            for i, p in enumerate(pairs):
                if not p.get("annotated_by"):
                    st.session_state.pair_index = i
                    st.rerun()
                    break
    with col_f2:
        if st.button("First causal", key="first_causal"):
            for i, p in enumerate(pairs):
                if p.get("label") == 1:
                    st.session_state.pair_index = i
                    st.rerun()
                    break
    
    # Current pair
    pair = pairs[st.session_state.pair_index]
    
    # Header
    st.title(f"📑 Pair {st.session_state.pair_index + 1} / {total_pairs}")
    
    # Metadata row
    col_meta1, col_meta2, col_meta3 = st.columns(3)
    with col_meta1:
        st.caption(f"👤 Child ID: {pair.get('child_id', 'N/A')}")
    with col_meta2:
        st.caption(f"📄 Narrative: {pair.get('narrative_id', pair.get('child_id', 'N/A'))}")
    with col_meta3:
        if pair.get("annotated_by"):
            st.caption(f"✏️ Annotated by: {pair.get('annotated_by')} @ {pair.get('annotated_at', 'N/A')[:16] if pair.get('annotated_at') else 'N/A'}")
    
    st.divider()
    
    # Event Display
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"🔵 Event {pair.get('event1_id', '1')}")
        
        e1_text = st.text_area(
            "Event 1 Text",
            value=pair.get("event1_text", ""),
            height=120,
            key=f"e1_text_{st.session_state.pair_index}"
        )
        
        e1_cue = st.checkbox(
            "🏷️ Contains causal cue/marker",
            value=bool(pair.get("cue1", False)),
            key=f"cue1_{st.session_state.pair_index}",
            help="Check if this event contains explicit causal markers (parce que, donc, à cause de, etc.)"
        )
    
    with col2:
        st.subheader(f"🟢 Event {pair.get('event2_id', '2')}")
        
        e2_text = st.text_area(
            "Event 2 Text",
            value=pair.get("event2_text", ""),
            height=120,
            key=f"e2_text_{st.session_state.pair_index}"
        )
        
        e2_cue = st.checkbox(
            "🏷️ Contains causal cue/marker",
            value=bool(pair.get("cue2", False)),
            key=f"cue2_{st.session_state.pair_index}",
            help="Check if this event contains explicit causal markers"
        )
    
    st.divider()
    
    # Causal relationship question
    st.subheader("❓ Is there a CAUSAL relationship?")
    st.caption("Does Event 1 cause or contribute to Event 2?")
    
    current_label = pair.get("label", 0)
    if current_label is None:
        current_label = 0
    
    label = st.radio(
        "Causal relationship",
        options=[0, 1],
        index=int(current_label),
        horizontal=True,
        format_func=lambda x: "✅ Yes (Causal)" if x == 1 else "❌ No (Not causal)",
        key=f"label_{st.session_state.pair_index}",
        label_visibility="collapsed"
    )
    
    # Optional confidence
    confidence = st.slider(
        "Confidence level",
        min_value=1,
        max_value=5,
        value=pair.get("confidence", 3),
        key=f"conf_{st.session_state.pair_index}",
        help="1 = very uncertain, 5 = very confident"
    )
    
    # Optional notes
    notes = st.text_input(
        "Notes (optional)",
        value=pair.get("notes", ""),
        key=f"notes_{st.session_state.pair_index}"
    )
    
    st.divider()
    
    # Navigation buttons
    col_prev, col_save, col_next = st.columns([1, 2, 1])
    
    with col_prev:
        if st.button("⬅️ Previous", disabled=st.session_state.pair_index == 0, key="prev_btn"):
            st.session_state.pair_index -= 1
            st.rerun()
    
    with col_save:
        if st.button("💾 Save & Next", type="primary", use_container_width=True, key="save_btn"):
            # Update pair data
            pair["event1_text"] = e1_text
            pair["event2_text"] = e2_text
            pair["cue1"] = int(e1_cue)
            pair["cue2"] = int(e2_cue)
            pair["label"] = int(label)
            pair["confidence"] = confidence
            pair["notes"] = notes
            pair["annotated_by"] = username
            pair["annotated_at"] = datetime.now().isoformat()
            
            pairs[st.session_state.pair_index] = pair
            
            # Save to file
            save_json(out_path, pairs)
            
            # Save progress
            annotated_count = sum(1 for p in pairs if p.get("annotated_by") == username)
            next_index = min(st.session_state.pair_index + 1, total_pairs - 1)
            save_progress(username, file_name, next_index, annotated_count)
            
            st.success("✅ Saved!")
            
            if st.session_state.pair_index < total_pairs - 1:
                st.session_state.pair_index += 1
            st.rerun()
    
    with col_next:
        if st.button("Skip ➡️", disabled=st.session_state.pair_index >= total_pairs - 1, key="skip_btn"):
            st.session_state.pair_index += 1
            st.rerun()
    
    # Download current progress
    st.markdown("---")
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            st.download_button(
                label="⬇️ Download current progress",
                data=f,
                file_name=file_name.replace(".json", f"_{username}_annotated.json"),
                mime="application/json",
                key="download_progress"
            )

# =========================
# View Annotations
# =========================

def view_annotations():
    """View and manage annotated files."""
    st.title("📂 Annotation Files")
    
    # List all annotated files
    if not os.path.exists(OUT_DIR):
        st.info("No output directory found.")
        return
    
    annotated_files = [f for f in os.listdir(OUT_DIR) if f.endswith("_annotated.json")]
    
    if not annotated_files:
        st.info("No annotated files yet.")
        return
    
    # File selector
    selected_file = st.selectbox("Select file to view", annotated_files)
    
    if selected_file:
        file_path = os.path.join(OUT_DIR, selected_file)
        data = load_json(file_path)
        
        # Handle both list and dict formats
        if isinstance(data, dict):
            data = data.get("pairs", [])
        
        if not data:
            st.warning("File is empty or has invalid format")
            return
        
        # Statistics
        stats = compute_annotation_stats(data)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Pairs", stats["total"])
        with col2:
            st.metric("Annotated", stats["annotated"])
        with col3:
            st.metric("Causal", stats["causal"])
        with col4:
            st.metric("Non-Causal", stats["non_causal"])
        
        st.divider()
        
        # Filter options
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filter_label = st.selectbox(
                "Filter by label",
                ["All", "Causal (1)", "Non-Causal (0)", "Unannotated"]
            )
        with col_f2:
            annotators = list(set(p.get("annotated_by", "") for p in data if p.get("annotated_by")))
            filter_annotator = st.selectbox(
                "Filter by annotator",
                ["All"] + annotators
            )
        with col_f3:
            filter_cue = st.selectbox(
                "Filter by cue",
                ["All", "Has cue", "No cue"]
            )
        
        # Apply filters
        filtered_data = data
        if filter_label == "Causal (1)":
            filtered_data = [p for p in filtered_data if p.get("label") == 1]
        elif filter_label == "Non-Causal (0)":
            filtered_data = [p for p in filtered_data if p.get("label") == 0]
        elif filter_label == "Unannotated":
            filtered_data = [p for p in filtered_data if not p.get("annotated_by")]
        
        if filter_annotator != "All":
            filtered_data = [p for p in filtered_data if p.get("annotated_by") == filter_annotator]
        
        if filter_cue == "Has cue":
            filtered_data = [p for p in filtered_data if p.get("cue1") or p.get("cue2")]
        elif filter_cue == "No cue":
            filtered_data = [p for p in filtered_data if not p.get("cue1") and not p.get("cue2")]
        
        st.caption(f"Showing {len(filtered_data)} pairs")
        
        # Display pairs
        for i, pair in enumerate(filtered_data[:100]):  # Limit to 100 for performance
            label_indicator = "✅" if pair.get("label") == 1 else "❌" if pair.get("label") == 0 else "❓"
            e1_preview = pair.get('event1_text', '')[:40] + "..." if len(pair.get('event1_text', '')) > 40 else pair.get('event1_text', '')
            e2_preview = pair.get('event2_text', '')[:40] + "..." if len(pair.get('event2_text', '')) > 40 else pair.get('event2_text', '')
            
            with st.expander(f"{label_indicator} {e1_preview} → {e2_preview}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Event 1:** {pair.get('event1_text', 'N/A')}")
                    st.caption(f"Cue: {'✅ Yes' if pair.get('cue1') else '❌ No'}")
                with col2:
                    st.markdown(f"**Event 2:** {pair.get('event2_text', 'N/A')}")
                    st.caption(f"Cue: {'✅ Yes' if pair.get('cue2') else '❌ No'}")
                
                label_text = "✅ Causal" if pair.get("label") == 1 else "❌ Non-Causal" if pair.get("label") == 0 else "❓ Not set"
                st.markdown(f"**Label:** {label_text}")
                
                meta_parts = []
                if pair.get("annotated_by"):
                    meta_parts.append(f"Annotated by: {pair.get('annotated_by')}")
                if pair.get("confidence"):
                    meta_parts.append(f"Confidence: {pair.get('confidence')}/5")
                if pair.get("child_id"):
                    meta_parts.append(f"Child: {pair.get('child_id')}")
                st.caption(" | ".join(meta_parts))
                
                if pair.get("notes"):
                    st.info(f"📝 Notes: {pair.get('notes')}")
        
        if len(filtered_data) > 100:
            st.warning(f"Showing first 100 of {len(filtered_data)} pairs. Download file for full data.")
        
        # Download
        st.divider()
        with open(file_path, "r", encoding="utf-8") as f:
            st.download_button(
                label="⬇️ Download this file",
                data=f,
                file_name=selected_file,
                mime="application/json",
                key="download_view"
            )

# =========================
# IAA Analysis
# =========================

def iaa_analysis():
    """Compute inter-annotator agreement."""
    st.title("📊 Inter-Annotator Agreement")
    
    if not os.path.exists(OUT_DIR):
        st.info("No output directory found.")
        return
    
    # Find all annotated files
    annotated_files = [f for f in os.listdir(OUT_DIR) if f.endswith("_annotated.json")]
    
    if len(annotated_files) < 2:
        st.info("Need at least 2 annotated files to compute IAA.")
        st.caption("Have multiple annotators annotate the same dataset.")
        return
    
    # Group by dataset
    datasets = {}
    for f in annotated_files:
        # Extract dataset name: {dataset}_{username}_annotated.json
        parts = f.replace("_annotated.json", "").rsplit("_", 1)
        if len(parts) == 2:
            dataset, annotator = parts
            if dataset not in datasets:
                datasets[dataset] = []
            datasets[dataset].append((annotator, f))
    
    # Show datasets with multiple annotators
    multi_annotator_datasets = {k: v for k, v in datasets.items() if len(v) >= 2}
    
    if not multi_annotator_datasets:
        st.warning("No datasets with multiple annotators found.")
        st.info("File naming pattern expected: `{dataset}_{username}_annotated.json`")
        
        st.markdown("**Available files:**")
        for f in annotated_files:
            st.code(f)
        return
    
    selected_dataset = st.selectbox(
        "Select dataset for IAA analysis",
        list(multi_annotator_datasets.keys())
    )
    
    if selected_dataset:
        annotators = multi_annotator_datasets[selected_dataset]
        st.success(f"**Annotators:** {', '.join([a[0] for a in annotators])}")
        
        # Load all annotations
        all_annotations = {}
        all_data = {}
        
        for annotator, filename in annotators:
            file_path = os.path.join(OUT_DIR, filename)
            data = load_json(file_path)
            if isinstance(data, dict):
                data = data.get("pairs", [])
            
            all_data[annotator] = data
            all_annotations[annotator] = {}
            
            for i, p in enumerate(data):
                # Create unique key for each pair
                key = (
                    p.get("event1_id", i),
                    p.get("event2_id", i),
                    p.get("event1_text", "")[:50]  # Include text snippet for uniqueness
                )
                if p.get("annotated_by") == annotator:  # Only count their own annotations
                    all_annotations[annotator][key] = {
                        "label": p.get("label"),
                        "cue1": p.get("cue1"),
                        "cue2": p.get("cue2"),
                        "confidence": p.get("confidence")
                    }
        
        st.divider()
        
        # Compute pairwise Cohen's kappa
        st.subheader("Cohen's κ (Pairwise Agreement)")
        
        annotator_names = list(all_annotations.keys())
        
        results = []
        
        for i, ann1 in enumerate(annotator_names):
            for ann2 in annotator_names[i+1:]:
                # Find common pairs (both annotated)
                common_keys = set(all_annotations[ann1].keys()) & set(all_annotations[ann2].keys())
                
                # Filter to pairs where both have labels
                valid_keys = [
                    k for k in common_keys 
                    if all_annotations[ann1][k]["label"] is not None 
                    and all_annotations[ann2][k]["label"] is not None
                ]
                
                if len(valid_keys) < 10:
                    st.warning(f"**{ann1}** vs **{ann2}**: Not enough common annotated pairs ({len(valid_keys)})")
                    continue
                
                labels1 = [all_annotations[ann1][k]["label"] for k in valid_keys]
                labels2 = [all_annotations[ann2][k]["label"] for k in valid_keys]
                
                # Compute agreement
                agree = sum(1 for l1, l2 in zip(labels1, labels2) if l1 == l2)
                po = agree / len(labels1)
                
                # Expected agreement (for binary labels)
                p1_pos = sum(labels1) / len(labels1) if labels1 else 0
                p2_pos = sum(labels2) / len(labels2) if labels2 else 0
                pe = p1_pos * p2_pos + (1 - p1_pos) * (1 - p2_pos)
                
                kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
                
                results.append({
                    "Annotator 1": ann1,
                    "Annotator 2": ann2,
                    "Common Pairs": len(valid_keys),
                    "Agreement": f"{po*100:.1f}%",
                    "Cohen's κ": round(kappa, 3)
                })
                
                # Display
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(f"{ann1} vs {ann2}", f"κ = {kappa:.3f}")
                with col2:
                    st.caption(f"Raw agreement: {po*100:.1f}%")
                with col3:
                    st.caption(f"Common pairs: {len(valid_keys)}")
                
                # Interpretation
                if kappa >= 0.8:
                    st.success("✅ Almost perfect agreement (κ ≥ 0.8)")
                elif kappa >= 0.6:
                    st.info("👍 Substantial agreement (0.6 ≤ κ < 0.8)")
                elif kappa >= 0.4:
                    st.warning("⚠️ Moderate agreement (0.4 ≤ κ < 0.6)")
                else:
                    st.error("❌ Fair or poor agreement (κ < 0.4)")
                
                st.markdown("---")
        
        # Summary table
        if results:
            st.subheader("Summary")
            st.dataframe(results)
        
        # Disagreement analysis
        st.divider()
        st.subheader("🔍 Disagreement Analysis")
        
        if len(annotator_names) >= 2:
            ann1, ann2 = annotator_names[0], annotator_names[1]
            
            common_keys = set(all_annotations[ann1].keys()) & set(all_annotations[ann2].keys())
            disagreements = []
            
            for key in common_keys:
                l1 = all_annotations[ann1][key]["label"]
                l2 = all_annotations[ann2][key]["label"]
                if l1 is not None and l2 is not None and l1 != l2:
                    # Find the original pair data
                    pair_data = None
                    for p in all_data[ann1]:
                        if p.get("event1_text", "")[:50] == key[2]:
                            pair_data = p
                            break
                    
                    if pair_data:
                        disagreements.append({
                            "event1": pair_data.get("event1_text", ""),
                            "event2": pair_data.get("event2_text", ""),
                            f"{ann1}_label": l1,
                            f"{ann2}_label": l2
                        })
            
            if disagreements:
                st.warning(f"Found {len(disagreements)} disagreements between {ann1} and {ann2}")
                
                for i, d in enumerate(disagreements[:20]):
                    with st.expander(f"Disagreement {i+1}: {d['event1'][:50]}..."):
                        st.markdown(f"**Event 1:** {d['event1']}")
                        st.markdown(f"**Event 2:** {d['event2']}")
                        col1, col2 = st.columns(2)
                        with col1:
                            label1 = "✅ Causal" if d[f"{ann1}_label"] == 1 else "❌ Non-Causal"
                            st.markdown(f"**{ann1}:** {label1}")
                        with col2:
                            label2 = "✅ Causal" if d[f"{ann2}_label"] == 1 else "❌ Non-Causal"
                            st.markdown(f"**{ann2}:** {label2}")
                
                if len(disagreements) > 20:
                    st.caption(f"Showing first 20 of {len(disagreements)} disagreements")
            else:
                st.success("No disagreements found!")

# =========================
# Main App
# =========================

def main():
    st.set_page_config(
        page_title="CausaFr Annotation",
        page_icon="🔗",
        layout="wide"
    )
    
    # Check authentication
    if "authenticated" not in st.session_state or not st.session_state.authenticated:
        login_page()
        return
    
    # Sidebar - User info and navigation
    st.sidebar.title(f"👤 {st.session_state.username}")
    if st.session_state.get('login_time'):
        st.sidebar.caption(f"Session: {st.session_state.login_time[:16]}")
    
    if st.sidebar.button("🚪 Logout"):
        logout()
    
    st.sidebar.divider()
    
    # Mode selection
    mode = st.sidebar.radio(
        "📌 Mode",
        ["Annotate Pairs", "View Annotations", "IAA Analysis"]
    )
    
    if mode == "Annotate Pairs":
        st.sidebar.divider()
        st.sidebar.subheader("📂 Dataset")
        
        # Check if data directory exists
        if not os.path.exists(DATA_DIR):
            st.error(f"Data directory not found: {DATA_DIR}/")
            st.info("Please create the directory and add JSON files.")
            return
        
        # List available datasets
        available_datasets = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]
        
        if not available_datasets:
            st.error(f"No JSON files found in {DATA_DIR}/")
            return
        
        file_name = st.sidebar.selectbox("Select dataset", available_datasets)
        
        # Show user's progress for this dataset
        progress = get_user_progress(st.session_state.username, file_name)
        if progress["current_index"] > 0:
            st.sidebar.success(f"📍 Resume from pair {progress['current_index'] + 1}")
            st.sidebar.caption(f"Last updated: {progress.get('last_updated', 'N/A')[:16] if progress.get('last_updated') else 'N/A'}")
        
        if st.sidebar.button("🔁 Restart from beginning"):
            st.session_state.pair_index = 0
            save_progress(st.session_state.username, file_name, 0, 0)
            st.rerun()
        
        annotate_pairs(st.session_state.username, file_name)
    
    elif mode == "View Annotations":
        view_annotations()
    
    elif mode == "IAA Analysis":
        iaa_analysis()

if __name__ == "__main__":
    main()
