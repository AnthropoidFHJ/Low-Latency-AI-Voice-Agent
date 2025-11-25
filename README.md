
## ⚡ Quick Start 

### 1. Clone & Setup Backend Environment
```bash
cd Backend
python -m venv .venv
```
```bash
.venv\Scripts\activate
```
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the `Backend` directory:

```env
GEMINI_API_KEY=
```

### 3. Setup Frontend Environment
```bash
cd ../Frontend
npm install
```

### 4. Start Backend Server
```bash
cd ../Backend
.venv\Scripts\activate
uvicorn main:app --reload
```

### 5. Start Frontend Development Server
```bash
cd ../Frontend
npm run dev
```

**Frontend : http://localhost:3000**  
**Backend  : http://127.0.0.1:8000**  
**API      : http://127.0.0.1:8000/docs**  