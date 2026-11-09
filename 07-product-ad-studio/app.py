#!/usr/bin/env python3
"""
AdCraft AI — Product Video Ad Studio (Showcase #3)
==================================================
เว็บแอปสร้างวิดีโอโฆษณาสินค้า (Product Commercial Video Generator)
โดยรับอินพุตเป็น "ภาพสินค้า 1–3 มุมมอง" + "ชุดตัวอย่าง Prompt โฆษณาสำเร็จรูป (6 Presets)"
ทำงานครอบ LM Studio (:1234) และ ComfyUI (:8188) บน Environment (.venv) เดิมของคอร์ส

ทำไมจึงออกแบบให้รับภาพสินค้า 1–3 ภาพ (3-Shot Commercial Formula)?
- ภาพที่ 1 (Hero / Front Packshot): ใช้ในฉากเปิด (0.0–1.0s) ดึงสายตาด้วยมุมตรงคมชัด
- ภาพที่ 2 (45° Angle / Texture Detail): ใช้ในฉากกลาง (1.0–2.0s) โชว์ดีเทลวัสดุและจุดเด่น
- ภาพที่ 3 (Lifestyle / Closing Packshot): ใช้ในฉากจบ (2.0–3.0s) ปิดท้ายพร้อมสโลแกนและป้าย Call-to-Action
*หมายเหตุ:* หากผู้ใช้อัปโหลดมาแค่ 1 ภาพ (หรือทดสอบโดยยังไม่อัปโหลดภาพ) ระบบจะสร้างมุมกล้อง
Dynamic Crop & Relighting ให้ครบทั้ง 3 ฉากโดยอัตโนมัติ

วิธีรันเปิด Web App (ค่าเริ่มต้นพอร์ต 8095):
    python 07-product-ad-studio/app.py
"""

from __future__ import annotations

import argparse
import base64
import copy
import csv
import io
import json
import math
import os
import random
import sys
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Auto-Switch to .venv Python if user forgot to activate .venv
# ---------------------------------------------------------------------------
STUDIO_DIR = Path(__file__).resolve().parent
ROOT_DIR = STUDIO_DIR.parent

def _maybe_reexec_in_venv() -> None:
    if os.environ.get("LOCAL_AI_VENV_ACTIVE") == "1":
        return
    candidates = [
        ROOT_DIR / ".venv" / "Scripts" / "python.exe",
        ROOT_DIR / ".venv" / "bin" / "python",
    ]
    for venv_py in candidates:
        if venv_py.exists() and Path(sys.executable).resolve() != venv_py.resolve():
            try:
                import PIL  # noqa: F401
            except ImportError:
                os.environ["LOCAL_AI_VENV_ACTIVE"] = "1"
                os.execv(str(venv_py), [str(venv_py), *sys.argv])

_maybe_reexec_in_venv()

try:
    from PIL import Image, ImageDraw, ImageEnhance
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ---------------------------------------------------------------------------
# Paths & Endpoints
# ---------------------------------------------------------------------------
TXT2IMG_WORKFLOW_PATH = ROOT_DIR / "03-comfyui-workflows" / "sd15_txt2img_api.json"
IMG2IMG_WORKFLOW_PATH = STUDIO_DIR / "workflows" / "sd15_product_img2img_api.json"
OUTPUT_DIR = STUDIO_DIR / "outputs"
HISTORY_CSV_PATH = OUTPUT_DIR / "ad_campaigns_history.csv"

LM_STUDIO_BASE_URL = "http://localhost:1234/v1"
COMFYUI_BASE_URL = "http://127.0.0.1:8188"


def _http_get_json(url: str, timeout: float = 3.0) -> dict[str, Any]:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_post_json(url: str, payload: dict[str, Any], timeout: float = 15.0) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_get_bytes(url: str, timeout: float = 15.0) -> bytes:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()

