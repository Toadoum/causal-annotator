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

    st.sidebar.info(f"📄 Total pairs: {len(pairs)}")

    if "pair_index" not in st.session_state:
        st.session_state.pair_index = 0

    total_pairs = len(pairs)

    if st.session_state.pair_index >= total_pairs:
        st.success("✅ All pairs annotated!")

        # Final download button
        with open(out_path, "r", encoding="utf-8") as f:
            st.download_button(
                label="⬇ Download FULL annotated file",
                data=f,
                file_name=file_name.replace(".json", "_annotated.json"),
                mime="application/json"
            )

        return

    pair = pairs[st.session_state.pair_index]

    st.title(f"📑 Pair {st.session_state.pair_index+1} / {total_pairs}")
    st.caption(f"👤 Child ID: {pair.get('child_id', 'N/A')}")

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
        format_func=lambda x: "✅ Yes" if x == 1 else "❌ No",
        key=f"label_{st.session_state.pair_index}"
    )

    # ====================
    # Save + Next
    # ====================

    colA, colB = st.columns([2,1])

    with colA:
        if st.button("➡️ Save & Next", key="save_next"):

            pair["event1_text"] = e1_text
            pair["event2_text"] = e2_text
            pair["cue1"] = int(e1_cue)
            pair["cue2"] = int(e2_cue)
            pair["label"] = int(label)

            pairs[st.session_state.pair_index] = pair

            # Save to server (temporary)
            save_json(out_path, pairs)

            st.success("✅ Pair saved!")

            st.session_state.pair_index += 1
            st.rerun()

    with colB:
        if os.path.exists(out_path):
            with open(out_path, "r", encoding="utf-8") as f:
                st.download_button(
                    label="⬇ Download progress",
                    data=f,
                    file_name=file_name.replace(".json", "_annotated.json"),
                    mime="application/json"
                )

# =========================
# Main
# =========================

def main():
    st.sidebar.title("📂 Choose Pair Dataset")

    file_name = st.sidebar.selectbox(
        "Select dataset",
        [
            "train_pairs_smart.json",
            "dev_pairs_smart.json",
            "eval_pairs_smart.json"
        ]
    )

    if st.sidebar.button("🔁 Restart annotation"):
        st.session_state.pair_index = 0
        st.rerun()

    annotate_pairs(file_name)

if __name__ == "__main__":
    main()
