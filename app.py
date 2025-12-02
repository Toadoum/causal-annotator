# """
# CausaFr - Outil d'Annotation Professionnelle
# =============================================
# Interface moderne et professionnelle pour l'annotation de relations causales.

# Lancer avec: streamlit run causafr_annotation_app.py
# """

# import streamlit as st
# import json
# import os
# import hashlib
# from datetime import datetime

# # =========================
# # Configuration
# # =========================

# DATA_DIR = "data"
# OUT_DIR = "output"
# USERS_FILE = "users.json"
# PROGRESS_FILE = "annotation_progress.json"

# os.makedirs(OUT_DIR, exist_ok=True)

# # =========================
# # Styles CSS Professionnels
# # =========================

# def load_custom_css():
#     st.markdown("""
#     <style>
#     /* === IMPORTS === */
#     @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
#     /* === VARIABLES === */
#     :root {
#         --primary: #6366F1;
#         --primary-dark: #4F46E5;
#         --success: #10B981;
#         --warning: #F59E0B;
#         --error: #EF4444;
#         --bg-dark: #0F172A;
#         --bg-card: #FFFFFF;
#         --text-primary: #1E293B;
#         --text-muted: #64748B;
#         --border: #E2E8F0;
#         --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
#         --radius: 12px;
#     }
    
#     /* === GLOBAL === */
#     .main .block-container {
#         padding: 1.5rem 2rem 3rem 2rem;
#         max-width: 1200px;
#     }
    
#     h1, h2, h3, h4 { font-family: 'Inter', sans-serif !important; }
    
#     /* === HEADER === */
#     .main-header {
#         background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #A855F7 100%);
#         padding: 2rem 2.5rem;
#         border-radius: 20px;
#         margin-bottom: 2rem;
#         position: relative;
#         overflow: hidden;
#     }
    
#     .main-header::before {
#         content: '';
#         position: absolute;
#         top: 0; right: 0; bottom: 0; left: 0;
#         background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
#         opacity: 0.5;
#     }
    
#     .main-header h1 {
#         color: white !important;
#         font-weight: 700;
#         font-size: 1.75rem;
#         margin: 0;
#         position: relative;
#         z-index: 1;
#     }
    
#     .main-header p {
#         color: rgba(255,255,255,0.9);
#         margin: 0.5rem 0 0 0;
#         font-size: 0.95rem;
#         position: relative;
#         z-index: 1;
#     }
    
#     /* === CARDS === */
#     .card {
#         background: white;
#         border-radius: var(--radius);
#         padding: 1.5rem;
#         box-shadow: var(--shadow);
#         border: 1px solid var(--border);
#         transition: transform 0.2s, box-shadow 0.2s;
#     }
    
#     .card:hover {
#         transform: translateY(-2px);
#         box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
#     }
    
#     /* === EVENT BOXES === */
#     .event-box {
#         border-radius: var(--radius);
#         padding: 1rem 1.25rem;
#         margin-bottom: 0.75rem;
#         border-left: 4px solid;
#     }
    
#     .event-box.cause {
#         background: linear-gradient(to right, #EFF6FF, #F8FAFC);
#         border-color: #3B82F6;
#     }
    
#     .event-box.effect {
#         background: linear-gradient(to right, #ECFDF5, #F8FAFC);
#         border-color: #10B981;
#     }
    
#     .event-box .label {
#         font-size: 0.7rem;
#         font-weight: 700;
#         text-transform: uppercase;
#         letter-spacing: 1px;
#         margin-bottom: 0.25rem;
#     }
    
#     .event-box.cause .label { color: #1D4ED8; }
#     .event-box.effect .label { color: #059669; }
    
#     /* === QUESTION BOX === */
#     .question-box {
#         background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
#         border: 2px solid #C7D2FE;
#         border-radius: var(--radius);
#         padding: 1.5rem;
#         margin: 1.5rem 0;
#         text-align: center;
#     }
    
#     .question-box h3 {
#         color: #4338CA;
#         font-size: 1.15rem;
#         margin: 0 0 0.5rem 0;
#     }
    
#     .question-box p {
#         color: #6366F1;
#         margin: 0;
#         font-size: 0.9rem;
#     }
    
#     /* === METRICS === */
#     .metric-grid {
#         display: grid;
#         grid-template-columns: repeat(4, 1fr);
#         gap: 1rem;
#         margin: 1.5rem 0;
#     }
    
#     .metric-item {
#         background: white;
#         border-radius: var(--radius);
#         padding: 1.25rem;
#         text-align: center;
#         border: 1px solid var(--border);
#         transition: all 0.2s;
#     }
    
#     .metric-item:hover {
#         border-color: var(--primary);
#         box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
#     }
    
#     .metric-item .icon { font-size: 1.5rem; margin-bottom: 0.5rem; }
#     .metric-item .value { font-size: 1.75rem; font-weight: 700; color: var(--primary); }
#     .metric-item .label { font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem; }
    
#     /* === PROGRESS === */
#     .progress-wrapper {
#         background: var(--border);
#         border-radius: 999px;
#         height: 10px;
#         overflow: hidden;
#         margin: 1rem 0;
#     }
    
#     .progress-fill {
#         height: 100%;
#         border-radius: 999px;
#         background: linear-gradient(90deg, #6366F1, #A855F7);
#         transition: width 0.5s ease;
#     }
    
#     /* === BADGE === */
#     .badge {
#         display: inline-flex;
#         align-items: center;
#         gap: 0.35rem;
#         padding: 0.35rem 0.85rem;
#         border-radius: 999px;
#         font-size: 0.75rem;
#         font-weight: 600;
#     }
    
#     .badge.success { background: #D1FAE5; color: #065F46; }
#     .badge.warning { background: #FEF3C7; color: #92400E; }
#     .badge.info { background: #DBEAFE; color: #1E40AF; }
#     .badge.error { background: #FEE2E2; color: #991B1B; }
    
#     /* === KAPPA RESULT === */
#     .kappa-card {
#         background: white;
#         border-radius: var(--radius);
#         padding: 1.25rem 1.5rem;
#         margin-bottom: 1rem;
#         border-left: 4px solid;
#         display: flex;
#         justify-content: space-between;
#         align-items: center;
#     }
    
#     .kappa-card.excellent { border-color: #10B981; }
#     .kappa-card.good { border-color: #3B82F6; }
#     .kappa-card.moderate { border-color: #F59E0B; }
#     .kappa-card.poor { border-color: #EF4444; }
    
#     .kappa-value {
#         font-size: 1.75rem;
#         font-weight: 700;
#     }
    
#     .kappa-card.excellent .kappa-value { color: #10B981; }
#     .kappa-card.good .kappa-value { color: #3B82F6; }
#     .kappa-card.moderate .kappa-value { color: #F59E0B; }
#     .kappa-card.poor .kappa-value { color: #EF4444; }
    
#     /* === SIDEBAR === */
#     section[data-testid="stSidebar"] {
#         background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
#     }
    
#     section[data-testid="stSidebar"] * {
#         color: #CBD5E1 !important;
#     }
    
#     section[data-testid="stSidebar"] h1,
#     section[data-testid="stSidebar"] h2,
#     section[data-testid="stSidebar"] h3,
#     section[data-testid="stSidebar"] strong {
#         color: white !important;
#     }
    