# ---------------------------------------------------------------------------
# 6 Ready-to-Use Commercial Prompt Presets
# ---------------------------------------------------------------------------
AD_PROMPT_PRESETS: dict[str, dict[str, str]] = {
    "coffee_beverage": {
        "title": "☕ กาแฟสกัดเย็น & เครื่องดื่มพรีเมียม (Cold Brew / Cafe Drink)",
        "product_name": "AURA Cold Brew Coffee",
        "selling_point": "สกัดเย็นนาน 18 ชั่วโมง หอมเมล็ดกาแฟอาราบิก้าแท้ สดชื่นไม่มีน้ำตาล",
        "cta_badge": "สั่งซื้อวันนี้ ลดทันที 20%",
        "scene_prompt": (
            "commercial product photography of a sleek cold brew coffee bottle on wet dark slate stone, "
            "splashing water droplets, crushed ice cubes, warm morning golden hour sunbeams through cafe window, "
            "cinematic rim lighting, shallow depth of field, 8kadvertising shot"
        ),
        "accent_hex": "#D97706",
    },
    "luxury_skincare": {
        "title": "🧴 สกินแคร์ & เซรั่มบำรุงผิว (Luxury Skincare / Serum)",
        "product_name": "LUMIÈRE Botanical Gold Serum",
        "selling_point": "เซรั่มเข้มข้นจากสารสกัดธรรมชาติ ฟื้นฟูผิวโกลว์ใสชุ่มชื้นใน 7 วัน",
        "cta_badge": "ทดลองขนาดพกพาเพียง 390.-",
        "scene_prompt": (
            "high-end cosmetic product photography on rippling crystal clear water surface, white botanical orchids, "
            "soft champagne gold caustic light reflections, luxury spa podium, macro studio lighting, photorealistic"
        ),
        "accent_hex": "#2E7D5B",
    },
    "tech_gadget": {
        "title": "🎧 หูฟังไร้สาย & แกดเจ็ตไอที (Tech Gadget / Wireless Audio)",
        "product_name": "NOVA Pulse ANC Earbuds",
        "selling_point": "ตัดเสียงรบกวนอัจฉริยะด้วย AI เบสแน่น คมชัดทุกมิติ แบตอึด 36 ชั่วโมง",
        "cta_badge": "ผ่อน 0% นาน 10 เดือน",
        "scene_prompt": (
            "futuristic commercial product shot on matte carbon fiber pedestal, neon cyan and emerald laser light streaks, "
            "floating holographic soundwaves, dark studio atmosphere, crisp rim lighting, octane render style"
        ),
        "accent_hex": "#0284C7",
    },
    "street_sneaker": {
        "title": "👟 รองเท้าผ้าใบ & สตรีทแวร์ (Streetwear Sneaker / Sport)",
        "product_name": "AERO-X Street Runner",
        "selling_point": "พื้นโฟมคาร์บอนเด้งรับแรงกระแทก น้ำหนักเบา ดีไซน์สตรีทลุยได้ทุกวัน",
        "cta_badge": "คอลเลกชันใหม่จำนวนจำกัด",
        "scene_prompt": (
            "dynamic commercial sneaker photography floating above wet urban asphalt street at night, "
            "glowing orange embers and mist, neon city bokeh reflections, dramatic low-angle hero lighting"
        ),
        "accent_hex": "#E11D48",
    },
    "gourmet_food": {
        "title": "🥐 ขนมโฮมเมด & อาหารพรีเมียม (Artisanal Bakery / Gourmet Snack)",
        "product_name": "MAISON Butter Croissant Box",
        "selling_point": "อบสดใหม่ทุกเช้าด้วยเนยแท้ฝรั่งเศส กรอบนอกนุ่มใน หอมกรุ่นจากเตา",
        "cta_badge": "ส่งด่วนถึงบ้านภายใน 1 ชม.",
        "scene_prompt": (
            "mouth-watering food commercial photography on rustic warm oak wood table, golden flaky crumbs, "
            "soft rising steam, morning sunlight through linen curtain, cozy artisanal bakery ambiance, 50mm lens"
        ),
        "accent_hex": "#B45309",
    },
    "minimal_watch": {
        "title": "⌚ นาฬิกาข้อมือ & แอ็กเซสซอรีหรู (Minimalist Watch / Jewelry)",
        "product_name": "CHRONO Verve Titanium",
        "selling_point": "ตัวเรือนไทเทเนียมเกรดการบิน กระจกแซฟไฟร์กันรอย กันน้ำลึก 100 เมตร",
        "cta_badge": "รับประกันศูนย์ไทย 5 ปีเต็ม",
        "scene_prompt": (
            "ultra-luxury timepiece product photography resting on black volcanic basalt rock, "
            "dramatic silver studio spotlight, subtle mist, razor-sharp metallic reflections, magazine ad quality"
        ),
        "accent_hex": "#4F46E5",
    },
}

ASPECT_DIMENSIONS: dict[str, tuple[int, int]] = {
    "9:16": (384, 640),  # TikTok / Reels / Shorts Vertical Ad (6GB VRAM Safe)
    "1:1": (512, 512),   # Instagram / Facebook Feed Square Ad
    "16:9": (640, 384),  # YouTube / Website Landscape Ad
}


# ---------------------------------------------------------------------------
# Environment Health Check
# ---------------------------------------------------------------------------
def inspect_servers() -> dict[str, Any]:
    info: dict[str, Any] = {
        "lm_studio_online": False,
        "lm_model": "",
        "comfyui_online": False,
    }
    try:
        r = _http_get_json(f"{LM_STUDIO_BASE_URL}/models", timeout=2.5)
        data = r.get("data", [])
        info["lm_studio_online"] = True
        info["lm_model"] = data[0].get("id", "Local LLM") if data else "Ready"
    except Exception:
        pass

    try:
        _http_get_json(f"{COMFYUI_BASE_URL}/system_stats", timeout=2.5)
        info["comfyui_online"] = True
    except Exception:
        pass

    return info


# ---------------------------------------------------------------------------
# Step 1: LM Studio Ad Copywriter (Creates 3-Act Headlines + Backdrop Prompt)
# ---------------------------------------------------------------------------
def generate_ad_copy_with_llm(
    product_name: str,
    selling_point: str,
    cta_badge: str,
    scene_prompt: str,
) -> dict[str, str]:
    """ให้ LM Studio แต่งคำโปรยโฆษณา 3 ฉาก (Hook -> Benefit -> CTA) และขัดเกลา English SD Prompt"""
    fallback_plan = {
        "hook_line": f"ใหม่! {product_name}",
        "benefit_line": selling_point[:55],
        "cta_line": cta_badge,
        "sd_backdrop_prompt": f"{scene_prompt}, masterpiece, best quality, commercial studio lighting",
    }

    try:
        models_res = _http_get_json(f"{LM_STUDIO_BASE_URL}/models", timeout=3.0)
        models_data = models_res.get("data", [])
        model_id = models_data[0].get("id", "local-model") if models_data else "local-model"

        sys_prompt = (
            "You are a creative director for short-form video ads (TikTok/Reels). "
            "Given a product name, selling point, and visual prompt, return ONLY valid JSON with keys: "
            '{"hook_line": "short punchy Thai hook (max 35 chars)", '
            '"benefit_line": "concise Thai key benefit (max 45 chars)", '
            '"cta_line": "short Thai call to action (max 30 chars)", '
            '"sd_backdrop_prompt": "refined English Stable Diffusion 1.5 studio background prompt (45 words)"}'
        )
        user_msg = (
            f"Product: {product_name}\n"
            f"Selling Point: {selling_point}\n"
            f"CTA: {cta_badge}\n"
            f"Visual Concept: {scene_prompt}"
        )
        res = _http_post_json(
            f"{LM_STUDIO_BASE_URL}/chat/completions",
            {
                "model": model_id,
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_msg},
                ],
                "temperature": 0.5,
                "max_tokens": 220,
            },
            timeout=20.0,
        )
        text = (res.get("choices", [{}])[0].get("message", {}).get("content", "") or "").strip()
        if "```" in text:
            text = text.split("```")[1].replace("json", "", 1).strip()
        parsed = json.loads(text)
        return {
            "hook_line": str(parsed.get("hook_line") or fallback_plan["hook_line"])[:42],
            "benefit_line": str(parsed.get("benefit_line") or fallback_plan["benefit_line"])[:55],
            "cta_line": str(parsed.get("cta_line") or fallback_plan["cta_line"])[:36],
            "sd_backdrop_prompt": str(parsed.get("sd_backdrop_prompt") or fallback_plan["sd_backdrop_prompt"]),
        }
    except Exception:
        return fallback_plan


