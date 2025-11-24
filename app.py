# import streamlit as st
# import json
# import os

# DATA_DIR = "data"
# OUT_DIR = "output"
# USER_FILE = "users.json"

# if not os.path.exists(OUT_DIR):
#     os.makedirs(OUT_DIR)

# # ================================
# # Utils
# # ================================

# def load_json(path):
#     with open(path, "r", encoding="utf-8") as f:
#         return json.load(f)

# def save_json(path, data):
#     with open(path, "w", encoding="utf-8") as f:
#         json.dump(data, f, indent=2, ensure_ascii=False)

# def load_users():
#     if os.path.exists(USER_FILE):
#         with open(USER_FILE, "r") as f:
#             return json.load(f)
#     return {}

# def authenticate(username, password):
#     users = load_users()
#     return users.get(username) == password

# # ================================
# # Login
# # ================================

# def login():
#     st.title("🔐 Causal Narratives Annotator — Login")

#     user = st.text_input("Username")
#     pwd = st.text_input("Password", type="password")

#     if st.button("Login"):
#         if authenticate(user, pwd):
#             st.session_state["user"] = user
#             st.rerun()
#         else:
#             st.error("❌ Invalid credentials")

# # ================================
# # Annotation UI
# # ================================

# def annotate_file(file_name):
#     path = os.path.join(DATA_DIR, file_name)

#     st.header(f"📂 File: {file_name}")

#     data = load_json(path)

#     record_ids = list(range(len(data)))

#     idx = st.sidebar.selectbox("Select narrative", record_ids)

#     record = data[idx]

#     st.subheader("📜 Narrative")
#     st.info(record.get("narrative", ""))

#     # --- EVENTS ---
#     st.subheader("🧩 Events")

#     updated_events = []

#     for ev in record["events"]:
#         with st.expander(f"Event {ev['event_id']}"):
#             text = st.text_area(
#                 "Event text",
#                 value=ev["text"],
#                 key=f"text_{ev['event_id']}"
#             )

#             cue = st.checkbox(
#                 "Cue flag (causal/temporal)",
#                 value=bool(ev["cue_flag"]),
#                 key=f"cue_{ev['event_id']}"
#             )

#             updated_events.append({
#                 "event_id": ev["event_id"],
#                 "text": text,
#                 "pos": ev["pos"],
#                 "cue_flag": int(cue)
#             })

#     # --- PAIRS ---
#     st.subheader("🔗 Causal pairs annotation")

#     pair_keys = []

#     for i in range(len(updated_events)):
#         for j in range(i + 1, len(updated_events)):
#             e1 = updated_events[i]
#             e2 = updated_events[j]

#             with st.container():
#                 st.markdown(f"**E{e1['event_id']} → E{e2['event_id']}**")
#                 st.write(e1["text"])
#                 st.write(e2["text"])

#                 label = st.checkbox(
#                     f"Causal? ({e1['event_id']} → {e2['event_id']})",
#                     key=f"pair_{e1['event_id']}_{e2['event_id']}"
#                 )

#                 pair_keys.append({
#                     "event1_id": e1["event_id"],
#                     "event2_id": e2["event_id"],
#                     "label": int(label)
#                 })

#     # ================= SAVE ====================

#     if st.button("💾 Save annotations"):
#         data[idx]["events"] = updated_events
#         data[idx]["causal_pairs"] = pair_keys

#         out_file = os.path.join(OUT_DIR, file_name.replace(".json", "_annotated.json"))
#         save_json(out_file, data)

#         st.success(f"✅ Saved to {out_file}")

# # ================================
# # Main App
# # ================================

# def main():
#     if "user" not in st.session_state:
#         login()
#         return

#     st.sidebar.title("📊 Files")

#     file = st.sidebar.selectbox(
#         "Choose dataset",
#         ["train_real_fr.json", "dev_real_fr.json", "eval_real_fr.json"]
#     )

#     annotate_file(file)

# if __name__ == "__main__":
#     main()


import streamlit as st
import json
import os

DATA_DIR = "data"
OUT_DIR = "output"

os.makedirs(OUT_DIR, exist_ok=True)

# =========================
# Utils
# =========================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# =========================
# Pair Annotation
# =========================

def annotate_pairs(file_name):
    path = os.path.join(DATA_DIR, file_name)
    out_path = os.path.join(OUT_DIR, file_name.replace(".json", "_annotated.json"))

    pairs = load_json(path)

    if "pair_index" not in st.session_state:
        st.session_state.pair_index = 0

    total_pairs = len(pairs)

    if st.session_state.pair_index >= total_pairs:
        st.success("✅ All pairs annotated!")
        return

    pair = pairs[st.session_state.pair_index]

    st.title(f"📑 Pair {st.session_state.pair_index+1} / {total_pairs}")
    st.caption(f"Child: {pair['child_id']}")

    # ====================
    # Event Display
    # ====================

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"Event {pair['event1_id']}")

        e1_text = st.text_area(
            "Event 1 Text",
            value=pair["event1_text"],
            key=f"e1_text_{st.session_state.pair_index}"
        )

        e1_cue = st.checkbox(
            "Event 1 Cue Flag",
            value=bool(pair["cue1"]),
            key=f"cue1_{st.session_state.pair_index}"
        )

    with col2:
        st.subheader(f"Event {pair['event2_id']}")

        e2_text = st.text_area(
            "Event 2 Text",
            value=pair["event2_text"],
            key=f"e2_text_{st.session_state.pair_index}"
        )

        e2_cue = st.checkbox(
            "Event 2 Cue Flag",
            value=bool(pair["cue2"]),
            key=f"cue2_{st.session_state.pair_index}"
        )

    st.divider()

    label = st.radio(
        "Is there a CAUSAL relationship?",
        options=[0, 1],
        index=int(pair["label"]),
        horizontal=True,
        format_func=lambda x: "✅ Yes" if x==1 else "❌ No",
        key=f"label_{st.session_state.pair_index}"
    )

    # ====================
    # Save + Next
    # ====================

    if st.button("➡️ Save & Next"):
        pair["event1_text"] = e1_text
        pair["event2_text"] = e2_text
        pair["cue1"] = int(e1_cue)
        pair["cue2"] = int(e2_cue)
        pair["label"] = int(label)

        pairs[st.session_state.pair_index] = pair

        # Save progressively
        save_json(out_path, pairs)

        st.session_state.pair_index += 1
        st.rerun()

# =========================
# Main
# =========================

def main():
    st.sidebar.title("📂 Choose Dataset")

    file_name = st.sidebar.selectbox(
        "Select pair dataset",
        [
            "train_pairs_smart.json",
            "dev_pairs_smart.json",
            "eval_pairs_smart.json",
        ]
    )

    annotate_pairs(file_name)

if __name__ == "__main__":
    main()
