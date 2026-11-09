# 05 — CineLocal Studio: AI Storyboard & Pitch Deck Director (Showcase Project)

> **โปรเจกต์ตัวอย่างสำหรับแจกให้ผู้เข้าอบรมศึกษาต่อยอดหลังจบคลาส 6 ชั่วโมง**  
> เปลี่ยนไอเดียภาษาไทยเพียง 1 บรรทัด ให้กลายเป็น **Storyboard ภาพยนตร์/แคมเปญ 3 ฉาก** พร้อมมุมกล้อง, โทนสี, บทบรรยายภาษาไทย, ภาพประกอบ `512x512` จาก Stable Diffusion 1.5 และส่งออกเป็นไฟล์ **HTML Pitch Deck** โดยรันแบบออฟไลน์ 100%

- **ทดลองเล่นผ่านหน้าเว็บทันที (มีโหมด Instant Demo ไม่ต้องรอเปิดเซิร์ฟเวอร์):** [`docs/showcase.html`](../docs/showcase.html) หรือผ่าน GitHub Pages ที่ **`https://dhanabhon.github.io/mastering-local-ai-stack/showcase.html`**
- **โค้ด Python ฉบับสมบูรณ์ (ใช้เฉพาะไลบรารีใน `requirements.txt`):** [`05-bonus-showcase/app.py`](./app.py)

---

## ทำไมโปรเจกต์นี้ถึงต่อยอดจากสิ่งที่เรียนในคลาส 6 ชั่วโมงได้ทันที?

โปรเจกต์นี้ **ไม่ได้ใช้ไลบรารีภายนอกเพิ่มเติมแม้แต่ตัวเดียว** แต่เกิดจากการนำฟังก์ชันพื้นฐานที่ผู้เรียนได้ลงมือทำใน **Module 1 ถึง Module 4** มาประกอบร่างเข้าด้วยกัน:

| โมดูลในห้องเรียน | สิ่งที่เรียนในคลาส | วิธีนำมาต่อยอดใน `CineLocal Studio` |
| :--- | :--- | :--- |
| **Module 1**<br>(`09:00 - 10:15`) | การใช้ `requests.get()` เช็กสถานะเซิร์ฟเวอร์ และการใช้ `pandas.DataFrame` จัดการตารางข้อมูล | ฟังก์ชัน `check_local_ai_stack()` ตรวจสอบความพร้อมของพอร์ต `1234` และ `8188` ก่อนเริ่มงาน และสรุปเวลาเรนเดอร์ของทั้ง 3 ฉากลง `DataFrame` พร้อมส่งออกเป็นไฟล์ HTML Pitch Deck |
| **Module 2**<br>(`10:30 - 12:00`) | การสั่ง LM Studio (`OpenAI` SDK) สกัดข้อมูลบทความภาษาไทยออกมาเป็น JSON Schema | ฟังก์ชัน `generate_storyboard_json()` ปรับ `DIRECTOR_SYSTEM_PROMPT` ให้ LLM สวมบทเป็นผู้กำกับภาพยนตร์ แตกไอเดียภาษาไทย 1 บรรทัดออกเป็น JSON Array `"scenes"` จำนวน 3 ฉาก พร้อมฟิลด์ `camera_angle`, `color_palette` และ `sd_positive_prompt` |
| **Module 3**<br>(`13:00 - 14:30`) | การแกะโครงสร้างไฟล์ `sd15_txt2img_api.json` (Node `"6"`, `"7"`, `"3"`, `"4"`, `"5"`, `"8"`, `"9"`) | ฟังก์ชัน `render_scene_image()` โหลดไฟล์ JSON ต้นแบบ แล้วแทนค่า `text`, `seed`, `steps` และ `cfg` ตาม `STYLE_PRESETS` (`cyberpunk`, `cinematic`, `watercolor`, `isometric`) |
| **Module 4**<br>(`14:45 - 16:00`) | การส่ง HTTP `POST /prompt`, วนลูปเช็ก `/history/{prompt_id}` และดึงภาพจาก `/view` ภายใต้ข้อจำกัด VRAM 6GB | แทนที่จะสั่งวาดพร้อมกัน 3 ภาพ (`batch_size = 3`) ซึ่งจะทำให้การ์ดจอ **RTX 3050 6GB** เต็ม ระบบใช้ลูป `for scene in storyboard["scenes"]:` ส่งคิวเรนเดอร์ทีละฉากด้วย `base_seed + idx` ทำให้กิน VRAM คงที่เพียง **~4.2 GB** |

---

## วิธีรันโปรเจกต์ด้วยตัวเอง (Step-by-Step Self-Study)

