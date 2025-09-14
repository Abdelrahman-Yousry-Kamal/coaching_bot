# app.py - Flask Backend for Nutrition Chatbot
import os
import io
import logging
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import chatbot
import db
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'wav', 'mp3', 'ogg', 'webm'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('data/users', exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_user_data(data):
    """Validate user registration data"""
    errors = []
    
    # Required fields
    required_fields = ['userId', 'name', 'age', 'weight', 'height', 'gender', 'activityLevel', 'goal']
    for field in required_fields:
        if not data.get(field):
            errors.append(f"{field} is required")
    
    # Validate ranges
    try:
        if data.get('age'):
            age = int(data['age'])
            if not (15 <= age <= 90):
                errors.append("Age must be between 15 and 90 years")
        
        if data.get('weight'):
            weight = float(data['weight'])
            if not (30 <= weight <= 300):
                errors.append("Weight must be between 30kg and 300kg")
        
        if data.get('height'):
            height = float(data['height'])
            if not (120 <= height <= 250):
                errors.append("Height must be between 120cm and 250cm")
        
        if data.get('gender') and data['gender'].lower() not in ['male', 'female']:
            errors.append("Gender must be 'male' or 'female'")
        
        if data.get('activityLevel') and data['activityLevel'] not in ['sedentary', 'light', 'moderate', 'very_active', 'extra_active']:
            errors.append("Invalid activity level")
        
        if data.get('goal') and data['goal'].lower() not in ['loss', 'gain', 'maintenance']:
            errors.append("Goal must be 'loss', 'gain', or 'maintenance'")
        
        if data.get('goal') == 'gain' and data.get('surplus'):
            surplus = int(data['surplus'])
            if not (300 <= surplus <= 500):
                errors.append("For muscle gain, surplus must be between 300 and 500 kcal")
    
    except (ValueError, TypeError) as e:
        errors.append(f"Invalid data format: {str(e)}")
    
    return errors

@app.route('/')
def index():
    """Serve the main HTML page"""
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return """
        <h1>Dietitian - Nutrition Chatbot</h1>
        <p>Please make sure 'index.html' is in the same directory as app.py</p>
        <p>The chatbot backend is running on <a href="/api/health">/api/health</a></p>
        """, 404

@app.route('/api/test')
def test_chatbot():
    """Test endpoint to verify chatbot connection"""
    try:
        # Test if modules are working
        print("Testing chatbot connection...")
        
        # Test database
        db.ensure_data_dir()
        print("✅ Database module working")
        
        # Test chatbot import
        if hasattr(chatbot, 'get_bot_response'):
            print("✅ Chatbot module has get_bot_response function")
        else:
            print("❌ Chatbot module missing get_bot_response function")
        
        return jsonify({
            'success': True,
            'message': 'Chatbot connection test passed',
            'modules': {
                'chatbot': str(chatbot),
                'db': str(db),
                'functions': {
                    'get_bot_response': hasattr(chatbot, 'get_bot_response'),
                    'load_user_data': hasattr(db, 'load_user_data'),
                    'create_user_file': hasattr(db, 'create_user_file')
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Dietitian API is running',
        'endpoints': {
            'register': '/api/register',
            'chat': '/api/chat',
            'user': '/api/user/<user_id>'
        }
    })

@app.route('/api/register', methods=['POST'])
def register_user():
    """Register a new user or check existing user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        logger.info(f"Registration attempt for user: {data.get('userId')}")
        
        # Validate input data
        validation_errors = validate_user_data(data)
        if validation_errors:
            return jsonify({
                'success': False, 
                'message': 'Validation failed',
                'errors': validation_errors
            }), 400
        
        user_id = data['userId'].strip()
        
        # Check if user already exists
        existing_user = db.load_user_data(user_id)
        if existing_user:
            return jsonify({
                'success': False, 
                'message': f'Username "{user_id}" already exists. Please choose a different username.'
            }), 409
        
        # Create new user
        try:
            db.create_user_file(
                user_id=user_id,
                name=data['name'],
                age=int(data['age']),
                weight=float(data['weight']),
                height=float(data['height']),
                goal=data['goal'].lower(),
                activity_level=data['activityLevel']
            )
            
            # Update user data with additional fields
            user_data = db.load_user_data(user_id)
            user_data.update({
                'gender': data['gender'].lower(),
                'surplus': int(data.get('surplus', 400)) if data['goal'].lower() == 'gain' else 400
            })
            db.save_user_data(user_id, user_data)
            
            # Calculate nutrition requirements
            nutrition_results = db.calculate_nutrition(user_id)
            
            logger.info(f"User {user_id} registered successfully")
            
            return jsonify({
                'success': True,
                'message': 'User registered successfully',
                'user_id': user_id,
                'nutrition': nutrition_results
            })
        
        except Exception as e:
            logger.error(f"Error creating user file: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Failed to create user profile: {str(e)}'
            }), 500
    
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Registration failed: {str(e)}'
        }), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with text, image, and voice support"""
    try:
        user_id = request.form.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'User ID is required'}), 400
        
        # Verify user exists
        user_data = db.load_user_data(user_id)
        if not user_data:
            return jsonify({
                'success': False, 
                'message': 'User not found. Please register first.'
            }), 404
        
        # Get message content
        message = request.form.get('message', '').strip()
        
        # Handle file uploads
        image_data = None
        voice_data = None
        
        # Process image upload
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename and allowed_file(image_file.filename):
                try:
                    image_data = image_file.read()
                    logger.info(f"Image uploaded for user {user_id}: {len(image_data)} bytes")
                except Exception as e:
                    logger.error(f"Error reading image: {str(e)}")
                    return jsonify({
                        'success': False,
                        'message': 'Failed to process image upload'
                    }), 400
        
        # Process voice upload
        if 'audio' in request.files:
            audio_file = request.files['audio']
            if audio_file and audio_file.filename:
                try:
                    voice_data = audio_file.read()
                    logger.info(f"Audio uploaded for user {user_id}: {len(voice_data)} bytes")
                except Exception as e:
                    logger.error(f"Error reading audio: {str(e)}")
                    return jsonify({
                        'success': False,
                        'message': 'Failed to process audio upload'
                    }), 400
        
        # Ensure we have some input
        if not message and not image_data and not voice_data:
            return jsonify({
                'success': False,
                'message': 'Please provide a message, image, or voice input'
            }), 400
        
        # Get bot response using your existing chatbot
        logger.info(f"Processing chat request for user {user_id}")
        
        try:
            bot_response = chatbot.get_bot_response(
                user_id=user_id,
                user_input=message if message else None,
                image_data=image_data,
                voice_data=voice_data
            )
            
            logger.info(f"Bot response generated for user {user_id}")
            
            return jsonify({
                'success': True,
                'response': bot_response,
                'user_id': user_id
            })
        
        except Exception as e:
            logger.error(f"Chatbot error for user {user_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Sorry, I encountered an error processing your request. Please try again.',
                'error': str(e)
            }), 500
    
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An unexpected error occurred'
        }), 500

