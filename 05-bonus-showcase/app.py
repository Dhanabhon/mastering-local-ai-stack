#!/usr/bin/env python3
"""
CineLocal Studio — AI Storyboard & Pitch Deck Director (Showcase Project)
==========================================================================
โปรเจกต์ตัวอย่างสำหรับศึกษาต่อยอดหลังจบคลาส "Mastering Local AI Stack 2026"
ใช้เฉพาะไลบรารีที่ติดตั้งไว้แล้วใน requirements.txt (requests, openai, pandas, Pillow)

การเชื่อมโยงความรู้จากทั้ง 4 โมดูลในห้องเรียน:
- Module 1: ตรวจสอบสถานะเซิร์ฟเวอร์ (Health Check) และจัดเก็บตารางข้อมูลสรุปด้วย pandas
- Module 2: สั่ง LM Studio (:1234) ตีความไอเดียภาษาไทย 1 บรรทัดเป็น JSON Storyboard 3 ฉาก
- Module 3: โหลดไฟล์เวิร์กโฟลว์ sd15_txt2img_api.json และแก้ไขโหนด "6", "7", "3" อัตโนมัติ
- Module 4: ส่งคิวเรนเดอร์ทีละฉากเข้า ComfyUI (:8188) เพื่อคุมงบ VRAM ไม่ให้เกิน 6GB (RTX 3050 Safe)
            พร้อมส่งออกเป็นไฟล์ HTML Pitch Deck ที่เปิดดูได้ทันที

วิธีรัน:
1) รันแบบสร้างไฟล์ Storyboard HTML Pitch Deck ทันทีผ่าน Command Line:
   python 05-bonus-showcase/app.py --idea "ตลาดน้ำไซเบอร์กรุงเทพปี 2088 ที่หุ่นยนต์ชงชาไทย" --style cyberpunk

2) รันแบบเปิด Web Studio Server ที่พอร์ต 8080:
   python 05-bonus-showcase/app.py --serve
"""

from __future__ import annotations

import argparse
import base64
import copy
import json
import random
import time
import urllib.parse
import urllib.request
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration & Paths
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
WORKFLOW_PATH = ROOT_DIR / "03-comfyui-workflows" / "sd15_txt2img_api.json"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"

LM_STUDIO_BASE_URL = "http://localhost:1234/v1"
COMFYUI_BASE_URL = "http://127.0.0.1:8188"

STYLE_PRESETS: dict[str, dict[str, Any]] = {
    "cyberpunk": {
        "name": "Cyberpunk Neon",
        "cfg": 7.5,
        "steps": 20,
        "suffix": (
            "cyberpunk neon lighting, rain-slicked reflections, volumetric teal and amber glow, "
            "35mm anamorphic cinema lens, ultra-detailed, masterpiece"
        ),
        "negative": "blurry, low quality, daylight, flat lighting, watermark, text, deformed hands",
    },
    "cinematic": {
        "name": "Golden Hour Film",
        "cfg": 7.0,
        "steps": 20,
        "suffix": (
            "golden hour sunlight, atmospheric morning mist, Kodak Portra 400 film grain, "
            "50mm prime lens, shallow depth of field, cinematic composition, photorealistic"
        ),
        "negative": "blurry, neon, cartoon, oversaturated, watermark, text, ugly, low resolution",
    },
    "watercolor": {
        "name": "Ghibli Anime Art",
        "cfg": 6.5,
        "steps": 20,
        "suffix": (
            "Studio Ghibli inspired hand-painted background art, lush gouache and watercolor textures, "
            "warm nostalgic lighting, expressive clouds, whimsical detail"
        ),
        "negative": "photorealistic, 3d render, gritty, dark horror, blurry, watermark, text",
    },
    "isometric": {
        "name": "Isometric 3D Box",
        "cfg": 8.0,
        "steps": 22,
        "suffix": (
            "isometric 3D miniature cutaway diorama, tilt-shift macro lens, Octane render, "
            "soft studio global illumination, clay and glass materials, intricate miniature details"
        ),
        "negative": "first person view, blurry, flat 2d, messy background, watermark, text, cropped",
    },
}

