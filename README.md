# Mastering Local AI Stack 2026: Jupyter Notebook × LM Studio × ComfyUI

> **โครงการอบรมเชิงปฏิบัติการเรื่อง การพัฒนาเวิร์กโฟลว์ปัญญาประดิษฐ์สำหรับสร้างข้อความและรูปภาพบนเครื่องคอมพิวเตอร์ส่วนบุคคล**  
> *Workshop materials, Jupyter Notebooks, ComfyUI workflows, and Setup Guide for "Mastering Local AI Stack: Jupyter Notebook × LM Studio × ComfyUI" (6-Hour University Training Course).*

[![Setup Guide](https://img.shields.io/badge/🌐_Live_Setup_Guide-GitHub_Pages-2563eb?style=for-the-badge)](https://dhanabhon.github.io/mastering-local-ai-stack/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![LM Studio](https://img.shields.io/badge/LM_Studio-Local_LLM_API-10b981?style=for-the-badge)](https://lmstudio.ai/)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-SD_1.5_Node_API-8b5cf6?style=for-the-badge)](https://github.com/comfyanonymous/ComfyUI)

ยินดีต้อนรับสู่คลังสื่อการสอนและใบงานปฏิบัติการ (Workshop Repository) สำหรับหลักสูตร **"Mastering Local AI Stack 2026"** หลักสูตร 6 ชั่วโมงที่ออกแบบมาเพื่อให้นักศึกษา อาจารย์ และนักพัฒนา สามารถสร้างไปป์ไลน์ AI อัตโนมัติ (Text-to-Text และ Text-to-Image) ที่รันบนเครื่องคอมพิวเตอร์ส่วนบุคคลแบบ Offline 100% โดยไม่มีค่าใช้จ่าย API และรักษาความเป็นส่วนตัวของข้อมูลอย่างสมบูรณ์

---

## 🔗 คู่มือการเตรียมความพร้อมของเครื่อง (Pre-Workshop Setup Guide)

ผู้เข้าอบรมและเจ้าหน้าที่ดูแลห้องปฏิบัติการสามารถเปิดดูคู่มือการติดตั้งโปรแกรม โมเดล และรายการตรวจสอบความพร้อม (Pre-flight Checklist) แยกตามระบบปฏิบัติการ (**Windows NVIDIA GPU** และ **macOS Apple Silicon**) ได้ที่หน้าเว็บคู่มือของเรา:

- 🌐 **GitHub Pages (Live Web Guide):** **[https://dhanabhon.github.io/mastering-local-ai-stack/](https://dhanabhon.github.io/mastering-local-ai-stack/)**
- 📄 **เปิดไฟล์ HTML จากในคลังโดยตรง:** [`docs/index.html`](./docs/index.html)

---

## 💻 สเปกเครื่องห้องปฏิบัติการและเกณฑ์การตั้งค่าโมเดล (Hardware Target & Constraints)

เนื้อหาและโค้ดทั้งหมดในหลักสูตรนี้ได้รับการออกแบบและปรับแต่ง (Optimize) ให้ทำงานได้อย่างราบรื่นภายใต้ข้อจำกัดของฮาร์ดแวร์จริงในห้องปฏิบัติการมหาวิทยาลัย รวมถึงเครื่องส่วนตัวของผู้เรียน:

| ประเภทเครื่อง | รายละเอียดสเปกฮาร์ดแวร์ (Specification) | ข้อจำกัดและการจัดการหน่วยความจำ |
| :--- | :--- | :--- |
| **เครื่องห้องปฏิบัติการ (Windows PC)** | • **CPU:** Intel Core Ultra 7 265 (20C/20T, up to 5.3GHz, NPU 13 TOPS)<br>• **GPU:** NVIDIA GeForce RTX 3050 **6GB GDDR6**<br>• **RAM:** 16GB DDR5-5600MT/s<br>• **Storage / OS:** 1TB SSD PCIe Gen4 / Windows 11 Home | **VRAM 6GB เป็นข้อจำกัดสำคัญที่สุด** ต้องเลือกขนาดโมเดลและการตั้งค่าให้ LLM และ Diffusion สามารถทำงานร่วมกันได้โดยไม่เกิดอาการ Out of Memory (OOM) |
| **เครื่องส่วนตัวผู้เรียน (macOS)** | • **SoC:** Apple Silicon (M1 / M2 / M3 / M4)<br>• **Memory:** Unified Memory 16GB ขึ้นไป | ใช้สถาปัตยกรรม **Unified Memory** แชร์แรมระหว่าง CPU และ GPU (Apple Metal / MPS) |

### 🎯 เกณฑ์การเลือกโมเดลและตั้งค่าระบบ (Standard Configuration)
1. **LM Studio Model (Local LLM):**
   - ใช้โมเดลขนาด **3B Parameters** (Quantization ระดับ `Q4_K_M` หรือ `Q8_0`) เช่น `Qwen2.5-3B-Instruct-GGUF` หรือ `Llama-3.2-3B-Instruct-GGUF` ซึ่งใช้ VRAM/Memory เพียง **~2.2 GB**
   - กำหนดค่า **Context Length** ไม่เกิน `2048` – `4096` tokens เพื่อประหยัด KV Cache บน VRAM
2. **ComfyUI Checkpoint (Image Generation):**
   - ใช้โมเดลตระกูล **Stable Diffusion 1.5 (SD 1.5)** เช่น `v1-5-pruned-emaonly.safetensors` หรือ `DreamShaper_8_pruned.safetensors` (ขนาดไฟล์ ~2 GB)
   - กำหนดความละเอียดเริ่มต้นที่ **`512x512` พิกเซล** (ใช้เวลาเรนเดอร์เพียง 2–3 วินาทีต่อภาพบน RTX 3050 6GB และ Apple Silicon)
3. **เทคนิคการรัน LM Studio คู่กับ ComfyUI ในช่วง Capstone (VRAM 6GB Management):**
   - การใช้โมเดล 3B (~2.2GB) คู่กับ SD 1.5 (~2.0GB) จะใช้ VRAM รวมกันราว ~4.2–4.8 GB ซึ่งพอดีกับเพดาน 6GB
   - **สำหรับ Windows (RTX 3050 6GB):** แนะนำให้เปิด ComfyUI ด้วยแฟล็ก `--lowvram` หรือลดสไลเดอร์ **GPU Offload** ใน LM Studio ลงมาประมาณ 50–70% เพื่อแบ่งภาระการคำนวณมายังซีพียู **Intel Core Ultra 7 265** ที่มีถึง 20 คอร์

---

## 🗓️ ตารางกำหนดการอบรม (6-Hour Workshop Schedule)

| เวลา | โมดูล | หัวข้อการเรียนรู้และกิจกรรมปฏิบัติการ (Hands-on Labs) | ไฟล์ปฏิบัติการ |
| :--- | :--- | :--- | :--- |
| **09:00 - 10:15** | **Module 1** | **Jupyter Notebook Basics & REST API**<br>• พื้นฐาน Interactive Computing (Kernel, Code vs Markdown cells, Virtual Env)<br>• การจัดการข้อมูล Text, Dictionary/JSON, `pandas.DataFrame`<br>• การเรียกใช้งาน REST API และตรวจสอบสถานะเซิร์ฟเวอร์ด้วย `requests` | [`01_python_and_api_basics.ipynb`](./01-jupyter-basics/01_python_and_api_basics.ipynb) |
| *10:15 - 10:30* | *Break* | *พักรับประทานอาหารว่าง (15 นาที)* | - |
| **10:30 - 12:00** | **Module 2** | **Local LLMs with LM Studio**<br>• สถาปัตยกรรม Local LLM, GGUF Format, Quantization และการคำนวณ VRAM 6GB<br>• การปรับพารามิเตอร์ System Prompt, Temperature, Top-P, Context Length, GPU Offload<br>• การเปิด Local OpenAI-Compatible API Server (`http://localhost:1234/v1`)<br>• **Lab:** เขียนโค้ดสั่งสกัดข้อมูลและสรุปบทความภาษาไทยเป็น JSON & ตาราง Pandas | [`02_local_llm_integration.ipynb`](./02-lm-studio-api/02_local_llm_integration.ipynb) |
| *12:00 - 13:00* | *Lunch* | *พักรับประทานอาหารกลางวัน (1 ชั่วโมง)* | - |
| **13:00 - 14:30** | **Module 3** | **Node-Based Image Generation with ComfyUI**<br>• โครงสร้าง Diffusion Model บนระบบ Node (Load Checkpoint, CLIP, KSampler, Latent, VAE)<br>• การสร้างเวิร์กโฟลว์ Text-to-Image และ Image-to-Image (SD 1.5, `512x512`) ตั้งแต่ศูนย์<br>• การเปิด Developer Mode และ Export เวิร์กโฟลว์เป็นรูปแบบ API JSON | [`sd15_txt2img_api.json`](./03-comfyui-workflows/sd15_txt2img_api.json) |
| *14:30 - 14:45* | *Break* | *พักรับประทานอาหารว่าง (15 นาที)* | - |
| **14:45 - 16:00** | **Module 4** | **Full-Stack Local AI Pipeline (Capstone Integration)**<br>• สถาปัตยกรรม Orchestration: Jupyter Notebook ➔ LM Studio API ➔ ComfyUI API<br>• การจัดการ VRAM 6GB เมื่อรันทั้งสองเซิร์ฟเวอร์พร้อมกัน<br>• **Capstone Lab:** รับหัวข้อภาษาไทย ➔ ให้ LLM แต่ง Image Prompt ภาษาอังกฤษ ➔ ส่งเรนเดอร์ใน ComfyUI (`http://127.0.0.1:8188`) ➔ ดึงภาพกลับมาแสดงผลใน Notebook ทันที | [`04_end_to_end_ai_pipeline.ipynb`](./04-capstone-pipeline/04_end_to_end_ai_pipeline.ipynb) |

---

## 📂 โครงสร้างโฟลเดอร์โปรเจกต์ (Repository Structure)

```text
mastering-local-ai-stack/
├── README.md                                      # คู่มือหลักสูตรและวิธีเริ่มต้นใช้งาน
├── requirements.txt                               # รายการไลบรารี Python ที่จำเป็น
├── .gitignore                                     # ตั้งค่าเพิกเฉยไฟล์ขยะ, .venv และไฟล์โมเดลขนาดใหญ่
├── docs/
│   └── index.html                                 # หน้าเว็บ GitHub Pages คู่มือเตรียมเครื่อง (Windows/macOS)
├── slides/
│   └── .gitkeep                                   # โฟลเดอร์สำหรับเก็บเอกสารประกอบการบรรยาย (Slides)
├── assets/
│   └── sample_article.txt                         # บทความภาษาไทยตัวอย่างสำหรับใช้ทดสอบใน Module 1 & 2
├── 01-jupyter-basics/
│   └── 01_python_and_api_basics.ipynb             # ใบงานที่ 1: พื้นฐาน Jupyter, JSON, Pandas และ REST API
├── 02-lm-studio-api/
│   └── 02_local_llm_integration.ipynb             # ใบงานที่ 2: การเชื่อมต่อ LM Studio API และสกัดข้อมูล JSON
├── 03-comfyui-workflows/
│   └── sd15_txt2img_api.json                      # เวิร์กโฟลว์ ComfyUI (API Format) สำหรับ SD 1.5 (512x512)
└── 04-capstone-pipeline/
    └── 04_end_to_end_ai_pipeline.ipynb            # ใบงานที่ 4: Capstone เชื่อมต่อ LM Studio + ComfyUI ครบวงจร
```

---

## 🚀 วิธีเริ่มต้นใช้งานอย่างรวดเร็ว (Quick Start)

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

### 2. เปิดใช้งานเซิร์ฟเวอร์ AI ท้องถิ่น
1. **LM Studio:** โหลดโมเดล `Qwen2.5-3B-Instruct (Q4_K_M)` ตั้งค่า Context Length = `2048` แล้วไปที่แท็บ **Developer (Local Server)** กด **Start Server** ที่พอร์ต `1234` (`http://localhost:1234/v1`)
2. **ComfyUI:** วางไฟล์โมเดล `v1-5-pruned-emaonly.safetensors` ลงในโฟลเดอร์ `models/checkpoints/` แล้วรันโปรแกรมให้ทำงานที่พอร์ต `8188` (`http://127.0.0.1:8188`)

### 3. เริ่มต้นเปิด JupyterLab
รันคำสั่งต่อไปนี้ใน Terminal/PowerShell ที่เปิดใช้งาน `.venv` แล้ว:
```bash
jupyter lab
```
เบราว์เซอร์จะเปิดหน้าต่าง JupyterLab ขึ้นมา ให้คลิกเข้าไปทำใบงานตามลำดับตั้งแต่โฟลเดอร์ `01-jupyter-basics` จนถึง `04-capstone-pipeline`

---

## 📄 สัญญาอนุญาต (License)
สื่อการสอนและซอร์สโค้ดในโปรเจกต์นี้เผยแพร่ภายใต้สัญญาอนุญาต [MIT License](./LICENSE) เพื่อประโยชน์ทางการศึกษาและการวิจัย
