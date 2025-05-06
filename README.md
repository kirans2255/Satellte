# Satellite Tracking Application

A modern web application for tracking satellites in real-time, built with Flask and React.

## Features

- User authentication (login/signup)
- Real-time satellite tracking
- Modern and responsive UI
- Secure password handling
- JWT-based authentication
- PostgreSQL database integration
- Dark mode support
- Password strength indicator
- Form validation
- Error handling
- Loading states
- Notifications

## Tech Stack

### Backend
- Python 3.8+
- Flask
- Flask-SQLAlchemy
- Flask-JWT-Extended
- Flask-Bcrypt
- PostgreSQL
- N2YO API

### Frontend
- HTML5
- CSS3 (with CSS Variables)
- JavaScript (ES6+)
- Fetch API
- Local Storage

## Prerequisites

- Python 3.8 or higher
- PostgreSQL
- Node.js (for development)
- npm (for development)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/satellite-tracking.git
cd satellite-tracking
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
flask db upgrade
```

5. Create a `.env` file in the root directory with the following variables:
```
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=True
DATABASE_URL=postgresql://postgres:yourpassword@localhost/Satellite
JWT_SECRET_KEY=your-secret-key-here
N2YO_API_KEY=your-n2yo-api-key
```

6. Run the application:
```bash
flask run
```

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
```

### Linting
```bash
flake8
```

## Project Structure

```
satellite-tracking/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
├── static/               # Static files
│   ├── styles.css        # Main styles
│   ├── login.css         # Login page styles
│   ├── signup.css        # Signup page styles
│   └── script.js         # Client-side JavaScript
├── templates/            # HTML templates
│   ├── login.html        # Login page
│   ├── signup.html       # Signup page
│   └── o.html           # Main page
└── README.md            # Project documentation
```

## Security Features

- Password hashing with bcrypt
- JWT-based authentication
- CSRF protection
- Secure session handling
- Input validation
- SQL injection prevention
- XSS protection

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- N2YO API for satellite data
- Flask community for the amazing framework
- All contributors who have helped improve this project 