DIRECTOR_SYSTEM_PROMPT = """You are an award-winning AI Film & Storyboard Director.
The user will give you a short concept in Thai and a visual style preset.
Break the concept into a cohesive 3-scene storyboard and return ONLY valid JSON matching this schema:
{
  "project_title_th": "ชื่อโปรเจกต์ภาษาไทยที่ฟังดูน่าตื่นเต้น",
  "project_title_en": "ENGLISH PROJECT TITLE",
  "logline_th": "คำโปรยสรุปแนวคิดหลักภาษาไทย 1-2 ประโยค",
  "color_palette": ["#0F172A", "#00F5D4", "#FF7B00", "#F43F5E"],
  "scenes": [
    {
      "scene_number": 1,
      "title_th": "ชื่อฉากที่ 1 ภาษาไทย (Establishing Shot)",
      "camera_angle": "Wide Establishing Shot • 24mm Lens",
      "narration_th": "บทบรรยายประกอบฉากที่ 1 ภาษาไทย",
      "sd_positive_prompt": "detailed English visual prompt for Stable Diffusion 1.5 describing Scene 1",
      "sd_negative_prompt": "blurry, low quality, watermark, text, deformed"
    },
    {
      "scene_number": 2,
      "title_th": "ชื่อฉากที่ 2 ภาษาไทย (Action / Character Shot)",
      "camera_angle": "Medium Tracking Shot • 50mm Lens",
      "narration_th": "บทบรรยายประกอบฉากที่ 2 ภาษาไทย",
      "sd_positive_prompt": "detailed English visual prompt for Stable Diffusion 1.5 describing Scene 2",
      "sd_negative_prompt": "blurry, low quality, watermark, text, deformed"
    },
    {
      "scene_number": 3,
      "title_th": "ชื่อฉากที่ 3 ภาษาไทย (Climax / Hero Close-Up)",
      "camera_angle": "Macro Hero Close-Up • 85mm Lens",
      "narration_th": "บทบรรยายประกอบฉากที่ 3 ภาษาไทย",
      "sd_positive_prompt": "detailed English visual prompt for Stable Diffusion 1.5 describing Scene 3",
      "sd_negative_prompt": "blurry, low quality, watermark, text, deformed"
    }
  ]
}
Do not wrap the response in markdown code fences. Return raw JSON only."""


# ---------------------------------------------------------------------------
# Module 1 Building Block: Server Health Check
# ---------------------------------------------------------------------------
def check_local_ai_stack() -> dict[str, bool]:
    """ตรวจสอบสถานะของ LM Studio (:1234) และ ComfyUI (:8188) ก่อนเริ่มรันไปป์ไลน์"""
    status = {"lm_studio": False, "comfyui": False}
    try:
        r1 = requests.get(f"{LM_STUDIO_BASE_URL}/models", timeout=3)
        status["lm_studio"] = r1.status_code == 200
    except requests.RequestException:
        pass

    try:
        r2 = requests.get(f"{COMFYUI_BASE_URL}/system_stats", timeout=3)
        status["comfyui"] = r2.status_code == 200
    except requests.RequestException:
        pass

    return status


