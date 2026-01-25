<div align="center">
  <img src="static/Banner.png" alt="ExpTrack Banner" width="800"/>
  
  # ExpTrack
  
  ### Master your money, achieve your dreams.
  
  [![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/) [![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/) [![Django](https://img.shields.io/badge/Django-5.0+-green.svg)](https://www.djangoproject.com/) [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://www.postgresql.org/)
</div>

---

## 🎯 About

**ExpTrack** is a comprehensive expense tracking and goal achievement platform designed to help you take control of your finances. Whether you're saving for a vacation, paying off debt, or building an emergency fund, ExpTrack provides the tools you need to succeed. 

Built with Django and PostgreSQL, ExpTrack offers a beautiful, intuitive interface that makes financial management simple, secure, and even enjoyable.

---

## ✨ Key Features

### 🔐 **Complete Authentication System**
- Secure user registration and login
- Password reset and email verification
- Profile management and security
- Session management with Django middleware
- Role-based access control

### 💰 **Balance Management**
- Track your current account balance in real-time
- Multiple account support
- Automatic balance updates with every transaction
- View balance history and trends
- Balance alerts and notifications

### 📈 **Income Tracking & Management**
- Add multiple income sources
- Categorize income streams
- Automatic balance addition on income entry
- Monthly and yearly income reports
- Income vs expense comparison

### 🎯 **Advanced Goal Setting**
- Create short-term and long-term financial goals
- Set target amounts and deadlines
- Track progress with visual indicators
- Goal milestones and achievements
- Smart goal recommendations

### 📊 **Goal Analytics with Advanced Charts**
- Interactive charts and graphs for goal tracking
- Progress visualization with Chart.js
- Comparative analysis of multiple goals
- Trend analysis and projections
- Goal success rate statistics
- Visual timeline of achievements

### 📑 **Advanced Visualization Reports**
- Comprehensive financial reports
- Spending pattern analysis
- Category-wise breakdowns
- Monthly/Yearly comparisons
- Custom date range reports
- PDF report generation

### 📤 **Excel Data Export**
- Export all financial data to Excel
- Customizable export templates
- Include charts and graphs in exports
- Multiple sheet exports (Income, Expenses, Goals, Balance)
- Automated monthly reports

### 🖥️ **Advanced Dashboard on Login**
- Personalized financial overview
- Quick stats: Balance, Income, Expenses, Goals
- Recent transactions feed
- Upcoming bill reminders
- Goal progress widgets
- Spending insights at a glance

### 📊 **Real-Time Expense Charts with Blocks**
- Live updating expense visualization
- Category-wise expense blocks
- Interactive pie charts and bar graphs
- Daily, weekly, monthly views
- Expense comparison charts
- Budget vs actual spending

### 📝 **Daily Expense Management**
- Quick expense entry system
- Categorize expenses efficiently
- Add notes and receipts
- Recurring expense automation
- Daily spending limits
- Expense calendar view

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

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/ompandey07/Exptrac.git
cd Exptrac
```

---

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

---

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

---

### Step 5: Configure Environment Variables

Create a `.env` file in the root directory and configure your settings (see [Environment Configuration](#environment-configuration) below).

---

### Step 6: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### Step 7: Create Superuser

```bash
python manage.py createsuperuser
```

---

### Step 8: Collect Static Files

```bash
python manage.py collectstatic
```

---

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

---

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

---

### User Features

1. **Register/Login** - Create your account or sign in securely
2. **Dashboard Overview** - View your complete financial summary at a glance
3. **Add Income** - Record income sources and watch your balance grow
4. **Track Expenses** - Log daily expenses with categories
5. **Set Goals** - Define financial objectives with target amounts
6. **View Analytics** - Analyze spending patterns with interactive charts
7. **Export Reports** - Download Excel reports of your financial data
8. **Monitor Balance** - Keep track of your real-time account balance

---

## 🛠️ Technologies Used

### Backend
- **Django** 5.0+ - High-level Python web framework
- **PostgreSQL** 13+ - Advanced relational database
- **Python** 3.12+ - Core programming language

### Frontend
- **HTML5** - Modern markup language
- **CSS3** - Advanced styling with animations
- **JavaScript** - Interactive client-side functionality
- **Chart.js** - Beautiful data visualization
- **Custom CSS** - Tailwind-inspired utility classes

### UI/UX Components
- **Icons:** Remix Icons, Lucide Icons
- **Fonts:** Google Fonts (Inter, Poppins, Kaushan Script, Agustina)
- **Charts:** Chart.js for advanced visualizations
- **Responsive Design:** Mobile-first approach

### Security & Tools
- **Django Security Middleware** - Built-in security features
- **CSRF Protection** - Cross-site request forgery prevention
- **Password Hashing** - Secure password storage
- **Session Management** - Secure user sessions
- **Excel Export** - openpyxl/xlsxwriter for data export

---

## 🤝 Contributing

Contributions are always welcome! Here's how you can help:

1. **Fork the repository**
2. **Create your feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

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
- Powered by open-source technologies

---

### "A budget is telling your money where to go instead of wondering where it went." 
― Dave Ramsey

---

**Made with ❤️ by Om Pandey**