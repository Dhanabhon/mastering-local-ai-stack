#!/usr/bin/env python3
"""
Local AI Media Studio — Custom Image & Video Web App (Showcase #2)
==================================================================
เว็บแอปพลิเคชันแบบครบวงจรที่ทำงานครอบ LM Studio (:1234) และ ComfyUI (:8188)
บน Environment (.venv) เดิมที่ติดตั้งไว้แล้ว โดยไม่ต้องลงไลบรารีเพิ่ม

ฟีเจอร์หลัก:
1) โหมด Generate Image (Custom Text-to-Image):
   - พิมพ์โจทย์ภาษาไทยหรืออังกฤษ (เลือกเปิด/ปิดให้ LM Studio ช่วยแต่ง Prompt ได้)
   - ปรับค่า Custom ได้ครบ: Aspect Ratio (1:1, 16:9, 9:16, 2:3), Steps, CFG, Sampler, Seed (สุ่มใหม่/ล็อกค่า)
   - ดึงรายชื่อไฟล์ Checkpoint (.safetensors) ที่มีอยู่ในโฟลเดอร์ ComfyUI มาให้เลือกอัตโนมัติ

2) โหมด Generate Video (เลือกได้ 2 รูปแบบ):
   - รูปแบบที่ 1 (SD 1.5 AI Motion Clip — รันได้ทันทีบน RTX 3050 6GB ไม่ต้องโหลดโมเดลวิดีโอเพิ่ม):
     ให้ LM Studio วางแผนคีย์เฟรมต่อเนื่อง แล้วสั่ง ComfyUI เรนเดอร์คีย์เฟรมด้วย Seed เดียวกัน
     พร้อมทำ Smooth Crossfade & Cinema Pan/Zoom ออกมาเป็นไฟล์วิดีโอแอนิเมชัน (.webp และ .gif)
   - รูปแบบที่ 2 (Custom ComfyUI Video API JSON — สำหรับ AnimateDiff / Wan2.1 / LTX-Video):
     รองรับการเลือกไฟล์ workflows/sd15_animatediff_api.json หรือวางเนื้อหาไฟล์ Export (API) .json
     จาก ComfyUI เพื่อสั่งเรนเดอร์วิดีโอผ่านหน้าเว็บได้โดยตรง

วิธีรันเปิด Web App (ค่าเริ่มต้นเปิดที่พอร์ต 8090):
    python 06-custom-media-studio/app.py
"""

from __future__ import annotations

import argparse
import base64
import copy
import io
import json
import random
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from openai import OpenAI
from PIL import Image, ImageDraw

# ---------------------------------------------------------------------------
# Paths & Endpoints
# ---------------------------------------------------------------------------
STUDIO_DIR = Path(__file__).resolve().parent
ROOT_DIR = STUDIO_DIR.parent
IMAGE_WORKFLOW_PATH = ROOT_DIR / "03-comfyui-workflows" / "sd15_txt2img_api.json"
VIDEO_WORKFLOW_PATH = STUDIO_DIR / "workflows" / "sd15_animatediff_api.json"
OUTPUT_DIR = STUDIO_DIR / "outputs"
HISTORY_CSV_PATH = OUTPUT_DIR / "generation_history.csv"

LM_STUDIO_BASE_URL = "http://localhost:1234/v1"
COMFYUI_BASE_URL = "http://127.0.0.1:8188"

ASPECT_RATIOS: dict[str, tuple[int, int, str]] = {
    "1:1": (512, 512, "512×512 (1:1 Square)"),
    "16:9": (640, 384, "640×384 (16:9 Widescreen • 6GB Safe)"),
    "9:16": (384, 640, "384×640 (9:16 Vertical • 6GB Safe)"),
    "2:3": (512, 768, "512×768 (2:3 Poster)"),
}

STYLE_SUFFIXES: dict[str, dict[str, str]] = {
    "photorealistic": {
        "label": "Photorealistic Cinema",
        "positive": "photorealistic, 35mm cinema lens, natural rim lighting, high dynamic range, ultra detailed, 8k texture",
        "negative": "cartoon, anime, 3d render, painting, blurry, watermark, text, deformed hands, low quality",
    },
    "cyberpunk": {
        "label": "Cyberpunk Neon",
        "positive": "cyberpunk futuristic aesthetic, neon teal and magenta reflections, rain-slicked street, volumetric fog, masterpiece",
        "negative": "daylight, flat lighting, blurry, watermark, text, low resolution, deformed",
    },
    "anime": {
        "label": "Anime / Studio Ghibli",
        "positive": "anime key visual, Studio Ghibli inspired hand-painted background, vibrant cel shading, atmospheric clouds, masterpiece",
        "negative": "photorealistic, 3d render, gritty, blurry, watermark, text, deformed fingers",
    },
    "product": {
        "label": "Commercial Product Shot",
        "positive": "commercial product photography, softbox studio lighting, clean minimalist podium background, macro lens sharpness",
        "negative": "cluttered background, harsh shadows, blurry, watermark, text, distorted geometry",
    },
    "raw": {
        "label": "Raw Custom (ไม่เติมแต่งสไตล์เพิ่ม)",
        "positive": "masterpiece, best quality, highly detailed",
        "negative": "blurry, low quality, watermark, text",
    },
}


# ---------------------------------------------------------------------------
# Environment & Server Discovery
# ---------------------------------------------------------------------------
def inspect_environment() -> dict[str, Any]:
    """ตรวจสอบสถานะ LM Studio (:1234) และ ComfyUI (:8188) พร้อมดึงรายชื่อโมเดลที่มีในเครื่อง"""
    status: dict[str, Any] = {
        "lm_studio_online": False,
        "lm_studio_models": [],
        "comfyui_online": False,
        "checkpoints": ["v1-5-pruned-emaonly.safetensors"],
    }

    try:
        res = requests.get(f"{LM_STUDIO_BASE_URL}/models", timeout=2.5)
        if res.status_code == 200:
            data = res.json().get("data", [])
            models = [m.get("id", "") for m in data if m.get("id")]
            status["lm_studio_online"] = True
            status["lm_studio_models"] = models
    except Exception:
        pass

    try:
        res = requests.get(f"{COMFYUI_BASE_URL}/system_stats", timeout=2.5)
        if res.status_code == 200:
            status["comfyui_online"] = True
            obj_res = requests.get(
                f"{COMFYUI_BASE_URL}/object_info/CheckpointLoaderSimple", timeout=3.0
            )
            if obj_res.status_code == 200:
                ckpt_list = (
                    obj_res.json()
                    .get("CheckpointLoaderSimple", {})
                    .get("input", {})
                    .get("required", {})
                    .get("ckpt_name", [[]])[0]
                )
                if isinstance(ckpt_list, list) and len(ckpt_list) > 0:
                    status["checkpoints"] = ckpt_list
    except Exception:
        pass

    return status