#     section[data-testid="stSidebar"] .stButton button {
#         background: rgba(255,255,255,0.1);
#         border: 1px solid rgba(255,255,255,0.2);
#         color: white !important;
#     }
    
#     section[data-testid="stSidebar"] .stButton button:hover {
#         background: rgba(255,255,255,0.2);
#         border-color: rgba(255,255,255,0.3);
#     }
    
#     /* === BUTTONS === */
#     .stButton button {
#         font-family: 'Inter', sans-serif;
#         font-weight: 500;
#         border-radius: 8px;
#         transition: all 0.2s;
#     }
    
#     .stButton button:hover {
#         transform: translateY(-1px);
#     }
    
#     .stButton button[kind="primary"] {
#         background: linear-gradient(135deg, #6366F1, #8B5CF6);
#         border: none;
#     }
    
#     .stButton button[kind="primary"]:hover {
#         background: linear-gradient(135deg, #4F46E5, #7C3AED);
#         box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
#     }
    
#     /* === ALERT BOX === */
#     .alert {
#         padding: 1rem 1.25rem;
#         border-radius: 8px;
#         margin-bottom: 1rem;
#         border-left: 4px solid;
#     }
    
#     .alert.info { background: #EFF6FF; border-color: #3B82F6; color: #1E40AF; }
#     .alert.success { background: #ECFDF5; border-color: #10B981; color: #065F46; }
#     .alert.warning { background: #FFFBEB; border-color: #F59E0B; color: #92400E; }
#     .alert.error { background: #FEF2F2; border-color: #EF4444; color: #991B1B; }
    
#     /* === HIDE STREAMLIT === */
#     #MainMenu, footer, header { visibility: hidden; }
    
#     /* === EXPANDER === */
#     .streamlit-expanderHeader {
#         font-family: 'Inter', sans-serif;
#         font-weight: 500;
#         background: #F8FAFC;
#         border-radius: 8px;
#         border: 1px solid var(--border);
#     }
    
#     /* === LOGIN === */
#     .login-box {
#         max-width: 380px;
#         margin: 0 auto;
#         padding: 2.5rem;
#         background: white;
#         border-radius: 20px;
#         box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15);
#     }
    
#     .login-logo {
#         text-align: center;
#         margin-bottom: 2rem;
#     }
    
#     .login-logo .icon { font-size: 3.5rem; }
#     .login-logo h1 { font-size: 1.5rem; margin: 0.5rem 0 0 0; color: #1E293B; }
#     .login-logo p { color: #64748B; font-size: 0.9rem; margin: 0.25rem 0 0 0; }
#     </style>
#     """, unsafe_allow_html=True)

# # =========================
# # Composants UI
# # =========================

# def render_header(title, subtitle=None):
#     sub_html = f"<p>{subtitle}</p>" if subtitle else ""
#     st.markdown(f"""
#     <div class="main-header">
#         <h1>🔗 {title}</h1>
#         {sub_html}
#     </div>
#     """, unsafe_allow_html=True)

# def render_metrics(stats):
#     st.markdown(f"""
#     <div class="metric-grid">
#         <div class="metric-item">
#             <div class="icon">📊</div>
#             <div class="value">{stats['total']}</div>
#             <div class="label">Total</div>
#         </div>
#         <div class="metric-item">
#             <div class="icon">✏️</div>
#             <div class="value">{stats['annotated']}</div>
#             <div class="label">Annotées</div>
#         </div>
#         <div class="metric-item">
#             <div class="icon">✅</div>
#             <div class="value">{stats['causal']}</div>
#             <div class="label">Causales</div>
#         </div>
#         <div class="metric-item">
#             <div class="icon">❌</div>
#             <div class="value">{stats['non_causal']}</div>
#             <div class="label">Non causales</div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

# def render_progress(current, total):
#     pct = (current / total * 100) if total > 0 else 0
#     st.markdown(f"""
#     <div class="progress-wrapper">
#         <div class="progress-fill" style="width: {pct}%"></div>
#     </div>
#     <p style="text-align: center; color: #64748B; font-size: 0.85rem;">
#         <strong>{current}</strong> sur {total} ({pct:.1f}%)
#     </p>
#     """, unsafe_allow_html=True)

# def render_kappa(ann1, ann2, kappa, agreement, count):
#     if kappa >= 0.8:
#         level, label = "excellent", "Excellent"
#     elif kappa >= 0.6:
#         level, label = "good", "Bon"
#     elif kappa >= 0.4:
#         level, label = "moderate", "Modéré"
#     else:
#         level, label = "poor", "Faible"
    
#     st.markdown(f"""
#     <div class="kappa-card {level}">
#         <div>
#             <strong style="font-size: 1.1rem;">{ann1} ↔ {ann2}</strong>
#             <br><span style="color: #64748B; font-size: 0.85rem;">{count} paires • Accord : {agreement:.1f}%</span>
#         </div>
#         <div style="text-align: right;">
#             <div class="kappa-value">κ = {kappa:.3f}</div>
#             <span class="badge {level}">{label}</span>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

# # =========================
# # Utilitaires
# # =========================

# def load_json(path):
#     if not os.path.exists(path):
#         return {}
#     with open(path, "r", encoding="utf-8") as f:
#         return json.load(f)

# def save_json(path, data):
#     with open(path, "w", encoding="utf-8") as f:
#         json.dump(data, f, indent=2, ensure_ascii=False)

# def hash_password(password):
#     return hashlib.sha256(password.encode()).hexdigest()

# def load_users():
#     return load_json(USERS_FILE) if os.path.exists(USERS_FILE) else {}

# def verify_user(username, password):
#     users = load_users()
#     if username in users:
#         stored = users[username]
#         return stored == (hash_password(password) if len(stored) == 64 else password)
#     return False

# def load_progress():
#     return load_json(PROGRESS_FILE) if os.path.exists(PROGRESS_FILE) else {}

# def save_progress(username, dataset, index, total):
#     progress = load_progress()
#     if username not in progress:
#         progress[username] = {}
#     progress[username][dataset] = {
#         "current_index": index,
#         "total_annotated": total,
#         "last_updated": datetime.now().isoformat()
#     }
#     save_json(PROGRESS_FILE, progress)

# def get_user_progress(username, dataset):
#     progress = load_progress()
#     return progress.get(username, {}).get(dataset, {"current_index": 0, "total_annotated": 0})

# def get_annotated_path(username, dataset):
#     return os.path.join(OUT_DIR, f"{dataset.replace('.json', '')}_{username}_annotated.json")

# def compute_stats(pairs):
#     total = len(pairs)
#     if total == 0:
#         return {"total": 0, "annotated": 0, "causal": 0, "non_causal": 0, "causal_rate": 0}
#     return {
#         "total": total,
#         "annotated": sum(1 for p in pairs if p.get("annotated_by")),
#         "causal": sum(1 for p in pairs if p.get("label") == 1),
#         "non_causal": sum(1 for p in pairs if p.get("label") == 0),
#         "causal_rate": sum(1 for p in pairs if p.get("label") == 1) / total * 100
#     }

# # =========================
# # Pages
# # =========================

# def login_page():
#     load_custom_css()
    
#     st.markdown("<div style='height: 3rem'></div>", unsafe_allow_html=True)
    
#     col1, col2, col3 = st.columns([1, 1.2, 1])
#     with col2:
#         st.markdown("""
#         <div class="login-box">
#             <div class="login-logo">
#                 <div class="icon">🔗</div>
#                 <h1>CausaFr</h1>
#                 <p>Annotation de Relations Causales</p>
#             </div>
#         </div>
#         """, unsafe_allow_html=True)
        
