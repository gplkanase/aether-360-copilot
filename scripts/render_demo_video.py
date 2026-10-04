#!/usr/bin/env python3
"""Render a 1080p narrated demo video of Aether 360 Copilot from live synthetic answers."""
from __future__ import annotations

import shutil
import subprocess
import sys
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aether360.qa import answer_question
from aether360.store import load_bundle

OUT_DIR = ROOT / "docs" / "demo"
FRAMES = OUT_DIR / "frames"
AUDIO = OUT_DIR / "audio"
SEGS = OUT_DIR / "segments"
W, H = 1920, 1080

NAVY = (11, 61, 74)
NAVY_DEEP = (7, 42, 51)
CREAM = (246, 243, 236)
INK = (28, 43, 51)
MUTED = (92, 107, 115)
LINE = (217, 210, 197)
WHITE = (255, 255, 255)
RUST = (196, 92, 38)
CRIMSON = (122, 31, 31)
GREEN = (47, 111, 78)
GOLD = (201, 162, 39)
TEAL = (213, 227, 230)
FONT_DIR = Path(r"C:\Windows\Fonts")


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    path = FONT_DIR / name
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def fonts() -> dict[str, ImageFont.FreeTypeFont]:
    return {
        "hero": font("georgia.ttf", 64),
        "h1": font("georgia.ttf", 44),
        "h2": font("georgia.ttf", 32),
        "h3": font("georgiab.ttf", 22),
        "body": font("calibri.ttf", 26),
        "body_b": font("calibrib.ttf", 26),
        "small": font("calibri.ttf", 20),
        "small_b": font("calibrib.ttf", 20),
        "tiny": font("calibri.ttf", 16),
        "code": font("consola.ttf", 18),
        "badge": font("calibrib.ttf", 16),
        "caption": font("calibri.ttf", 28),
    }


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, width: int) -> list[str]:
    words = (text or "").replace("\n", " ").split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def rounded(draw: ImageDraw.ImageDraw, box, fill, radius=8, outline=None):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline)


def text_h(draw, text, fnt) -> int:
    b = draw.textbbox((0, 0), text, font=fnt)
    return b[3] - b[1]


def draw_caption(im: Image.Image, caption: str, f: dict) -> None:
    draw = ImageDraw.Draw(im)
    bar_h = 118
    rounded(draw, (0, H - bar_h, W, H), NAVY_DEEP, radius=0)
    lines = wrap(draw, caption, f["caption"], W - 120)
    y = H - bar_h + 28
    for line in lines[:2]:
        draw.text((60, y), line, font=f["caption"], fill=WHITE)
        y += 36


def chrome(active_tab: str, sidebar_title: str, f: dict) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    rounded(d, (0, 0, 320, H - 118), NAVY, radius=0)
    d.text((28, 28), "Aether 360", font=f["h2"], fill=WHITE)
    d.text((28, 72), "Copilot", font=f["small"], fill=TEAL)
    d.text((28, 120), sidebar_title, font=f["tiny"], fill=TEAL)
    tabs = ["Population", "Member 360", "Cited copilot", "Evidence", "CoCo"]
    x = 360
    for t in tabs:
        on = t == active_tab
        tw = int(d.textlength(t, font=f["small_b"])) + 28
        rounded(d, (x, 28, x + tw, 64), NAVY if on else WHITE, radius=4, outline=LINE)
        d.text((x + 14, 34), t, font=f["small_b"], fill=WHITE if on else INK)
        x += tw + 10
    return im, d


def metric_card(d, x, y, w, label, value, f, accent=NAVY):
    rounded(d, (x, y, x + w, y + 110), WHITE, radius=6, outline=LINE)
    d.rectangle((x, y, x + 6, y + 110), fill=accent)
    d.text((x + 22, y + 18), label, font=f["tiny"], fill=MUTED)
    d.text((x + 22, y + 46), str(value), font=f["h1"], fill=NAVY)


def badge(d, x, y, label, f, fill=CRIMSON):
    tw = int(d.textlength(label.upper(), font=f["badge"])) + 20
    rounded(d, (x, y, x + tw, y + 28), fill, radius=3)
    d.text((x + 10, y + 5), label.upper(), font=f["badge"], fill=WHITE)
    return tw


