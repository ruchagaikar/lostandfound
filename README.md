# 🔍 Lost & Found Web Application

A modern, secure, and visually stunning web platform for reporting and tracking lost or found items. Built with Python, Flask, and a custom Glassmorphism UI.

---

## 🌟 Features

### 🛡️ Security & Stability
- **Password Hashing:** Uses `pbkdf2:sha256` for secure user credential storage.
- **Secure File Uploads:** Validates file extensions and renames images with unique UUIDs to prevent overwriting and path traversal.
- **Access Control:** Restricted Edit/Delete/Resolve permissions—only item owners can manage their listings.
- **Environment Safety:** Uses `.env` for managing sensitive keys (SECRET_KEY).

### 📋 Item Management
- **Smart Filtering:** Filter the dashboard by Type (Lost/Found), Category, Location, or Keyword search.
- **Status Tracking:** Mark items as "Active" or "Resolved" to keep the community informed.
- **User Dashboard:** Dedicated "My Items" page for users to track their own reports.
- **Statistics:** Real-time dashboard stats showing current counts of lost and found items.

### 🎨 Premium UI/UX
- **Glassmorphism Design:** A modern dark-mode aesthetic with frosted glass elements and vibrant accents.
- **Fully Responsive:** Optimized for all devices, from mobile phones to desktop monitors.
- **Interactive Forms:** Features image upload previews and slide-in flash notifications.

---

## 🛠️ Tech Stack

- **Backend:** Python 3 + [Flask](https://flask.palletsprojects.com/)
- **Database:** SQLite3
- **Frontend:** HTML5 + Jinja2 + Vanilla CSS3 (Custom Design System)
- **Deployment:** Ready for [Azure App Service](https://azure.microsoft.com/en-us/products/app-service/)
- **Server:** Gunicorn (WSGI)

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/lost_found_azure.git
   cd lost_found_azure
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your_secure_random_key_here
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```
   Open `http://127.0.0.1:5000` in your browser.

---

## 📁 Project Structure

```text
├── app.py              # Main Flask application logic
├── requirements.txt    # Project dependencies
├── Procfile            # Deployment instructions for Azure
├── .env                # Environment secrets (ignored by Git)
├── .gitignore          # Git ignore rules
├── static/
│   ├── style.css       # Custom design system
│   └── uploads/        # Directory for user-uploaded images
└── templates/          # Jinja2 HTML templates
    ├── base.html       # Master layout
    ├── dashboard.html  # Main feed with filters
    └── ...             # Other functional pages
```

---

## ☁️ Deployment on Azure

This project is pre-configured for **Azure App Service**. To deploy:
1. Initialize a Git repo and push to GitHub.
2. In the Azure Portal, create a new **Web App** (Python 3.9+ runtime).
3. Connect the Web App to your GitHub repository under the **Deployment Center**.
4. Add your `SECRET_KEY` in the **Configuration** settings on Azure.

---

## 📜 License
This project is open-source and available under the [MIT License](LICENSE).
