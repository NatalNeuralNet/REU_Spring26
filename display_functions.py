import streamlit as st
from pathlib import Path
from physics_functions import *

# Local database root (yours)
DB_ROOT = Path(r"C:\Users\arnol\.refractiveindex.info-database")
NK_ROOT = DB_ROOT / "data-nk"   # n-k database folder


# Functions. ----> move to new file in the future

# ---- Build dropdown options from local folder structure ----
@st.cache_resource
def build_tree():
    """
    Returns:
      shelves: sorted list
      books_by_shelf: dict shelf -> sorted list of books
      pages_by_shelf_book: dict (shelf, book) -> sorted list of pages
    Expected paths: data-nk/<shelf>/<book>/<page>.yml
    Example: data-nk/main/Si/Aspnes.yml  -> shelf=main book=Si page=Aspnes
    """
    books_by_shelf = {}
    pages_by_shelf_book = {}

    if not NK_ROOT.exists():
        raise FileNotFoundError(f"Missing folder: {NK_ROOT} (do you have data-nk in the DB?)")

    for shelf_dir in NK_ROOT.iterdir():
        if not shelf_dir.is_dir():
            continue
        shelf = shelf_dir.name
        books = []

        for book_dir in shelf_dir.iterdir():
            if not book_dir.is_dir():
                continue
            book = book_dir.name
            books.append(book)

            pages = sorted([p.stem for p in book_dir.glob("*.yml")])
            pages_by_shelf_book[(shelf, book)] = pages

        books_by_shelf[shelf] = sorted(books)

    shelves = sorted(books_by_shelf.keys())
    return shelves, books_by_shelf, pages_by_shelf_book


# -------------------------------------------
# Helpers for build/display of table
# -------------------------------------------
@st.cache_data(show_spinner=False)
def cached_build_tree():
    return build_tree()

@st.cache_data(show_spinner=False)
def cached_get_nk(shelf: str, book: str, page: str, wavelength_nm: float):
    mat = RefractiveIndexMaterial(shelf=shelf, book=book, page=page)
    n = mat.get_refractive_index(wavelength_nm)
    try:
        k = mat.get_extinction_coefficient(wavelength_nm)
        err = ""
    except Exception as ke:
        k = None
        err = f"k failed: {type(ke).__name__}"
    
    n = round(float(n), 4)
    k = round(float(k), 4)
    N = (complex(n, k))
         
    return n, k, N, err

def empty_row(layer_num: int):
    return {
        "layer": layer_num,
        "shelf": None,
        "book": None,
        "page": None,
        "n": None,
        "k": None,
        "N": None,
        "error": ""
    }

def ensure_state(max_layers: int):
    if "layer_rows" not in st.session_state:
        st.session_state.layer_rows = {}
    if "current_layer" not in st.session_state:
        st.session_state.current_layer = 1

    # keep only coating layers 1..max_layers
    st.session_state.layer_rows = {
        k: v for k, v in st.session_state.layer_rows.items() if 1 <= k <= max_layers
    }

    if max_layers <= 0:
        st.session_state.current_layer = 1
    else:
        st.session_state.current_layer = max(1, min(st.session_state.current_layer, max_layers))

def is_saved(layer_num: int) -> bool:
    return layer_num in st.session_state.layer_rows

def medium_row(medium: str):
    medium_l = medium.lower()

    if medium_l == "vacuum":
        n0 = 1.0
    else:  # "air"
        n0 = 1.0

    N = complex(n0,0)
    return {
        "layer": 0,
        "shelf": None,
        "book": medium_l,
        "page": None,
        "n": N.real,
        "k": N.imag,
        "N": N,
        "error": ""
    }


def glass_row(layer_num: int, wavelength_nm: float):
    # Fixed substrate: BK7 glass (common default)
    # Adjust these if your database uses different keys.
    shelf, book, page = "3d", "glass", "BK7"

    try:
        n, k, N, err = cached_get_nk(shelf, book, page, wavelength_nm)
    except Exception as e:
        n, k, N, err = None, None, None, f"glass failed: {type(e).__name__}"

    return {
        "layer": layer_num,
        "shelf": shelf,
        "book": book,
        "page": page,
        "n": n,
        "k": k,
        "N": N,
        "error": err
    }

def build_display_table(max_layers: int, medium: str, wavelength_nm: float):
    rows = []
    rows.append(medium_row(medium))

    # coating layers 1..max_layers
    for layer_num in range(1, max_layers + 1):
        rows.append(st.session_state.layer_rows.get(layer_num, empty_row(layer_num)))

    # last row: glass substrate
    rows.append(glass_row(max_layers + 1, wavelength_nm))
    return rows