#         with st.form("login"):
#             username = st.text_input("👤 Identifiant", placeholder="Votre nom d'utilisateur")
#             password = st.text_input("🔒 Mot de passe", type="password", placeholder="Votre mot de passe")
            
#             st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
            
#             if st.form_submit_button("Se connecter", use_container_width=True, type="primary"):
#                 if verify_user(username, password):
#                     st.session_state.authenticated = True
#                     st.session_state.username = username
#                     st.session_state.login_time = datetime.now().isoformat()
#                     st.rerun()
#                 else:
#                     st.error("❌ Identifiants incorrects")

# def logout():
#     for key in ['authenticated', 'username', 'login_time', 'pair_index', 'current_dataset']:
#         st.session_state.pop(key, None)
#     st.rerun()

# def annotate_page(username, file_name):
#     path = os.path.join(DATA_DIR, file_name)
#     out_path = get_annotated_path(username, file_name)
    
#     if not os.path.exists(path):
#         st.error(f"❌ Fichier introuvable : {path}")
#         return
    
#     # Load data
#     pairs = load_json(out_path) if os.path.exists(out_path) else load_json(path)
#     if isinstance(pairs, dict):
#         pairs = pairs.get("pairs", [])
    
#     if not pairs:
#         st.error("❌ Aucune paire trouvée")
#         return
    
#     # Progress management
#     user_prog = get_user_progress(username, file_name)
#     if st.session_state.get("current_dataset") != file_name:
#         st.session_state.current_dataset = file_name
#         st.session_state.pair_index = user_prog["current_index"]
    
#     if "pair_index" not in st.session_state:
#         st.session_state.pair_index = user_prog["current_index"]
    
#     total = len(pairs)
#     st.session_state.pair_index = max(0, min(st.session_state.pair_index, total - 1))
#     idx = st.session_state.pair_index
#     pair = pairs[idx]
#     stats = compute_stats(pairs)
    
#     # Sidebar
#     with st.sidebar:
#         st.markdown("### 📊 Statistiques")
#         col1, col2 = st.columns(2)
#         with col1:
#             st.metric("Total", stats["total"])
#             st.metric("Causales", stats["causal"])
#         with col2:
#             st.metric("Annotées", stats["annotated"])
#             st.metric("Taux", f"{stats['causal_rate']:.0f}%")
        
#         st.markdown("---")
#         st.markdown("### 📍 Progression")
#         render_progress(idx + 1, total)
        
#         st.markdown("---")
#         st.markdown("### 🧭 Navigation")
        
#         jump = st.number_input("Aller à", 1, total, idx + 1, label_visibility="collapsed")
#         col1, col2 = st.columns(2)
#         with col1:
#             if st.button("📍 Aller", use_container_width=True):
#                 st.session_state.pair_index = jump - 1
#                 st.rerun()
#         with col2:
#             if st.button("⏭️ Non annotée", use_container_width=True):
#                 for i, p in enumerate(pairs):
#                     if not p.get("annotated_by"):
#                         st.session_state.pair_index = i
#                         st.rerun()
#                         break
    
#     # Main content
#     render_header(f"Paire {idx + 1} / {total}", f"📄 {file_name} • 👤 {pair.get('child_id', 'N/A')}")
    
#     if pair.get("annotated_by"):
#         st.markdown(f"""
#         <div class="alert warning">
#             ✏️ <strong>Déjà annotée</strong> par {pair['annotated_by']} — {pair.get('annotated_at', '')[:16]}
#         </div>
#         """, unsafe_allow_html=True)
    
#     # Events
#     col1, col2 = st.columns(2)
    
#     with col1:
#         st.markdown("""
#         <div class="event-box cause">
#             <div class="label">🔵 Événement 1 — Cause potentielle</div>
#         </div>
#         """, unsafe_allow_html=True)
#         e1_text = st.text_area("E1", pair.get("event1_text", ""), height=130, key=f"e1_{idx}", label_visibility="collapsed")
#         e1_cue = st.checkbox("🏷️ Marqueur causal explicite", pair.get("cue1", False), key=f"c1_{idx}")
    
#     with col2:
#         st.markdown("""
#         <div class="event-box effect">
#             <div class="label">🟢 Événement 2 — Effet potentiel</div>
#         </div>
#         """, unsafe_allow_html=True)
#         e2_text = st.text_area("E2", pair.get("event2_text", ""), height=130, key=f"e2_{idx}", label_visibility="collapsed")
#         e2_cue = st.checkbox("🏷️ Marqueur causal explicite", pair.get("cue2", False), key=f"c2_{idx}")
    
#     # Question
#     st.markdown("""
#     <div class="question-box">
#         <h3>❓ Existe-t-il une relation CAUSALE ?</h3>
#         <p>L'événement 1 cause-t-il ou contribue-t-il à l'événement 2 ?</p>
#     </div>
#     """, unsafe_allow_html=True)
    
#     col1, col2 = st.columns(2)
#     with col1:
#         current = pair.get("label", 0) or 0
#         label = st.radio("Label", [1, 0], index=0 if current == 1 else 1,
#                         format_func=lambda x: "✅ OUI — Causal" if x == 1 else "❌ NON — Pas causal",
#                         key=f"lbl_{idx}", horizontal=False, label_visibility="collapsed")
    
#     with col2:
#         confidence = st.slider("🎯 Confiance", 1, 5, pair.get("confidence", 3), key=f"conf_{idx}")
#         notes = st.text_input("📝 Notes", pair.get("notes", ""), key=f"note_{idx}", placeholder="Optionnel...")
    
#     st.markdown("---")
    
#     # Actions
#     col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
    
#     with col1:
#         if st.button("⬅️", disabled=idx == 0, use_container_width=True):
#             st.session_state.pair_index -= 1
#             st.rerun()
    
#     with col2:
#         if st.button("💾 Enregistrer & Suivant", type="primary", use_container_width=True):
#             pair.update({
#                 "event1_text": e1_text, "event2_text": e2_text,
#                 "cue1": int(e1_cue), "cue2": int(e2_cue),
#                 "label": int(label), "confidence": confidence, "notes": notes,
#                 "annotated_by": username, "annotated_at": datetime.now().isoformat()
#             })
#             pairs[idx] = pair
#             save_json(out_path, pairs)
#             count = sum(1 for p in pairs if p.get("annotated_by") == username)
#             save_progress(username, file_name, min(idx + 1, total - 1), count)
#             if idx < total - 1:
#                 st.session_state.pair_index += 1
#             st.rerun()
    
#     with col3:
#         if st.button("⏭️ Passer", disabled=idx >= total - 1, use_container_width=True):
#             st.session_state.pair_index += 1
#             st.rerun()
    
#     with col4:
#         if st.button("➡️", disabled=idx >= total - 1, use_container_width=True):
#             st.session_state.pair_index += 1
#             st.rerun()
    
#     # Download
#     if os.path.exists(out_path):
#         st.markdown("---")
#         with open(out_path, "r", encoding="utf-8") as f:
#             st.download_button("⬇️ Télécharger mes annotations", f,
#                              file_name=f"{file_name.replace('.json', '')}_{username}.json",
#                              mime="application/json", use_container_width=True)

# def view_page():
#     render_header("Fichiers d'Annotation", "Visualisez et téléchargez les annotations")
    