# ---------------------------------------------------------------------------
# Step 2: Decode Uploaded Product Images (1 to 3 Shots) or Generate Sample
# ---------------------------------------------------------------------------
def decode_data_uri_image(data_uri: str) -> Any:
    if not HAS_PIL or not data_uri or "," not in data_uri:
        return None
    try:
        raw_b64 = data_uri.split(",", 1)[1]
        img_bytes = base64.b64decode(raw_b64)
        return Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    except Exception:
        return None


def create_sample_product_packshot(product_name: str, accent_hex: str, shot_index: int = 0) -> Any:
    """สร้างภาพสินค้าจำลองทรงขวด/กล่องพรีเมียมพร้อมเงาสะท้อน กรณีผู้ใช้กดทดสอบโดยยังไม่ได้อัปโหลดไฟล์"""
    size = 420
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    hex_clean = accent_hex.lstrip("#")
    ar = int(hex_clean[0:2], 16) if len(hex_clean) == 6 else 46
    ag = int(hex_clean[2:4], 16) if len(hex_clean) == 6 else 125
    ab = int(hex_clean[4:6], 16) if len(hex_clean) == 6 else 91

    draw.ellipse([95, 335, 325, 375], fill=(0, 0, 0, 110))

    offset_x = (shot_index - 1) * 10
    left, top, right, bottom = 135 + offset_x, 75, 285 + offset_x, 345
    draw.rounded_rectangle([left, top, right, bottom], radius=26, fill=(ar, ag, ab, 245), outline=(255, 255, 255, 210), width=3)
    draw.rounded_rectangle([left + 36, top - 34, right - 36, top + 6], radius=8, fill=(30, 35, 42, 255), outline=(220, 225, 230, 200), width=2)
    draw.rounded_rectangle([left + 14, top + 68, right - 14, bottom - 55], radius=12, fill=(248, 248, 245, 235))
    draw.rounded_rectangle([left + 10, top + 18, left + 22, bottom - 20], radius=6, fill=(255, 255, 255, 95))

    short_brand = (product_name.split()[0] if product_name else "BRAND")[:10].upper()
    draw.text((left + 32, top + 115), short_brand, fill=(18, 22, 26, 255))
    draw.text((left + 32, top + 142), f"SHOT #{shot_index + 1}", fill=(ar, ag, ab, 255))
    return canvas