def bars(d, x, y, w, h, series: list[tuple[str, int, tuple]], f):
    mx = max((v for _, v, _ in series), default=1) or 1
    bw = 70
    gap = (w - bw * len(series)) / max(1, len(series))
    for i, (label, val, color) in enumerate(series):
        bx = x + i * (bw + gap) + gap / 2
        bh = int((val / mx) * (h - 48))
        rounded(d, (bx, y + h - 28 - bh, bx + bw, y + h - 28), color, radius=4)
        d.text((bx, y + h - 24), label, font=f["tiny"], fill=MUTED)
        lab = str(val)
        d.text((bx + 18, y + h - 28 - bh - 26), lab, font=f["small_b"], fill=INK)


def strip_md(text: str) -> str:
    return (text or "").replace("**", "").replace("`", "").replace(">", "")


def ffmpeg_bin() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        found = shutil.which("ffmpeg")
        if not found:
            raise RuntimeError("ffmpeg not found")
        return found


def speak(path: Path, text: str) -> float:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import pyttsx3

        engine = pyttsx3.init()
        for v in engine.getProperty("voices"):
            name = (v.name or "").lower()
            if "zira" in name or "female" in name:
                engine.setProperty("voice", v.id)
                break
        engine.setProperty("rate", 168)
        engine.setProperty("volume", 1.0)
        engine.save_to_file(text, str(path))
        engine.runAndWait()
        engine.stop()
    except Exception as exc:
        print("TTS failed, using silence:", exc)
        # 1 second silent wav
        with wave.open(str(path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(22050)
            wf.writeframes(b"\x00\x00" * 22050)
    with wave.open(str(path), "r") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate() or 22050
        return max(3.0, frames / float(rate) + 0.35)


def encode_segment(ffmpeg: str, png: Path, wav: Path, mp4: Path, duration: float) -> None:
    cmd = [
        ffmpeg,
        "-y",
        "-loop",
        "1",
        "-i",
        str(png),
        "-i",
        str(wav),
        "-c:v",
        "libx264",
        "-tune",
        "stillimage",
        "-pix_fmt",
        "yuv420p",
        "-vf",
        "fps=30,format=yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-t",
        f"{duration:.2f}",
        str(mp4),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def concat(ffmpeg: str, segments: list[Path], dest: Path) -> None:
    lst = dest.parent / "concat.txt"
    lst.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in segments), encoding="utf-8")
    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(lst),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        str(dest),
    ]
    subprocess.run(cmd, check=True)


def scene_title(f) -> Image.Image:
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    d.text((80, 280), "Aether 360 Copilot", font=f["hero"], fill=WHITE)
    d.text((80, 370), "Patient / Member 360  ·  Cited clinical & regulatory Q&A", font=f["h2"], fill=TEAL)
    rounded(d, (80, 460, 520, 508), RUST, radius=4)
    d.text((100, 470), "FULLY SYNTHETIC CORPUS  ·  NO PHI", font=f["small_b"], fill=WHITE)
    d.text((80, 560), "Snowflake CoCo hackathon  ·  Care + life sciences", font=f["body"], fill=TEAL)
    return im


def scene_problem(f) -> Image.Image:
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    d.text((80, 60), "The silo problem", font=f["h1"], fill=NAVY)
    d.text((80, 120), "Care and life sciences teams work across disconnected systems.", font=f["body"], fill=INK)
    cards = [
        (80, "EHR", "Encounters, meds, labs, notes\nClinic keys PAT-*"),
        (680, "Claims", "Coverage, medical & pharmacy\nPayer keys MEM-*"),
        (1280, "Documents", "Labels, NCD, PA, safety alerts\nDense unstructured text"),
    ]
    for x, title, body in cards:
        rounded(d, (x, 220, x + 540, 520), WHITE, radius=8, outline=LINE)
        d.rectangle((x, 220, x + 8, 520), fill=NAVY)
        d.text((x + 36, 250), title, font=f["h2"], fill=NAVY)
        y = 320
        for line in body.split("\n"):
            d.text((x + 36, y), line, font=f["body"], fill=INK)
            y += 40
    d.text((80, 580), "They cannot audit an opaque “risk 0.81”. They need sources.", font=f["h2"], fill=RUST)
    return im