#     if not os.path.exists(OUT_DIR):
#         st.info("📂 Aucun fichier trouvé")
#         return
    
#     files = [f for f in os.listdir(OUT_DIR) if f.endswith("_annotated.json")]
#     if not files:
#         st.info("📂 Aucun fichier annoté")
#         return
    
#     selected = st.selectbox("📁 Fichier", files)
#     if not selected:
#         return
    
#     data = load_json(os.path.join(OUT_DIR, selected))
#     if isinstance(data, dict):
#         data = data.get("pairs", [])
    
#     stats = compute_stats(data)
#     render_metrics(stats)
    
#     st.markdown("---")
    
#     # Filters
#     col1, col2, col3 = st.columns(3)
#     with col1:
#         f_label = st.selectbox("🏷️ Label", ["Tous", "Causal", "Non causal", "Non annoté"])
#     with col2:
#         annotators = list({p.get("annotated_by") for p in data if p.get("annotated_by")})
#         f_ann = st.selectbox("👤 Annotateur", ["Tous"] + annotators)
#     with col3:
#         f_cue = st.selectbox("🔍 Marqueur", ["Tous", "Avec", "Sans"])
    
#     filtered = data
#     if f_label == "Causal":
#         filtered = [p for p in filtered if p.get("label") == 1]
#     elif f_label == "Non causal":
#         filtered = [p for p in filtered if p.get("label") == 0]
#     elif f_label == "Non annoté":
#         filtered = [p for p in filtered if not p.get("annotated_by")]
    
#     if f_ann != "Tous":
#         filtered = [p for p in filtered if p.get("annotated_by") == f_ann]
    
#     if f_cue == "Avec":
#         filtered = [p for p in filtered if p.get("cue1") or p.get("cue2")]
#     elif f_cue == "Sans":
#         filtered = [p for p in filtered if not p.get("cue1") and not p.get("cue2")]
    
#     st.caption(f"📋 {len(filtered)} paires")
    
#     for i, p in enumerate(filtered[:50]):
#         icon = "✅" if p.get("label") == 1 else "❌" if p.get("label") == 0 else "❓"
#         e1 = (p.get("event1_text", "")[:45] + "...") if len(p.get("event1_text", "")) > 45 else p.get("event1_text", "")
#         e2 = (p.get("event2_text", "")[:45] + "...") if len(p.get("event2_text", "")) > 45 else p.get("event2_text", "")
        
#         with st.expander(f"{icon} {e1} → {e2}"):
#             col1, col2 = st.columns(2)
#             with col1:
#                 st.markdown(f"**🔵 E1:** {p.get('event1_text', 'N/A')}")
#             with col2:
#                 st.markdown(f"**🟢 E2:** {p.get('event2_text', 'N/A')}")
#             if p.get("annotated_by"):
#                 st.caption(f"👤 {p['annotated_by']} • 🎯 {p.get('confidence', '?')}/5")
    
#     if len(filtered) > 50:
#         st.warning("⚠️ 50 premières paires affichées")
    
#     st.markdown("---")
#     with open(os.path.join(OUT_DIR, selected), "r", encoding="utf-8") as f:
#         st.download_button("⬇️ Télécharger", f, selected, "application/json", use_container_width=True)

# def iaa_page():
#     render_header("Accord Inter-Annotateurs", "Analyse de la cohérence des annotations")
    
#     if not os.path.exists(OUT_DIR):
#         st.info("📂 Aucun fichier")
#         return
    
#     files = [f for f in os.listdir(OUT_DIR) if f.endswith("_annotated.json")]
#     if len(files) < 2:
#         st.info("ℹ️ 2 fichiers minimum requis")
#         return
    
#     # Group by dataset
#     datasets = {}
#     for f in files:
#         parts = f.replace("_annotated.json", "").rsplit("_", 1)
#         if len(parts) == 2:
#             ds, ann = parts
#             datasets.setdefault(ds, []).append((ann, f))
    
#     multi = {k: v for k, v in datasets.items() if len(v) >= 2}
#     if not multi:
#         st.warning("⚠️ Aucun jeu avec plusieurs annotateurs")
#         return
    
#     selected = st.selectbox("📁 Jeu de données", list(multi.keys()))
#     if not selected:
#         return
    
#     annotators = multi[selected]
#     st.success(f"👥 Annotateurs : {', '.join(a[0] for a in annotators)}")
    
#     # Load annotations
#     all_ann = {}
#     all_data = {}
#     for ann, fname in annotators:
#         data = load_json(os.path.join(OUT_DIR, fname))
#         if isinstance(data, dict):
#             data = data.get("pairs", [])
#         all_data[ann] = data
#         all_ann[ann] = {
#             (p.get("event1_id", i), p.get("event2_id", i), p.get("event1_text", "")[:40]): p.get("label")
#             for i, p in enumerate(data) if p.get("annotated_by") == ann
#         }
    
#     st.markdown("---")
#     st.markdown("### 📊 Kappa de Cohen")
    
#     names = list(all_ann.keys())
#     for i, a1 in enumerate(names):
#         for a2 in names[i+1:]:
#             common = set(all_ann[a1].keys()) & set(all_ann[a2].keys())
#             valid = [k for k in common if all_ann[a1][k] is not None and all_ann[a2][k] is not None]
            
#             if len(valid) < 10:
#                 st.warning(f"⚠️ {a1} ↔ {a2} : {len(valid)} paires (min 10)")
#                 continue
            
#             l1 = [all_ann[a1][k] for k in valid]
#             l2 = [all_ann[a2][k] for k in valid]
            
#             po = sum(x == y for x, y in zip(l1, l2)) / len(l1)
#             p1 = sum(l1) / len(l1)
#             p2 = sum(l2) / len(l2)
#             pe = p1 * p2 + (1 - p1) * (1 - p2)
#             kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
            
#             render_kappa(a1, a2, kappa, po * 100, len(valid))
    
#     # Disagreements
#     st.markdown("---")
#     st.markdown("### 🔍 Désaccords")
    
#     if len(names) >= 2:
#         a1, a2 = names[0], names[1]
#         common = set(all_ann[a1].keys()) & set(all_ann[a2].keys())
        
#         disagree = []
#         for k in common:
#             if all_ann[a1][k] is not None and all_ann[a2][k] is not None and all_ann[a1][k] != all_ann[a2][k]:
#                 for p in all_data[a1]:
#                     if p.get("event1_text", "")[:40] == k[2]:
#                         disagree.append((p, all_ann[a1][k], all_ann[a2][k]))
#                         break
        
#         if disagree:
#             st.warning(f"⚠️ {len(disagree)} désaccords entre {a1} et {a2}")
#             for i, (p, l1, l2) in enumerate(disagree[:10]):
#                 with st.expander(f"Désaccord {i+1}"):
#                     st.markdown(f"**E1:** {p.get('event1_text', '')}")
#                     st.markdown(f"**E2:** {p.get('event2_text', '')}")
#                     col1, col2 = st.columns(2)
#                     with col1:
#                         st.markdown(f"**{a1}:** {'✅' if l1 == 1 else '❌'}")
#                     with col2:
#                         st.markdown(f"**{a2}:** {'✅' if l2 == 1 else '❌'}")
#         else:
#             st.success("✅ Aucun désaccord !")

# # =========================
# # Main
# # =========================