# ---------------------------------------------------------------------------
# Step 1: LM Studio Prompt Enhancement (Image & Video Keyframes)
# ---------------------------------------------------------------------------
def enhance_prompt_with_llm(user_prompt: str, style_key: str, is_video: bool = False) -> str:
    """ใช้ LM Studio แปลงโจทย์ภาษาไทยหรืออังกฤษให้เป็น English SD Prompt ที่สมบูรณ์"""
    style_cfg = STYLE_SUFFIXES.get(style_key, STYLE_SUFFIXES["photorealistic"])
    try:
        client = OpenAI(base_url=LM_STUDIO_BASE_URL, api_key="lm-studio")
        models = client.models.list()
        if not models.data:
            raise RuntimeError("No model loaded in LM Studio")
        model_id = models.data[0].id

        motion_hint = (
            "Include dynamic motion cues (flowing movement, cinematic camera pan, atmospheric particles). "
            if is_video
            else ""
        )
        system_msg = (
            "You are an expert Stable Diffusion 1.5 prompt engineer. "
            "Translate and expand the user's Thai or English idea into a concise comma-separated English visual prompt "
            f"(40-65 words). {motion_hint}"
            "Output ONLY the raw English prompt without quotes or explanations."
        )
        resp = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": f"Concept: {user_prompt}\nStyle: {style_cfg['label']}"},
            ],
            temperature=0.65,
            max_tokens=160,
        )
        base_en = (resp.choices[0].message.content or "").strip().strip('"').strip("'")
        if base_en:
            return f"{base_en}, {style_cfg['positive']}"
    except Exception:
        pass

    return f"{user_prompt}, {style_cfg['positive']}"


def generate_motion_keyframe_prompts(user_prompt: str, style_key: str, num_keyframes: int = 2) -> list[str]:
    """สร้าง Prompt สำหรับคีย์เฟรมต่อเนื่องเพื่อให้ภาพเคลื่อนไหวลื่นไหล"""
    base_prompt = enhance_prompt_with_llm(user_prompt, style_key, is_video=True)
    if num_keyframes <= 1:
        return [base_prompt]

    return [
        f"{base_prompt}, establishing wide view, golden ambient light",
        f"{base_prompt}, dynamic close-up motion, glowing atmospheric particles, dramatic rim lighting",
    ][:num_keyframes]


# ---------------------------------------------------------------------------
# Step 2: ComfyUI Workflow Injection & Queue Helper
# ---------------------------------------------------------------------------
def inject_workflow_params(
    workflow: dict[str, Any],
    positive_prompt: str,
    negative_prompt: str,
    seed: int,
    steps: int,
    cfg: float,
    sampler_name: str,
    width: int,
    height: int,
    ckpt_name: str,
) -> dict[str, Any]:
    """ค้นหาและแทนที่ค่าใน JSON Workflow (รองรับทั้งไฟล์มาตรฐานและไฟล์ Custom Export API)"""
    wf = copy.deepcopy(workflow)

    # หากเป็นโครงสร้างมาตรฐานโหนด "6", "7", "3", "4", "5"
    if "6" in wf and wf["6"].get("class_type") == "CLIPTextEncode":
        wf["6"]["inputs"]["text"] = positive_prompt
    if "7" in wf and wf["7"].get("class_type") == "CLIPTextEncode":
        wf["7"]["inputs"]["text"] = negative_prompt

    # รองรับกรณีผู้ใช้ใส่ไฟล์ Custom JSON จาก ComfyUI ที่หมายเลขโหนดอาจเปลี่ยนไป
    clip_nodes = [
        nid for nid, node in wf.items() if isinstance(node, dict) and node.get("class_type") == "CLIPTextEncode"
    ]
    if len(clip_nodes) >= 1 and "6" not in wf:
        wf[clip_nodes[0]]["inputs"]["text"] = positive_prompt
    if len(clip_nodes) >= 2 and "7" not in wf:
        wf[clip_nodes[1]]["inputs"]["text"] = negative_prompt

    for _, node in wf.items():
        if not isinstance(node, dict):
            continue
        ctype = node.get("class_type", "")
        inputs = node.get("inputs", {})

        if ctype in ("KSampler", "KSamplerAdvanced"):
            if "seed" in inputs:
                inputs["seed"] = int(seed)
            if "noise_seed" in inputs:
                inputs["noise_seed"] = int(seed)
            if "steps" in inputs:
                inputs["steps"] = int(steps)
            if "cfg" in inputs:
                inputs["cfg"] = float(cfg)
            if "sampler_name" in inputs and sampler_name:
                inputs["sampler_name"] = sampler_name

        elif ctype == "EmptyLatentImage":
            inputs["width"] = int(width)
            inputs["height"] = int(height)

        elif ctype == "CheckpointLoaderSimple" and ckpt_name:
            inputs["ckpt_name"] = ckpt_name

    return wf