def scene_architecture(f) -> Image.Image:
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    d.text((80, 50), "What we built", font=f["h1"], fill=NAVY)
    steps = [
        ("Bronze", "Siloed EHR + claims\n+ document stage"),
        ("Silver DT", "Conform, parse,\nchunk 1800 / 300"),
        ("Gold 360", "MEMBER_360 +\nATRI factor ledger"),
        ("Retrieve", "Analyst + two\nCortex Search indexes"),
        ("Copilot", "Cited answer\nor abstain"),
    ]
    for i, (title, body) in enumerate(steps):
        x = 70 + i * 370
        rounded(d, (x, 180, x + 330, 430), WHITE, radius=8, outline=LINE)
        d.rectangle((x, 180, x + 330, 188), fill=NAVY)
        d.text((x + 24, 220), f"{i+1}. {title}", font=f["h3"], fill=NAVY)
        y = 280
        for line in body.split("\n"):
            d.text((x + 24, y), line, font=f["body"], fill=INK)
            y += 36
        if i < len(steps) - 1:
            d.polygon([(x + 338, 300), (x + 358, 312), (x + 338, 324)], fill=RUST)
    d.text((80, 500), "ATRI is a published point system. Python and SQL match. Unit tested.", font=f["body"], fill=INK)
    d.text((80, 550), "Reusable CoCo skills: $patient-360-builder  $cited-clinical-qa  $synthetic-care-data", font=f["small"], fill=MUTED)
    return im


def scene_population(bundle, f) -> Image.Image:
    im, d = chrome("Population", "36 synthetic members\nAs of 2026-08-31", f)
    rows = bundle.member_360
    vh = sum(1 for r in rows if r["atri_tier"] == "Very High")
    high = sum(1 for r in rows if r["atri_tier"] == "High")
    readmit = sum(1 for r in rows if r["readmit_30d_flag"])
    metric_card(d, 360, 100, 280, "Members", len(rows), f)
    metric_card(d, 660, 100, 280, "Very High ATRI", vh, f, CRIMSON)
    metric_card(d, 960, 100, 280, "High ATRI", high, f, RUST)
    metric_card(d, 1260, 100, 280, "30-day readmit", readmit, f, GOLD)
    rounded(d, (360, 250, 1000, 900), WHITE, radius=8, outline=LINE)
    d.text((384, 270), "Panel by ATRI tier", font=f["h3"], fill=NAVY)
    counts = {
        "Very High": vh,
        "High": high,
        "Moderate": sum(1 for r in rows if r["atri_tier"] == "Moderate"),
        "Low": sum(1 for r in rows if r["atri_tier"] == "Low"),
    }
    bars(
        d,
        400,
        330,
        560,
        500,
        [
            ("V.High", counts["Very High"], CRIMSON),
            ("High", counts["High"], RUST),
            ("Mod", counts["Moderate"], GOLD),
            ("Low", counts["Low"], GREEN),
        ],
        f,
    )
    rounded(d, (1040, 250, 1840, 900), WHITE, radius=8, outline=LINE)
    d.text((1064, 270), "Highest ATRI members", font=f["h3"], fill=NAVY)
    y = 330
    for r in rows[:7]:
        d.text((1064, y), r["member_id"], font=f["code"], fill=MUTED)
        d.text((1220, y), r["full_name"][:22], font=f["small_b"], fill=INK)
        d.text((1520, y), str(r["atri_score"]), font=f["small_b"], fill=NAVY)
        badge(d, 1600, y - 2, r["atri_tier"], f, {"Very High": CRIMSON, "High": RUST, "Moderate": GOLD, "Low": GREEN}[r["atri_tier"]])
        y += 72
    return im


def scene_member360(bundle, f) -> Image.Image:
    im, d = chrome("Member 360", "Focus\nMEM-10007\nJordan Hale", f)
    row = bundle.member("MEM-10007")
    rounded(d, (360, 96, 1840, 230), NAVY, radius=6)
    d.text((384, 112), row["full_name"], font=f["h1"], fill=WHITE)
    d.text((384, 170), f"{row['member_id']}  ·  EHR {row['patient_id']}  ·  {row['age_years']}y  ·  {row['panel']}  ·  {row['line_of_business']}", font=f["small"], fill=TEAL)
    badge(d, 1500, 130, f"ATRI {row['atri_score']}  {row['atri_tier']}", f, CRIMSON)
    d.text((384, 250), "ATRI is a transparent rules index — not a mortality prediction. Each row cites a table and key.", font=f["small"], fill=MUTED)
    factors = sorted(
        [x for x in bundle.atri_factors if x["member_id"] == "MEM-10007"],
        key=lambda z: -z["points"],
    )
    headers = ["Factor", "Pts", "Source", "Evidence"]
    xs = [380, 700, 780, 1180]
    y = 300
    for htxt, x in zip(headers, xs):
        d.text((x, y), htxt, font=f["tiny"], fill=MUTED)
    y = 340
    for fac in factors[:8]:
        rounded(d, (360, y - 6, 1840, y + 46), WHITE, radius=4, outline=LINE)
        d.text((380, y + 8), fac["factor_code"], font=f["code"], fill=NAVY)
        d.text((710, y + 8), f"+{fac['points']}", font=f["small_b"], fill=RUST)
        d.text((780, y + 10), fac["source_object"][:28], font=f["tiny"], fill=MUTED)
        ev = fac["evidence"][:70]
        d.text((1180, y + 8), ev, font=f["small"], fill=INK)
        y += 62
    return im