# def main():
#     st.set_page_config("CausaFr", "🔗", "wide", "expanded")
#     load_custom_css()
    
#     if not st.session_state.get("authenticated"):
#         login_page()
#         return
    
#     # Sidebar
#     with st.sidebar:
#         st.markdown(f"""
#         <div style="text-align: center; padding: 1.5rem 0;">
#             <div style="font-size: 2.5rem;">🔗</div>
#             <h2 style="margin: 0.5rem 0 0 0;">CausaFr</h2>
#         </div>
#         """, unsafe_allow_html=True)
        
#         st.markdown("---")
        
#         st.markdown(f"""
#         <div style="background: rgba(255,255,255,0.08); padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 1rem;">
#             👤 <strong>{st.session_state.username}</strong>
#         </div>
#         """, unsafe_allow_html=True)
        
#         if st.button("🚪 Déconnexion", use_container_width=True):
#             logout()
        
#         st.markdown("---")
        
#         mode = st.radio("Mode", ["✏️ Annoter", "📂 Voir", "📊 IAA"], label_visibility="collapsed")
    
#     # Content
#     if mode == "✏️ Annoter":
#         with st.sidebar:
#             st.markdown("### 📁 Données")
#             if not os.path.exists(DATA_DIR):
#                 st.error("Dossier data/ manquant")
#                 return
            
#             datasets = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]
#             if not datasets:
#                 st.error("Aucun JSON")
#                 return
            
#             file = st.selectbox("Fichier", datasets, label_visibility="collapsed")
#             prog = get_user_progress(st.session_state.username, file)
#             if prog["current_index"] > 0:
#                 st.info(f"📍 Paire {prog['current_index'] + 1}")
        
#         annotate_page(st.session_state.username, file)
    
#     elif mode == "📂 Voir":
#         view_page()
    
#     elif mode == "📊 IAA":
#         iaa_page()

# if __name__ == "__main__":
#     main()





"""
CausaFr - Outil d'Annotation Professionnelle
=============================================
Interface moderne et professionnelle pour l'annotation de relations causales.

Lancer avec: streamlit run causafr_annotation_app.py
"""

import streamlit as st
import json
import os
import hashlib
from datetime import datetime

# =========================
# Configuration
# =========================

DATA_DIR = "data"
OUT_DIR = "output"
USERS_FILE = "users.json"
PROGRESS_FILE = "annotation_progress.json"

os.makedirs(OUT_DIR, exist_ok=True)

# =========================
# Styles CSS Professionnels
# =========================

def load_custom_css():
    st.markdown("""
    <style>
    /* === IMPORTS === */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* === VARIABLES === */
    :root {
        --primary: #6366F1;
        --primary-dark: #4F46E5;
        --success: #10B981;
        --warning: #F59E0B;
        --error: #EF4444;
        --bg-dark: #0F172A;
        --bg-card: #FFFFFF;
        --text-primary: #1E293B;
        --text-muted: #64748B;
        --border: #E2E8F0;
        --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --radius: 12px;
    }
    
    /* === GLOBAL === */
    .main .block-container {
        padding: 1.5rem 2rem 3rem 2rem;
        max-width: 1200px;
    }
    
    h1, h2, h3, h4 { font-family: 'Inter', sans-serif !important; }
    
    /* === HEADER === */
    .main-header {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #A855F7 100%);
        padding: 2rem 2.5rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0; right: 0; bottom: 0; left: 0;
        background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        opacity: 0.5;
    }
    
    .main-header h1 {
        color: white !important;
        font-weight: 700;
        font-size: 1.75rem;
        margin: 0;
        position: relative;
        z-index: 1;
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9);
        margin: 0.5rem 0 0 0;
        font-size: 0.95rem;
        position: relative;
        z-index: 1;
    }
    
    /* === CARDS === */
    .card {
        background: white;
        border-radius: var(--radius);
        padding: 1.5rem;
        box-shadow: var(--shadow);
        border: 1px solid var(--border);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
    }
    
    /* === EVENT BOXES === */
    .event-box {
        border-radius: var(--radius);
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        border-left: 4px solid;
    }
    
    .event-box.cause {
        background: linear-gradient(to right, #EFF6FF, #F8FAFC);
        border-color: #3B82F6;
    }
    
    .event-box.effect {
        background: linear-gradient(to right, #ECFDF5, #F8FAFC);
        border-color: #10B981;
    }
    
    .event-box .label {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.25rem;
    }
    
    .event-box.cause .label { color: #1D4ED8; }
    .event-box.effect .label { color: #059669; }
    
    /* === QUESTION BOX === */
    .question-box {
        background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
        border: 2px solid #C7D2FE;
        border-radius: var(--radius);
        padding: 1.5rem;
        margin: 1.5rem 0;
        text-align: center;
    }
    
    .question-box h3 {
        color: #4338CA;
        font-size: 1.15rem;
        margin: 0 0 0.5rem 0;
    }
    
    .question-box p {
        color: #6366F1;
        margin: 0;
        font-size: 0.9rem;
    }
    
    /* === METRICS === */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    .metric-item {
        background: white;
        border-radius: var(--radius);
        padding: 1.25rem;
        text-align: center;
        border: 1px solid var(--border);
        transition: all 0.2s;
    }
    
    .metric-item:hover {
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }
    
    .metric-item .icon { font-size: 1.5rem; margin-bottom: 0.5rem; }
    .metric-item .value { font-size: 1.75rem; font-weight: 700; color: var(--primary); }
    .metric-item .label { font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem; }
    
    /* === PROGRESS === */
    .progress-wrapper {
        background: var(--border);
        border-radius: 999px;
        height: 10px;
        overflow: hidden;
        margin: 1rem 0;
    }
    
    .progress-fill {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #6366F1, #A855F7);
        transition: width 0.5s ease;
    }
    
    /* === BADGE === */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.35rem 0.85rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .badge.success { background: #D1FAE5; color: #065F46; }
    .badge.warning { background: #FEF3C7; color: #92400E; }
    .badge.info { background: #DBEAFE; color: #1E40AF; }
    .badge.error { background: #FEE2E2; color: #991B1B; }
    
    /* === KAPPA RESULT === */
    .kappa-card {
        background: white;
        border-radius: var(--radius);
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .kappa-card.excellent { border-color: #10B981; }
    .kappa-card.good { border-color: #3B82F6; }
    .kappa-card.moderate { border-color: #F59E0B; }
    .kappa-card.poor { border-color: #EF4444; }
    
    .kappa-value {
        font-size: 1.75rem;
        font-weight: 700;
    }
    
    .kappa-card.excellent .kappa-value { color: #10B981; }
    .kappa-card.good .kappa-value { color: #3B82F6; }
    .kappa-card.moderate .kappa-value { color: #F59E0B; }
    .kappa-card.poor .kappa-value { color: #EF4444; }
    
    /* === SIDEBAR === */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
    }
    
    section[data-testid="stSidebar"] * {
        color: #CBD5E1 !important;
    }
    
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] strong {
        color: white !important;
    }
    
    section[data-testid="stSidebar"] .stButton button {
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        color: white !important;
    }
    
    section[data-testid="stSidebar"] .stButton button:hover {
        background: rgba(255,255,255,0.2);
        border-color: rgba(255,255,255,0.3);
    }
    
    /* === BUTTONS === */
    .stButton button {
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        border-radius: 8px;
        transition: all 0.2s;
    }
    
    .stButton button:hover {
        transform: translateY(-1px);
    }
    
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #6366F1, #8B5CF6);
        border: none;
    }
    
    .stButton button[kind="primary"]:hover {
        background: linear-gradient(135deg, #4F46E5, #7C3AED);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
    }
    
    /* === ALERT BOX === */
    .alert {
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid;
    }
    
    .alert.info { background: #EFF6FF; border-color: #3B82F6; color: #1E40AF; }
    .alert.success { background: #ECFDF5; border-color: #10B981; color: #065F46; }
    .alert.warning { background: #FFFBEB; border-color: #F59E0B; color: #92400E; }
    .alert.error { background: #FEF2F2; border-color: #EF4444; color: #991B1B; }
    
    /* === HIDE STREAMLIT === */
    #MainMenu, footer, header { visibility: hidden; }
    
    /* === EXPANDER === */
    .streamlit-expanderHeader {
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        background: #F8FAFC;
        border-radius: 8px;
        border: 1px solid var(--border);
    }
    
    /* === LOGIN === */
    .login-box {
        max-width: 380px;
        margin: 0 auto;
        padding: 2.5rem;
        background: white;
        border-radius: 20px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15);
    }
    
    .login-logo {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .login-logo .icon { font-size: 3.5rem; }
    .login-logo h1 { font-size: 1.5rem; margin: 0.5rem 0 0 0; color: #1E293B; }
    .login-logo p { color: #64748B; font-size: 0.9rem; margin: 0.25rem 0 0 0; }
    </style>
    """, unsafe_allow_html=True)