@app.route('/api/user/<user_id>')
def get_user(user_id):
    """Get user information and chat history"""
    try:
        user_data = db.load_user_data(user_id)
        if not user_data:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        chats = db.get_chats(user_id)
        
        # Remove sensitive data before sending
        safe_user_data = {
            'user_id': user_data.get('user_id'),
            'name': user_data.get('name'),
            'created_at': user_data.get('created_at'),
            'nutrition': user_data.get('nutrition', {}),
            'goal': user_data.get('goal'),
            'activity_level': user_data.get('activity_level')
        }
        
        return jsonify({
            'success': True,
            'user': safe_user_data,
            'chats': chats[-10:]  # Return last 10 chats
        })
    
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve user data'
        }), 500

@app.route('/api/nutrition/<user_id>')
def get_nutrition(user_id):
    """Get user's nutrition calculations"""
    try:
        results = db.calculate_nutrition(user_id)
        if isinstance(results, str):  # Error message
            return jsonify({'success': False, 'message': results}), 400
        
        return jsonify({
            'success': True,
            'nutrition': results
        })
    
    except Exception as e:
        logger.error(f"Error calculating nutrition for {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to calculate nutrition'
        }), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({
        'success': False,
        'message': 'File too large. Maximum size is 16MB.'
    }), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'message': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🌱 DIETITIAN - AI NUTRITION COACH")
    print("=" * 50)
    print("🚀 Starting Flask server...")
    print("📱 Open your browser to: http://localhost:5000")
    print("🔧 API Health Check: http://localhost:5000/api/health")
    print("💬 Make sure 'index.html' is in the same directory")
    print("=" * 50)
    
    # Ensure required files exist
    required_files = ['chatbot.py', 'db.py', 'cleaned_food_data.csv']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print(f"⚠️  Warning: Missing files: {missing_files}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)