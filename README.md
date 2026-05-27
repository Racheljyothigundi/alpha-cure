# 🔬 Alpha-Cure — AI-Powered Cancer Detection & Care Platform

A production-grade full-stack healthcare web application combining deep learning, real-time communication, and clinical decision support.

---

## 🏗️ Architecture Overview

```
alpha-cure/
├── backend/                    # Flask (Python) API Server
│   ├── app.py                  # Main entry point + Socket.IO
│   ├── model_selector.py       # AI model loader + prediction pipeline
│   ├── requirements.txt
│   ├── .env.example
│   ├── routes/                 # URL routing blueprints
│   │   ├── auth_routes.py
│   │   ├── user_routes.py
│   │   ├── prediction_routes.py
│   │   ├── report_routes.py
│   │   ├── chat_routes.py
│   │   ├── hospital_routes.py
│   │   └── doctor_routes.py
│   ├── controllers/            # Business logic
│   │   ├── auth_controller.py
│   │   ├── user_controller.py
│   │   ├── prediction_controller.py
│   │   ├── report_controller.py
│   │   ├── chat_controller.py
│   │   ├── hospital_controller.py
│   │   └── doctor_controller.py
│   ├── services/               # Shared services
│   │   ├── email_service.py    # SMTP OTP emails
│   │   └── socket_service.py   # Socket.IO real-time events
│   ├── utils/
│   │   ├── db.py               # MongoDB connection
│   │   └── jwt_utils.py        # JWT auth decorators
│   ├── models/                 # Place .h5 + .pkl here
│   ├── uploads/                # Temp file storage
│   └── reports/                # Generated PDFs
│
└── frontend/                   # React.js Application
    ├── public/
    │   └── index.html
    ├── src/
    │   ├── App.js              # Router + auth guards
    │   ├── index.js
    │   ├── index.css           # Tailwind + global styles
    │   ├── context/
    │   │   └── AuthContext.js  # Auth state management
    │   ├── services/
    │   │   ├── api.js          # Axios instance
    │   │   └── socket.js       # Socket.IO client
    │   ├── components/
    │   │   └── common/
    │   │       └── Sidebar.js  # Shared sidebar nav
    │   └── pages/
    │       ├── LandingPage.js  # Public homepage
    │       ├── LoginPage.js    # Authentication
    │       ├── SignupPage.js   # Registration (patient/doctor)
    │       ├── VerifyOtpPage.js
    │       ├── PatientDashboard.js
    │       ├── DoctorDashboard.js  # With charts
    │       ├── PredictionPage.js   # Core AI feature
    │       ├── ChatPage.js         # AI chatbot + doctor chat
    │       ├── ReportsPage.js      # PDF download
    │       ├── HospitalsPage.js    # Maps integration
    │       └── ProfilePage.js
    ├── tailwind.config.js
    └── package.json
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB (local or Atlas)
- Git

---

### Step 1 — Clone & Navigate
```bash
git clone <your-repo>
cd alpha-cure
```

---

### Step 2 — Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

Edit `.env` with your actual values:
```env
MONGO_URI=mongodb://localhost:27017/alphacure
JWT_SECRET=your_super_secret_key_change_this_in_production
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_gmail@gmail.com
SMTP_PASS=your_gmail_app_password
OPENAI_API_KEY=sk-...                      # Optional
GOOGLE_MAPS_API_KEY=AIzaSy...              # Optional
FRONTEND_URL=http://localhost:3000
```

> **Gmail App Password**: Go to Google Account → Security → 2FA → App Passwords → Generate

#### Place Your AI Models (Optional)
```bash
# If you have the trained model from your notebook:
cp /path/to/cancer_model.h5 backend/models/
cp /path/to/model_artifacts.pkl backend/models/

# Without model files, Alpha-Cure runs in MOCK MODE (still fully functional)
```

#### Start Backend
```bash
python app.py
# → Running on http://localhost:5000
```

---

### Step 3 — Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
# → Running on http://localhost:3000
```

---

## 📡 API Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup` | Register (sends OTP) |
| POST | `/api/auth/verify-otp` | Verify email OTP |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/resend-otp` | Resend OTP |

### Prediction (JWT Required)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/predict` | Run AI cancer risk assessment |
| GET | `/api/predictions` | Get prediction history |

### User
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/user/profile` | Get profile |
| PUT | `/api/user/profile` | Update profile |
| GET | `/api/user/dashboard` | Dashboard stats |

### Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reports/` | List reports |
| GET | `/api/reports/download/<id>` | Download PDF |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/ai` | AI chatbot message |
| GET | `/api/chat/rooms` | Get chat rooms |
| POST | `/api/chat/rooms` | Create chat room |
| GET | `/api/chat/messages/<room_id>` | Get messages |

### Doctor
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/doctor/list` | List all doctors |
| GET | `/api/doctor/patients` | High-risk patients (doctor only) |
| GET | `/api/doctor/stats` | Doctor dashboard stats |
| POST | `/api/doctor/consultation/create-order` | Create Razorpay order (Rs. 5) |
| POST | `/api/doctor/consultation/verify-payment` | Verify payment and open chat room |