# ---------------------------------------------------------------------------
# Module 2 Building Block: LM Studio Structured JSON Storyboard Director
# ---------------------------------------------------------------------------
def generate_storyboard_json(thai_idea: str, style_key: str = "cyberpunk") -> dict[str, Any]:
    """ส่งแนวคิดภาษาไทยให้ LM Studio แตกเป็น JSON 3 ฉาก พร้อมมุมกล้องและ SD 1.5 Prompt"""
    style = STYLE_PRESETS.get(style_key, STYLE_PRESETS["cyberpunk"])
    client = OpenAI(base_url=LM_STUDIO_BASE_URL, api_key="lm-studio")

    response = client.chat.completions.create(
        model="local-model",
        messages=[
            {"role": "system", "content": DIRECTOR_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"แนวคิดภาษาไทย: {thai_idea}\n"
                    f"สไตล์ภาพ (Visual Style): {style['name']} ({style['suffix']})"
                ),
            },
        ],
        temperature=0.45,
        max_tokens=1000,
    )

    raw_text = response.choices[0].message.content.strip()
    start_idx = raw_text.find("{")
    end_idx = raw_text.rfind("}") + 1
    if start_idx == -1 or end_idx <= 0:
        raise ValueError(f"LLM did not return valid JSON:\n{raw_text}")

    storyboard = json.loads(raw_text[start_idx:end_idx])
    storyboard["style"] = style_key

    base_seed = random.randint(100000, 899999)
    for idx, scene in enumerate(storyboard.get("scenes", []), start=1):
        scene["scene_number"] = idx
        scene["seed"] = base_seed + idx
        if style["suffix"] not in scene.get("sd_positive_prompt", ""):
            scene["sd_positive_prompt"] = f"{scene.get('sd_positive_prompt', '')}, {style['suffix']}"
        if not scene.get("sd_negative_prompt"):
            scene["sd_negative_prompt"] = style["negative"]

    return storyboard


# ---------------------------------------------------------------------------
# Module 3 & 4 Building Block: ComfyUI Workflow Mutation & Sequential Queue
# ---------------------------------------------------------------------------
def render_scene_image(workflow_template: dict[str, Any], scene: dict[str, Any], style_key: str) -> bytes:
    """แทนค่า Prompt ลงในโหนด ComfyUI แล้วส่งคิวเรนเดอร์ภาพ 512x512 ทีละฉาก (ปลอดภัยต่อ VRAM 6GB)"""
    style = STYLE_PRESETS.get(style_key, STYLE_PRESETS["cyberpunk"])
    wf = copy.deepcopy(workflow_template)

    # Node "6": Positive Prompt | Node "7": Negative Prompt | Node "3": KSampler
    wf["6"]["inputs"]["text"] = scene["sd_positive_prompt"]
    wf["7"]["inputs"]["text"] = scene["sd_negative_prompt"]
    wf["3"]["inputs"]["seed"] = int(scene.get("seed", random.randint(1, 999999)))
    wf["3"]["inputs"]["steps"] = int(style["steps"])
    wf["3"]["inputs"]["cfg"] = float(style["cfg"])
    wf["9"]["inputs"]["filename_prefix"] = f"CineLocal_Scene0{scene['scene_number']}"

    res = requests.post(f"{COMFYUI_BASE_URL}/prompt", json={"prompt": wf}, timeout=10)
    res.raise_for_status()
    prompt_id = res.json()["prompt_id"]

    while True:
        hist_res = requests.get(f"{COMFYUI_BASE_URL}/history/{prompt_id}", timeout=5)
        hist_data = hist_res.json()
        if prompt_id in hist_data:
            outputs = hist_data[prompt_id]["outputs"]
            for node_output in outputs.values():
                if "images" in node_output and node_output["images"]:
                    img_meta = node_output["images"][0]
                    params = urllib.parse.urlencode(
                        {
                            "filename": img_meta["filename"],
                            "subfolder": img_meta["subfolder"],
                            "type": img_meta["type"],
                        }
                    )
                    view_url = f"{COMFYUI_BASE_URL}/view?{params}"
                    with urllib.request.urlopen(view_url) as img_stream:
                        return img_stream.read()
        time.sleep(1.0)


