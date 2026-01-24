# ExpTrack

<div align="center">
  <img src="static/Banner.png" alt="ExpTrack Banner" width="100%">
  
  ### Master your money, achieve your dreams.
  
  [![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
  [![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
  [![Django](https://img.shields.io/badge/Django-5.0+-green.svg)](https://www.djangoproject.com/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://www.postgresql.org/)
</div>

---

## 📋 Table of Contents

- [About](#about)
- [Key Features](#key-features)
- [Demo](#demo)
- [Installation](#installation)
- [Environment Configuration](#environment-configuration)
- [Usage](#usage)
- [Technologies Used](#technologies-used)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## 🎯 About

**ExpTrack** is a comprehensive expense tracking and goal achievement platform designed to help you take control of your finances. Whether you're saving for a vacation, paying off debt, or building an emergency fund, ExpTrack provides the tools you need to succeed.

Built with Django and PostgreSQL, ExpTrack offers a beautiful, intuitive interface that makes financial management simple, secure, and even enjoyable.

---

## ✨ Key Features

- ⚡ **Lightning Fast Analysis** - Complete site audit in under 30 seconds
- 📊 **Professional Excel Reports** - 7 detailed sheets with color-coded insights
- 🔒 **Security Assessment** - Validates critical security headers and vulnerabilities
- 📈 **SEO Analysis** - Meta tags, headings, image alt text, and link optimization
- 🖼️ **Image Optimization** - Size analysis, format suggestions, and compression tips
- 🔗 **Broken Link Detection** - Identifies and reports 404s and failed requests
- 📱 **Mobile-Friendly Checks** - Responsive design and viewport validation
- 💡 **Performance Boost Guide** - Step-by-step improvement recommendations
- 🎯 **Rating System** - Get scored from Beginner to Champion level
- 🖥️ **Both CLI and Python API** - Use in terminal or integrate into your projects
- 📊 **Visual Reports** - Beautiful charts and graphs for spending patterns
- 🎯 **Goal Setting** - Define and track short-term and long-term financial goals
- 💰 **Budget Planning** - Create and manage monthly budgets
- 🔔 **Smart Reminders** - Never miss a bill payment
- 🌐 **Cloud Sync** - Access your data from anywhere
- 📤 **Export Data** - Download your financial reports

---

## 🎬 Demo

🔗 **Live Demo:** [https://github.com/ompandey07/Exptrac](https://github.com/ompandey07/Exptrac)

---

## 🚀 Installation

### Prerequisites

- Python 3.12 or higher
- Django 5.0 or higher
- PostgreSQL 13 or higher
- pip (Python package installer)
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/ompandey07/Exptrac.git
cd Exptrac
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up PostgreSQL Database

Create a new PostgreSQL database for ExpTrack:

```sql
CREATE DATABASE exptrack_db;
CREATE USER exptrack_user WITH PASSWORD 'your_password';
ALTER ROLE exptrack_user SET client_encoding TO 'utf8';
ALTER ROLE exptrack_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE exptrack_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE exptrack_db TO exptrack_user;
```

### Step 5: Configure Environment Variables

Create a `.env` file in the root directory and configure your settings (see [Environment Configuration](#environment-configuration) below).

### Step 6: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 7: Create Superuser

```bash
python manage.py createsuperuser
```

### Step 8: Collect Static Files

```bash
python manage.py collectstatic
```

### Step 9: Run the Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser to access ExpTrack!

---

## 🔐 Environment Configuration

Create a `.env` file in the root directory with the following configuration:

```env
# Django Settings
SECRET_KEY=your-secret-key-here-generate-a-new-one
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings (PostgreSQL)
DB_NAME=exptrack_db
DB_USER=exptrack_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432

# Email Settings (Optional - for password reset, notifications)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password

# Security Settings (Production)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS=DENY

# Additional Settings
LANGUAGE_CODE=en-us
TIME_ZONE=UTC
USE_I18N=True
USE_TZ=True
```

### Generating a Secret Key

To generate a new secret key, run:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Or use this command:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 💻 Usage

### Admin Panel

Access the Django admin panel at `http://127.0.0.1:8000/admin/` with your superuser credentials.

### User Features

1. **Register/Login** - Create your account or sign in
2. **Set Goals** - Define your financial objectives
3. **Track Expenses** - Log your daily spending
4. **View Reports** - Analyze your financial data
5. **Manage Budgets** - Create and monitor monthly budgets
6. **Achieve Goals** - Track progress and celebrate milestones

---

## 🛠️ Technologies Used

- **Backend:** Django 5.0+
- **Database:** PostgreSQL 13+
- **Python:** 3.12+
- **Frontend:** HTML5, CSS3, JavaScript
- **UI Framework:** Custom CSS with Tailwind-inspired utilities
- **Icons:** Remix Icons, Lucide Icons
- **Fonts:** Google Fonts (Inter, Poppins, Kaushan Script, Agustina)
- **Charts:** Chart.js / Custom SVG
- **Security:** Django security middleware, CSRF protection

---

## 🤝 Contributing

Contributions are always welcome! Here's how you can help:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please make sure to update tests as appropriate and adhere to the existing coding style.

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📧 Contact

**Om Pandey**

- GitHub: [@ompandey07](https://github.com/ompandey07)
- Project Link: [https://github.com/ompandey07/Exptrac](https://github.com/ompandey07/Exptrac)

---

## 🙏 Acknowledgments

- Inspired by the need for simple, effective personal finance management
- Built with love for the financial wellness community
- Special thanks to all contributors and users

---

<div align="center">
  
  ### "A budget is telling your money where to go instead of wondering where it went."
  ― Dave Ramsey
  
  **Made with ❤️ by Om Pandey**
  
</div>