### วิธีที่ 1: เปิดทดลองเล่นผ่านหน้าเว็บ (`docs/showcase.html`)
หากต้องการดูการทำงานของระบบทันที (หรือวิทยากรใช้เปิดสาธิตหน้าชั้นเรียน):
1. เปิดไฟล์ [`docs/showcase.html`](../docs/showcase.html) บนเว็บเบราว์เซอร์ทั่วไป หรือรันคำสั่ง:
   ```bash
   python 05-bonus-showcase/app.py --serve
   ```
   แล้วเปิดเบราว์เซอร์ไปที่ `http://localhost:8080/showcase.html`
2. เลือกโหมด **Instant Demo (จำลองทันที)** เพื่อทดลองกดเปลี่ยนโจทย์ภาษาไทย เปลี่ยนสไตล์ภาพ ดูกราฟโหนด ComfyUI ทำงานทีละสเต็ป และกดปุ่ม **Export Pitch Deck (.html)** ได้ทันที
3. หากเปิด **LM Studio (`:1234`)** ไว้แล้ว สามารถสลับสวิตช์เป็น **Live Local AI (`:1234` + `:8188`)** เพื่อให้หน้าเว็บยิง API ไปให้โมเดล LLM บนเครื่องคิดบท 3 ฉากสดๆ ได้เลย

---

### วิธีที่ 2: รันไปป์ไลน์เต็มรูปแบบผ่าน Command Line (LLM + วาดภาพจริง 3 ฉาก)
เมื่อเปิด **LM Studio Server (Port 1234)** และ **ComfyUI (Port 8188)** เรียบร้อยแล้ว:

```bash
# ตัวอย่างที่ 1: สไตล์ Cyberpunk Neon
python 05-bonus-showcase/app.py \
  --idea "ตลาดน้ำอัจฉริยะในกรุงเทพปี 2088 ที่เรือหางยาวขับเคลื่อนด้วยพลังงานแม่เหล็กและหุ่นยนต์ชงชาไทย" \
  --style cyberpunk

# ตัวอย่างที่ 2: สไตล์ภาพยนตร์ Golden Hour Film
python 05-bonus-showcase/app.py \
  --idea "แคมเปญกาแฟดริปออร์แกนิกจากยอดดอยแม่ฮ่องสอนท่ามกลางทะเลหมอกยามเช้า" \
  --style cinematic

# ตัวอย่างที่ 3: สไตล์ Ghibli Watercolor
python 05-bonus-showcase/app.py \
  --idea "นักศึกษาวิศวกรรมศาสตร์สร้างโดรนสำรวจวิหารโบราณกลางป่าหิมพานต์" \
  --style watercolor
```

เมื่อรันเสร็จ ระบบจะบันทึกไฟล์ผลลัพธ์ไว้ในโฟลเดอร์ `05-bonus-showcase/outputs/`:
- `scene_01.png`, `scene_02.png`, `scene_03.png` — ภาพขนาด `512x512` พิกเซลจาก ComfyUI
- `storyboard_data.json` — ข้อมูล JSON ทั้งหมดที่ LM Studio สร้างขึ้น
- `storyboard_pitch_deck.html` — ไฟล์หน้าเว็บนำเสนอผลงาน (ฝังรูปภาพแบบ Base64 เรียบร้อย ส่งไฟล์เดียวไปเปิดพรีเซนต์ได้ทุกเครื่อง)

---

## ไอเดียสำหรับนำไปพัฒนาต่อยอดเป็นโปรเจกต์ของตัวเอง

1. **Product Packaging & Ad Studio:** เปลี่ยน `DIRECTOR_SYSTEM_PROMPT` ให้รับชื่อสินค้า OTOP หรือธุรกิจ SME ไทย แล้วสร้างภาพตัวอย่างบรรจุภัณฑ์ 3 มุมมองพร้อมคำโฆษณาภาษาไทย-อังกฤษ
2. **Interactive Visual Novel / Game Quest Maker:** ให้ LM Studio แต่งเนื้อเรื่องเกมแนวตั้งคำถาม พร้อมสร้างตัวเลือก A/B และสั่ง ComfyUI วาดฉากประกอบตามการตัดสินใจของผู้เล่น
3. **Slide Deck Visual Generator:** อ่านเนื้อหาจากไฟล์เลกเชอร์ภาษาไทย (`.txt` หรือ `.md`) แล้วสั่งสรุปเป็นหัวข้อย่อยพร้อมวาดภาพประกอบประจำแต่ละหัวข้อโดยอัตโนมัติ
4. **Image-to-Image Restyler:** แก้ไขเวิร์กโฟลว์ใน Module 3 จาก `EmptyLatentImage` เป็น `LoadImage` + `VAEEncode` (`denoise = 0.60`) เพื่ออัปโหลดภาพสเก็ตช์ลายเส้นแล้วสั่งวาดใหม่เป็น 3 สไตล์เปรียบเทียบกัน
