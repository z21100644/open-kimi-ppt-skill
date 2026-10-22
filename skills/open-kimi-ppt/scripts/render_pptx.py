"""Render a .pptx to per-slide PNGs, a stitched overview and a PDF for visual QA — offline.

Usage:
  python render_pptx.py deck.pptx --output .qa-images [--pages 2,3,8] [--cols 2] [--width 1920]
  python render_pptx.py deck.pptx --embed-fonts --pdf-to deck.pdf     # final pass: deliverable PPTX + PDF

--embed-fonts (PowerPoint backend): saves the deck back over deck.pptx with TrueType fonts embedded, so it
opens with the right typefaces on machines without them. LibreOffice cannot embed fonts into PPTX; the
summary then reports "fonts_embedded": false. --pdf-to copies the PDF export to the given path.

Backends (auto, first available):
  1. Microsoft PowerPoint via COM (Windows) — the most faithful renderer for decks meant for PowerPoint.
  2. LibreOffice `soffice --headless` -> PDF -> PyMuPDF raster (macOS / Linux / Windows without Office).

Outputs in --output:
  pages/<n>.png     full-resolution slide images (1-based)
  overview.jpg      all (or --pages) slides stitched, labelled P1..Pn
  overview-<k>.jpg  the same slides in sheets of --per-sheet (default 6 when more than 8 slides) — read these:
                    one tall overview of a long deck is scaled down until the copy is illegible
  <deck>.pdf        PDF export of the deck
Prints a JSON summary.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def ensure(mod, pkg):
    try:
        __import__(mod)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "-q", pkg])


def render_powerpoint(pptx, pages_dir, pdf, width, embed=False):
    # PowerPoint locks files it opens and dislikes non-ASCII paths in some setups: work on an ASCII temp copy.
    tmp = Path(tempfile.mkdtemp(prefix="pptxqa_"))
    src = tmp / "deck.pptx"
    shutil.copyfile(pptx, src)
    height = round(width * 9 / 16)
    save_embedded = f"$pres.SaveAs('{tmp}\\embedded.pptx', 24, -1)" if embed else ""   # 24 = OpenXML, -1 = embed fonts
    # Windows PowerShell writes in the console code page (cp950, cp936…): switch it to UTF-8 so error
    # messages survive decoding. Quit PowerPoint even when Open fails, or a hidden instance lingers.
    ps = f"""
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'Stop'
$app = New-Object -ComObject PowerPoint.Application
try {{
  $pres = $app.Presentations.Open('{src}', $true, $false, $false)
  $h = [int]($pres.PageSetup.SlideHeight / $pres.PageSetup.SlideWidth * {width})
  $i = 0
  foreach ($s in $pres.Slides) {{ $i++; $s.Export('{tmp}\\s' + $i + '.png', 'PNG', {width}, $h) }}
  {save_embedded}
  $pres.SaveAs('{tmp}\\deck.pdf', 32)
  $pres.Close()
}} catch {{ $err = $_.Exception.Message }} finally {{ $app.Quit() }}
if ($err) {{ [Console]::Error.WriteLine($err); exit 1 }}
Write-Output $i
"""
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "PowerPoint COM failed")
    n = int(r.stdout.strip().splitlines()[-1])
    for i in range(1, n + 1):
        shutil.move(str(tmp / f"s{i}.png"), pages_dir / f"{i}.png")
    shutil.move(str(tmp / "deck.pdf"), pdf)
    if embed:                                          # ppSaveAsOpenXMLPresentation with EmbedTrueTypeFonts
        shutil.copyfile(tmp / "embedded.pptx", pptx)
    shutil.rmtree(tmp, ignore_errors=True)
    return n


def find_soffice():
    for name in ("soffice", "libreoffice"):
        p = shutil.which(name)
        if p:
            return p
    for p in (r"C:\Program Files\LibreOffice\program\soffice.exe", "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        if Path(p).exists():
            return p
    return None


def render_libreoffice(pptx, pages_dir, pdf, width):
    soffice = find_soffice()
    if not soffice:
        raise RuntimeError("LibreOffice not found")
    tmp = Path(tempfile.mkdtemp(prefix="pptxqa_"))
    src = tmp / "deck.pptx"
    shutil.copyfile(pptx, src)
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(tmp), str(src)],
                   check=True, capture_output=True, timeout=600)
    shutil.move(str(tmp / "deck.pdf"), pdf)
    ensure("fitz", "PyMuPDF")
    import fitz
    doc = fitz.open(pdf)
    for i, page in enumerate(doc, 1):
        zoom = width / page.rect.width
        page.get_pixmap(matrix=fitz.Matrix(zoom, zoom)).save(pages_dir / f"{i}.png")
    n = len(doc)
    shutil.rmtree(tmp, ignore_errors=True)
    return n


def stitch(pages_dir, picks, out, cols, thumb_w=960):
    ensure("PIL", "Pillow")
    from PIL import Image, ImageDraw, ImageFont
    ims = []
    for i in picks:
        im = Image.open(pages_dir / f"{i}.png").convert("RGB")
        ims.append((i, im.resize((thumb_w, round(im.height * thumb_w / im.width)))))
    th = ims[0][1].height
    gap, cap = 12, 40                    # each slide gets a caption strip above it: no corner of the slide is covered
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb_w + (cols + 1) * gap, rows * (th + cap) + (rows + 1) * gap), "#9AA4B2")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arialbd.ttf", 28)
    except OSError:
        font = ImageFont.load_default()
    for k, (i, im) in enumerate(ims):
        x, y = gap + (k % cols) * (thumb_w + gap), gap + (k // cols) * (th + cap + gap)
        draw.rectangle([x, y, x + 76, y + cap - 4], fill="#D7263D")
        draw.text((x + 12, y + 3), f"P{i}", fill="white", font=font)
        sheet.paste(im, (x, y + cap))
    sheet.save(out, quality=88)


def write_sheets(pages_dir, picks, out, cols, per):
    """overview-1.jpg, overview-2.jpg… with `per` slides each (stale sheets removed first)."""
    for old in out.glob("overview-*.jpg"):
        old.unlink()
    sheets = []
    for k, i in enumerate(range(0, len(picks), per) if per else [], 1):
        sheets.append(out / f"overview-{k}.jpg")
        stitch(pages_dir, picks[i:i + per], sheets[-1], cols)
    return sheets


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pptx")
    ap.add_argument("-o", "--output", default=None, help="QA folder (default: <pptx dir>/.qa-images)")
    ap.add_argument("--pages", default=None, help="comma list of 1-based slides for the overview")
    ap.add_argument("--cols", type=int, default=2)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--backend", choices=["auto", "powerpoint", "libreoffice"], default="auto")
    ap.add_argument("--embed-fonts", action="store_true", help="PowerPoint: save the deck back with fonts embedded")
    ap.add_argument("--pdf-to", default=None, help="also copy the PDF export to this path (the deliverable PDF)")
    ap.add_argument("--per-sheet", type=int, default=None,
                    help="slides per overview sheet (default 6 when more than 8 slides; 0 = single overview only)")
    a = ap.parse_args()
    pptx = Path(a.pptx).resolve()
    out = Path(a.output or pptx.parent / ".qa-images").resolve()
    pages_dir = out / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    for old in pages_dir.glob("*.png"):
        old.unlink()
    pdf = out / (pptx.stem + ".pdf")
    order = {"auto": ["powerpoint", "libreoffice"], "powerpoint": ["powerpoint"], "libreoffice": ["libreoffice"]}[a.backend]
    if os.name != "nt" and "powerpoint" in order and a.backend == "auto":
        order.remove("powerpoint")
    errors, used, n = {}, None, 0
    for name in order:
        try:
            n = (render_powerpoint(pptx, pages_dir, pdf, a.width, a.embed_fonts) if name == "powerpoint"
                 else render_libreoffice(pptx, pages_dir, pdf, a.width))
            used = name
            break
        except Exception as exc:  # noqa: BLE001
            errors[name] = str(exc)[:300]
    if not used:
        print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False, indent=2))
        sys.exit(1)
    if a.pdf_to:
        shutil.copyfile(pdf, Path(a.pdf_to).resolve())
    picks = [int(x) for x in a.pages.split(",")] if a.pages else list(range(1, n + 1))
    stitch(pages_dir, picks, out / "overview.jpg", a.cols)
    per = a.per_sheet if a.per_sheet is not None else (6 if len(picks) > 8 else 0)
    sheets = write_sheets(pages_dir, picks, out, a.cols, per)
    print(json.dumps({"ok": True, "backend": used, "slides": n, "overview": str(out / "overview.jpg"),
                      "sheets": [str(p) for p in sheets], "pages_dir": str(pages_dir), "pdf": str(pdf),
                      "fonts_embedded": bool(a.embed_fonts and used == "powerpoint")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    # Emit UTF-8 regardless of the Windows code page (cp950, cp936…) so callers that capture the
    # output as UTF-8 — agents, tests, CI — can read CJK messages.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    main()
