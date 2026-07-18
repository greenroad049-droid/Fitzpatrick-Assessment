import streamlit as st
import streamlit.components.v1 as components
import time
import random
import os
import io
from datetime import datetime
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ------------------------------------------------------------------
# GENERAL CONFIG
# ------------------------------------------------------------------
st.set_page_config(page_title="Skin Tone Evaluation", page_icon="🧑‍⚕️", layout="centered")

IMAGES_FOLDER = "images"
VALID_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
FITZ_OPTIONS = ["1", "2", "3", "4", "5", "6"]  # Fitzpatrick types I-VI, shown as digits

SHEET_HEADER = ["timestamp", "evaluator", "photo", "fitzpatrick", "time_seconds"]


def add_keyboard_shortcuts():
    """Lets evaluators press keys 1-6 instead of clicking, for a faster flow."""
    components.html(
        """
        <script>
        (function() {
            const doc = window.parent.document;
            if (doc._fitzShortcutsAdded) { return; }
            doc._fitzShortcutsAdded = true;

            function clickButtonByLabel(label) {
                const buttons = doc.querySelectorAll('button');
                for (const btn of buttons) {
                    if (btn.innerText.trim() === label) {
                        btn.click();
                        break;
                    }
                }
            }

            doc.addEventListener('keydown', function(e) {
                const tag = (e.target && e.target.tagName) || '';
                if (tag === 'INPUT' || tag === 'TEXTAREA') { return; }
                if (['1', '2', '3', '4', '5', '6'].includes(e.key)) {
                    clickButtonByLabel(e.key);
                }
            });
        })();
        </script>
        """,
        height=0,
        width=0,
    )


# ------------------------------------------------------------------
# CONEXIÓN A GOOGLE SHEETS
# ------------------------------------------------------------------
@st.cache_resource
def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(st.secrets["sheet_id"]).sheet1

    # Si la hoja está vacía, agrega el encabezado
    if sheet.row_count == 0 or not sheet.get_all_values():
        sheet.append_row(SHEET_HEADER)
    return sheet


def save_evaluation(evaluator, photo, fitzpatrick, time_seconds):
    sheet = get_sheet()
    row = [
        datetime.now().isoformat(timespec="seconds"),
        evaluator,
        photo,
        fitzpatrick,
        round(time_seconds, 2),
    ]
    sheet.append_row(row)


# ------------------------------------------------------------------
# UTILITIES
# ------------------------------------------------------------------
@st.cache_data
def list_photos():
    if not os.path.isdir(IMAGES_FOLDER):
        return []
    files = [
        f for f in os.listdir(IMAGES_FOLDER) if f.lower().endswith(VALID_EXTENSIONS)
    ]
    files.sort()
    return files


def start_evaluator_session(name):
    photos = list_photos()
    order = photos.copy()
    random.shuffle(order)  # different random order per evaluator
    st.session_state.evaluator = name.strip()
    st.session_state.photo_order = order
    st.session_state.index = 0
    st.session_state.photo_start_time = time.time()
    st.session_state.started = True


def save_uploaded_photos(uploaded_files):
    """Saves photos uploaded directly (already unzipped) from the browser
    straight into images/. No ZIP involved, so nothing can fail unzipping."""
    os.makedirs(IMAGES_FOLDER, exist_ok=True)
    added, skipped = 0, 0
    for uploaded_file in uploaded_files:
        filename = os.path.basename(uploaded_file.name)
        if not filename.lower().endswith(VALID_EXTENSIONS):
            skipped += 1
            continue
        target_path = os.path.join(IMAGES_FOLDER, filename)
        with open(target_path, "wb") as target:
            target.write(uploaded_file.getbuffer())
        added += 1
    return added, skipped