# =========================
# Composants UI
# =========================

def render_header(title, subtitle=None):
    sub_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f"""
    <div class="main-header">
        <h1>🔗 {title}</h1>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)

def render_metrics(stats):
    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-item">
            <div class="icon">📊</div>
            <div class="value">{stats['total']}</div>
            <div class="label">Total</div>
        </div>
        <div class="metric-item">
            <div class="icon">✏️</div>
            <div class="value">{stats['annotated']}</div>
            <div class="label">Annotées</div>
        </div>
        <div class="metric-item">
            <div class="icon">✅</div>
            <div class="value">{stats['causal']}</div>
            <div class="label">Causales</div>
        </div>
        <div class="metric-item">
            <div class="icon">❌</div>
            <div class="value">{stats['non_causal']}</div>
            <div class="label">Non causales</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_progress(current, total):
    pct = (current / total * 100) if total > 0 else 0
    st.markdown(f"""
    <div class="progress-wrapper">
        <div class="progress-fill" style="width: {pct}%"></div>
    </div>
    <p style="text-align: center; color: #64748B; font-size: 0.85rem;">
        <strong>{current}</strong> sur {total} ({pct:.1f}%)
    </p>
    """, unsafe_allow_html=True)

def render_kappa(ann1, ann2, kappa, agreement, count):
    if kappa >= 0.8:
        level, label = "excellent", "Excellent"
    elif kappa >= 0.6:
        level, label = "good", "Bon"
    elif kappa >= 0.4:
        level, label = "moderate", "Modéré"
    else:
        level, label = "poor", "Faible"
    
    st.markdown(f"""
    <div class="kappa-card {level}">
        <div>
            <strong style="font-size: 1.1rem;">{ann1} ↔ {ann2}</strong>
            <br><span style="color: #64748B; font-size: 0.85rem;">{count} paires • Accord : {agreement:.1f}%</span>
        </div>
        <div style="text-align: right;">
            <div class="kappa-value">κ = {kappa:.3f}</div>
            <span class="badge {level}">{label}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# Utilitaires
# =========================

def load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Corrupted JSON
        return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    return load_json(USERS_FILE) if os.path.exists(USERS_FILE) else {}

def verify_user(username, password):
    users = load_users()
    if username in users:
        stored = users[username]
        # allow either hashed or plain (for backward compatibility)
        if len(stored) == 64:
            return stored == hash_password(password)
        return stored == password
    return False

def load_progress():
    return load_json(PROGRESS_FILE) if os.path.exists(PROGRESS_FILE) else {}

def save_progress(username, dataset, index, total):
    progress = load_progress()
    if username not in progress:
        progress[username] = {}
    progress[username][dataset] = {
        "current_index": index,
        "total_annotated": total,
        "last_updated": datetime.now().isoformat()
    }
    save_json(PROGRESS_FILE, progress)

def get_user_progress(username, dataset):
    progress = load_progress()
    return progress.get(username, {}).get(dataset, {"current_index": 0, "total_annotated": 0})

def get_annotated_path(username, dataset):
    return os.path.join(OUT_DIR, f"{dataset.replace('.json', '')}_{username}_annotated.json")

def compute_stats(pairs):
    total = len(pairs)
    if total == 0:
        return {"total": 0, "annotated": 0, "causal": 0, "non_causal": 0, "causal_rate": 0}
    causal = sum(1 for p in pairs if p.get("label") == 1)
    non_causal = sum(1 for p in pairs if p.get("label") == 0)
    annotated = sum(1 for p in pairs if p.get("annotated_by"))
    return {
        "total": total,
        "annotated": annotated,
        "causal": causal,
        "non_causal": non_causal,
        "causal_rate": causal / total * 100 if total > 0 else 0
    }

# ---------- NEW: safe loader for pairs ----------

def load_pairs_from_any(data_obj):
    """
    Accept both:
      - list of pairs (preferred, Format A)
      - dict with "pairs": [...]
    Always return a list (possibly empty).
    """
    if isinstance(data_obj, list):
        return data_obj
    if isinstance(data_obj, dict):
        pairs = data_obj.get("pairs", [])
        return pairs if isinstance(pairs, list) else []
    return []

def load_pairs_for_user(username, dataset):
    """
    Load pairs for annotation for a given user and dataset.

    Priority:
      1. user-specific annotated file in OUT_DIR (Format A: list)
      2. original dataset in DATA_DIR

    Handles legacy {"pairs": [...]} format, but always returns a list.
    """
    data_path = os.path.join(DATA_DIR, dataset)
    out_path = get_annotated_path(username, dataset)

    # 1. If user-specific annotation file exists, try that first
    if os.path.exists(out_path):
        raw = load_json(out_path)
        pairs = load_pairs_from_any(raw)
        if pairs:
            return pairs, out_path
        else:
            st.warning(
                "⚠️ Le fichier d’annotations de l’utilisateur existe mais ne contient aucune paire "
                "(format inattendu ou vide). Utilisation du jeu de données original."
            )

    # 2. Fallback to original dataset
    if not os.path.exists(data_path):
        st.error(f"❌ Fichier de données introuvable : {data_path}")
        return [], out_path

    raw = load_json(data_path)
    pairs = load_pairs_from_any(raw)
    if not pairs:
        st.error("❌ Aucune paire valide trouvée dans le jeu de données.")
        return [], out_path

    return pairs, out_path

def load_pairs_for_view_or_iaa(path):
    """
    Used in view_page() and iaa_page() to load any annotated file safely.
    Returns a list of pairs.
    """
    raw = load_json(path)
    return load_pairs_from_any(raw)

# =========================
# Pages
# =========================