def scene_qa(question: str, result: dict, tab_note: str, f) -> Image.Image:
    im, d = chrome("Cited copilot", tab_note, f)
    rounded(d, (360, 96, 1840, 190), WHITE, radius=6, outline=LINE)
    q_lines = wrap(d, "Q  " + question, f["body_b"], 1400)
    d.text((384, 118), q_lines[0], font=f["body_b"], fill=NAVY)
    kind = result["response_type"]
    fill = GREEN if kind == "cited" else (CRIMSON if kind == "refuse" else GOLD)
    badge(d, 360, 210, kind, f, fill)
    d.text((460, 212), f"confidence {result.get('confidence') or 'n/a'}  ·  {len(result.get('sources') or [])} sources", font=f["small"], fill=MUTED)

    body = strip_md(result["answer"]).replace("\n\n", "\n")
    y = 260
    for para in body.split("\n"):
        para = para.strip()
        if not para:
            continue
        for line in wrap(d, para, f["small"], 1440)[:4]:
            d.text((380, y), line, font=f["small"], fill=INK)
            y += 26
            if y > 560:
                break
        y += 8
        if y > 560:
            break

    d.text((380, 580), "Source evidence", font=f["h3"], fill=NAVY)
    y = 620
    srcs = result.get("sources") or []
    docs = [s for s in srcs if s.get("source_type") == "document"]
    rest = [s for s in srcs if s.get("source_type") != "document"]
    ordered = (docs + rest)[:4]
    for i, src in enumerate(ordered, start=1):
        rounded(d, (360, y, 1840, y + 78), WHITE, radius=4, outline=LINE)
        d.text((380, y + 8), f"[{i}] {src.get('source_type')}  ·  {src.get('object')}  ·  {src.get('key')}", font=f["code"], fill=NAVY)
        snip = strip_md(src.get("snippet") or src.get("claim") or "")[:110]
        d.text((380, y + 40), snip, font=f["tiny"], fill=MUTED)
        y += 88
    return im


def scene_coco(f) -> Image.Image:
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    d.text((80, 50), "CoCo across the full lifecycle", font=f["h1"], fill=NAVY)
    d.text((80, 110), "Judges can replay each phase from coco/prompts/ — not a one-shot script dump.", font=f["body"], fill=INK)
    phases = [
        ("1 Planning", "Explore the silo problem.\nDraft ontology, ATRI catalog,\nand citation contract first."),
        ("2 Development", "Skills generate data,\nDynamic Tables, Search,\nsemantic view, and agent."),
        ("3 Execution", "Nightly ATRI snapshot task.\nAgent chat + Streamlit.\nMCP care-gap tickets."),
        ("4 Testing", "Eval questions, abstain,\nrefuse real-PHI, and\nwarfarin NSAID citations."),
    ]
    for i, (title, body) in enumerate(phases):
        x = 80 + (i % 4) * 460
        y = 200
        rounded(d, (x, y, x + 430, y + 420), WHITE, radius=8, outline=LINE)
        d.rectangle((x, y, x + 430, y + 8), fill=NAVY if i < 3 else RUST)
        d.text((x + 28, y + 40), title, font=f["h2"], fill=NAVY)
        yy = y + 120
        for line in body.split("\n"):
            d.text((x + 28, yy), line, font=f["body"], fill=INK)
            yy += 40
    d.text((80, 680), "Plugin aether-360  ·  MCP aether-care-ops  ·  hook blocks DROP DATABASE / SSN literals", font=f["small"], fill=MUTED)
    return im


def scene_end(f) -> Image.Image:
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    d.text((80, 300), "Cited evidence, or abstain.", font=f["hero"], fill=WHITE)
    d.text((80, 400), "Never an opaque score. Never a guessed coverage rule.", font=f["h2"], fill=TEAL)
    d.text((80, 500), "Aether Care Alliance  ·  synthetic only  ·  Snowflake CoCo", font=f["body"], fill=TEAL)
    d.text((80, 620), "Local app:  streamlit run app/streamlit_app.py", font=f["code"], fill=WHITE)
    d.text((80, 660), "Hero member:  MEM-10007 Jordan Hale", font=f["code"], fill=WHITE)
    return im


