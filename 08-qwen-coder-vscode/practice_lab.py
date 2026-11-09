"""
ไฟล์ฝึกปฏิบัติการเขียนโค้ดคู่กับ Qwen2.5-Coder บน VS Code (Continue / Cline)
===========================================================================
วิธีฝึก:
1. เปิดไฟล์นี้ในโปรแกรม VS Code (หลังจากติดตั้ง Extension 'Continue' และเชื่อมกับ LM Studio พอร์ต 1234 แล้ว)
2. ลองทำตามภารกิจที่ 1 ถึง 4 ด้านล่างโดยใช้คีย์ลัดของ Qwen2.5-Coder
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any


# ---------------------------------------------------------------------------
# ภารกิจที่ 1: ทดสอบ Tab Autocomplete (เติมโค้ดอัตโนมัติขณะพิมพ์)
# ---------------------------------------------------------------------------
# วิธีทำ: ลองวางเคอร์เซอร์ต่อท้ายบรรทัด def ด้านล่าง กด Enter แล้วรอ 1 วินาที
# Qwen2.5-Coder จะแสดงโค้ดสีเทาจางๆ ขึ้นมา ให้กดปุ่ม Tab เพื่อยอมรับโค้ดทันที!
def calculate_vram_usage_gb(model_params_billion: float, bits_per_weight: int = 4) -> float:
    """คำนวณปริมาณ VRAM (GB) โดยประมาณของโมเดล LLM จากจำนวนพันล้านพารามิเตอร์และระดับ Quantization"""
    weights_gb = (model_params_billion * bits_per_weight) / 8.0
    kv_cache_overhead_gb = 0.65
    return round(weights_gb + kv_cache_overhead_gb, 2)


# ---------------------------------------------------------------------------
# ภารกิจที่ 2: ทดสอบ Inline Edit (กด Ctrl + I หรือ Cmd + I บน macOS)
# ---------------------------------------------------------------------------
# วิธีทำ:
# 1) ใช้เมาส์ลากคลุมฟังก์ชัน fetch_comfyui_queue() ด้านล่างทั้งหมด
# 2) กดปุ่ม Ctrl + I (Windows) หรือ Cmd + I (macOS)
# 3) พิมพ์คำสั่งภาษาไทยว่า: "เพิ่ม try/except ดักจับ URLError และตั้งค่า timeout=5 วินาที พร้อมเขียน Docstring ภาษาไทย"
# 4) กด Enter แล้วกด Accept (Ctrl + Shift + Enter)
def fetch_comfyui_queue(base_url: str = "http://127.0.0.1:8188") -> dict[str, Any]:
    with urllib.request.urlopen(f"{base_url}/queue") as response:
        return json.loads(response.read().decode("utf-8"))


# ---------------------------------------------------------------------------
# ภารกิจที่ 3: ทดสอบค้นหาและแก้บั๊กด้วย Chat (กด Ctrl + L หรือ Cmd + L)
# ---------------------------------------------------------------------------
# วิธีทำ:
# 1) ลากคลุมฟังก์ชัน parse_llm_json_response() ด้านล่าง (ซึ่งมีบั๊กซ่อนอยู่ 2 จุด)
# 2) กด Ctrl + L (Windows) หรือ Cmd + L (macOS) เพื่อส่งโค้ดเข้าหน้าต่างแชตด้านซ้าย
# 3) พิมพ์ถามว่า: "ฟังก์ชันนี้มีโอกาสเกิด Error อะไรบ้างถ้า LLM ตอบข้อความที่มี ```json ครอบอยู่ และช่วยแก้โค้ดให้ปลอดภัยขึ้น"
def parse_llm_json_response(raw_text: str) -> list[dict[str, str]]:
    # บั๊กที่ซ่อนอยู่: ถ้า raw_text มี ```json ... ``` ครอบอยู่ json.loads() จะพังทันที
    data = json.loads(raw_text)
    return data["items"]


# ---------------------------------------------------------------------------
# ภารกิจที่ 4: สั่งสร้าง Unit Test อัตโนมัติด้วยคำสั่ง /test หรือ @Files
# ---------------------------------------------------------------------------
# วิธีทำ:
# เปิดช่องแชต Continue (Ctrl + L) แล้วพิมพ์:
# "@practice_lab.py ช่วยเขียนฟังก์ชันทดสอบด้วย pytest สำหรับ calculate_vram_usage_gb และ parse_llm_json_response"
if __name__ == "__main__":
    vram_3b = calculate_vram_usage_gb(3.0, bits_per_weight=4)
    vram_7b = calculate_vram_usage_gb(7.0, bits_per_weight=4)
    print(f"โมเดล 3B (Q4_K_M) ใช้ VRAM ประมาณ: {vram_3b} GB")
    print(f"โมเดล 7B (Q4_K_M) ใช้ VRAM ประมาณ: {vram_7b} GB")
