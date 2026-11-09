# 08-qwen-coder-vscode: การใช้ Qwen2.5-Coder ช่วยเขียนโค้ดบน VS Code (Local AI Coding Assistant)

คู่มือพิเศษสำหรับเปลี่ยนโปรแกรม **Visual Studio Code (VS Code)** ให้กลายเป็น **AI Coding Assistant ส่วนตัว (ทำงานคล้าย GitHub Copilot และ Cursor แบบออฟไลน์ 100%)** โดยใช้โมเดลตระกูล **Qwen2.5-Coder** ที่เปิดรันผ่าน **LM Studio (`http://localhost:1234/v1`)** ที่เราตั้งค่าไว้แล้วในคอร์สเรียน

---

## 1. เลือกขนาดโมเดล Qwen2.5-Coder ให้เหมาะกับการ์ดจอของคุณ

โมเดลตระกูล **Qwen2.5-Coder** จากทีม Alibaba Cloud เป็นโมเดล Open-Weight สำหรับงานเขียนโค้ดที่ได้รับความนิยมสูงสุดในปัจจุบัน เพราะฝึกฝนมาบนโค้ดกว่า 5.5 ล้านล้านโทเคน รองรับทั้งการเติมโค้ดระหว่างบรรทัด (**FIM — Fill-In-the-Middle**) และการสนทนาแก้บั๊กภาษาไทยและอังกฤษ:

| รุ่นโมเดลใน LM Studio (ค้นหาในช่อง Search) | ระดับ Quantization | กินพื้นที่ VRAM | เหมาะกับเครื่องสเปกใด / งานแบบใด |
| :--- | :--- | :--- | :--- |
| **`Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF`** | `Q4_K_M` หรือ `Q8_0` | **~1.0 – 1.6 GB** | **สายเติมโค้ดไว (Tab Autocomplete):** ตอบสนองไวมาก (<150ms) เหมาะเปิดทิ้งไว้เติมโค้ดอัตโนมัติขณะพิมพ์โดยไม่กินการ์ดจอ |
| **`Qwen/Qwen2.5-Coder-3B-Instruct-GGUF`** ⭐ *(แนะนำหลัก)* | `Q4_K_M` | **~2.1 GB** | **สมดุลที่สุดสำหรับ RTX 3050 (6GB VRAM):** ใช้ได้ทั้ง **Chat ถาม-ตอบโค้ด (`Ctrl+L`)**, **สั่งแก้โค้ดในไฟล์ (`Ctrl+I`)**, และ **Tab Autocomplete** พร้อมเปิดคู่กับโปรแกรมอื่นได้สบาย |
| **`Qwen/Qwen2.5-Coder-7B-Instruct-GGUF`** 🔥 *(ฉลาดสุดในงบ 6GB)* | `Q4_K_M` | **~4.7 GB** | **สำหรับการ์ดจอ RTX 3050 6GB (เมื่อปิด ComfyUI แล้ว) หรือ Mac 16GB:** ความฉลาดในการเขียน Python, JS/TS, SQL และแก้บั๊กซับซ้อนใกล้เคียงโมเดล Cloud ขนาดใหญ่ |

---

## 2. ขั้นตอนการตั้งค่าฝั่ง LM Studio (`Port 1234`)

1. เปิดโปรแกรม **LM Studio** ไปที่แถบ **🔍 Discover (แว่นขยาย)**
2. พิมพ์ค้นหาคำว่า **`Qwen2.5-Coder-3B-Instruct-GGUF`** (หรือรุ่น **`7B-Instruct-GGUF`** หากไม่ได้เปิด ComfyUI พร้อมกัน) แล้วกดดาวน์โหลดไฟล์ระดับ **`Q4_K_M`**
3. ไปที่แถบ **💻 Developer (Local Server)** ด้านซ้ายมือ แล้วเลือกโหลดโมเดล `Qwen2.5-Coder` ด้านบนสุด
4. **สำคัญมากสำหรับงานเขียนโค้ด:** ในช่องตั้งค่า **Context Length** ด้านขวามือ ให้ปรับเพิ่มขึ้นจาก `2048` เป็น **`4096` หรือ `8192`** (เพื่อให้โมเดลอ่านไฟล์โค้ดขนาดยาวทั้งไฟล์ได้โดยไม่ถูกตัดทอน)
5. กดสวิตช์ **Start Server** ที่พอร์ต `1234` (`http://localhost:1234/v1`)

---

## 3. การเชื่อมต่อเข้ากับ VS Code (เลือกใช้ได้ 2 Extension ยอดนิยม)

### วิธีที่ 1: ใช้ Extension **Continue** (แนะนำอันดับ 1 — ได้ครบทั้ง Chat, Ctrl+I แก้โค้ด และ Tab Autocomplete)

