# Invoice Extraction Portal

A free, open-source MVP for extracting line-item tables from digital PDF invoices and exporting them to Excel.

---

## Features

- Upload one or multiple digital PDF invoices
- Automatically finds and extracts the line-item table (any format, any columns)
- Exports each invoice to its own colour-coded `.xlsx` file
- Multiple invoices → ZIP download
- Debug mode to inspect raw extracted text
- 100% free — no paid APIs

---

## Quick Start (Local)

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the app

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

---

## Share with a Client using ngrok

ngrok creates a temporary public URL that tunnels to your local app.
Your client opens the link in their browser — no installation needed on their side.

---

### Step 1 — Install ngrok

1. Go to **https://ngrok.com/download**
2. Download the Windows ZIP
3. Extract `ngrok.exe` to a folder (e.g. `C:\ngrok\`)
4. Add that folder to your system PATH:
   - Search "Environment Variables" in Start Menu
   - Edit `Path` under System Variables
   - Add `C:\ngrok\`
   - Click OK

Or simply drop `ngrok.exe` directly into this project folder.

---

### Step 2 — Create a free ngrok account & get your auth token

1. Sign up at **https://dashboard.ngrok.com/signup** (free)
2. After login go to **https://dashboard.ngrok.com/get-started/your-authtoken**
3. Copy your auth token
4. Run this once in terminal (only needed once per machine):

```bash
ngrok config add-authtoken YOUR_TOKEN_HERE
```

---

### Step 3 — Start everything (one click)

Double-click **`start.bat`** in this folder.

It will open two windows:
- **Window 1** — Streamlit running on `localhost:8501`
- **Window 2** — ngrok tunnel

In the ngrok window you will see something like:

```
Forwarding   https://abc123.ngrok-free.app  ->  http://localhost:8501
```

**Copy that `https://` URL and share it with your client.**

---

### Step 4 — Client opens the link

Your client pastes the URL in any browser on any device.
They see your app exactly as you do — they can upload PDFs and download Excel files.

---

### Manual start (without the batch file)

Open two separate terminals:

**Terminal 1:**
```bash
streamlit run app.py
```

**Terminal 2:**
```bash
ngrok http 8501
```

---

## Important Things to Know

| Thing | Explanation |
|---|---|
| **Laptop must stay ON** | The app runs on your machine. If you close the laptop or the terminal, the link stops working. |
| **URL changes every time** | Free ngrok gives a new random URL each session. Re-share the new URL with your client each time you restart. |
| **Free plan limit** | Free ngrok allows 1 tunnel, up to 40 connections/minute. Fine for demos and small clients. |
| **Link is public** | Anyone with the link can access your app. Don't share it beyond your intended client. Close ngrok when done. |

---

## Troubleshooting

### "ngrok is not recognized as a command"
- `ngrok.exe` is not in PATH.
- Fix: either add its folder to PATH (see Step 1) or copy `ngrok.exe` into this project folder and run `.\ngrok http 8501`.

### "Port 8501 already in use"
```bash
# Find and kill what's using the port
netstat -ano | findstr :8501
taskkill /PID <PID_NUMBER> /F
```
Or run Streamlit on a different port and match it in ngrok:
```bash
streamlit run app.py --server.port 8502
ngrok http 8502
```

### "ngrok tunnel not showing a URL"
- Check your auth token is set: `ngrok config check`
- Re-run: `ngrok config add-authtoken YOUR_TOKEN`

### "Client sees a browser warning"
ngrok shows an interstitial warning page on free plan for new visitors.
Client clicks **"Visit Site"** to proceed. This is normal.

### "Firewall blocking ngrok"
- Run as Administrator
- Or allow `ngrok.exe` through Windows Defender Firewall:
  - Search "Allow an app through Windows Firewall"
  - Add `ngrok.exe`

---

## Project Structure

```
invoice_extracter/
├── app.py            ← Streamlit UI
├── extractor.py      ← pdfplumber text + table extraction
├── parser.py         ← Header row detection, raw table extraction
├── excel_writer.py   ← Per-invoice Excel generation (openpyxl)
├── utils.py          ← Date normalisation, number cleaning
├── start.bat         ← One-click launcher (Streamlit + ngrok)
├── uploads/          ← Temp PDF storage (git-ignored)
├── outputs/          ← Generated Excel files (git-ignored)
├── requirements.txt
└── README.md
```

---

## Requirements

```
streamlit>=1.32.0
pdfplumber>=0.10.0
pandas>=2.0.0
openpyxl>=3.1.0
```

---

## Future Roadmap

- [ ] Claude API integration for scanned PDF support
- [ ] OCR fallback (Tesseract) for image-based PDFs
- [ ] Persistent public URL (ngrok paid / Railway / Streamlit Cloud deployment)
- [ ] Customer-specific extraction templates