def main() -> None:
    for p in (FRAMES, AUDIO, SEGS):
        p.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    f = fonts()
    bundle = load_bundle()
    q1 = "Is ibuprofen safe given MEM-10007's anticoagulant?"
    q2 = "River Chen is on an SGLT2. What does the safety communication require?"
    q3 = "Does Ellis Navarro meet PA-GLP1-2026 diabetes criteria?"
    q4 = "What is Elon Musk's A1c in production EHR?"
    r1 = answer_question(q1, bundle)
    r2 = answer_question(q2, bundle)
    r3 = answer_question(q3, bundle)
    r4 = answer_question(q4, bundle)
    hale = bundle.member("MEM-10007")

    scenes = [
        (
            "title",
            scene_title(f),
            "Aether 360 Copilot. A patient and member 360 with cited clinical and regulatory answers. Fully synthetic data only.",
        ),
        (
            "problem",
            scene_problem(f),
            "Care teams work across siloed E H R, claims, and dense documents. They need one picture of the member, and answers they can audit.",
        ),
        (
            "arch",
            scene_architecture(f),
            "We unify those silos, score risk with transparent A T R I rules, and retrieve notes and policies. If evidence is missing, the copilot abstains.",
        ),
        (
            "pop",
            scene_population(bundle, f),
            f"On a synthetic panel of {len(bundle.member_360)} members, A T R I flags outreach. {hale['full_name']} is very high risk, score {hale['atri_score']}.",
        ),
        (
            "m360",
            scene_member360(bundle, f),
            "Open Jordan Hale. Every point is a fired rule with a source table and key. Readmission, heart failure, warfarin plus ibuprofen. This is not a black box.",
        ),
        (
            "qa1",
            scene_qa(q1, r1, "MEM-10007\nWarfarin + NSAID", f),
            "Is ibuprofen safe with her anticoagulant? The copilot cites the medication row, the dental note, and the synthetic warfarin label on N S A I D bleeding risk.",
        ),
        (
            "qa2",
            scene_qa(q2, r2, "MEM-10014\nSGLT2 safety", f),
            "River Chen is on an S G L T 2. The safety communication and the E D note both require holding the drug during vomiting and checking ketones.",
        ),
        (
            "qa3",
            scene_qa(q3, r3, "MEM-10031\nGLP-1 prior auth", f),
            "Ellis Navarro's G L P 1 request is checked against prior auth criteria: diabetes, A1c 8.1, metformin trial. Not obesity-only coverage.",
        ),
        (
            "refuse",
            scene_qa(q4, r4, "Guardrail\nRefuse real PHI", f),
            "Ask for a real person's production record, and the copilot refuses. No evidence, no answer.",
        ),
        (
            "coco",
            scene_coco(f),
            "Snowflake CoCo runs the full lifecycle: planning, pipelines, a nightly risk snapshot, and citation tests. Skills are reusable as the Aether 360 plugin.",
        ),
        (
            "end",
            scene_end(f),
            "Aether 360. Cited evidence, or abstain.",
        ),
    ]

    ffmpeg = ffmpeg_bin()
    segments: list[Path] = []
    for i, (name, image, narration) in enumerate(scenes):
        png = FRAMES / f"{i:02d}_{name}.png"
        wav = AUDIO / f"{i:02d}_{name}.wav"
        mp4 = SEGS / f"{i:02d}_{name}.mp4"
        draw_caption(image, narration.replace(" A T R I", " ATRI").replace(" E H R", " EHR").replace(" N S A I D", " NSAID").replace(" S G L T 2", " SGLT2").replace(" G L P 1", " GLP-1").replace(" E D ", " ED "), f)
        # Caption uses readable acronyms; TTS uses spaced letters for pronunciation.
        image.save(png)
        dur = speak(wav, narration)
        encode_segment(ffmpeg, png, wav, mp4, dur)
        segments.append(mp4)
        print(f"[{i+1}/{len(scenes)}] {name}  {dur:.1f}s")

    dest = OUT_DIR / "Aether360-demo.mp4"
    concat(ffmpeg, segments, dest)
    size_mb = dest.stat().st_size / (1024 * 1024)
    print(f"Wrote {dest} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