def queue_and_fetch_comfy_media(workflow: dict[str, Any], timeout_sec: int = 150) -> tuple[bytes, str]:
    """ส่ง JSON Workflow เข้าคิว ComfyUI และดึงไบต์รูปภาพหรือวิดีโอที่เรนเดอร์เสร็จแล้วกลับมา"""
    res = requests.post(f"{COMFYUI_BASE_URL}/prompt", json={"prompt": workflow}, timeout=10)
    res.raise_for_status()
    prompt_id = res.json()["prompt_id"]

    t0 = time.time()
    while time.time() - t0 < timeout_sec:
        hist_res = requests.get(f"{COMFYUI_BASE_URL}/history/{prompt_id}", timeout=5)
        hist_data = hist_res.json()
        if prompt_id in hist_data:
            outputs = hist_data[prompt_id].get("outputs", {})
            for _, node_out in outputs.items():
                for media_key in ("images", "gifs", "videos"):
                    if media_key in node_out and len(node_out[media_key]) > 0:
                        item = node_out[media_key][0]
                        filename = item["filename"]
                        ext = Path(filename).suffix.lower() or ".png"
                        query = urllib.parse.urlencode(
                            {
                                "filename": filename,
                                "subfolder": item.get("subfolder", ""),
                                "type": item.get("type", "output"),
                            }
                        )
                        view_res = requests.get(f"{COMFYUI_BASE_URL}/view?{query}", timeout=15)
                        view_res.raise_for_status()
                        return view_res.content, ext
        time.sleep(0.75)

    raise TimeoutError(f"ComfyUI ใช้เวลาเรนเดอร์เกิน {timeout_sec} วินาที")


def create_fallback_canvas(width: int, height: int, prompt_text: str, seed: int, frame_idx: int = 0) -> Image.Image:
    """สร้างภาพจำลองกรณีไม่ได้เปิด ComfyUI เพื่อให้ทดสอบระบบ UI และการสร้างไฟล์วิดีโอได้เสมอ"""
    img = Image.new("RGB", (width, height), (16, 20, 28))
    draw = ImageDraw.Draw(img)
    shift = frame_idx * 6
    for y in range(0, height, 4):
        r = min(255, max(15, int(24 + (y / height) * 60 + (shift % 40))))
        g = min(255, max(20, int(90 + (y / height) * 85)))
        b = min(255, max(40, int(110 + (1 - y / height) * 90)))
        draw.line([(0, y), (width, y)], fill=(r, g, b), width=4)

    cx = width // 2 + int(shift * 1.5) - 18
    cy = height // 2
    radius = min(width, height) // 5
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=(247, 246, 242), width=3)
    draw.text((20, 20), f"PREVIEW MODE (ComfyUI Offline) | Seed: {seed}", fill=(247, 246, 242))
    draw.text((20, height - 36), prompt_text[:65], fill=(220, 235, 230))
    return img