### Hospitals
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/hospitals/nearby?lat=&lng=&type=` | Nearby hospitals/vaccination |

---

## 🔌 Socket.IO Events

### Client → Server
| Event | Payload | Description |
|-------|---------|-------------|
| `join_room` | `{token, room_id}` | Join a chat room |
| `leave_room` | `{room_id}` | Leave a chat room |
| `send_message` | `{token, room_id, message}` | Send message |
| `typing` | `{room_id, user_name}` | Typing indicator |
| `stop_typing` | `{room_id}` | Stop typing |

### Server → Client
| Event | Payload | Description |
|-------|---------|-------------|
| `receive_message` | `{content, sender_id, timestamp}` | New message |
| `user_typing` | `{user_name}` | Someone is typing |
| `room_joined` | `{room_id}` | Confirmation |

---

## 🤖 AI Model Details

The model pipeline (from `model_selector.py`), matching your training notebook exactly:

```
Raw Input (9 clinical features)
       ↓
StandardScaler.transform()
       ↓
SelectFromModel (RandomForest threshold="median")
       ↓
RF probability augmentation (np.hstack)
       ↓
ANN: Dense(128) → Dropout(0.3) → Dense(64) → Dropout(0.2) → Dense(32) → Dense(4, softmax)
       ↓
Prediction + Confidence + Suggestions
```

**Input Features:**
1. `age` — Patient age (years)
2. `gender` — 0=Female, 1=Male
3. `bmi` — Body Mass Index
4. `smoking` — 0=No, 1=Yes
5. `genetic_risk` — 0=Low, 1=Medium, 2=High
6. `physical_activity` — Hours per week
7. `alcohol_intake` — Units per week
8. `cancer_history` — 0=No, 1=Yes
9. `diagnosis` — 0=None, 1=Prior diagnosis

**Output Classes:**
- Class 0 → Normal (No Cancer) → LOW risk
- Class 1 → Benign Tumor → MODERATE risk
- Class 2 → Malignant Stage I/II → HIGH risk
- Class 3 → Malignant Stage III/IV → CRITICAL risk

---

## 🔐 Security Features
- JWT tokens with configurable expiry
- bcrypt password hashing (12 salt rounds)
- OTP-based email verification (10-minute expiry)
- Role-based access control (patient/doctor)
- CORS configured for frontend origin only
- Input validation on all endpoints
- Environment variables for all secrets

---

## 🌐 Environment Variables

### Backend (.env)
```
MONGO_URI           MongoDB connection string
JWT_SECRET          Secret key for JWT signing
JWT_EXPIRY_DAYS     Token expiry (default: 7)
SMTP_HOST           Email server host
SMTP_PORT           Email server port
SMTP_USER           Email address
SMTP_PASS           Email app password
OPENAI_API_KEY      OpenAI API key (optional)
GOOGLE_MAPS_API_KEY Google Maps API key (optional)
FRONTEND_URL        React dev server URL
FLASK_ENV           development / production
```

### Frontend (.env)
```
REACT_APP_API_URL       Backend API base URL (default: /api via proxy)
REACT_APP_SOCKET_URL    Socket.IO server URL
```

---

## 🏗️ Production Deployment

### Backend (Gunicorn + Nginx)
```bash
pip install gunicorn
gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:5000 app:app
```

### Frontend (Build)
```bash
npm run build
# Deploy /build to Nginx, Vercel, or Netlify
```

### MongoDB Atlas
Replace `MONGO_URI` with your Atlas connection string.

---

## 📦 Key Dependencies

### Backend
| Package | Purpose |
|---------|---------|
| Flask 3.0 | Web framework |
| Flask-SocketIO | Real-time WebSocket |
| PyMongo | MongoDB driver |
| PyJWT | JWT authentication |
| bcrypt | Password hashing |
| TensorFlow 2.16 | AI model inference |
| scikit-learn | Preprocessing pipeline |
| ReportLab | PDF generation |
| OpenAI | AI chatbot (optional) |

### Frontend
| Package | Purpose |
|---------|---------|
| React 18 | UI framework |
| React Router v6 | Navigation |
| Axios | HTTP client |
| Socket.IO Client | Real-time chat |
| Tailwind CSS | Styling |
| Recharts | Analytics charts |
| React Hot Toast | Notifications |
| Lucide React | Icons |

---

## ⚠️ Medical Disclaimer

Alpha-Cure is an **AI-assisted screening tool** for educational and informational purposes only.
It does **not** replace professional medical diagnosis or treatment.
Always consult a qualified healthcare provider for medical decisions.

---

*Built with ❤️ for early cancer detection and care*