# ------------------------------------------------------------------
# PANEL DE ADMINISTRACIÓN (?admin=1 en la URL)
# ------------------------------------------------------------------
def admin_panel():
    st.title("🔒 Admin panel")
    password = st.text_input("Admin password", type="password")
    if password != st.secrets.get("admin_password", ""):
        if password:
            st.error("Incorrect password.")
        st.stop()

    st.subheader("📤 Upload photos")
    st.caption(
        "Select all your photo files at once (already unzipped) and upload "
        "them directly — no ZIP involved."
    )
    uploaded_files = st.file_uploader(
        "Choose image files",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
    )
    if uploaded_files and st.button("Add to gallery"):
        added, skipped = save_uploaded_photos(uploaded_files)
        list_photos.clear()
        st.success(f"Added {added} photos ✅ ({skipped} invalid files skipped).")
        st.info(
            "Note: photos are stored on the app's temporary disk. They stay "
            "available while the app is running, but could be lost if the app "
            "restarts or redeploys (e.g. after Streamlit Cloud puts it to sleep "
            "from inactivity). Keep your photos handy so you can re-upload if "
            "that happens."
        )

    st.divider()
    st.subheader("📊 Results")

    sheet = get_sheet()
    data = sheet.get_all_records()
    if not data:
        st.info("No evaluations recorded yet.")
        st.stop()

    df = pd.DataFrame(data)
    st.success(f"{len(df)} evaluations recorded from {df['evaluator'].nunique()} evaluator(s).")
    st.dataframe(df, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download CSV", data=csv_bytes,
            file_name="fitzpatrick_evaluations.csv", mime="text/csv"
        )
    with col2:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Evaluations")
        st.download_button(
            "⬇️ Download Excel", data=buffer.getvalue(),
            file_name="fitzpatrick_evaluations.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# ------------------------------------------------------------------
# FLUJO PRINCIPAL DE EVALUACIÓN
# ------------------------------------------------------------------
def welcome_screen():
    st.title("🧑‍⚕️ Skin Tone Evaluation (Fitzpatrick Scale)")
    photos = list_photos()
    if not photos:
        st.error(
            "No photos were found in the 'images/' folder. "
            "Ask the administrator to upload them to the repository."
        )
        st.stop()

    st.write(f"There are **{len(photos)} photos** to evaluate. This will take a few minutes.")
    name = st.text_input("Enter your name to begin:")
    if st.button("Start evaluation", disabled=not name.strip()):
        start_evaluator_session(name)
        st.rerun()


def evaluation_screen():
    add_keyboard_shortcuts()

    order = st.session_state.photo_order
    total = len(order)
    index = st.session_state.index

    st.progress(index / total)
    st.caption(f"Photo {index + 1} of {total} — Evaluator: {st.session_state.evaluator}")

    current_photo = order[index]
    path = os.path.join(IMAGES_FOLDER, current_photo)
    st.image(path, use_container_width=True)

    st.write("### Fitzpatrick skin type? (press 1-6 or click)")
    cols = st.columns(len(FITZ_OPTIONS))
    for i, option in enumerate(FITZ_OPTIONS):
        if cols[i].button(option, use_container_width=True, key=f"btn_{index}_{option}"):
            elapsed_time = time.time() - st.session_state.photo_start_time
            save_evaluation(
                st.session_state.evaluator, current_photo, option, elapsed_time
            )
            st.session_state.index += 1
            st.session_state.photo_start_time = time.time()
            st.rerun()


def final_screen():
    st.title("✅ Thank you for your evaluation!")
    st.write(
        f"{st.session_state.evaluator}, you finished evaluating "
        f"all {len(st.session_state.photo_order)} photos. You can close this window now."
    )


# ------------------------------------------------------------------
# ROUTER
# ------------------------------------------------------------------
def main():
    query_params = st.query_params
    if query_params.get("admin") is not None:
        admin_panel()
        return

    if "started" not in st.session_state:
        welcome_screen()
    elif st.session_state.index < len(st.session_state.photo_order):
        evaluation_screen()
    else:
        final_screen()


if __name__ == "__main__":
    main()