# ---------------------------------------------------------------------------
# Step 3: Video Synthesis (SD 1.5 AI Motion Clip — 6GB VRAM Safe)
# ---------------------------------------------------------------------------
def build_animated_motion_clip(
    keyframes: list[Image.Image], total_frames: int = 24
) -> tuple[bytes, bytes]:
    """
    สร้างแอนิเมชัน 24 เฟรม (12 FPS) จากภาพคีย์เฟรมด้วยเอฟเฟกต์ Cinema Ken Burns Zoom + Crossfade
    คืนค่าเป็น (webp_bytes, gif_bytes) โดยใช้เฉพาะ Pillow ที่อยู่ใน .venv
    """
    base_w, base_h = keyframes[0].size
    frames: list[Image.Image] = []
    img_a = keyframes[0].convert("RGB")
    img_b = keyframes[-1].convert("RGB")

    for idx in range(total_frames):
        # ไป-กลับ (Ping-pong loop) เพื่อให้วิดีโอเล่นวนลูปได้เนียนตา
        half = max(1, total_frames // 2)
        progress = (idx / half) if idx < half else ((total_frames - idx) / half)
        progress = max(0.0, min(1.0, progress))

        blended = Image.blend(img_a, img_b, alpha=progress)

        # ซูมเข้าอย่างนุ่มนวล (สูงสุด 10%) พร้อมแพนกล้องแนวนอนเล็กน้อย
        zoom = 1.0 + (0.10 * progress)
        crop_w = int(base_w / zoom)
        crop_h = int(base_h / zoom)
        left = int((base_w - crop_w) * (0.35 + 0.30 * progress))
        top = int((base_h - crop_h) * 0.5)

        cropped = blended.crop((left, top, left + crop_w, top + crop_h))
        frame = cropped.resize((base_w, base_h), Image.Resampling.LANCZOS)
        frames.append(frame)

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


# ---------------------------------------------------------------------------
# Unified Generation Controller
# ---------------------------------------------------------------------------
def execute_studio_job(params: dict[str, Any]) -> dict[str, Any]:
    """ประมวลผลงานสร้างภาพนิ่ง (Image) หรือภาพเคลื่อนไหว (Video) และบันทึกลงโฟลเดอร์ outputs/"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    t_start = time.time()

    mode = params.get("mode", "image")  # "image" or "video"
    user_prompt = str(params.get("prompt", "")).strip() or "หุ่นยนต์บาริสต้าชงกาแฟในคาเฟ่ไม้สไตล์มินิมอล"
    style_key = str(params.get("style", "photorealistic"))
    use_llm = bool(params.get("use_llm", True))
    aspect_key = str(params.get("aspect_ratio", "1:1"))
    width, height, _ = ASPECT_RATIOS.get(aspect_key, ASPECT_RATIOS["1:1"])

    steps = max(5, min(50, int(params.get("steps", 20))))
    cfg = max(1.0, min(20.0, float(params.get("cfg", 7.0))))
    sampler_name = str(params.get("sampler_name", "euler"))
    ckpt_name = str(params.get("ckpt_name", "v1-5-pruned-emaonly.safetensors"))

    style_defaults = STYLE_SUFFIXES.get(style_key, STYLE_SUFFIXES["photorealistic"])
    negative_prompt = str(params.get("negative_prompt", "")).strip() or style_defaults["negative"]

    seed_mode = str(params.get("seed_mode", "random"))
    raw_seed = str(params.get("seed_value", "42")).strip()
    if seed_mode == "fixed" and raw_seed.isdigit():
        seed = int(raw_seed)
    else:
        seed = random.randint(100_000_000, 999_999_999_999)

    timestamp = int(time.time())
    used_fallback = False

    if mode == "image":
        final_prompt = (
            enhance_prompt_with_llm(user_prompt, style_key, is_video=False)
            if use_llm
            else f"{user_prompt}, {style_defaults['positive']}"
        )
        base_wf = json.loads(IMAGE_WORKFLOW_PATH.read_text(encoding="utf-8"))
        wf = inject_workflow_params(
            base_wf, final_prompt, negative_prompt, seed, steps, cfg, sampler_name, width, height, ckpt_name
        )

        try:
            img_bytes, ext = queue_and_fetch_comfy_media(wf)
        except Exception:
            used_fallback = True
            ext = ".png"
            buf = io.BytesIO()
            create_fallback_canvas(width, height, final_prompt, seed).save(buf, format="PNG")
            img_bytes = buf.getvalue()

        out_name = f"image_{timestamp}_seed{seed}{ext}"
        out_path = OUTPUT_DIR / out_name
        out_path.write_bytes(img_bytes)

        mime = "image/webp" if ext == ".webp" else "image/png"
        b64_data = f"data:{mime};base64,{base64.b64encode(img_bytes).decode('ascii')}"
        result_meta = {
            "mode": "image",
            "media_type": "image",
            "prompt_input": user_prompt,
            "final_prompt": final_prompt,
            "negative_prompt": negative_prompt,
            "seed": seed,
            "steps": steps,
            "cfg": cfg,
            "width": width,
            "height": height,
            "filename": out_name,
            "SavedPath": str(out_path.relative_to(ROOT_DIR)),
            "data_uri": b64_data,
            "used_fallback": used_fallback,
            "elapsed_sec": round(time.time() - t_start, 2),
        }

    else:
        # โหมด Video Studio
        video_engine = str(params.get("video_engine", "sd15_motion"))
        custom_json_str = str(params.get("custom_workflow_json", "")).strip()

        if video_engine == "comfy_video_api":
            final_prompt = (
                enhance_prompt_with_llm(user_prompt, style_key, is_video=True)
                if use_llm
                else f"{user_prompt}, {style_defaults['positive']}"
            )
            if custom_json_str:
                raw_wf = json.loads(custom_json_str)
            else:
                raw_wf = json.loads(VIDEO_WORKFLOW_PATH.read_text(encoding="utf-8"))

            wf = inject_workflow_params(
                raw_wf, final_prompt, negative_prompt, seed, steps, cfg, sampler_name, width, height, ckpt_name
            )
            try:
                media_bytes, ext = queue_and_fetch_comfy_media(wf, timeout_sec=240)
                out_name = f"video_{timestamp}_seed{seed}{ext}"
                out_path = OUTPUT_DIR / out_name
                out_path.write_bytes(media_bytes)
                mime = "image/gif" if ext == ".gif" else "image/webp"
                b64_data = f"data:{mime};base64,{base64.b64encode(media_bytes).decode('ascii')}"
            except Exception:
                used_fallback = True
                kf1 = create_fallback_canvas(width, height, final_prompt, seed, 0)
                kf2 = create_fallback_canvas(width, height, final_prompt, seed, 4)
                webp_bytes, gif_bytes = build_animated_motion_clip([kf1, kf2], total_frames=24)
                out_name = f"video_{timestamp}_seed{seed}.webp"
                out_path = OUTPUT_DIR / out_name
                out_path.write_bytes(webp_bytes)
                (OUTPUT_DIR / f"video_{timestamp}_seed{seed}.gif").write_bytes(gif_bytes)
                b64_data = f"data:image/webp;base64,{base64.b64encode(webp_bytes).decode('ascii')}"
        else:
            # sd15_motion: สร้างคีย์เฟรมด้วย SD 1.5 ตัวเดิม (ประหยัด VRAM 6GB) แล้วประกอบร่างเป็นวิดีโอแอนิเมชัน 24 เฟรม
            kf_prompts = (
                generate_motion_keyframe_prompts(user_prompt, style_key, num_keyframes=2)
                if use_llm
                else [
                    f"{user_prompt}, {style_defaults['positive']}, wide view",
                    f"{user_prompt}, {style_defaults['positive']}, close-up dynamic lighting",
                ]
            )
            final_prompt = kf_prompts[0]
            base_wf = json.loads(IMAGE_WORKFLOW_PATH.read_text(encoding="utf-8"))
            keyframes: list[Image.Image] = []

            for idx, kf_p in enumerate(kf_prompts):
                wf = inject_workflow_params(
                    base_wf, kf_p, negative_prompt, seed + idx, steps, cfg, sampler_name, width, height, ckpt_name
                )
                try:
                    raw_bytes, _ = queue_and_fetch_comfy_media(wf)
                    keyframes.append(Image.open(io.BytesIO(raw_bytes)).convert("RGB"))
                except Exception:
                    used_fallback = True
                    keyframes.append(create_fallback_canvas(width, height, kf_p, seed, idx * 4))

            webp_bytes, gif_bytes = build_animated_motion_clip(keyframes, total_frames=24)
            out_name = f"motion_{timestamp}_seed{seed}.webp"
            gif_name = f"motion_{timestamp}_seed{seed}.gif"
            out_path = OUTPUT_DIR / out_name
            out_path.write_bytes(webp_bytes)
            (OUTPUT_DIR / gif_name).write_bytes(gif_bytes)
            b64_data = f"data:image/webp;base64,{base64.b64encode(webp_bytes).decode('ascii')}"

        result_meta = {
            "mode": "video",
            "media_type": "animated_webp",
            "prompt_input": user_prompt,
            "final_prompt": final_prompt,
            "negative_prompt": negative_prompt,
            "seed": seed,
            "steps": steps,
            "cfg": cfg,
            "width": width,
            "height": height,
            "filename": out_name,
            "SavedPath": str(out_path.relative_to(ROOT_DIR)),
            "data_uri": b64_data,
            "used_fallback": used_fallback,
            "elapsed_sec": round(time.time() - t_start, 2),
        }

    # บันทึกประวัติลงตาราง CSV ด้วย pandas
    row_df = pd.DataFrame(
        [
            {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "mode": result_meta["mode"],
                "prompt_input": result_meta["prompt_input"],
                "final_prompt": result_meta["final_prompt"],
                "seed": result_meta["seed"],
                "steps": result_meta["steps"],
                "cfg": result_meta["cfg"],
                "resolution": f"{width}x{height}",
                "filename": result_meta["filename"],
                "elapsed_sec": result_meta["elapsed_sec"],
            }
        ]
    )
    if HISTORY_CSV_PATH.exists():
        prev_df = pd.read_csv(HISTORY_CSV_PATH)
        pd.concat([row_df, prev_df], ignore_index=True).head(30).to_csv(HISTORY_CSV_PATH, index=False, encoding="utf-8")
    else:
        row_df.to_csv(HISTORY_CSV_PATH, index=False, encoding="utf-8")

    return result_meta


# ---------------------------------------------------------------------------
# Web App UI HTML (Accessible, Brand-Consistent Forms, Light/Dark Support)
# ---------------------------------------------------------------------------
STUDIO_UI_HTML = """<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Local AI Media Studio — Custom Image &amp; Video Web App</title>
  <style>
    :root {
      color-scheme: light dark;
      --brand-color: #216E5A;
      --bg-page: #F7F6F2;
      --bg-card: #FFFFFF;
      --bg-subtle: #EAE7DF;
      --text-main: #101317;
      --text-muted: #525866;
      --border-color: #D8D4CA;
      --focus-ring: #216E5A;
    }

    @media (prefers-color-scheme: dark) {
      :root {
        --brand-color: #2F9E80;
        --bg-page: #101317;
        --bg-card: #181C22;
        --bg-subtle: #222831;
        --text-main: #F7F6F2;
        --text-muted: #9BA3B0;
        --border-color: #2E3642;
        --focus-ring: #2F9E80;
      }
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: var(--bg-page);
      color: var(--text-main);
      accent-color: var(--brand-color);
      line-height: 1.5;
    }

    /* Progressive enhancement fallback when accent-color is not supported */
    @supports not (accent-color: var(--brand-color)) {
      input[type="range"] {
        -webkit-appearance: none;
        appearance: none;
        background: transparent;
      }
      input[type="range"]::-webkit-slider-runnable-track {
        width: 100%;
        height: 8px;
        background: var(--border-color);
        border-radius: 4px;
      }
      input[type="range"]::-webkit-slider-thumb {
        -webkit-appearance: none;
        appearance: none;
        height: 18px;
        width: 18px;
        border-radius: 50%;
        background: var(--brand-color);
        cursor: pointer;
        margin-top: -5px;
      }
    }

    .topbar {
      border-bottom: 1px solid var(--border-color);
      background: var(--bg-card);
      padding: 0.875rem 1.5rem;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }

    .brand-title {
      font-weight: 800;
      font-size: 1.15rem;
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }

    .badge {
      font-size: 0.75rem;
      font-weight: 700;
      padding: 0.25rem 0.65rem;
      border-radius: 999px;
      border: 1px solid var(--border-color);
      background: var(--bg-subtle);
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #9BA3B0;
    }
    .status-dot.online {
      background: #10B981;
    }
    .status-dot.offline {
      background: #F59E0B;
    }

    .layout {
      max-width: 1280px;
      margin: 0 auto;
      padding: 1.5rem;
      display: grid;
      grid-template-columns: 1fr;
      gap: 1.5rem;
    }

    @media (min-width: 960px) {
      .layout {
        grid-template-columns: 460px 1fr;
        align-items: start;
      }
    }

    .panel {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 1.25rem;
    }

    fieldset {
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 0.9rem 1rem;
      margin: 0 0 1.1rem 0;
    }

    legend {
      font-weight: 700;
      font-size: 0.85rem;
      padding: 0 0.4rem;
      color: var(--brand-color);
    }

    .form-group {
      margin-block-end: 1rem;
    }
    .form-group:last-child {
      margin-block-end: 0;
    }

    label.field-label {
      display: block;
      font-weight: 600;
      font-size: 0.875rem;
      margin-block-end: 0.35rem;
    }

    .hint {
      display: block;
      font-size: 0.78rem;
      color: var(--text-muted);
      margin-block-start: 0.25rem;
    }

    input[type="text"],
    select,
    textarea {
      width: 100%;
      font-size: 1rem;
      font-family: inherit;
      padding: 0.65rem 0.8rem;
      min-height: 44px;
      border-radius: 10px;
      border: 1px solid var(--border-color);
      background: var(--bg-page);
      color: var(--text-main);
    }

    textarea {
      resize: vertical;
      min-height: 82px;
    }

    input:focus-visible,
    select:focus-visible,
    textarea:focus-visible,
    button:focus-visible {
      outline: 3px solid var(--focus-ring);
      outline-offset: 2px;
    }

    .radio-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.5rem;
    }

    .radio-card {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.55rem 0.75rem;
      border: 1px solid var(--border-color);
      border-radius: 10px;
      background: var(--bg-page);
      cursor: pointer;
      font-size: 0.85rem;
      font-weight: 600;
      min-height: 44px;
    }

    .slider-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.85rem;
    }

    input[type="range"] {
      width: 100%;
      cursor: pointer;
    }

    .submit-btn {
      width: 100%;
      min-height: 50px;
      border: none;
      border-radius: 12px;
      background: var(--brand-color);
      color: #FFFFFF;
      font-size: 1rem;
      font-weight: 700;
      cursor: pointer;
      transition: opacity 0.15s ease;
    }
    .submit-btn:disabled {
      opacity: 0.55;
      cursor: wait;
    }

    .preview-stage {
      min-height: 440px;
      border: 1px dashed var(--border-color);
      border-radius: 14px;
      background: var(--bg-page);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 1.25rem;
      text-align: center;
    }

    .preview-media {
      max-width: 100%;
      max-height: 540px;
      border-radius: 12px;
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.18);
    }

    .meta-box {
      width: 100%;
      margin-top: 1rem;
      padding: 1rem;
      border-radius: 12px;
      background: var(--bg-subtle);
      text-align: left;
      font-size: 0.85rem;
    }

    .meta-code {
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 0.8rem;
      background: var(--bg-card);
      padding: 0.6rem;
      border-radius: 8px;
      border: 1px solid var(--border-color);
      display: block;
      margin-top: 0.35rem;
      word-break: break-word;
    }

    .hidden {
      display: none !important;
    }
  </style>
