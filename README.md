# AspireEC Chatbot

A sophisticated educational consulting chatbot system developed by Arham. This project combines a user-friendly form interface with an intelligent chatbot to provide comprehensive educational consulting services.

## 🌟 Features

### Form Interface
- Beautiful and responsive design
- Comprehensive student information collection
- Fields for:
  - Name
  - Email
  - Phone Number (Optional)
  - Level of Study
  - Field of Interest
  - Desired Course
- Form validation
- Email notifications to admin
- Smooth animations and transitions

### Chatbot Interface
- Intelligent response system
- Context-aware conversations
- Real-time message handling
- Beautiful UI with message bubbles
- Typing indicators
- Session management
- Responsive design

### Toggle Widget
- Floating chat button
- Smooth popup animations
- Mobile-responsive design
- Easy integration with any website
- Attention-grabbing animations
- User-friendly interface

## 🛠️ Technology Stack

- **Backend**: Python with FastAPI
- **Frontend**: HTML, CSS, JavaScript
- **Styling**: Custom CSS with modern design principles
- **Email**: SMTP for form submissions
- **Deployment**: Heroku-ready with Procfile

## 📋 Prerequisites

- Python 3.8+
- pip (Python package manager)
- Virtual environment (recommended)

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/aspireec-chatbot.git
cd aspireec-chatbot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure email settings in `app/main.py`:
```python
ADMIN_EMAIL = "your-admin-email@example.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your-email@gmail.com"
SMTP_PASSWORD = "your-app-password"
```

## 🏃‍♂️ Running the Application

1. Start the development server:
```bash
uvicorn app.main:app --reload
```

2. Access the application:
- Form: http://localhost:8000/
- Chatbot: http://localhost:8000/chat
- Toggle Widget: http://localhost:8000/toggle

## 🌐 Integration

### WordPress Integration
Add this code to your WordPress page to embed the toggle widget:
```html
<iframe src="http://your-domain.com/toggle" width="100%" height="100px" frameborder="0" style="border: none; position: fixed; bottom: 0; right: 0; z-index: 9999;"></iframe>
```

### Direct Form Integration
Add this code to embed the form directly:
```html
<iframe src="http://your-domain.com/" width="100%" height="800px" frameborder="0" style="border: none;"></iframe>
```

## 📱 Responsive Design

The application is fully responsive and works seamlessly on:
- Desktop computers
- Tablets
- Mobile phones
- Different screen sizes and orientations

## 🔒 Security Features

- CORS protection
- Form validation
- Secure email handling
- XSS protection
- CSRF protection

## 🎨 Customization

The application can be customized by modifying:
- Colors in CSS variables
- Form fields in `form.html`
- Chatbot responses in `chatbot_core.py`
- Email templates in `main.py`

## 👨‍💻 Developer

**Arham**
- Lead Developer
- Full-stack developer
- Educational technology specialist

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For support, email info.aibytech@gmail.com or create an issue in the repository.

## 🙏 Acknowledgments

- FastAPI team for the amazing framework
- All contributors who have helped shape this project
- The educational consulting community for their valuable feedback 