1. เปิดโปรแกรม **VS Code** คลิกไอคอน **Extensions** ด้านซ้ายมือ (`Ctrl + Shift + X` หรือ `Cmd + Shift + X`)
2. ค้นหาคำว่า **`Continue`** (*Continue - open-source AI code agent*) แล้วกด **Install**
3. เมื่อติดตั้งเสร็จ จะมีไอคอน **`Continue`** ปรากฏที่แถบด้านซ้ายมือ ให้คลิกเปิดขึ้นมา
4. คลิกไอคอนรูปเฟือง **⚙️ (Open Continue Config)** มุมขวาบนของแถบ Continue เพื่อเปิดไฟล์ตั้งค่า แล้วคัดลอกเนื้อหาจากไฟล์ [`08-qwen-coder-vscode/continue_config.yaml`](./continue_config.yaml) (หรือ [`continue_config.json`](./continue_config.json)) ไปวางทับได้เลย:

```yaml
name: Local Qwen2.5-Coder (LM Studio)
version: 1.0.0
schema: v1

models:
  - name: Qwen2.5-Coder (LM Studio Chat & Edit)
    provider: lmstudio
    model: qwen2.5-coder-3b-instruct
    apiBase: http://localhost:1234/v1
    roles:
      - chat
      - edit
      - apply
    defaultCompletionOptions:
      contextLength: 8192
      temperature: 0.2

  - name: Qwen2.5-Coder Autocomplete
    provider: lmstudio
    model: qwen2.5-coder-3b-instruct
    apiBase: http://localhost:1234/v1
    roles:
      - autocomplete
    defaultCompletionOptions:
      contextLength: 4096
      maxTokens: 128
      temperature: 0.1
```
*(หมายเหตุ: ช่อง `model:` ให้เปลี่ยนเป็นชื่อ Identifier ของโมเดลที่แสดงอยู่ในหน้า Developer ของ LM Studio เช่น `qwen2.5-coder-3b-instruct` หรือ `qwen2.5-coder-7b-instruct`)*

---

### วิธีที่ 2: ใช้ Extension **Cline** / **Roo Code** (สาย Autonomous Coding Agent สร้างไฟล์และรัน Terminal อัตโนมัติ)

หากต้องการให้ AI สร้างไฟล์โปรเจกต์ใหม่หลายไฟล์เอง หรือรันคำสั่งทดสอบใน Terminal เอง:
1. ค้นหาและติดตั้ง Extension **`Cline`** (หรือ **`Roo Code`**) ใน VS Code
2. คลิกเปิดไอคอน Cline ด้านซ้ายมือ แล้วกดปุ่ม **⚙️ Settings**
3. ตั้งค่าดังนี้:
   - **API Provider:** เลือก **`LM Studio`** (หรือ `OpenAI Compatible`)
   - **Base URL:** `http://localhost:1234` (หรือ `http://localhost:1234/v1`)
   - **Model ID:** เลือกโมเดล `qwen2.5-coder-...` ที่เปิดค้างไว้ใน LM Studio

---

## 4. คีย์ลัดและเทคนิคใช้งานจริง 5 รูปแบบใน VS Code

คุณสามารถเปิดไฟล์ฝึกหัด [`08-qwen-coder-vscode/practice_lab.py`](./practice_lab.py) ใน VS Code เพื่อทดลองกดคีย์ลัดทั้ง 5 รูปแบบนี้ได้ทันที:

| รูปแบบการใช้งาน | คีย์ลัด (Windows) | คีย์ลัด (macOS) | วิธีใช้งานจริง |
| :--- | :--- | :--- | :--- |
| **1. เติมโค้ดอัตโนมัติ (Tab Autocomplete)** | `Tab` | `Tab` | พิมพ์ชื่อฟังก์ชันหรือคอมเมนต์ภาษาไทย รอ 0.5 วินาที จะมีโค้ดสีเทาขึ้นมา กด `Tab` เพื่อรับโค้ดทันที |
| **2. สั่งแก้โค้ดในจุดที่เลือก (Inline Edit)** | `Ctrl + I` | `Cmd + I` | ลากคลุมฟังก์ชันที่ต้องการแก้ กด `Ctrl+I` แล้วพิมพ์สั่ง เช่น *"เพิ่ม try/except และใส่ Type Hints"* |
| **3. ส่งโค้ดเข้าห้องแชตเพื่อถามหรือหาบั๊ก** | `Ctrl + L` | `Cmd + L` | ลากคลุมโค้ดที่มีปัญหาแล้วกด `Ctrl+L` โค้ดจะถูกแนบเข้าช่องแชตพร้อมถามสาเหตุบั๊กได้ทันที |
| **4. อ้างอิงไฟล์อื่นในโปรเจกต์ (`@Files`)** | พิมพ์ `@` ในช่องแชต | พิมพ์ `@` ในช่องแชต | พิมพ์ `@app.py` หรือ `@Codebase` เพื่อให้ Qwen2.5-Coder อ่านโครงสร้างไฟล์อื่นก่อนเขียนโค้ดเชื่อมต่อกัน |
| **5. ส่ง Error จาก Terminal ไปให้แก้ทันที** | `Ctrl + Shift + R` | `Cmd + Shift + R` | เมื่อรันโค้ดใน Terminal ของ VS Code แล้วขึ้น Error สีแดง กดคีย์ลัดนี้เพื่อส่ง Error ไปให้ AI วิเคราะห์วิธีแก้ทันที |