</head>
<body>
  <header class="topbar">
    <div class="brand-title">
      <span>🎨 Local AI Media Studio</span>
      <span class="badge">Showcase #2 • Image &amp; Video Web App</span>
    </div>
    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
      <span class="badge" id="lm-badge">
        <span class="status-dot" id="lm-dot"></span>
        <span id="lm-status-text">LM Studio (:1234) Checking...</span>
      </span>
      <span class="badge" id="comfy-badge">
        <span class="status-dot" id="comfy-dot"></span>
        <span id="comfy-status-text">ComfyUI (:8188) Checking...</span>
      </span>
    </div>
  </header>

  <main class="layout">
    <!-- Left Column: Custom Controls Form -->
    <section class="panel" aria-labelledby="form-heading">
      <h2 id="form-heading" style="margin-top: 0; font-size: 1.1rem;">ตั้งค่าการสร้างสื่อ (Custom Parameters)</h2>

      <form id="studio-form" action="/api/generate" method="POST">
        <!-- 1. Mode Selection -->
        <fieldset>
          <legend>1. เลือกโหมดการทำงาน (Output Mode)</legend>
          <div class="radio-grid">
            <label class="radio-card" for="mode-image">
              <input type="radio" id="mode-image" name="mode" value="image" checked />
              <span>🖼️ Generate Image</span>
            </label>
            <label class="radio-card" for="mode-video">
              <input type="radio" id="mode-video" name="mode" value="video" />
              <span>🎬 Generate Video</span>
            </label>
          </div>
        </fieldset>

        <!-- 2. Prompt & LM Studio Enhancer -->
        <fieldset>
          <legend>2. คำสั่งสร้างภาพ / วิดีโอ (Prompt &amp; AI Enhancer)</legend>
          <div class="form-group">
            <label class="field-label" for="prompt-input">พิมพ์โจทย์ภาษาไทย หรือ ภาษาอังกฤษ (Required):</label>
            <textarea
              id="prompt-input"
              name="prompt"
              required
              aria-describedby="prompt-help"
              placeholder="เช่น แมวส้มใส่ชุดอวกาศกำลังจิบกาแฟบนสถานีอวกาศรอบดาวเสาร์"
            >แมวส้มใส่แว่นตานักวิทยาศาสตร์กำลังทดลองสร้างหุ่นยนต์ AI ในห้องแล็บอนาคต</textarea>
            <span id="prompt-help" class="hint">สามารถพิมพ์ภาษาไทยสั้นๆ แล้วให้ LM Studio ขยายเป็น English Prompt อัตโนมัติได้</span>
          </div>

          <div class="form-group">
            <label for="use-llm" style="display: inline-flex; align-items: center; gap: 0.5rem; font-size: 0.875rem; font-weight: 600; cursor: pointer;">
              <input type="checkbox" id="use-llm" name="use_llm" checked />
              <span>ให้ LM Studio (:1234) ช่วยแปลและขยาย Prompt อัตโนมัติ</span>
            </label>
          </div>

          <div class="form-group">
            <label class="field-label" for="style-select">โทนภาพและแสง (Visual Style Preset):</label>
            <select id="style-select" name="style">
              <option value="photorealistic">Photorealistic Cinema (ภาพถ่ายสมจริง แสงภาพยนตร์)</option>
              <option value="cyberpunk">Cyberpunk Neon (ไฟนีออนไซเบอร์พังก์)</option>
              <option value="anime">Anime / Studio Ghibli (ภาพวาดอนิเมะสีอบอุ่น)</option>
              <option value="product">Commercial Product Shot (ภาพถ่ายสินค้าในสตูดิโอ)</option>
              <option value="raw">Raw Custom (ใช้ตามข้อความที่พิมพ์ตรงๆ)</option>
            </select>
          </div>
        </fieldset>

        <!-- 3. Video Engine Options (Visible only when Video mode is selected) -->
        <fieldset id="video-options-group" class="hidden">
          <legend>3. รูปแบบการสร้างวิดีโอ (Video Generation Engine)</legend>
          <div class="form-group">
            <label class="radio-card" for="vengine-motion" style="margin-bottom: 0.5rem;">
              <input type="radio" id="vengine-motion" name="video_engine" value="sd15_motion" checked />
              <span>⚡ AI Motion Clip (ใช้ SD 1.5 ตัวเดิม • รันผ่าน 100% บน VRAM 6GB)</span>
            </label>
            <label class="radio-card" for="vengine-comfy">
              <input type="radio" id="vengine-comfy" name="video_engine" value="comfy_video_api" />
              <span>🧩 Custom ComfyUI Video JSON (สำหรับ AnimateDiff / Wan2.1)</span>
            </label>
          </div>

          <div class="form-group hidden" id="custom-json-box">
            <label class="field-label" for="custom-workflow-json">วางโค้ด JSON ที่กด Export (API) จาก ComfyUI (เว้นว่างเพื่อใช้ไฟล์ตัวอย่าง AnimateDiff):</label>
            <textarea
              id="custom-workflow-json"
              name="custom_workflow_json"
              placeholder='วางเนื้อหาไฟล์ .json ที่ได้จากเมนู Workflow -> Export (API) ที่นี่...'
              autocorrect="off"
              autocapitalize="off"
              spellcheck="false"
            ></textarea>
          </div>
        </fieldset>

        <!-- 4. ComfyUI Node Parameters -->
        <fieldset>
          <legend>4. ตั้งค่าพารามิเตอร์โหนด ComfyUI (Node "3", "4", "5", "7")</legend>

          <div class="form-group">
            <label class="field-label" for="ckpt-select">โมเดล Checkpoint (Node "4"):</label>
            <select id="ckpt-select" name="ckpt_name">
              <option value="v1-5-pruned-emaonly.safetensors">v1-5-pruned-emaonly.safetensors</option>
            </select>
          </div>

          <div class="form-group">
            <span class="field-label">สัดส่วนภาพ Aspect Ratio (Node "5"):</span>
            <div class="radio-grid">
              <label class="radio-card" for="ar-1-1">
                <input type="radio" id="ar-1-1" name="aspect_ratio" value="1:1" checked />
                <span>1:1 (512×512)</span>
              </label>
              <label class="radio-card" for="ar-16-9">
                <input type="radio" id="ar-16-9" name="aspect_ratio" value="16:9" />
                <span>16:9 (640×384)</span>
              </label>
              <label class="radio-card" for="ar-9-16">
                <input type="radio" id="ar-9-16" name="aspect_ratio" value="9:16" />
                <span>9:16 (384×640)</span>
              </label>
              <label class="radio-card" for="ar-2-3">
                <input type="radio" id="ar-2-3" name="aspect_ratio" value="2:3" />
                <span>2:3 (512×768)</span>
              </label>
            </div>
          </div>

          <div class="slider-row form-group">
            <div>
              <label class="field-label" for="steps-range">Steps: <span id="steps-val">20</span></label>
              <input type="range" id="steps-range" name="steps" min="10" max="35" step="1" value="20" />
            </div>
            <div>
              <label class="field-label" for="cfg-range">CFG Scale: <span id="cfg-val">7.0</span></label>
              <input type="range" id="cfg-range" name="cfg" min="3.0" max="12.0" step="0.5" value="7.0" />
            </div>
          </div>

          <div class="form-group">
            <span class="field-label">การกำหนดค่า Seed (Node "3" KSampler):</span>
            <div class="radio-grid" style="margin-bottom: 0.5rem;">
              <label class="radio-card" for="seed-random">
                <input type="radio" id="seed-random" name="seed_mode" value="random" checked />
                <span>🎲 สุ่ม Seed ใหม่</span>
              </label>
              <label class="radio-card" for="seed-fixed">
                <input type="radio" id="seed-fixed" name="seed_mode" value="fixed" />
                <span>📌 ล็อกค่า Seed เดิม</span>
              </label>
            </div>
            <label class="field-label" for="seed-value">หมายเลข Seed (ใช้เมื่อเลือกโหมดล็อกค่า):</label>
            <input
              type="text"
              id="seed-value"
              name="seed_value"
              value="42"
              inputmode="numeric"
              pattern="[0-9]+"
              autocorrect="off"
              autocapitalize="off"
              spellcheck="false"
            />
          </div>

          <div class="form-group">
            <label class="field-label" for="neg-input">Negative Prompt (Node "7" สิ่งที่ไม่ต้องการให้ปรากฏ):</label>
            <input
              type="text"
              id="neg-input"
              name="negative_prompt"
              value="text, watermark, blurry, low quality, deformed hands"
            />
          </div>
        </fieldset>

        <button type="submit" id="generate-btn" class="submit-btn">
          🚀 สั่งสร้างสื่อด้วย Local AI (Generate Now)
        </button>
      </form>
    </section>

    <!-- Right Column: Output Preview & History -->
    <section class="panel" aria-labelledby="output-heading">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
        <h2 id="output-heading" style="margin: 0; font-size: 1.1rem;">ผลลัพธ์จากไปป์ไลน์ (Studio Viewport)</h2>
        <button
          type="button"
          id="reuse-seed-btn"
          class="badge"
          style="cursor: pointer; display: none;"
        >
          📌 นำ Seed ของภาพนี้ไปล็อกค่า
        </button>
      </div>

      <div class="preview-stage" id="preview-stage" aria-live="polite">
        <div id="empty-state">
          <p style="font-size: 1.05rem; font-weight: 700; margin-bottom: 0.35rem;">พร้อมสร้างภาพนิ่งและวิดีโอแอนิเมชัน</p>
          <p style="font-size: 0.85rem; color: var(--text-muted); max-width: 420px;">
            ตั้งค่าพารามิเตอร์ด้านซ้ายมือ แล้วกดปุ่ม <strong>สั่งสร้างสื่อด้วย Local AI</strong> ระบบจะส่งโจทย์ไปให้ LM Studio แต่ง Prompt และสั่ง ComfyUI เรนเดอร์กลับมาแสดงที่นี่ทันที
          </p>
        </div>

        <img id="result-img" class="preview-media hidden" alt="ผลลัพธ์จาก Local AI Studio" />

        <div id="result-meta" class="meta-box hidden">
          <div><strong>สถานะ:</strong> <span id="meta-status"></span></div>
          <div style="margin-top: 0.35rem;">
            <strong>ไฟล์ที่บันทึกไว้:</strong> <code id="meta-file"></code>
            • <strong>Seed:</strong> <code id="meta-seed"></code>
            • <strong>เวลาที่ใช้:</strong> <span id="meta-time"></span> วินาที
          </div>
          <div style="margin-top: 0.5rem;">
            <strong>English Prompt ที่ส่งเข้าโหนด "6" ของ ComfyUI:</strong>
            <span class="meta-code" id="meta-prompt"></span>
          </div>
        </div>
      </div>
    </section>
  </main>

  <script>
    const form = document.getElementById('studio-form');
    const generateBtn = document.getElementById('generate-btn');
    const stepsRange = document.getElementById('steps-range');
    const stepsVal = document.getElementById('steps-val');
    const cfgRange = document.getElementById('cfg-range');
    const cfgVal = document.getElementById('cfg-val');
    const videoOptionsGroup = document.getElementById('video-options-group');
    const customJsonBox = document.getElementById('custom-json-box');
    const reuseSeedBtn = document.getElementById('reuse-seed-btn');
    const seedValueInput = document.getElementById('seed-value');
    const seedFixedRadio = document.getElementById('seed-fixed');

    let lastGeneratedSeed = null;

    stepsRange.addEventListener('input', () => {
      stepsVal.textContent = stepsRange.value;
    });

    cfgRange.addEventListener('input', () => {
      cfgVal.textContent = Number(cfgRange.value).toFixed(1);
    });

    document.querySelectorAll('input[name="mode"]').forEach((radio) => {
      radio.addEventListener('change', () => {
        const isVideo = document.getElementById('mode-video').checked;
        videoOptionsGroup.classList.toggle('hidden', !isVideo);
      });
    });

    document.querySelectorAll('input[name="video_engine"]').forEach((radio) => {
      radio.addEventListener('change', () => {
        const isCustomApi = document.getElementById('vengine-comfy').checked;
        customJsonBox.classList.toggle('hidden', !isCustomApi);
      });
    });

    reuseSeedBtn.addEventListener('click', () => {
      if (lastGeneratedSeed !== null) {
        seedValueInput.value = String(lastGeneratedSeed);
        seedFixedRadio.checked = true;
      }
    });

    async function refreshStatus() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();

        const lmDot = document.getElementById('lm-dot');
        const lmText = document.getElementById('lm-status-text');
        if (data.lm_studio_online) {
          lmDot.className = 'status-dot online';
          const modelName = data.lm_studio_models[0] || 'Ready';
          lmText.textContent = 'LM Studio: ' + modelName;
        } else {
          lmDot.className = 'status-dot offline';
          lmText.textContent = 'LM Studio: Offline (ใช้ Prompt ตรงๆ)';
        }

        const comfyDot = document.getElementById('comfy-dot');
        const comfyText = document.getElementById('comfy-status-text');
        const ckptSelect = document.getElementById('ckpt-select');
        if (data.comfyui_online) {
          comfyDot.className = 'status-dot online';
          comfyText.textContent = 'ComfyUI (:8188): Online';
          if (Array.isArray(data.checkpoints) && data.checkpoints.length > 0) {
            ckptSelect.innerHTML = '';
            data.checkpoints.forEach((ckpt) => {
              const opt = document.createElement('option');
              opt.value = ckpt;
              opt.textContent = ckpt;
              ckptSelect.appendChild(opt);
            });
          }
        } else {
          comfyDot.className = 'status-dot offline';
          comfyText.textContent = 'ComfyUI: Offline (Preview Mode)';
        }
      } catch (err) {
        console.error(err);
      }
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      generateBtn.disabled = true;
      generateBtn.textContent = '⏳ กำลังประมวลผลผ่าน LM Studio & ComfyUI...';

      const formData = new FormData(form);
      const payload = {
        mode: formData.get('mode'),
        prompt: formData.get('prompt'),
        use_llm: document.getElementById('use-llm').checked,
        style: formData.get('style'),
        video_engine: formData.get('video_engine') || 'sd15_motion',
        custom_workflow_json: formData.get('custom_workflow_json') || '',
        ckpt_name: formData.get('ckpt_name'),
        aspect_ratio: formData.get('aspect_ratio'),
        steps: Number(formData.get('steps')),
        cfg: Number(formData.get('cfg')),
        seed_mode: formData.get('seed_mode'),
        seed_value: formData.get('seed_value'),
        negative_prompt: formData.get('negative_prompt'),
      };

      try {
        const res = await fetch('/api/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const result = await res.json();

        document.getElementById('empty-state').classList.add('hidden');
        const imgEl = document.getElementById('result-img');
        imgEl.src = result.data_uri;
        imgEl.classList.remove('hidden');

        const metaBox = document.getElementById('result-meta');
        metaBox.classList.remove('hidden');
        document.getElementById('meta-status').textContent = result.used_fallback
          ? 'โหมดจำลองภาพ (ไม่ได้เปิด ComfyUI จึงสร้างภาพ Preview ให้แทน)'
          : (result.mode === 'video' ? 'สร้างวิดีโอแอนิเมชันสำเร็จ (Animated WebP + GIF)' : 'เรนเดอร์ภาพนิ่งจาก ComfyUI สำเร็จ');
        document.getElementById('meta-file').textContent = result.SavedPath;
        document.getElementById('meta-seed').textContent = result.seed;
        document.getElementById('meta-time').textContent = result.elapsed_sec;
        document.getElementById('meta-prompt').textContent = result.final_prompt;

        lastGeneratedSeed = result.seed;
        reuseSeedBtn.style.display = 'inline-flex';
      } catch (err) {
        alert('เกิดข้อผิดพลาดในการสร้างสื่อ: ' + err.message);
      } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = '🚀 สั่งสร้างสื่อด้วย Local AI (Generate Now)';
      }
    });

    refreshStatus();
  </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# HTTP Server Handler
