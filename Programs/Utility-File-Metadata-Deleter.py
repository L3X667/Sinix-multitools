# Copyright (c) 2025-2026 v4lkyr0 — SINIX
# See the file 'LICENSE' for copying permission.
# --------------------------------------------------------
# EN: Non-commercial use only. Do not sell, remove cgreenits
#     or greenistribute without prior written permission.
# FR: Usage non-commercial uniquement. Ne pas vendre, supprimer
#     les crédits ou greenistribuer sans autorisation écrite.

from Core.Utils import *
from Core.Config import *

try:
    import pathlib
    import tempfile
    import shutil
    import zipfile
    import tarfile
    import wave
    import contextlib
    import sqlite3
    import PIL.Image
    import fitz  # PyMuPDF
except Exception as e:
    MissingModule(e)

EXT_IMAGE    = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".gif", ".webp", ".ico", ".heic", ".heif"}
EXT_PDF      = {".pdf"}
EXT_ZIP      = {".docx", ".xlsx", ".pptx", ".odt", ".ods", ".odp", ".epub", ".jar", ".apk"}
EXT_AUDIO    = {".wav", ".flac", ".aiff", ".aif", ".mp3"}
EXT_VIDEO    = {".mp4", ".mov", ".mkv", ".avi", ".wmv", ".flv", ".webm", ".m4v", ".mpeg", ".mpg"}
EXT_ARCHIVE  = {".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz"}
EXT_DATABASE = {".sqlite", ".db", ".sqlite3"}


def WipeImage(path):
    ext = path.suffix.lower()
    tmp = path.with_suffix(".tmp" + path.suffix)
    with PIL.Image.open(path) as img:
        if ext in (".png", ".webp", ".tiff", ".tif", ".gif", ".ico", ".heic", ".heif"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")
        if ext in (".jpg", ".jpeg"):
            img.save(tmp, format="JPEG")
        elif ext in (".png", ".bmp", ".gif", ".webp", ".ico"):
            img.save(tmp, format=img.format or "PNG")
        elif ext in (".tiff", ".tif"):
            img.save(tmp, format="TIFF")
        else:
            img.save(tmp)
    os.replace(tmp, path)


def WipePdf(path):
    doc   = fitz.open(path)
    clean = fitz.open()
    for page in doc:
        pix      = page.get_pixmap()
        rect     = fitz.Rect(0, 0, pix.width, pix.height)
        new_page = clean.new_page(width=pix.width, height=pix.height)
        new_page.insert_image(rect, pixmap=pix)
    clean.set_metadata({})
    tmp = path.with_suffix(".tmp.pdf")
    clean.save(tmp)
    clean.close()
    doc.close()
    os.replace(tmp, path)


def WipeZip(path):
    tmp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(path, "r") as z:
        z.extractall(tmp_dir)
    for f in pathlib.Path(tmp_dir).rglob("*"):
        if f.is_file():
            WipeBinary(f)
    tmp_zip = path.with_suffix(".tmp")
    with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for f in pathlib.Path(tmp_dir).rglob("*"):
            if f.is_file():
                z.write(f, f.relative_to(tmp_dir))
    shutil.rmtree(tmp_dir, ignore_errors=True)
    os.replace(tmp_zip, path)


def WipeArchive(path):
    tmp_dir = tempfile.mkdtemp()
    if path.suffix == ".zip":
        with zipfile.ZipFile(path, "r") as z:
            z.extractall(tmp_dir)
    else:
        with tarfile.open(path, "r:*") as t:
            t.extractall(tmp_dir)
    for f in pathlib.Path(tmp_dir).rglob("*"):
        if f.is_file():
            WipeBinary(f)
    tmp_archive = path.with_suffix(".tmp")
    with tarfile.open(tmp_archive, "w:gz") as t:
        for f in pathlib.Path(tmp_dir).rglob("*"):
            t.add(f, arcname=f.relative_to(tmp_dir))
    shutil.rmtree(tmp_dir, ignore_errors=True)
    os.replace(tmp_archive, path)


def WipeWav(path):
    with contextlib.closing(wave.open(str(path), "rb")) as r:
        params = r.getparams()
        frames = r.readframes(params.nframes)
    tmp = path.with_suffix(".tmp.wav")
    with wave.open(str(tmp), "wb") as w:
        w.setparams(params)
        w.writeframes(frames)
    os.replace(tmp, path)


def WipeAudio(path):
    tmp = path.with_suffix(".tmp" + path.suffix)
    ext = path.suffix.lower()
    with open(path, "rb") as f:
        data = f.read()
    if ext == ".mp3":
        if len(data) > 128 and data[-128:-125] == b"TAG":
            data = data[:-128]
        while data[:3] == b"ID3" and len(data) > 10:
            size_bytes = data[6:10]
            size = ((size_bytes[0] & 0x7f) << 21) | ((size_bytes[1] & 0x7f) << 14) | ((size_bytes[2] & 0x7f) << 7) | (size_bytes[3] & 0x7f)
            data = data[10 + size:]
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def WipeSqlite(path):
    conn = sqlite3.connect(path)
    conn.execute("VACUUM;")
    conn.commit()
    conn.close()


def WipeBinary(path):
    with open(path, "rb") as f:
        data = f.read()
    tmp = path.with_suffix(".tmp")
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def ProcessFile(path):
    ext = path.suffix.lower()
    print(f"{LOADING} Processing:{green} {path.name}", reset)
    try:
        if   ext in EXT_IMAGE   : WipeImage(path)
        elif ext in EXT_PDF     : WipePdf(path)
        elif ext in EXT_ZIP     : WipeZip(path)
        elif ext in EXT_AUDIO   :
            if ext == ".wav"    : WipeWav(path)
            else                : WipeAudio(path)
        elif ext in EXT_VIDEO   : WipeBinary(path)
        elif ext in EXT_ARCHIVE : WipeArchive(path)
        elif ext in EXT_DATABASE: WipeSqlite(path)
        else                    : WipeBinary(path)
        print(f"{SUCCESS} Metadata removed:{green} {path.name}", reset)
    except Exception as e:
        print(f"{ERROR} Failed on {path.name}:{green} {e}", reset)


Title("File Metadata Deleter")

Scroll(GradientBanner(osint_banner))

try:
    print(f"{INFO} Removes maximum metadata Python can handle. Verify result with a metadata viewer.", reset)

    path_input = input(f"{INPUT} File or folder path {green}->{reset} ").strip().strip('"').strip("'")

    if not path_input or not os.path.exists(path_input):
        print(f"{ERROR} Path not found!", reset)
        Continue()
        Reset()

    target = pathlib.Path(path_input)
    print(f"{LOADING} Deleting metadata..", reset)

    if target.is_file():
        ProcessFile(target)
    elif target.is_dir():
        files = [f for f in target.rglob("*") if f.is_file()]
        print(f"{INFO} Files found:{green} {len(files)}", reset)
        for f in files:
            ProcessFile(f)
    else:
        print(f"{ERROR} Not a valid file or directory!", reset)

    Continue()
    Reset()

except Exception as e:
    Error(e)