# ---------------------------------------------------------------------------
# Step 3: Render Studio Backdrop via ComfyUI (:8188) or Rich Studio Fallback
# ---------------------------------------------------------------------------
def render_studio_backdrop(prompt_en: str, width: int, height: int, seed: int, accent_hex: str) -> tuple[Any, bool]:
    """สั่ง ComfyUI เรนเดอร์ฉากหลังสตูดิโอความละเอียดตามสัดส่วนโฆษณา หรือสร้างฉากสตูดิโอจำลองหากออฟไลน์"""
    try:
        wf = json.loads(TXT2IMG_WORKFLOW_PATH.read_text(encoding="utf-8"))
        wf["6"]["inputs"]["text"] = prompt_en
        wf["7"]["inputs"]["text"] = "text, watermark, blurry, low quality, human hands, ugly, cluttered"
        wf["5"]["inputs"]["width"] = int(width)
        wf["5"]["inputs"]["height"] = int(height)
        wf["3"]["inputs"]["seed"] = int(seed)
        wf["3"]["inputs"]["steps"] = 18
        wf["3"]["inputs"]["cfg"] = 7.0

        res = _http_post_json(f"{COMFYUI_BASE_URL}/prompt", {"prompt": wf}, timeout=8.0)
        prompt_id = res["prompt_id"]

        t0 = time.time()
        while time.time() - t0 < 120:
            hist = _http_get_json(f"{COMFYUI_BASE_URL}/history/{prompt_id}", timeout=4.0)
            if prompt_id in hist:
                outputs = hist[prompt_id].get("outputs", {})
                for _, nout in outputs.items():
                    if "images" in nout and nout["images"]:
                        img_meta = nout["images"][0]
                        q = urllib.parse.urlencode(
                            {
                                "filename": img_meta["filename"],
                                "subfolder": img_meta.get("subfolder", ""),
                                "type": img_meta.get("type", "output"),
                            }
                        )
                        v_bytes = _http_get_bytes(f"{COMFYUI_BASE_URL}/view?{q}", timeout=10.0)
                        return Image.open(io.BytesIO(v_bytes)).convert("RGB"), False
            time.sleep(0.75)
    except Exception:
        pass

    hex_clean = accent_hex.lstrip("#")
    ar = int(hex_clean[0:2], 16) if len(hex_clean) == 6 else 46
    ag = int(hex_clean[2:4], 16) if len(hex_clean) == 6 else 125
    ab = int(hex_clean[4:6], 16) if len(hex_clean) == 6 else 91

    bg = Image.new("RGB", (width, height), (14, 18, 24))
    draw = ImageDraw.Draw(bg)
    for y in range(0, height, 3):
        ratio = y / max(1, height)
        r = int(14 + ratio * (ar * 0.45))
        g = int(18 + ratio * (ag * 0.45))
        b = int(24 + ratio * (ab * 0.45))
        draw.line([(0, y), (width, y)], fill=(min(255, r), min(255, g), min(255, b)), width=3)

    podium_top = int(height * 0.68)
    draw.ellipse(
        [int(width * 0.12), podium_top - 22, int(width * 0.88), podium_top + 38],
        fill=(min(255, ar // 2 + 25), min(255, ag // 2 + 25), min(255, ab // 2 + 25)),
        outline=(255, 255, 255),
    )
    return bg, True


# ---------------------------------------------------------------------------
# Step 4: Synthesize 36-Frame Commercial Video Ad (.webp & .gif)
# ---------------------------------------------------------------------------
def build_product_ad_video(
    backdrop: Any,
    product_shots: list[Any],
    product_name: str,
    ad_copy: dict[str, str],
    accent_hex: str,
    total_frames: int = 36,
) -> tuple[bytes, bytes]:
    width, height = backdrop.size
    frames: list[Any] = []

    hex_clean = accent_hex.lstrip("#")
    ar = int(hex_clean[0:2], 16) if len(hex_clean) == 6 else 46
    ag = int(hex_clean[2:4], 16) if len(hex_clean) == 6 else 125
    ab = int(hex_clean[4:6], 16) if len(hex_clean) == 6 else 91

    shots: list[Any] = []
    for idx in range(3):
        if idx < len(product_shots):
            shots.append(product_shots[idx])
        else:
            base_shot = product_shots[0].copy()
            if idx == 1:
                base_shot = base_shot.rotate(-5, resample=Image.Resampling.BICUBIC, expand=False)
            elif idx == 2:
                base_shot = ImageEnhance.Brightness(base_shot).enhance(1.06)
            shots.append(base_shot)

    for f_idx in range(total_frames):
        act_idx = min(2, f_idx // (total_frames // 3))
        local_t = (f_idx % (total_frames // 3)) / max(1, (total_frames // 3) - 1)

        bg_zoom = 1.0 + 0.08 * (f_idx / total_frames)
        cw, ch = int(width / bg_zoom), int(height / bg_zoom)
        left = (width - cw) // 2
        top = (height - ch) // 2
        frame_bg = backdrop.crop((left, top, left + cw, top + ch)).resize(
            (width, height), Image.Resampling.LANCZOS
        ).convert("RGBA")

        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        for p in range(8):
            angle = (p * 45 + f_idx * 10) * (math.pi / 180.0)
            px = int(width * 0.5 + math.cos(angle) * (width * 0.34))
            py = int(height * 0.42 + math.sin(angle * 1.3) * (height * 0.22))
            rad = 6 + (p % 4) * 3
            odraw.ellipse([px - rad, py - rad, px + rad, py + rad], fill=(ar, ag, ab, 95))

        active_shot = shots[act_idx]
        target_box = int(min(width, height) * (0.58 + 0.08 * local_t))
        prod_resized = active_shot.copy()
        prod_resized.thumbnail((target_box, target_box), Image.Resampling.LANCZOS)

        pw, ph = prod_resized.size
        px_pos = (width - pw) // 2 + int(math.sin(local_t * math.pi) * 8 * (1 if act_idx == 1 else 0))
        py_pos = int(height * 0.44) - (ph // 2)

        composed = Image.alpha_composite(frame_bg, overlay)
        composed.alpha_composite(prod_resized, dest=(max(0, px_pos), max(0, py_pos)))

        hud = ImageDraw.Draw(composed)
        hud.rounded_rectangle([14, 14, width - 14, 48], radius=10, fill=(16, 19, 23, 205))
        hud.text((26, 24), f"ADCRAFT STUDIO • {product_name[:28]}", fill=(247, 246, 242, 255))

        banner_top = height - 96
        hud.rounded_rectangle(
            [14, banner_top, width - 14, height - 14],
            radius=12,
            fill=(16, 19, 23, 225),
            outline=(ar, ag, ab, 255),
            width=2,
        )

        act_labels = [
            f"SCENE 1 (HOOK): {ad_copy['hook_line']}",
            f"SCENE 2 (DETAIL): {ad_copy['benefit_line']}",
            f"SCENE 3 (OFFER): {ad_copy['cta_line']}",
        ]
        hud.text((28, banner_top + 16), act_labels[act_idx], fill=(255, 255, 255, 255))
        hud.text((28, banner_top + 46), ad_copy["cta_line"], fill=(min(255, ar + 60), min(255, ag + 60), min(255, ab + 60), 255))

        frames.append(composed.convert("RGB"))

    webp_buf = io.BytesIO()
    frames[0].save(
        webp_buf,
        format="WEBP",
        save_all=True,
        append_images=frames[1:],
        duration=85,
        loop=0,
        quality=88,
    )

    gif_buf = io.BytesIO()
    frames[0].save(
        gif_buf,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=85,
        loop=0,
    )
    return webp_buf.getvalue(), gif_buf.getvalue()


def _append_ad_history_csv(row: dict[str, Any]) -> None:
    """บันทึกประวัติแคมเปญลงไฟล์ CSV ด้วยโมดูล csv มาตรฐานของ Python (ไม่ต้องพึ่งพา pandas)"""
    fieldnames = [
        "timestamp",
        "preset",
        "product_name",
        "uploaded_photos",
        "aspect_ratio",
        "seed",
        "output_webp",
        "elapsed_sec",
    ]
    exists = HISTORY_CSV_PATH.exists()
    with HISTORY_CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


# ---------------------------------------------------------------------------
# Main Controller for Ad Generation
# ---------------------------------------------------------------------------
def execute_product_ad_job(payload: dict[str, Any]) -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    preset_key = str(payload.get("preset_key", "coffee_beverage"))
    preset = AD_PROMPT_PRESETS.get(preset_key, AD_PROMPT_PRESETS["coffee_beverage"])

    product_name = str(payload.get("product_name", "")).strip() or preset["product_name"]
    selling_point = str(payload.get("selling_point", "")).strip() or preset["selling_point"]
    cta_badge = str(payload.get("cta_badge", "")).strip() or preset["cta_badge"]
    scene_prompt = str(payload.get("scene_prompt", "")).strip() or preset["scene_prompt"]
    aspect_ratio = str(payload.get("aspect_ratio", "9:16"))
    width, height = ASPECT_DIMENSIONS.get(aspect_ratio, (384, 640))

    raw_seed = str(payload.get("seed_value", "")).strip()
    seed = int(raw_seed) if raw_seed.isdigit() else random.randint(100_000, 999_999)

    ad_copy = generate_ad_copy_with_llm(product_name, selling_point, cta_badge, scene_prompt)
    ts = int(time.time())

    if HAS_PIL:
        uploaded_uris = payload.get("product_images", [])
        decoded_shots: list[Any] = []
        if isinstance(uploaded_uris, list):
            for uri in uploaded_uris[:3]:
                img = decode_data_uri_image(str(uri))
                if img is not None:
                    decoded_shots.append(img)

        uploaded_count = len(decoded_shots)
        if uploaded_count == 0:
            decoded_shots = [
                create_sample_product_packshot(product_name, preset["accent_hex"], i) for i in range(3)
            ]

        backdrop_img, used_fallback = render_studio_backdrop(
            ad_copy["sd_backdrop_prompt"], width, height, seed, preset["accent_hex"]
        )

        webp_bytes, gif_bytes = build_product_ad_video(
            backdrop_img,
            decoded_shots,
            product_name,
            ad_copy,
            preset["accent_hex"],
            total_frames=36,
        )

        webp_name = f"product_ad_{ts}_seed{seed}.webp"
        gif_name = f"product_ad_{ts}_seed{seed}.gif"
        webp_path = OUTPUT_DIR / webp_name
        gif_path = OUTPUT_DIR / gif_name
        webp_path.write_bytes(webp_bytes)
        gif_path.write_bytes(gif_bytes)
        video_data_uri = f"data:image/webp;base64,{base64.b64encode(webp_bytes).decode('ascii')}"
    else:
        uploaded_count = 0
        used_fallback = True
        svg_str = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
          <rect width="100%" height="100%" fill="#101317"/>
          <rect x="24" y="80" width="{width - 48}" height="{height - 200}" rx="20" fill="{preset['accent_hex']}" opacity="0.85">
            <animate attributeName="opacity" values="0.65;0.95;0.65" dur="2.5s" repeatCount="indefinite"/>
          </rect>
          <text x="32" y="46" fill="#ffffff" font-family="sans-serif" font-size="15" font-weight="bold">{product_name}</text>
          <text x="32" y="{height - 70}" fill="#ffffff" font-family="sans-serif" font-size="13">{ad_copy['hook_line']}</text>
          <text x="32" y="{height - 40}" fill="#69b98e" font-family="sans-serif" font-size="13">{ad_copy['cta_line']}</text>
        </svg>"""
        svg_bytes = svg_str.encode("utf-8")
        webp_name = f"product_ad_{ts}_seed{seed}.svg"
        gif_name = webp_name
        webp_path = OUTPUT_DIR / webp_name
        gif_path = webp_path
        webp_path.write_bytes(svg_bytes)
        video_data_uri = f"data:image/svg+xml;base64,{base64.b64encode(svg_bytes).decode('ascii')}"

    _append_ad_history_csv(
        {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "preset": preset_key,
            "product_name": product_name,
            "uploaded_photos": uploaded_count,
            "aspect_ratio": aspect_ratio,
            "seed": seed,
            "output_webp": webp_name,
            "elapsed_sec": round(time.time() - t0, 2),
        }
    )

    return {
        "product_name": product_name,
        "uploaded_photos_count": uploaded_count,
        "aspect_ratio": aspect_ratio,
        "width": width,
        "height": height,
        "seed": seed,
        "ad_copy": ad_copy,
        "saved_webp": str(webp_path.relative_to(ROOT_DIR)),
        "saved_gif": str(gif_path.relative_to(ROOT_DIR)),
        "used_fallback": used_fallback,
        "elapsed_sec": round(time.time() - t0, 2),
        "video_data_uri": video_data_uri,
    }


# ---------------------------------------------------------------------------
# Web UI HTML (Accessible, Brand-Consistent Forms, 3-Slot Product Uploader)
# ---------------------------------------------------------------------------
PRESETS_JSON_STR = json.dumps(AD_PROMPT_PRESETS, ensure_ascii=False)

AD_STUDIO_HTML = f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AdCraft AI — Product Video Ad Studio (Showcase #3)</title>
  <style>
    :root {{
      color-scheme: light dark;
      --brand-color: #216E5A;
      --bg-page: #F7F6F2;
      --bg-card: #FFFFFF;
      --bg-subtle: #EAE7DF;
      --text-main: #101317;
      --text-muted: #525866;
      --border-color: #D8D4CA;
      --focus-ring: #216E5A;
    }}

    @media (prefers-color-scheme: dark) {{
      :root {{
        --brand-color: #2F9E80;
        --bg-page: #101317;
        --bg-card: #181C22;
        --bg-subtle: #222831;
        --text-main: #F7F6F2;
        --text-muted: #9BA3B0;
        --border-color: #2E3642;
        --focus-ring: #2F9E80;
      }}
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg-page);
      color: var(--text-main);
      accent-color: var(--brand-color);
      line-height: 1.5;
    }}

    @supports not (accent-color: var(--brand-color)) {{
      input[type="radio"]:checked {{
        outline: 2px solid var(--brand-color);
      }}
    }}

    .topbar {{
      background: var(--bg-card);
      border-bottom: 1px solid var(--border-color);
      padding: 0.9rem 1.5rem;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }}

    .badge {{
      font-size: 0.75rem;
      font-weight: 700;
      padding: 0.25rem 0.65rem;
      border-radius: 999px;
      border: 1px solid var(--border-color);
      background: var(--bg-subtle);
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
    }}

    .layout {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 1.5rem;
      display: grid;
      grid-template-columns: 1fr;
      gap: 1.5rem;
    }}

    @media (min-width: 980px) {{
      .layout {{
        grid-template-columns: 500px 1fr;
        align-items: start;
      }}
    }}

    .panel {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 1.25rem;
    }}

    fieldset {{
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 0.95rem 1rem;
      margin: 0 0 1.1rem 0;
    }}

    legend {{
      font-weight: 700;
      font-size: 0.85rem;
      padding: 0 0.4rem;
      color: var(--brand-color);
    }}

    .form-group {{
      margin-block-end: 0.9rem;
    }}
    .form-group:last-child {{
      margin-block-end: 0;
    }}

    label.field-label {{
      display: block;
      font-weight: 600;
      font-size: 0.85rem;
      margin-block-end: 0.3rem;
    }}

    .hint {{
      display: block;
      font-size: 0.76rem;
      color: var(--text-muted);
      margin-block-start: 0.25rem;
    }}

    input[type="text"],
    select,
    textarea {{
      width: 100%;
      font-size: 0.95rem;
      font-family: inherit;
      padding: 0.6rem 0.75rem;
      min-height: 44px;
      border-radius: 10px;
      border: 1px solid var(--border-color);
      background: var(--bg-page);
      color: var(--text-main);
    }}

    textarea {{
      min-height: 76px;
      resize: vertical;
    }}

    input:focus-visible,
    select:focus-visible,
    textarea:focus-visible,
    button:focus-visible {{
      outline: 3px solid var(--focus-ring);
      outline-offset: 2px;
    }}

    .upload-slots {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 0.6rem;
    }}

    .slot-card {{
      border: 1px dashed var(--border-color);
      border-radius: 10px;
      padding: 0.55rem;
      background: var(--bg-page);
      text-align: center;
      font-size: 0.75rem;
    }}

    .slot-thumb {{
      width: 100%;
      height: 74px;
      object-fit: contain;
      border-radius: 6px;
      background: var(--bg-subtle);
      margin-top: 0.35rem;
      display: none;
    }}

    .preset-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.45rem;
      margin-bottom: 0.75rem;
    }}

    .preset-btn {{
      padding: 0.5rem 0.65rem;
      border-radius: 8px;
      border: 1px solid var(--border-color);
      background: var(--bg-page);
      color: var(--text-main);
      font-size: 0.78rem;
      font-weight: 600;
      text-align: left;
      cursor: pointer;
    }}
    .preset-btn:hover {{
      border-color: var(--brand-color);
    }}

    .radio-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 0.5rem;
    }}

    .radio-card {{
      display: flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.5rem 0.6rem;
      border: 1px solid var(--border-color);
      border-radius: 10px;
      background: var(--bg-page);
      font-size: 0.8rem;
      font-weight: 600;
      min-height: 44px;
      cursor: pointer;
    }}

    .submit-btn {{
      width: 100%;
      min-height: 50px;
      border: none;
      border-radius: 12px;
      background: var(--brand-color);
      color: #FFFFFF;
      font-size: 1rem;
      font-weight: 700;
      cursor: pointer;
    }}
    .submit-btn:disabled {{
      opacity: 0.55;
      cursor: wait;
    }}

    .viewport {{
      min-height: 480px;
      border: 1px dashed var(--border-color);
      border-radius: 14px;
      background: var(--bg-page);
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }}

    .ad-video-img {{
      max-width: 100%;
      max-height: 540px;
      border-radius: 14px;
      box-shadow: 0 14px 34px rgba(0, 0, 0, 0.22);
    }}

    .script-card {{
      width: 100%;
      margin-top: 1rem;
      padding: 1rem;
      border-radius: 12px;
      background: var(--bg-subtle);
      font-size: 0.84rem;
    }}

    .hidden {{
      display: none !important;
    }}
  </style>
</head>
<body>
  <header class="topbar">
    <div style="font-weight: 800; font-size: 1.15rem; display: flex; align-items: center; gap: 0.6rem;">
      <span>🛍️ AdCraft AI — Product Video Ad Studio</span>
      <span class="badge">Showcase #3 • 3-Shot Product Ad Video</span>
    </div>
    <div style="display: flex; gap: 0.5rem;">
      <span class="badge" id="server-status">กำลังตรวจสอบ LM Studio &amp; ComfyUI...</span>
    </div>
  </header>

  <main class="layout">
    <!-- Left Column: Product Upload + Prompt Presets -->
    <section class="panel" aria-labelledby="ad-form-title">
      <h2 id="ad-form-title" style="margin-top: 0; font-size: 1.08rem;">สร้างวิดีโอโฆษณาสินค้า 3 ฉาก (Hook → Detail → Offer)</h2>

      <form id="ad-form" action="/api/generate-ad" method="POST">
        <!-- 1. Product Image Upload (1 to 3 Shots) -->
        <fieldset>
          <legend>1. โยนภาพสินค้าเข้าสู่ระบบ (แนะนำ 1–3 ภาพตามสูตรโฆษณา 3 ฉาก)</legend>
          <span class="hint" style="margin-bottom: 0.65rem;">
            <strong>ทำไมต้อง 3 ภาพ?</strong> โฆษณาวิดีโอสั้นที่ได้ผลดีที่สุดจะแบ่งเป็น <strong>ฉากที่ 1 มุมตรงเปิดเรื่อง (Hook)</strong>, <strong>ฉากที่ 2 มุมเจาะดีเทล (Detail)</strong>, และ <strong>ฉากที่ 3 ภาพปิดการขาย (Offer)</strong> — <em>หากอัปโหลดแค่ 1 ภาพ (หรือเว้นว่างไว้เพื่อใช้ภาพตัวอย่าง) ระบบจะสร้างมุมกล้องทั้ง 3 ฉากให้อัตโนมัติ!</em>
          </span>

          <div class="upload-slots">
            <div class="slot-card">
              <label class="field-label" for="shot-1">ภาพที่ 1: มุมหลัก (Hero)</label>
              <input type="file" id="shot-1" name="shot_1" accept="image/*" style="font-size: 0.7rem; width: 100%;" />
              <img id="thumb-1" class="slot-thumb" alt="ตัวอย่างภาพสินค้าที่ 1" />
            </div>
            <div class="slot-card">
              <label class="field-label" for="shot-2">ภาพที่ 2: มุมดีเทล (45°)</label>
              <input type="file" id="shot-2" name="shot_2" accept="image/*" style="font-size: 0.7rem; width: 100%;" />
              <img id="thumb-2" class="slot-thumb" alt="ตัวอย่างภาพสินค้าที่ 2" />
            </div>
            <div class="slot-card">
              <label class="field-label" for="shot-3">ภาพที่ 3: ตอนใช้งาน</label>
              <input type="file" id="shot-3" name="shot_3" accept="image/*" style="font-size: 0.7rem; width: 100%;" />
              <img id="thumb-3" class="slot-thumb" alt="ตัวอย่างภาพสินค้าที่ 3" />
            </div>
          </div>
        </fieldset>

        <!-- 2. Ready-to-Use Commercial Prompt Presets -->
        <fieldset>
          <legend>2. เลือกชุดตัวอย่าง Prompt โฆษณาสินค้า (คลิกเลือกเพื่อเติมข้อมูลอัตโนมัติ)</legend>
          <input type="hidden" id="preset-key" name="preset_key" value="coffee_beverage" />

          <div class="preset-grid" role="group" aria-label="ชุดตัวอย่าง Prompt โฆษณา">
            <button type="button" class="preset-btn" data-preset="coffee_beverage">☕ กาแฟสกัดเย็น / เครื่องดื่ม</button>
            <button type="button" class="preset-btn" data-preset="luxury_skincare">🧴 สกินแคร์ / เซรั่มหรู</button>
            <button type="button" class="preset-btn" data-preset="tech_gadget">🎧 หูฟังไร้สาย / แกดเจ็ต</button>
            <button type="button" class="preset-btn" data-preset="street_sneaker">👟 รองเท้าผ้าใบ / สตรีท</button>
            <button type="button" class="preset-btn" data-preset="gourmet_food">🥐 ขนมอบ / อาหารพรีเมียม</button>
            <button type="button" class="preset-btn" data-preset="minimal_watch">⌚ นาฬิกาข้อมือ / แฟชั่น</button>
          </div>

          <div class="form-group">
            <label class="field-label" for="product-name">ชื่อแบรนด์และสินค้า (Product Name):</label>
            <input type="text" id="product-name" name="product_name" required value="AURA Cold Brew Coffee" />
          </div>

          <div class="form-group">
            <label class="field-label" for="selling-point">จุดขายหลักภาษาไทย (ให้ LM Studio นำไปแต่งบทโฆษณา 3 ฉาก):</label>
            <input type="text" id="selling-point" name="selling_point" required value="สกัดเย็นนาน 18 ชั่วโมง หอมเมล็ดกาแฟอาราบิก้าแท้ สดชื่นไม่มีน้ำตาล" />
          </div>

          <div class="form-group">
            <label class="field-label" for="cta-badge">ข้อความโปรโมชันปิดท้าย (Call-to-Action Badge):</label>
            <input type="text" id="cta-badge" name="cta_badge" required value="สั่งซื้อวันนี้ ลดทันที 20%" />
          </div>

          <div class="form-group">
            <label class="field-label" for="scene-prompt">Prompt ฉากหลังสตูดิโอสำหรับส่งให้ ComfyUI (แก้ไขปรับแต่งได้):</label>
            <textarea id="scene-prompt" name="scene_prompt" required>commercial product photography of a sleek cold brew coffee bottle on wet dark slate stone, splashing water droplets, crushed ice cubes, warm morning golden hour sunbeams through cafe window, cinematic rim lighting, shallow depth of field, 8k advertising shot</textarea>
          </div>
        </fieldset>

        <!-- 3. Video Format & Seed -->
        <fieldset>
          <legend>3. สัดส่วนวิดีโอโฆษณา &amp; ค่า Seed</legend>
          <div class="form-group">
            <span class="field-label">สัดส่วนวิดีโอ (Video Aspect Ratio):</span>
            <div class="radio-grid">
              <label class="radio-card" for="ar-9-16">
                <input type="radio" id="ar-9-16" name="aspect_ratio" value="9:16" checked />
                <span>📱 9:16 (TikTok/Reels)</span>
              </label>
              <label class="radio-card" for="ar-1-1">
                <input type="radio" id="ar-1-1" name="aspect_ratio" value="1:1" />
                <span>🟦 1:1 (Feed Square)</span>
              </label>
              <label class="radio-card" for="ar-16-9">
                <input type="radio" id="ar-16-9" name="aspect_ratio" value="16:9" />
                <span>🖥️ 16:9 (YouTube)</span>
              </label>
            </div>
          </div>

          <div class="form-group">
            <label class="field-label" for="seed-input">หมายเลข Seed ของฉากหลัง (เว้นว่างเพื่อสุ่มใหม่):</label>
            <input
              type="text"
              id="seed-input"
              name="seed_value"
              placeholder="เช่น 42 (เว้นว่างเพื่อให้ระบบสุ่มใหม่)"
              inputmode="numeric"
              autocorrect="off"
              autocapitalize="off"
              spellcheck="false"
            />
          </div>
        </fieldset>

        <button type="submit" id="generate-ad-btn" class="submit-btn">
          🎬 สร้างวิดีโอโฆษณาสินค้า (Generate Product Video Ad)
        </button>
      </form>
    </section>

    <!-- Right Column: Video Ad Output -->
    <section class="panel" aria-labelledby="ad-Result-heading">
      <h2 id="ad-Result-heading" style="margin-top: 0; font-size: 1.08rem;">ผลลัพธ์วิดีโอโฆษณาสินค้า (36-Frame Commercial Loop)</h2>

      <div class="viewport" aria-live="polite">
        <div id="empty-ad-msg" style="text-align: center; max-width: 420px;">
          <p style="font-weight: 700; font-size: 1.05rem; margin-bottom: 0.35rem;">พร้อมสร้างวิดีโอโฆษณาสินค้า</p>
          <p style="font-size: 0.85rem; color: var(--text-muted);">
            โยนภาพสินค้า 1–3 ภาพ (หรือกดเลือกชุดตัวอย่าง Prompt ด้านซ้ายมือ) แล้วกดปุ่ม <strong>สร้างวิดีโอโฆษณาสินค้า</strong> ระบบจะสร้างวิดีโอแอนิเมชันพร้อมคำโปรย 3 ฉากให้อัตโนมัติ
          </p>
        </div>

        <img id="ad-video-output" class="ad-video-img hidden" alt="วิดีโอโฆษณาสินค้าที่สร้างจาก AdCraft AI" />

        <div id="ad-script-box" class="script-card hidden">
          <div><strong>ไฟล์วิดีโอที่บันทึกไว้:</strong> <code id="out-webp"></code> และ <code id="out-gif"></code></div>
          <div style="margin-top: 0.35rem;">
            <strong>จำนวนภาพสินค้าที่รับเข้า:</strong> <span id="out-photos"></span> ภาพ
            • <strong>Seed:</strong> <code id="out-seed"></code>
            • <strong>เวลาประมวลผล:</strong> <span id="out-time"></span> วินาที
          </div>
          <hr style="border: none; border-top: 1px solid var(--border-color); margin: 0.65rem 0;" />
          <div><strong>ฉากที่ 1 (Hook):</strong> <span id="out-hook"></span></div>
          <div><strong>ฉากที่ 2 (Benefit):</strong> <span id="out-benefit"></span></div>
          <div><strong>ฉากที่ 3 (Offer CTA):</strong> <span id="out-cta"></span></div>
        </div>
      </div>
    </section>
  </main>

  <script>
    const PRESETS = {PRESETS_JSON_STR};
    const uploadedDataUris = [null, null, null];

    [1, 2, 3].forEach((idx) => {{
      const fileInput = document.getElementById('shot-' + idx);
      const thumbImg = document.getElementById('thumb-' + idx);
      fileInput.addEventListener('change', () => {{
        const file = fileInput.files && fileInput.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = () => {{
          uploadedDataUris[idx - 1] = reader.result;
          thumbImg.src = reader.result;
          thumbImg.style.display = 'block';
        }};
        reader.readAsDataURL(file);
      }});
    }});

    document.querySelectorAll('.preset-btn').forEach((btn) => {{
      btn.addEventListener('click', () => {{
        const key = btn.getAttribute('data-preset');
        const p = PRESETS[key];
        if (!p) return;
        document.getElementById('preset-key').value = key;
        document.getElementById('product-name').value = p.product_name;
        document.getElementById('selling-point').value = p.selling_point;
        document.getElementById('cta-badge').value = p.cta_badge;
        document.getElementById('scene-prompt').value = p.scene_prompt;
      }});
    }});

    async function checkServers() {{
      try {{
        const res = await fetch('/api/status');
        const st = await res.json();
        const badge = document.getElementById('server-status');
        const lmTxt = st.lm_studio_online ? 'LM Studio: Online' : 'LM Studio: Fallback Copy';
        const cfTxt = st.comfyui_online ? 'ComfyUI: Online' : 'ComfyUI: Studio Preview';
        badge.textContent = lmTxt + ' • ' + cfTxt;
      }} catch (e) {{
        console.error(e);
      }}
    }}

    const form = document.getElementById('ad-form');
    const submitBtn = document.getElementById('generate-ad-btn');
    form.addEventListener('submit', async (e) => {{
      e.preventDefault();
      submitBtn.disabled = true;
      submitBtn.textContent = '⏳ กำลังแต่งคำโปรยและเรนเดอร์วิดีโอโฆษณา 36 เฟรม...';

      const fd = new FormData(form);
      const activePhotos = uploadedDataUris.filter(Boolean);
      const payload = {{
        preset_key: fd.get('preset_key'),
        product_name: fd.get('product_name'),
        selling_point: fd.get('selling_point'),
        cta_badge: fd.get('cta_badge'),
        scene_prompt: fd.get('scene_prompt'),
        aspect_ratio: fd.get('aspect_ratio'),
        seed_value: fd.get('seed_value'),
        product_images: activePhotos,
      }};

      try {{
        const res = await fetch('/api/generate-ad', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(payload),
        }});
        const data = await res.json();

        document.getElementById('empty-ad-msg').classList.add('hidden');
        const vidImg = document.getElementById('ad-video-output');
        vidImg.src = data.video_data_uri;
        vidImg.classList.remove('hidden');

        const scriptBox = document.getElementById('ad-script-box');
        scriptBox.classList.remove('hidden');
        document.getElementById('out-webp').textContent = data.saved_webp;
        document.getElementById('out-gif').textContent = data.saved_gif;
        document.getElementById('out-photos').textContent = data.uploaded_photos_count || '3 (ภาพสินค้าจำลอง)';
        document.getElementById('out-seed').textContent = data.seed;
        document.getElementById('out-time').textContent = data.elapsed_sec;
        document.getElementById('out-hook').textContent = data.ad_copy.hook_line;
        document.getElementById('out-benefit').textContent = data.ad_copy.benefit_line;
        document.getElementById('out-cta').textContent = data.ad_copy.cta_line;
      }} catch (err) {{
        alert('เกิดข้อผิดพลาด: ' + err.message);
      }} finally {{
        submitBtn.disabled = false;
        submitBtn.textContent = '🎬 สร้างวิดีโอโฆษณาสินค้า (Generate Product Video Ad)';
      }}
    }});

    checkServers();
  </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# HTTP Server Handler
# ---------------------------------------------------------------------------
class ProductAdStudioHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/" or self.path.startswith("/index.html"):
            body = AD_STUDIO_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/status":
            body = json.dumps(inspect_servers(), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self) -> None:
        if self.path == "/api/generate-ad":
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw) if raw else {}
            result = execute_product_ad_job(payload)
            body = json.dumps(result, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404, "Not Found")

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="AdCraft AI — Product Video Ad Studio (Showcase #3)")
    parser.add_argument("--port", type=int, default=8095, help="พอร์ตสำหรับเปิด Web App (ค่าเริ่มต้น: 8095)")
    parser.add_argument(
        "--cli-preset",
        choices=list(AD_PROMPT_PRESETS.keys()),
        help="รันสร้างวิดีโอโฆษณาสินค้าผ่าน Command Line ทันทีตาม Preset ที่เลือก",
    )
    args = parser.parse_args()

    if args.cli_preset:
        print(f"กำลังสร้างวิดีโอโฆษณาสินค้าสำหรับชุดตัวอย่าง: {args.cli_preset} ...")
        res = execute_product_ad_job({"preset_key": args.cli_preset})
        print(f"บันทึกไฟล์วิดีโอโฆษณาสำเร็จ: {res['saved_webp']} และ {res['saved_gif']} ({res['elapsed_sec']}s)")
        return

    server = HTTPServer(("127.0.0.1", args.port), ProductAdStudioHandler)
    print("=" * 68)
    print("🛍️ AdCraft AI — Product Video Ad Studio (Showcase #3)")
    print(f"👉 เปิดเบราว์เซอร์ไปที่: http://127.0.0.1:{args.port}")
    print("   (กด Ctrl + C เพื่อปิดเซิร์ฟเวอร์)")
    print("=" * 68)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nปิดเซิร์ฟเวอร์ AdCraft AI เรียบร้อยแล้ว")


if __name__ == "__main__":
    main()