# ---------------------------------------------------------------------------
class MediaStudioRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/" or self.path.startswith("/index.html"):
            body = STUDIO_UI_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/status":
            status = inspect_environment()
            body = json.dumps(status, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self) -> None:
        if self.path == "/api/generate":
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length).decode("utf-8")
            params = json.loads(raw_body) if raw_body else {}
            result = execute_studio_job(params)
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
    parser = argparse.ArgumentParser(description="Local AI Media Studio — Custom Image & Video Web App")
    parser.add_argument("--port", type=int, default=8090, help="พอร์ตสำหรับเปิด Web App (ค่าเริ่มต้น: 8090)")
    parser.add_argument(
        "--cli-mode",
        choices=["image", "video"],
        help="หากระบุ --cli-mode จะรันสร้างไฟล์ผ่าน Command Line ทันทีโดยไม่เปิด Web Server",
    )
    parser.add_argument("--prompt", type=str, default="แมวส้มนักบินอวกาศลอยตัวอยู่ในสถานีอวกาศ", help="คำสั่งสร้างภาพ/วิดีโอ")
    args = parser.parse_args()

    if args.cli_mode:
        print(f"กำลังรันโหมด CLI ({args.cli_mode}) สำหรับโจทย์: {args.prompt}")
        res = execute_studio_job({"mode": args.cli_mode, "prompt": args.prompt})
        print(f"บันทึกไฟล์สำเร็จที่: {res['SavedPath']} (Seed: {res['seed']}, เวลา: {res['elapsed_sec']}s)")
        return

    server = HTTPServer(("127.0.0.1", args.port), MediaStudioRequestHandler)
    print("=" * 68)
    print("🎨 Local AI Media Studio (Custom Image & Video Web App)")
    print(f"👉 เปิดเบราว์เซอร์ไปที่: http://127.0.0.1:{args.port}")
    print("   (กด Ctrl + C เพื่อปิดเซิร์ฟเวอร์)")
    print("=" * 68)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nปิดเซิร์ฟเวอร์ Local AI Media Studio เรียบร้อยแล้ว")


if __name__ == "__main__":
    main()
