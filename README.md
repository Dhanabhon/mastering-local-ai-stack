# Mastering Local AI Stack 2026: Jupyter Notebook × LM Studio × ComfyUI

> **โครงการอบรมเชิงปฏิบัติการเรื่อง การพัฒนาเวิร์กโฟลว์ปัญญาประดิษฐ์สำหรับสร้างข้อความและรูปภาพบนเครื่องคอมพิวเตอร์ส่วนบุคคล**  
> *Workshop materials, Jupyter Notebooks, ComfyUI workflows, and Setup Guide for "Mastering Local AI Stack: Jupyter Notebook × LM Studio × ComfyUI" (6-Hour University Training Course).*

[![Setup Guide](https://img.shields.io/badge/Live_Setup_Guide-GitHub_Pages-2563eb?style=for-the-badge)](https://dhanabhon.github.io/mastering-local-ai-stack/)
[![6-Hour Lab Guide](https://img.shields.io/badge/6--Hour_Lab_Guide-Hands--On_Labs-2e7d5b?style=for-the-badge)](https://dhanabhon.github.io/mastering-local-ai-stack/labs.html)
[![Showcase Demo](https://img.shields.io/badge/Showcase_Demo-CineLocal_Studio-181d19?style=for-the-badge)](https://dhanabhon.github.io/mastering-local-ai-stack/showcase.html)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![LM Studio](https://img.shields.io/badge/LM_Studio-Local_LLM_API-10b981?style=for-the-badge)](https://lmstudio.ai/)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-SD_1.5_Node_API-8b5cf6?style=for-the-badge)](https://github.com/comfyanonymous/ComfyUI)

คลังสื่อการสอนและใบงานปฏิบัติการสำหรับหลักสูตร **"Mastering Local AI Stack 2026"** (อบรม 6 ชั่วโมง) เนื้อหาในคลังนี้ออกแบบมาให้ผู้เรียนสร้างไปป์ไลน์ AI สำหรับสรุปข้อความและสร้างรูปภาพที่รันบนคอมพิวเตอร์ส่วนบุคคลแบบออฟไลน์ โดยไม่ต้องพึ่งพา Cloud API และไม่เสียค่าใช้จ่ายรายเดือน

---

## คู่มือการเตรียมเครื่อง, ใบงาน 6 ชั่วโมง และโปรเจกต์ Showcase ต่อยอด

1. **คู่มือเตรียมเครื่องก่อนเข้าห้องอบรม (Pre-Workshop Setup Guide):**
   - **GitHub Pages (ออนไลน์):** **[https://dhanabhon.github.io/mastering-local-ai-stack/](https://dhanabhon.github.io/mastering-local-ai-stack/)**
   - **ไฟล์ HTML ในคลัง:** [`docs/index.html`](./docs/index.html)
2. **ใบงานปฏิบัติการ 6 ชั่วโมง + โจทย์ Bonus Challenges (6-Hour Hands-On Lab Guide):**
   - **GitHub Pages (ออนไลน์):** **[https://dhanabhon.github.io/mastering-local-ai-stack/labs.html](https://dhanabhon.github.io/mastering-local-ai-stack/labs.html)**
   - **ไฟล์ HTML ในคลัง:** [`docs/labs.html`](./docs/labs.html)
3. **✨ โปรเจกต์ตัวอย่างต่อยอด #1 (CineLocal Studio — AI Storyboard & Pitch Deck Director):**
   - **Interactive Web Demo:** **[https://dhanabhon.github.io/mastering-local-ai-stack/showcase.html](https://dhanabhon.github.io/mastering-local-ai-stack/showcase.html)** | [`docs/showcase.html`](./docs/showcase.html)
   - **ซอร์สโค้ด Python และคู่มือแกะรอยด้วยตัวเอง:** [`05-bonus-showcase/app.py`](./05-bonus-showcase/app.py) | [`05-bonus-showcase/README.md`](./05-bonus-showcase/README.md)
4. **🎬 โปรเจกต์ตัวอย่างต่อยอด #2 (Local AI Media Studio — Custom Image & Video Web App):**
   - **Interactive Web Demo:** **[https://dhanabhon.github.io/mastering-local-ai-stack/media-studio.html](https://dhanabhon.github.io/mastering-local-ai-stack/media-studio.html)** | [`docs/media-studio.html`](./docs/media-studio.html)
   - **ซอร์สโค้ด Web App ครอบ LM Studio + ComfyUI (เลือกโหมด Image / Video ได้):** [`06-custom-media-studio/app.py`](./06-custom-media-studio/app.py) | [`06-custom-media-studio/README.md`](./06-custom-media-studio/README.md)
5. **สไลด์ประกอบการบรรยาย (Workshop Slides - ธีม Tomera AI & Google Sans Thai):**
   - **Google Slides:** **[เปิดสไลด์ออนไลน์](https://docs.google.com/presentation/d/10N29z8f3cRq-Ykom9XH18NkSwTtvkkwUQXoFYmqj3zo/edit?usp=sharing)**
   - **ไฟล์ PDF / PPTX ในคลัง:** [`slides/Mastering_Local_AI_Stack_2026.pdf`](./slides/Mastering_Local_AI_Stack_2026.pdf) | [`slides/Mastering_Local_AI_Stack_2026.pptx`](./slides/Mastering_Local_AI_Stack_2026.pptx)

---

## สเปกเครื่องห้องปฏิบัติการและการตั้งค่าโมเดล (Hardware Target & Constraints)

โค้ดและไฟล์เวิร์กโฟลว์ทั้งหมดในหลักสูตรนี้ปรับแต่งมาให้รันได้บนฮาร์ดแวร์จริงของห้องปฏิบัติการมหาวิทยาลัย รวมถึงเครื่องส่วนตัวที่ผู้เรียนนำมาเอง:

| ประเภทเครื่อง | รายละเอียดสเปกฮาร์ดแวร์ (Specification) | ข้อจำกัดและการจัดการหน่วยความจำ |
| :--- | :--- | :--- |
| **เครื่องห้องปฏิบัติการ (Windows PC)** | • **CPU:** Intel Core Ultra 7 265 (20C/20T, up to 5.3GHz, NPU 13 TOPS)<br>• **GPU:** NVIDIA GeForce RTX 3050 **6GB GDDR6**<br>• **RAM:** 16GB DDR5-5600MT/s<br>• **Storage / OS:** 1TB SSD PCIe Gen4 / Windows 11 Home | **VRAM 6GB คือเพดานสำคัญที่สุด** ต้องเลือกขนาดโมเดลและปรับค่าพารามิเตอร์ให้ทั้ง LLM และ Diffusion ทำงานพร้อมกันได้โดยการ์ดจอไม่เต็ม (Out of Memory) |
| **เครื่องส่วนตัวผู้เรียน (macOS)** | • **SoC:** Apple Silicon (M1 / M2 / M3 / M4)<br>• **Memory:** Unified Memory 16GB ขึ้นไป | ใช้สถาปัตยกรรม **Unified Memory** แชร์แรมร่วมกันระหว่าง CPU และ GPU (Apple Metal / MPS) |

### เกณฑ์การเลือกโมเดลและตั้งค่าระบบ
1. **LM Studio Model (Local LLM):**
   - ใช้โมเดลขนาด **3B Parameters** (Quantization ระดับ `Q4_K_M` หรือ `Q8_0`) เช่น `Qwen2.5-3B-Instruct-GGUF` หรือ `Llama-3.2-3B-Instruct-GGUF` ซึ่งกิน VRAM ประมาณ **2.2 GB**
   - กำหนดค่า **Context Length** ไม่เกิน `2048` ถึง `4096` tokens เพื่อกันไม่ให้ KV Cache ใช้พื้นที่การ์ดจอมากเกินไป
2. **ComfyUI Checkpoint (Image Generation):**
   - ใช้โมเดลตระกูล **Stable Diffusion 1.5 (SD 1.5)** เช่น `v1-5-pruned-emaonly.safetensors` หรือ `DreamShaper_8_pruned.safetensors` (ขนาดไฟล์ประมาณ 2 GB)
   - ตั้งความละเอียดภาพเริ่มต้นที่ **`512x512` พิกเซล** ใช้เวลาเรนเดอร์ประมาณ 2 ถึง 3 วินาทีต่อภาพบน RTX 3050 6GB และ Apple Silicon
3. **การจัดการ VRAM 6GB ในช่วง Capstone (รัน LM Studio คู่กับ ComfyUI):**
   - เมื่อรันโมเดล 3B (~2.2GB) พร้อมกับ SD 1.5 (~2.0GB) ตัวระบบจะใช้ VRAM รวมกันราว 4.2 ถึง 4.8 GB ซึ่งอยู่ในงบ 6GB
   - **สำหรับ Windows (RTX 3050 6GB):** แนะนำให้เปิด ComfyUI ด้วยแฟล็ก `--lowvram` หรือลดสไลเดอร์ **GPU Offload** ใน LM Studio ลงมาที่ 50% ถึง 70% เพื่อแบ่งงานบางส่วนไปให้ซีพียู **Intel Core Ultra 7 265** ช่วยประมวลผล

---

## ตารางกำหนดการอบรม (6-Hour Workshop Schedule)

| เวลา | โมดูล | หัวข้อการเรียนรู้และกิจกรรมปฏิบัติการ | ไฟล์ปฏิบัติการ |
| :--- | :--- | :--- | :--- |
| **09:00 - 10:15** | **Module 1** | **Jupyter Notebook Basics & REST API**<br>• พื้นฐาน Interactive Computing (Kernel, Code vs Markdown cells, Virtual Env)<br>• การจัดการข้อมูลข้อความ, Dictionary/JSON และ `pandas.DataFrame`<br>• การเรียก REST API และเช็กสถานะเซิร์ฟเวอร์ด้วย `requests` | [`01_python_and_api_basics.ipynb`](./01-jupyter-basics/01_python_and_api_basics.ipynb) |
| *10:15 - 10:30* | *Break* | *พักรับประทานอาหารว่าง (15 นาที)* | - |
| **10:30 - 12:00** | **Module 2** | **Local LLMs with LM Studio**<br>• โครงสร้าง Local LLM, ฟอร์แมต GGUF, Quantization และการคำนวณ VRAM 6GB<br>• การปรับค่า System Prompt, Temperature, Top-P, Context Length และ GPU Offload<br>• การเปิด Local OpenAI-Compatible API Server (`http://localhost:1234/v1`)<br>• **Lab:** เขียนโค้ดสั่งสกัดข้อมูลและสรุปบทความภาษาไทยเป็น JSON ลงตาราง Pandas | [`02_local_llm_integration.ipynb`](./02-lm-studio-api/02_local_llm_integration.ipynb) |
| *12:00 - 13:00* | *Lunch* | *พักรับประทานอาหารกลางวัน (1 ชั่วโมง)* | - |
| **13:00 - 14:30** | **Module 3** | **Node-Based Image Generation with ComfyUI**<br>• โครงสร้าง Diffusion Model บนระบบ Node (Load Checkpoint, CLIP, KSampler, Latent, VAE)<br>• การต่อเวิร์กโฟลว์ Text-to-Image และ Image-to-Image (SD 1.5, `512x512`) ตั้งแต่ศูนย์<br>• การเปิด Developer Mode เพื่อส่งออกเวิร์กโฟลว์เป็นไฟล์ API JSON | [`sd15_txt2img_api.json`](./03-comfyui-workflows/sd15_txt2img_api.json) |
| *14:30 - 14:45* | *Break* | *พักรับประทานอาหารว่าง (15 นาที)* | - |
| **14:45 - 16:00** | **Module 4** | **Full-Stack Local AI Pipeline (Capstone Integration)**<br>• การเชื่อมระบบ: Jupyter Notebook -> LM Studio API -> ComfyUI API<br>• การบริหาร VRAM 6GB เมื่อเปิดทั้งสองโปรแกรมพร้อมกัน<br>• **Capstone Lab:** รับหัวข้อภาษาไทย ส่งให้ LLM เขียน Image Prompt ภาษาอังกฤษ แล้วสั่ง ComfyUI (`http://127.0.0.1:8188`) วาดภาพกลับมาแสดงใน Notebook | [`04_end_to_end_ai_pipeline.ipynb`](./04-capstone-pipeline/04_end_to_end_ai_pipeline.ipynb) |

---

## โครงสร้างโฟลเดอร์โปรเจกต์ (Repository Structure)

```text
mastering-local-ai-stack/
├── README.md                                      # คู่มือหลักสูตรและวิธีรันโปรเจกต์เบื้องต้น
├── requirements.txt                               # รายการไลบรารี Python ที่ใช้ในหลักสูตร
├── .gitignore                                     # เพิกเฉยไฟล์ขยะ, .venv และไฟล์โมเดลขนาดใหญ่
├── docs/
│   ├── index.html                                 # หน้าเว็บคู่มือเตรียมเครื่อง (Pre-Workshop Setup Guide)
│   ├── labs.html                                  # หน้าเว็บใบงานปฏิบัติการ 6 ชั่วโมง + โจทย์ Bonus Challenges
│   ├── showcase.html                              # หน้าเว็บ Interactive Showcase #1 (CineLocal Storyboard)
│   └── media-studio.html                          # หน้าเว็บ Interactive Showcase #2 (Custom Image & Video Studio)
├── slides/
│   ├── Mastering_Local_AI_Stack_2026.pdf          # ไฟล์สไลด์บรรยาย PDF (ธีม Tomera AI & Google Sans Thai)
│   └── Mastering_Local_AI_Stack_2026.pptx         # ไฟล์สไลด์บรรยาย PowerPoint (.pptx)
├── assets/
│   └── sample_article.txt                         # บทความภาษาไทยตัวอย่างสำหรับใช้ใน Module 1 และ 2
├── 01-jupyter-basics/
│   └── 01_python_and_api_basics.ipynb             # ใบงานที่ 1: พื้นฐาน Jupyter, JSON, Pandas และ REST API
├── 02-lm-studio-api/
│   └── 02_local_llm_integration.ipynb             # ใบงานที่ 2: การเชื่อมต่อ LM Studio API และสกัดข้อมูล JSON
├── 03-comfyui-workflows/
│   └── sd15_txt2img_api.json                      # เวิร์กโฟลว์ ComfyUI (API Format) สำหรับ SD 1.5 (512x512)
├── 04-capstone-pipeline/
│   └── 04_end_to_end_ai_pipeline.ipynb            # ใบงานที่ 4: Capstone เชื่อมต่อ LM Studio คู่กับ ComfyUI
├── 05-bonus-showcase/
│   ├── README.md                                  # คู่มือแกะรอยโปรเจกต์ต่อยอด #1 (Storyboard Pitch Deck)
│   └── app.py                                     # สคริปต์ Python Full-Stack สร้าง Storyboard 3 ฉาก + HTML Pitch Deck
└── 06-custom-media-studio/
    ├── README.md                                  # คู่มือใช้งานโปรเจกต์ต่อยอด #2 (Custom Image & Video Web App)
    ├── app.py                                     # เว็บแอปครอบ LM Studio + ComfyUI เลือกโหมด Image / Video (พอร์ต 8090)
    └── workflows/
        └── sd15_animatediff_api.json              # เวิร์กโฟลว์ตัวอย่างสำหรับโหมดสร้างวิดีโอด้วย AnimateDiff API
```

---

## วิธีเริ่มต้นใช้งาน (Quick Start)

### 1. โคลนโปรเจกต์และสร้าง Virtual Environment

**สำหรับ Windows (PowerShell / Command Prompt):**
```powershell
git clone https://github.com/Dhanabhon/mastering-local-ai-stack.git
cd mastering-local-ai-stack
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**สำหรับ macOS (Terminal):**
```bash
git clone https://github.com/Dhanabhon/mastering-local-ai-stack.git
cd mastering-local-ai-stack
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. เปิดใช้งานเซิร์ฟเวอร์ AI ในเครื่อง
1. **LM Studio:** โหลดโมเดล `Qwen2.5-3B-Instruct (Q4_K_M)` ตั้งค่า Context Length เป็น `2048` จากนั้นไปที่แถบ **Developer (Local Server)** แล้วกด **Start Server** ที่พอร์ต `1234` (`http://localhost:1234/v1`)
2. **ComfyUI:** วางไฟล์โมเดล `v1-5-pruned-emaonly.safetensors` ลงในโฟลเดอร์ `models/checkpoints/` แล้วรันโปรแกรมที่พอร์ต `8188` (`http://127.0.0.1:8188`)

### 3. เปิด JupyterLab
รันคำสั่งด้านล่างในหน้าต่าง Terminal หรือ PowerShell ที่เปิด `.venv` ไว้แล้ว:
```bash
jupyter lab
```
เมื่อเบราว์เซอร์เปิดหน้าต่าง JupyterLab ขึ้นมาแล้ว ให้คลิกเข้าไปทำใบงานตามลำดับตั้งแต่โฟลเดอร์ `01-jupyter-basics` จนถึง `04-capstone-pipeline`

---

## สัญญาอนุญาต (License)
สื่อการสอนและซอร์สโค้ดในโปรเจกต์นี้เผยแพร่ภายใต้สัญญาอนุญาต [MIT License](./LICENSE)
