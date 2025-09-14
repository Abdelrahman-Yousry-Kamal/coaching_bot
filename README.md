# Dietitian - AI Nutrition Coach 🥗🤖

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-red.svg)](https://ai.google.dev/)

An intelligent nutrition coaching application that combines AI-powered food analysis with personalized nutrition guidance. Get instant calorie estimates, nutritional breakdowns, and expert advice through text, voice, or image inputs.

## 🌟 Features

### Multi-Modal Input Support
- **💬 Text Chat**: Natural conversation with AI nutritionist
- **📸 Image Analysis**: Advanced food recognition using Google Gemini Vision
- **🎤 Voice Input**: Speech-to-text for hands-free interaction

### AI-Powered Analysis
- **🔍 Food Recognition**: Identify multiple foods in complex images
- **⚖️ Portion Estimation**: Automatic portion size detection
- **🧮 Calorie Calculation**: Accurate per-item and total calorie estimation
- **📊 Nutritional Breakdown**: Detailed macro and micronutrient analysis

### Personalized Nutrition
- **📈 BMR/TDEE Calculations**: Science-based metabolic rate calculations
- **🎯 Goal-Based Recommendations**: Customized for weight loss, gain, or maintenance
- **🥘 Smart Food Database**: Vector search with 10,000+ food items
- **📱 Responsive Design**: Works seamlessly on all devices

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Google Gemini API key ([Get one here](https://ai.google.dev/))
- 2GB+ RAM recommended
- Internet connection for AI features

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/dietitian-ai.git
   cd dietitian-ai
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file
   echo "GEMINI_API_KEY=your_api_key_here" > .env
   ```

5. **Run the application**
   ```bash
   python flask_server.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:5000`

## 🛠️ Project Structure

```
dietitian-ai/
├── 📄 flask_server.py          # Main Flask application
├── 🤖 chatbot.py               # AI chatbot functionality
├── 🗄️ db.py                    # Database operations
├── 🔍 searchengine.py          # Vector search utilities
├── 🌐 index.html               # Frontend interface
├── 📊 cleaned_food_data.csv    # Nutrition database (10,000+ foods)
├── 📁 data/                    # User data storage
│   ├── users/                  # Individual user profiles
│   └── index.json              # User index
├── 📁 uploads/                 # Temporary file storage
├── 📁 chroma_nutrition/        # Vector database
├── 📁 static/                  # CSS, JS, and assets
└── 📄 requirements.txt         # Python dependencies
```

## 📚 API Documentation

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/register` | Register new user |
| `GET` | `/api/user/<id>` | Get user profile |
| `POST` | `/api/chat` | Send message/image/voice |
| `GET` | `/api/nutrition/<id>` | Get nutrition calculations |
| `GET` | `/api/health` | Health check |

### Example Usage

**Register a new user:**
```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "age": 30,
    "weight": 70.0,
    "height": 175.0,
    "gender": "male",
    "activity_level": "moderate",
    "goal": "maintenance"
  }'
```

**Analyze food image:**
```bash
curl -X POST http://localhost:5000/api/chat \
  -F "user_id=your_user_id" \
  -F "file=@your_food_image.jpg"
```

## 🧠 AI Capabilities

### Image Analysis Pipeline
1. **Preprocessing**: Image optimization and format standardization
2. **AI Analysis**: Google Gemini 1.5-flash vision model processing
3. **Food Detection**: Multi-food identification with confidence scores
4. **Portion Estimation**: Visual cue analysis for serving sizes
5. **Nutrition Mapping**: Database matching for accurate nutritional data

### Supported Formats
- **Images**: JPEG, PNG, WebP (max 16MB)
- **Audio**: WAV, MP3, OGG (max 10MB)
- **Text**: UTF-8 encoded messages

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | ✅ | - |
| `FLASK_ENV` | Environment mode | ❌ | `production` |
| `FLASK_DEBUG` | Debug mode | ❌ | `False` |
| `MAX_CONTENT_LENGTH` | Max upload size (bytes) | ❌ | `16777216` |

### Advanced Configuration

```python
# config.py (optional)
class Config:
    # Database settings
    DATABASE_PATH = './data'
    UPLOAD_FOLDER = './uploads'
    
    # AI settings
    MAX_TOKENS = 1000
    TEMPERATURE = 0.7
    
    # Performance settings
    CACHE_TIMEOUT = 3600
    MAX_WORKERS = 4
```

## 🔧 Development

### Setting Up Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run with debug mode
export FLASK_ENV=development
export FLASK_DEBUG=True
python flask_server.py
```

### Optimization Tips
- Use high-quality, well-lit images for better accuracy
- Ensure clear audio with minimal background noise
- Keep user profiles updated for accurate recommendations
- Monitor API usage to stay within rate limits

## 🔒 Security & Privacy

### Data Protection
- ✅ Local JSON file storage (no cloud databases)
- ✅ Automatic cleanup of temporary files
- ✅ Input validation and sanitization
- ✅ No sensitive data in API responses
- ✅ CORS protection configured

### Privacy Features
- 🔒 Data stays on your server
- 🗑️ User data deletion capability
- 📊 Anonymous usage analytics only
- 🔐 Secure API key management

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Style
- Follow PEP 8 for Python code
- Use type hints where appropriate
- Write comprehensive docstrings
- Maintain test coverage above 80%

## 🐛 Troubleshooting

### Common Issues

**API Connection Failed**
```bash
# Check your API key
echo $GEMINI_API_KEY

# Test API connectivity
python -c "import google.generativeai as genai; genai.configure(api_key='your_key'); print('Connected!')"
```

**Image Analysis Not Working**
- Ensure image is well-lit and clear
- Check file format (JPEG, PNG, WebP only)
- Verify file size < 16MB
- Try different image angles

**Voice Recognition Issues**
- Check microphone permissions
- Use supported audio formats (WAV recommended)
- Ensure clear speech with minimal background noise
- Test with shorter audio clips

**Performance Issues**
```bash
# Check system resources
htop  # or top on macOS

# Monitor application logs
tail -f logs/application.log

# Clear cache
rm -rf chroma_nutrition/
python flask_server.py  # Will rebuild vector database
```

## 📈 Roadmap

**Disclaimer**: This application provides nutritional information for educational purposes only. It is not intended to replace professional medical advice, diagnosis, or treatment. Always consult with a qualified healthcare provider before making significant changes to your diet or exercise routine.