# ---------------------------------------------------------------------------
# HTML Pitch Deck Exporter
# ---------------------------------------------------------------------------
def build_pitch_deck_html(storyboard: dict[str, Any], output_file: Path) -> Path:
    """สร้างไฟล์ HTML Storyboard Pitch Deck พร้อมฝังภาพ Base64 เพื่อเปิดดูได้ทุกเครื่อง"""
    cards_html = []
    for sc in storyboard["scenes"]:
        img_tag = (
            f'<img src="{sc["image_data_url"]}" alt="{sc["title_th"]}" style="width:100%;aspect-ratio:1/1;object-fit:cover;display:block;" />'
            if sc.get("image_data_url")
            else '<div style="aspect-ratio:1/1;background:#121714;display:grid;place-items:center;color:#69b98e;">[ComfyUI Offline — Prompt Ready]</div>'
        )
        cards_html.append(
            f"""
            <article class="card">
              {img_tag}
              <div class="card-body">
                <div class="meta">SCENE 0{sc['scene_number']} • {sc.get('camera_angle', '35mm Lens')} • SEED {sc.get('seed', 42)}</div>
                <h3>{sc['title_th']}</h3>
                <p>{sc['narration_th']}</p>
                <div class="prompt"><strong>SD 1.5 Positive Prompt:</strong><br/>{sc['sd_positive_prompt']}</div>
              </div>
            </article>
            """
        )

    swatches = "".join(
        f'<span style="display:inline-block;width:20px;height:20px;border-radius:4px;background:{c};border:1px solid #323d35;"></span>'
        for c in storyboard.get("color_palette", ["#2e7d5b", "#69b98e"])
    )

    html = f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8" />
  <title>{storyboard['project_title_th']} — CineLocal Pitch Deck</title>
  <link href="https://fonts.googleapis.com/css2?family=Google+Sans+Thai:wght@400;600;700&family=JetBrains+Mono&display=swap" rel="stylesheet" />
  <style>
    body {{ font-family: 'Google Sans Thai', sans-serif; background: #181d19; color: #f7f6f2; margin: 0; padding: 2.5rem; line-height: 1.6; }}
    .wrap {{ max-width: 1120px; margin: 0 auto; }}
    .head {{ border-bottom: 1px solid #323d35; padding-bottom: 1.25rem; margin-bottom: 1.75rem; display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 1rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(310px, 1fr)); gap: 1.25rem; }}
    .card {{ background: #1f2621; border: 1px solid #323d35; border-radius: 14px; overflow: hidden; }}
    .card-body {{ padding: 1.15rem; }}
    .meta {{ font-size: 12px; font-weight: 700; color: #69b98e; }}
    h3 {{ margin: 0.35rem 0 0.5rem 0; font-size: 18px; }}
    .prompt {{ font-family: 'JetBrains Mono', monospace; font-size: 11.5px; color: #acb3a8; background: #121714; padding: 0.65rem; border-radius: 8px; margin-top: 0.75rem; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="head">
      <div>
        <div style="font-size:12px;font-weight:700;color:#69b98e;">CINELOCAL STUDIO • MASTERING LOCAL AI STACK 2026</div>
        <h1 style="margin:0.25rem 0;">{storyboard['project_title_th']}</h1>
        <div style="font-family:'JetBrains Mono',monospace;font-size:13px;color:#acb3a8;">{storyboard.get('project_title_en', '')}</div>
        <p style="margin:0.6rem 0 0 0;max-width:75ch;">{storyboard['logline_th']}</p>
      </div>
      <div style="display:flex;gap:6px;align-items:center;">{swatches}</div>
    </div>
    <div class="grid">
      {''.join(cards_html)}
    </div>
  </div>
</body>
</html>"""

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html, encoding="utf-8")
    return output_file


# ---------------------------------------------------------------------------
# Full CLI Execution Flow
# ---------------------------------------------------------------------------
def run_cli_pipeline(idea: str, style_key: str) -> None:
    print("=" * 72)
    print("CineLocal Studio — Full-Stack Local AI Storyboard Director")
    print("=" * 72)

    health = check_local_ai_stack()
    print(f"[Module 1 Health Check] LM Studio (:1234) = {health['lm_studio']} | ComfyUI (:8188) = {health['comfyui']}")

    if not health["lm_studio"]:
        print("\n[!] ไม่พบ LM Studio ที่พอร์ต 1234 กรุณาเปิด Local Server ก่อนรันสคริปต์นี้")
        print("    หรือเปิดไฟล์ docs/showcase.html บนเบราว์เซอร์เพื่อทดลองโหมด Instant Simulation ได้ทันที!")
        return

    print(f"\n[Module 2 LM Studio] กำลังสั่ง LLM แตกไอเดียเป็น Storyboard 3 ฉาก (สไตล์: {style_key})...")
    storyboard = generate_storyboard_json(idea, style_key)
    print(f"  -> ชื่อโปรเจกต์: {storyboard['project_title_th']}")
    print(f"  -> คำโปรย: {storyboard['logline_th']}")

    workflow_template = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    for scene in storyboard["scenes"]:
        idx = scene["scene_number"]
        print(f"\n[Module 3 & 4 ComfyUI] ฉากที่ {idx}/3: {scene['title_th']}")
        print(f"  -> Camera: {scene.get('camera_angle')}")
        print(f"  -> Prompt: {scene['sd_positive_prompt'][:90]}...")

        if health["comfyui"]:
            t0 = time.perf_counter()
            img_bytes = render_scene_image(workflow_template, scene, style_key)
            elapsed = round(time.perf_counter() - t0, 2)
            img_file = OUTPUT_DIR / f"scene_0{idx}.png"
            img_file.write_bytes(img_bytes)
            b64 = base64.b64encode(img_bytes).decode("ascii")
            scene["image_data_url"] = f"data:image/png;base64,{b64}"
            print(f"  -> วาดภาพ 512x512 สำเร็จใน {elapsed} วินาที ({img_file.name})")
        else:
            elapsed = 0.0
            print("  -> [ข้ามการวาดภาพเนื่องจาก ComfyUI (:8188) ปิดอยู่]")

        rows.append(
            {
                "scene": idx,
                "title_th": scene["title_th"],
                "camera": scene.get("camera_angle", ""),
                "seed": scene["seed"],
                "render_sec": elapsed,
            }
        )

    # สรุปผลด้วย Pandas DataFrame (ต่อยอดจาก Module 1)
    df = pd.DataFrame(rows)
    print("\n[สรุปตารางการผลิต Storyboard ด้วย Pandas DataFrame]")
    print(df.to_string(index=False))

    html_out = build_pitch_deck_html(storyboard, OUTPUT_DIR / "storyboard_pitch_deck.html")
    json_out = OUTPUT_DIR / "storyboard_data.json"
    json_out.write_text(json.dumps(storyboard, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 72)
    print(f"สำเร็จครบทุกขั้นตอน! เปิดไฟล์ Pitch Deck ได้ที่:\n  {html_out}")
    print("=" * 72)


# ---------------------------------------------------------------------------
# Local Web Studio Server (--serve)
# ---------------------------------------------------------------------------
class ShowcaseRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT_DIR / "docs"), **kwargs)


def run_web_server(port: int = 8080) -> None:
    server = HTTPServer(("127.0.0.1", port), ShowcaseRequestHandler)
    print(f"เปิด CineLocal Studio Web Demo ที่: http://localhost:{port}/showcase.html")
    print("กด Ctrl+C เพื่อปิดเซิร์ฟเวอร์")
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CineLocal Studio — Local AI Storyboard Director")
    parser.add_argument(
        "--idea",
        type=str,
        default="ตลาดน้ำอัจฉริยะในกรุงเทพปี 2088 ที่เรือหางยาวขับเคลื่อนด้วยพลังงานแม่เหล็กและหุ่นยนต์ชงชาไทย",
        help="แนวคิดภาษาไทย 1 บรรทัดสำหรับสร้าง Storyboard 3 ฉาก",
    )
    parser.add_argument(
        "--style",
        type=str,
        default="cyberpunk",
        choices=list(STYLE_PRESETS.keys()),
        help="สไตล์ภาพของผู้กำกับ (cyberpunk, cinematic, watercolor, isometric)",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="เปิด Local Web Server เพื่อดูหน้าเว็บ docs/showcase.html ที่พอร์ต 8080",
    )
    args = parser.parse_args()

    if args.serve:
        run_web_server()
    else:
        run_cli_pipeline(args.idea, args.style)