def login_page():
    load_custom_css()
    
    st.markdown("<div style='height: 3rem'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div class="login-box">
            <div class="login-logo">
                <div class="icon">🔗</div>
                <h1>CausaFr</h1>
                <p>Annotation de Relations Causales</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login"):
            username = st.text_input("👤 Identifiant", placeholder="Votre nom d'utilisateur")
            password = st.text_input("🔒 Mot de passe", type="password", placeholder="Votre mot de passe")
            
            st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
            
            if st.form_submit_button("Se connecter", use_container_width=True, type="primary"):
                if verify_user(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.login_time = datetime.now().isoformat()
                    st.rerun()
                else:
                    st.error("❌ Identifiants incorrects")

def logout():
    for key in ['authenticated', 'username', 'login_time', 'pair_index', 'current_dataset']:
        st.session_state.pop(key, None)
    st.rerun()

def annotate_page(username, file_name):
    # Load data safely
    pairs, out_path = load_pairs_for_user(username, file_name)
    if not pairs:
        st.error("❌ Aucune paire trouvée pour l'annotation.")
        return
    
    # Progress management
    user_prog = get_user_progress(username, file_name)
    if st.session_state.get("current_dataset") != file_name:
        st.session_state.current_dataset = file_name
        st.session_state.pair_index = user_prog["current_index"]
    
    if "pair_index" not in st.session_state:
        st.session_state.pair_index = user_prog["current_index"]
    
    total = len(pairs)
    st.session_state.pair_index = max(0, min(st.session_state.pair_index, total - 1))
    idx = st.session_state.pair_index
    pair = pairs[idx]
    stats = compute_stats(pairs)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📊 Statistiques")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total", stats["total"])
            st.metric("Causales", stats["causal"])
        with col2:
            st.metric("Annotées", stats["annotated"])
            st.metric("Taux", f"{stats['causal_rate']:.0f}%")
        
        st.markdown("---")
        st.markdown("### 📍 Progression")
        render_progress(idx + 1, total)
        
        st.markdown("---")
        st.markdown("### 🧭 Navigation")
        
        jump = st.number_input("Aller à", 1, total, idx + 1, label_visibility="collapsed")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📍 Aller", use_container_width=True):
                st.session_state.pair_index = int(jump) - 1
                st.rerun()
        with col2:
            if st.button("⏭️ Non annotée", use_container_width=True):
                for i, p in enumerate(pairs):
                    if not p.get("annotated_by"):
                        st.session_state.pair_index = i
                        st.rerun()
                        break
    
    # Main content
    render_header(f"Paire {idx + 1} / {total}", f"📄 {file_name} • 👤 {pair.get('child_id', 'N/A')}")
    
    if pair.get("annotated_by"):
        st.markdown(f"""
        <div class="alert warning">
            ✏️ <strong>Déjà annotée</strong> par {pair['annotated_by']} — {pair.get('annotated_at', '')[:16]}
        </div>
        """, unsafe_allow_html=True)
    
    # Events
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="event-box cause">
            <div class="label">🔵 Événement 1 — Cause potentielle</div>
        </div>
        """, unsafe_allow_html=True)
        e1_text = st.text_area("E1", pair.get("event1_text", ""), height=130, key=f"e1_{idx}", label_visibility="collapsed")
        e1_cue = st.checkbox("🏷️ Marqueur causal explicite", bool(pair.get("cue1", False)), key=f"c1_{idx}")
    
    with col2:
        st.markdown("""
        <div class="event-box effect">
            <div class="label">🟢 Événement 2 — Effet potentiel</div>
        </div>
        """, unsafe_allow_html=True)
        e2_text = st.text_area("E2", pair.get("event2_text", ""), height=130, key=f"e2_{idx}", label_visibility="collapsed")
        e2_cue = st.checkbox("🏷️ Marqueur causal explicite", bool(pair.get("cue2", False)), key=f"c2_{idx}")
    
    # Question
    st.markdown("""
    <div class="question-box">
        <h3>❓ Existe-t-il une relation CAUSALE ?</h3>
        <p>L'événement 1 cause-t-il ou contribue-t-il à l'événement 2 ?</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        current = pair.get("label", 0) or 0
        label = st.radio(
            "Label",
            [1, 0],
            index=0 if current == 1 else 1,
            format_func=lambda x: "✅ OUI — Causal" if x == 1 else "❌ NON — Pas causal",
            key=f"lbl_{idx}",
            horizontal=False,
            label_visibility="collapsed"
        )
    
    with col2:
        confidence = st.slider("🎯 Confiance", 1, 5, int(pair.get("confidence", 3)), key=f"conf_{idx}")
        notes = st.text_input("📝 Notes", pair.get("notes", ""), key=f"note_{idx}", placeholder="Optionnel...")
    
    st.markdown("---")
    
    # Actions
    col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
    
    with col1:
        if st.button("⬅️", disabled=idx == 0, use_container_width=True):
            st.session_state.pair_index -= 1
            st.rerun()
    
    with col2:
        if st.button("💾 Enregistrer & Suivant", type="primary", use_container_width=True):
            pair.update({
                "event1_text": e1_text,
                "event2_text": e2_text,
                "cue1": int(bool(e1_cue)),
                "cue2": int(bool(e2_cue)),
                "label": int(label),
                "confidence": int(confidence),
                "notes": notes,
                "annotated_by": username,
                "annotated_at": datetime.now().isoformat()
            })
            pairs[idx] = pair

            # Always save as raw list (Format A)
            save_json(out_path, pairs)

            count = sum(1 for p in pairs if p.get("annotated_by") == username)
            next_index = min(idx + 1, total - 1)
            save_progress(username, file_name, next_index, count)

            if idx < total - 1:
                st.session_state.pair_index += 1
            st.rerun()
    
    with col3:
        if st.button("⏭️ Passer", disabled=idx >= total - 1, use_container_width=True):
            st.session_state.pair_index += 1
            st.rerun()
    
    with col4:
        if st.button("➡️", disabled=idx >= total - 1, use_container_width=True):
            st.session_state.pair_index += 1
            st.rerun()
    
    # Download
    if os.path.exists(out_path):
        st.markdown("---")
        with open(out_path, "r", encoding="utf-8") as f:
            st.download_button(
                "⬇️ Télécharger mes annotations",
                f,
                file_name=f"{file_name.replace('.json', '')}_{username}.json",
                mime="application/json",
                use_container_width=True
            )

def view_page():
    render_header("Fichiers d'Annotation", "Visualisez et téléchargez les annotations")
    
    if not os.path.exists(OUT_DIR):
        st.info("📂 Aucun fichier trouvé")
        return
    
    files = [f for f in os.listdir(OUT_DIR) if f.endswith("_annotated.json")]
    if not files:
        st.info("📂 Aucun fichier annoté")
        return
    
    selected = st.selectbox("📁 Fichier", files)
    if not selected:
        return
    
    data = load_pairs_for_view_or_iaa(os.path.join(OUT_DIR, selected))
    if not data:
        st.error("❌ Aucune paire valide dans ce fichier.")
        return
    
    stats = compute_stats(data)
    render_metrics(stats)
    
    st.markdown("---")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        f_label = st.selectbox("🏷️ Label", ["Tous", "Causal", "Non causal", "Non annoté"])
    with col2:
        annotators = sorted({p.get("annotated_by") for p in data if p.get("annotated_by")})
        f_ann = st.selectbox("👤 Annotateur", ["Tous"] + annotators)
    with col3:
        f_cue = st.selectbox("🔍 Marqueur", ["Tous", "Avec", "Sans"])
    
    filtered = data
    if f_label == "Causal":
        filtered = [p for p in filtered if p.get("label") == 1]
    elif f_label == "Non causal":
        filtered = [p for p in filtered if p.get("label") == 0]
    elif f_label == "Non annoté":
        filtered = [p for p in filtered if not p.get("annotated_by")]
    
    if f_ann != "Tous":
        filtered = [p for p in filtered if p.get("annotated_by") == f_ann]
    
    if f_cue == "Avec":
        filtered = [p for p in filtered if p.get("cue1") or p.get("cue2")]
    elif f_cue == "Sans":
        filtered = [p for p in filtered if not p.get("cue1") and not p.get("cue2")]
    
    st.caption(f"📋 {len(filtered)} paires")
    
    for i, p in enumerate(filtered[:50]):
        icon = "✅" if p.get("label") == 1 else "❌" if p.get("label") == 0 else "❓"
        e1_full = p.get("event1_text", "") or ""
        e2_full = p.get("event2_text", "") or ""
        e1 = (e1_full[:45] + "...") if len(e1_full) > 45 else e1_full
        e2 = (e2_full[:45] + "...") if len(e2_full) > 45 else e2_full
        
        with st.expander(f"{icon} {e1} → {e2}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**🔵 E1:** {e1_full or 'N/A'}")
            with col2:
                st.markdown(f"**🟢 E2:** {e2_full or 'N/A'}")
            if p.get("annotated_by"):
                st.caption(f"👤 {p['annotated_by']} • 🎯 {p.get('confidence', '?')}/5")
    
    if len(filtered) > 50:
        st.warning("⚠️ 50 premières paires affichées")
    
    st.markdown("---")
    with open(os.path.join(OUT_DIR, selected), "r", encoding="utf-8") as f:
        st.download_button(
            "⬇️ Télécharger",
            f,
            selected,
            "application/json",
            use_container_width=True
        )

def iaa_page():
    render_header("Accord Inter-Annotateurs", "Analyse de la cohérence des annotations")
    
    if not os.path.exists(OUT_DIR):
        st.info("📂 Aucun fichier")
        return
    
    files = [f for f in os.listdir(OUT_DIR) if f.endswith("_annotated.json")]
    if len(files) < 2:
        st.info("ℹ️ 2 fichiers minimum requis")
        return
    
    # Group by dataset
    datasets = {}
    for f in files:
        parts = f.replace("_annotated.json", "").rsplit("_", 1)
        if len(parts) == 2:
            ds, ann = parts
            datasets.setdefault(ds, []).append((ann, f))
    
    multi = {k: v for k, v in datasets.items() if len(v) >= 2}
    if not multi:
        st.warning("⚠️ Aucun jeu avec plusieurs annotateurs")
        return
    
    selected = st.selectbox("📁 Jeu de données", list(multi.keys()))
    if not selected:
        return
    
    annotators = multi[selected]
    st.success(f"👥 Annotateurs : {', '.join(a[0] for a in annotators)}")
    
    # Load annotations
    all_ann = {}
    all_data = {}

    for ann, fname in annotators:
        path = os.path.join(OUT_DIR, fname)
        data = load_pairs_for_view_or_iaa(path)
        all_data[ann] = data

        # Key by (event1_id, event2_id) if available, else by index
        key_to_label = {}
        for i, p in enumerate(data):
            if p.get("annotated_by") != ann:
                # ignore unowned pairs if ever mixed
                continue
            e1_id = p.get("event1_id", i)
            e2_id = p.get("event2_id", i)
            key_to_label[(e1_id, e2_id)] = p.get("label")
        all_ann[ann] = key_to_label
    
    st.markdown("---")
    st.markdown("### 📊 Kappa de Cohen")
    
    names = list(all_ann.keys())
    for i, a1 in enumerate(names):
        for a2 in names[i+1:]:
            common = set(all_ann[a1].keys()) & set(all_ann[a2].keys())
            valid = [k for k in common
                     if all_ann[a1][k] is not None and all_ann[a2][k] is not None]
            
            if len(valid) < 10:
                st.warning(f"⚠️ {a1} ↔ {a2} : {len(valid)} paires (min 10)")
                continue
            
            l1 = [all_ann[a1][k] for k in valid]
            l2 = [all_ann[a2][k] for k in valid]
            
            po = sum(x == y for x, y in zip(l1, l2)) / len(l1)
            p1 = sum(l1) / len(l1)
            p2 = sum(l2) / len(l2)
            pe = p1 * p2 + (1 - p1) * (1 - p2)
            kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
            
            render_kappa(a1, a2, kappa, po * 100, len(valid))
    
    # Disagreements
    st.markdown("---")
    st.markdown("### 🔍 Désaccords")
    
    if len(names) >= 2:
        a1, a2 = names[0], names[1]
        common = set(all_ann[a1].keys()) & set(all_ann[a2].keys())
        
        disagree = []
        # Build a map from key -> pair object for one annotator
        index_map = {}
        for i, p in enumerate(all_data[a1]):
            e1_id = p.get("event1_id", i)
            e2_id = p.get("event2_id", i)
            index_map[(e1_id, e2_id)] = p
        
        for k in common:
            if (all_ann[a1][k] is not None and
                all_ann[a2][k] is not None and
                all_ann[a1][k] != all_ann[a2][k]):
                p = index_map.get(k)
                if p:
                    disagree.append((p, all_ann[a1][k], all_ann[a2][k]))
        
        if disagree:
            st.warning(f"⚠️ {len(disagree)} désaccords entre {a1} et {a2}")
            for i, (p, l1, l2) in enumerate(disagree[:10]):
                with st.expander(f"Désaccord {i+1}"):
                    st.markdown(f"**E1:** {p.get('event1_text', '')}")
                    st.markdown(f"**E2:** {p.get('event2_text', '')}")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**{a1}:** {'✅' if l1 == 1 else '❌'}")
                    with col2:
                        st.markdown(f"**{a2}:** {'✅' if l2 == 1 else '❌'}")
        else:
            st.success("✅ Aucun désaccord !")

# =========================
# Main
# =========================

def main():
    st.set_page_config("CausaFr", "🔗", "wide", "expanded")
    load_custom_css()
    
    if not st.session_state.get("authenticated"):
        login_page()
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; padding: 1.5rem 0;">
            <div style="font-size: 2.5rem;">🔗</div>
            <h2 style="margin: 0.5rem 0 0 0;">CausaFr</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.08); padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 1rem;">
            👤 <strong>{st.session_state.username}</strong>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Déconnexion", use_container_width=True):
            logout()
        
        st.markdown("---")
        
        mode = st.radio("Mode", ["✏️ Annoter", "📂 Voir", "📊 IAA"], label_visibility="collapsed")
    
    # Content
    if mode == "✏️ Annoter":
        with st.sidebar:
            st.markdown("### 📁 Données")
            if not os.path.exists(DATA_DIR):
                st.error("Dossier data/ manquant")
                return
            
            datasets = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]
            if not datasets:
                st.error("Aucun JSON")
                return
            
            file = st.selectbox("Fichier", datasets, label_visibility="collapsed")
            prog = get_user_progress(st.session_state.username, file)
            if prog["current_index"] > 0:
                st.info(f"📍 Paire {prog['current_index'] + 1}")
        
        annotate_page(st.session_state.username, file)
    
    elif mode == "📂 Voir":
        view_page()
    
    elif mode == "📊 IAA":
        iaa_page()

if __name__ == "__main__":
    main()
