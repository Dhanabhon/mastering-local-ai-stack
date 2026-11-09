"""
ตัวเชื่อมต่อ ComfyUI (:8188) ที่แลป 06 และ 07 ใช้ร่วมกัน
ทุกความล้มเหลวจะถูกแปลงเป็น StudioError พร้อมข้อความบอกวิธีแก้ เพื่อไม่ให้ผู้เรียนเข้าใจผิดว่า AI ทำงานแล้ว
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

COMFYUI_BASE_URL = "http://127.0.0.1:8188"
COMFY_OFFLINE_MESSAGE = "เชื่อมต่อ ComfyUI ที่ http://127.0.0.1:8188 ไม่ได้ กรุณาเปิด ComfyUI ก่อนแล้วลองใหม่"
NO_CHECKPOINT_MESSAGE = (
    "ComfyUI ยังไม่มีไฟล์โมเดล กรุณาวางไฟล์ .safetensors เช่น v1-5-pruned-emaonly.safetensors "
    "ในโฟลเดอร์ ComfyUI/models/checkpoints แล้วรีสตาร์ต ComfyUI"
)


class StudioError(Exception):
    """ความล้มเหลวที่ผู้เรียนแก้เองได้ ข้อความใน Exception จะแสดงบนหน้าเว็บโดยตรง"""


def http_get_json(url: str, timeout: float = 3.0) -> dict[str, Any]:
    with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_post_json(url: str, payload: dict[str, Any], timeout: float = 15.0) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_get_bytes(url: str, timeout: float = 15.0) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=timeout) as resp:
        return resp.read()


def describe_comfy_rejection(payload: dict[str, Any]) -> str:
    """แปลง JSON ที่ ComfyUI ตอบกลับ (HTTP 400 จาก /prompt) เป็นข้อความบอกวิธีแก้"""
    error = payload.get("error", {})
    if error.get("type") == "missing_node_type":
        class_type = error.get("extra_info", {}).get("class_type", "ไม่ทราบชื่อ")
        return (
            f"ComfyUI ไม่มีโหนด {class_type} กรุณาติดตั้ง Custom Node ที่ Workflow นี้ต้องใช้ "
            "(AnimateDiff ใช้ ComfyUI-AnimateDiff-Evolved) ผ่าน ComfyUI Manager แล้วรีสตาร์ต ComfyUI"
        )

    problems: list[str] = []
    for node in payload.get("node_errors", {}).values():
        for item in node.get("errors", []):
            if item.get("extra_info", {}).get("input_name") == "ckpt_name":
                return NO_CHECKPOINT_MESSAGE
            problems.append(f"{node.get('class_type', 'Node')}: {item.get('message')} ({item.get('details')})")

    return "ComfyUI ปฏิเสธ Workflow: " + ("; ".join(problems) or str(error.get("message", "ไม่ทราบสาเหตุ")))


def describe_execution_error(status: dict[str, Any]) -> str:
    """ดึงสาเหตุจากประวัติงานที่ ComfyUI รันแล้วล้มเหลว เช่น หน่วยความจำไม่พอ"""
    for name, detail in status.get("messages", []):
        if name == "execution_error":
            return f"ComfyUI รันโหนด {detail.get('node_type')} ไม่สำเร็จ: {detail.get('exception_message', '').strip()}"
    return "ComfyUI รัน Workflow ไม่สำเร็จ กรุณาดูรายละเอียดในหน้าต่าง ComfyUI"


def _rejection_message(exc: urllib.error.HTTPError) -> str:
    try:
        return describe_comfy_rejection(json.loads(exc.read().decode("utf-8")))
    except ValueError:
        return f"ComfyUI ตอบกลับ HTTP {exc.code}"


def list_checkpoints() -> list[str]:
    """รายชื่อไฟล์โมเดลที่ ComfyUI เห็น (ส่ง OSError ออกไปถ้าเซิร์ฟเวอร์ไม่เปิด)"""
    info = http_get_json(f"{COMFYUI_BASE_URL}/object_info/CheckpointLoaderSimple", timeout=3.0)
    return info["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]


def pick_checkpoint(preferred: str) -> str:
    """ตรวจก่อนเริ่มงานว่า ComfyUI เปิดอยู่และมีโมเดล แล้วคืนชื่อไฟล์ที่จะใช้"""
    try:
        names = list_checkpoints()
    except OSError as exc:
        raise StudioError(COMFY_OFFLINE_MESSAGE) from exc
    if not names:
        raise StudioError(NO_CHECKPOINT_MESSAGE)
    return preferred if preferred in names else names[0]


def upload_image(png_bytes: bytes, filename: str) -> str:
    """อัปโหลดภาพเข้าโฟลเดอร์ input ของ ComfyUI สำหรับโหนด LoadImage และคืนชื่อไฟล์"""
    boundary = "----LocalAiStackBoundary"
    head = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="{Path(filename).name}"\r\n'
        "Content-Type: image/png\r\n\r\n"
    ).encode("utf-8")
    tail = f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n--{boundary}--\r\n'
    req = urllib.request.Request(
        f"{COMFYUI_BASE_URL}/upload/image",
        data=head + png_bytes + tail.encode("utf-8"),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            return json.loads(resp.read().decode("utf-8"))["name"]
    except urllib.error.HTTPError as exc:
        raise StudioError(f"อัปโหลดภาพเข้า ComfyUI ไม่สำเร็จ (HTTP {exc.code})") from exc
    except OSError as exc:
        raise StudioError(COMFY_OFFLINE_MESSAGE) from exc


def _wait_for_media(prompt_id: str, timeout_sec: int) -> tuple[bytes, str]:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        entry = http_get_json(f"{COMFYUI_BASE_URL}/history/{prompt_id}", timeout=5.0).get(prompt_id)
        if entry is None:
            time.sleep(0.75)
            continue

        status = entry.get("status", {})
        if status.get("status_str") == "error":
            raise StudioError(describe_execution_error(status))

        for node_out in entry.get("outputs", {}).values():
            for media_key in ("images", "gifs", "videos"):
                if node_out.get(media_key):
                    item = node_out[media_key][0]
                    query = urllib.parse.urlencode(
                        {
                            "filename": item["filename"],
                            "subfolder": item.get("subfolder", ""),
                            "type": item.get("type", "output"),
                        }
                    )
                    media = http_get_bytes(f"{COMFYUI_BASE_URL}/view?{query}", timeout=15.0)
                    return media, Path(item["filename"]).suffix.lower() or ".png"
        raise StudioError("ComfyUI รันเสร็จแต่ไม่มีไฟล์ผลลัพธ์ กรุณาตรวจว่า Workflow มีโหนด Save")

    raise StudioError(
        f"ComfyUI ใช้เวลาเกิน {timeout_sec} วินาที งานอาจยังรันอยู่ในคิว ลดความละเอียดหรือจำนวน Steps แล้วลองใหม่"
    )


def queue_and_fetch_comfy_media(workflow: dict[str, Any], timeout_sec: int = 150) -> tuple[bytes, str]:
    """ส่ง Workflow เข้าคิว ComfyUI แล้วคืน (ไบต์ของไฟล์, นามสกุล) ถ้าไม่สำเร็จจะ raise StudioError"""
    try:
        queued = http_post_json(f"{COMFYUI_BASE_URL}/prompt", {"prompt": workflow}, timeout=10.0)
        return _wait_for_media(queued["prompt_id"], timeout_sec)
    except urllib.error.HTTPError as exc:
        raise StudioError(_rejection_message(exc)) from exc
    except OSError as exc:
        raise StudioError(COMFY_OFFLINE_MESSAGE) from exc
