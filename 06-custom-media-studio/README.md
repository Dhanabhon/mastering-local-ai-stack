# 06-custom-media-studio: Local AI Media Studio (Custom Image & Video Web App)

โปรเจกต์ Showcase ตัวที่ 2 สำหรับผู้เรียนที่ต้องการ **Web Application ส่วนตัวบนเครื่อง (Local Web UI)** ที่ทำงานครอบ **LM Studio (`:1234`)** และ **ComfyUI (`:8188`)** บน Environment (`.venv`) เดิมที่ติดตั้งไว้แล้ว โดยไม่ต้องเปิดหน้ากราฟโหนดที่ซับซ้อนของ ComfyUI ทุกครั้ง

---

## จุดเด่นของระบบ (Features)

1. **สลับโหมดการทำงานได้ในคลิกเดียว (`Generate Image` / `Generate Video`):**
   - 🖼️ **Generate Image (Custom Text-to-Image):**
     - พิมพ์โจทย์ภาษาไทยหรืออังกฤษ (เลือกเปิด/ปิดให้ **LM Studio** ช่วยขยายเป็น English Prompt ได้)
     - ปรับพารามิเตอร์โหนด ComfyUI ได้ครบจากหน้าเว็บ: **โมเดล Checkpoint (ดึงรายชื่อไฟล์ `.safetensors` จาก ComfyUI อัตโนมัติ)**, **สัดส่วนภาพ Aspect Ratio (`1:1`, `16:9`, `9:16`, `2:3`)**, **Steps**, **CFG Scale**, **Seed (`สุ่มใหม่` หรือ `ล็อกค่าคงที่`)**, และ **Negative Prompt**
   - 🎬 **Generate Video (รองรับ 2 รูปแบบ):**
     - **รูปแบบที่ 1 (`Ken Burns Slideshow` • ใช้โมเดล SD 1.5 เดิม เหมาะกับการ์ดจอ 6GB VRAM แต่ไม่ใช่ AI Video):** สั่ง ComfyUI วาดภาพนิ่ง 2 ภาพด้วย Seed เดียวกัน แล้วใช้ Pillow ทำ Crossfade และซูมออกมาเป็น `.webp` และ `.gif` (24 เฟรม, 12 FPS) การเคลื่อนไหวเกิดจากการตัดต่อ ไม่ได้เกิดจากโมเดล
     - **รูปแบบที่ 2 (`Custom ComfyUI Video JSON` • สำหรับ AnimateDiff / Wan2.1 / LTX-Video):** รองรับการนำไฟล์ `.json` ที่กด `Workflow → Export (API)` จาก ComfyUI มาวางในหน้าเว็บ (หรือใช้ไฟล์แม่แบบ `workflows/sd15_animatediff_api.json` ที่เตรียมไว้ให้) เพื่อสั่งเรนเดอร์วิดีโอผ่านหน้าเว็บได้โดยตรง
       - แม่แบบ AnimateDiff ต้องติดตั้ง Custom Node `ComfyUI-AnimateDiff-Evolved` และวาง Motion Model `mm_sd_v15_v2.ckpt` ใน `ComfyUI/models/animatediff_models/` ก่อน
2. **ไม่ต้องติดตั้งไลบรารีเพิ่ม (Zero Extra Dependencies):**
   - ใช้เฉพาะไลบรารีมาตรฐานใน `.venv` ของคอร์ส (`requests`, `openai`, `Pillow`, `pandas`)
3. **บันทึกไฟล์ผลลัพธ์และประวัติอัตโนมัติ:**
   - ทุกครั้งที่กดสร้าง ไฟล์ภาพนิ่งหรือวิดีโอแอนิเมชันจะถูกบันทึกไว้ใน `06-custom-media-studio/outputs/` พร้อมบันทึกรายละเอียด Prompt และเลข Seed ลงตาราง `generation_history.csv`

---

## ก่อนเริ่ม

เปิด ComfyUI และวางไฟล์ Checkpoint ใน `ComfyUI/models/checkpoints/` ให้เรียบร้อย หากขาดส่วนใด หน้าเว็บจะแจ้งสาเหตุและวิธีแก้ โดยไม่สร้างภาพแทนให้ ถ้าเปิดตัวเลือกให้ LM Studio ช่วยแปล ต้องเปิด Local Server ที่พอร์ต `1234` ด้วย

---

## วิธีเปิดใช้งาน Web App

เปิด Terminal / PowerShell ที่โฟลเดอร์หลักของโปรเจกต์ (`mastering-local-ai-stack`) เปิดใช้งาน `.venv` แล้วรันคำสั่ง:

```bash
python 06-custom-media-studio/app.py
```

จากนั้นเปิดเบราว์เซอร์ไปที่:
👉 **`http://127.0.0.1:8090`**

*(หากต้องการเปลี่ยนพอร์ต สามารถระบุ `--port 8095` ได้ หรือหากต้องการรันแบบ Command Line ทันทีโดยไม่เปิดหน้าเว็บ ใช้คำสั่ง `python 06-custom-media-studio/app.py --cli-mode video --prompt "แมวส้มนักบินอวกาศ"`)*
