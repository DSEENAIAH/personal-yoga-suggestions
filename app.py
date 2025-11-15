from flask import Flask, render_template, request, jsonify
from models import db, Asana, Sequence, Session, User
from textblob import TextBlob
import json
import os
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yoga_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def is_greeting(text):
    """Check if text is ONLY a greeting (no emotional content)"""
    text_lower = text.lower()
    greeting_words = ['hi', 'hello', 'hey', 'namaste', 'vannakkam', 'em chestunav', 'ela unnav', 'epdi iruka', 'kaise ho']
    emotion_words = ['tension', 'stress', 'sad', 'happy', 'tired', 'worried', 'badhaga', 'santhosham', 'kopam', 'angry']
    
    has_greeting = any(word in text_lower for word in greeting_words)
    has_emotion = any(word in text_lower for word in emotion_words)
    
    # Only consider it a pure greeting if it has greeting words but NO emotional content
    return has_greeting and not has_emotion and len(text.split()) <= 6

def analyze_emotion_and_language(text):
    """Analyze emotion and language with greeting priority"""
    text_lower = text.lower().strip()
    
    # Detect language first
    language = detect_language(text)
    print(f"Language detected: {language}")
    
    # Check for common greetings/questions first (override emotion analysis)
    greeting_patterns = {
        'telugu': ['em chestunav', 'enti chestunav', 'ela unnav', 'namaste'],
        'tamil': ['epdi iruka', 'enna panra', 'vanakkam'],
        'hindi': ['kaise ho', 'kya kar rahe ho', 'namaste'],
        'english': ['how are you', 'what are you doing', 'hello', 'hi']
    }
    
    # Check if it's a greeting in detected language
    for lang, patterns in greeting_patterns.items():
        if any(pattern in text_lower for pattern in patterns):
            print(f"Detected greeting pattern in {lang}")
            return 'neutral', 3, language  # Neutral emotion for greetings
    
    # Only do emotion analysis if not a greeting
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    
    print(f"TextBlob polarity: {polarity}")
    
    # Convert polarity to emotion
    if polarity > 0.3:
        emotion = 'happy'
        intensity = min(5, int((polarity + 1) * 2.5))
    elif polarity < -0.3:
        emotion = 'stressed'  # Simplified emotion detection
        intensity = min(5, int(abs(polarity) * 5) + 2)
    else:
        emotion = 'neutral'
        intensity = 3
    
    print(f"Final emotion: {emotion}, intensity: {intensity}, language: {language}")
    return emotion, intensity, language

def detect_language(text):
    """Simple but effective language detection"""
    text_lower = text.lower().strip()
    
    print(f"Detecting language for: '{text_lower}'")
    
    # Direct phrase matching (highest priority)
    if 'em chestunav' in text_lower or 'enti chestunav' in text_lower:
        print("Detected Telugu via phrase matching")
        return 'telugu'
    
    if 'epdi iruka' in text_lower or 'enna panra' in text_lower:
        print("Detected Tamil via phrase matching")
        return 'tamil'
    
    if 'kaise ho' in text_lower or 'kya kar rahe ho' in text_lower:
        print("Detected Hindi via phrase matching")
        return 'hindi'
    
    # Word-based detection
    telugu_words = ['nenu', 'nuvvu', 'unnav', 'chestunav', 'ela', 'emi', 'enti', 'bagundi', 'ledhu']
    tamil_words = ['naan', 'nee', 'iruku', 'epdi', 'enna', 'panra', 'sollu', 'illa', 'aama']
    hindi_words = ['main', 'tum', 'kaise', 'kya', 'kar', 'rahe', 'ho', 'hai', 'achha', 'nahi']
    
    # Count matches
    telugu_count = sum(1 for word in telugu_words if word in text_lower)
    tamil_count = sum(1 for word in tamil_words if word in text_lower)
    hindi_count = sum(1 for word in hindi_words if word in text_lower)
    
    print(f"Word counts - Telugu: {telugu_count}, Tamil: {tamil_count}, Hindi: {hindi_count}")
    
    if telugu_count > 0:
        print("Detected Telugu via word matching")
        return 'telugu'
    elif tamil_count > 0:
        print("Detected Tamil via word matching")
        return 'tamil'
    elif hindi_count > 0:
        print("Detected Hindi via word matching")
        return 'hindi'
    else:
        print("Defaulting to English")
        return 'english'

@app.route('/')
def index():
    return render_template('emotion_selection.html')

@app.route('/chat')
def chat_interface():
    return render_template('chat_interface.html')

@app.route('/voice-chat')
def voice_chat():
    return render_template('voice_chat.html')

@app.route('/guided-flow')
def guided_flow():
    return render_template('guided_flow.html')

@app.errorhandler(404)
def not_found(error):
    return render_template('emotion_selection.html'), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/debug/database', methods=['GET'])
def debug_database():
    try:
        asana_count = Asana.query.count()
        sequence_count = Sequence.query.count()
        user_count = User.query.count()
        
        sequences = Sequence.query.all()
        sequence_emotions = [seq.emotion for seq in sequences]
        
        return jsonify({
            'asanas': asana_count,
            'sequences': sequence_count,
            'users': user_count,
            'available_emotions': sequence_emotions,
            'database_status': 'initialized' if sequence_count > 0 else 'empty'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'database_status': 'error'}), 500

@app.route('/api/analyze-conversation', methods=['POST'])
def analyze_conversation():
    try:
        data = request.get_json()
        if not data or 'conversation_history' not in data:
            return jsonify({'error': 'Conversation history is required'}), 400
        
        conversation_history = data['conversation_history']
        
        # Extract all user messages
        user_messages = [msg['content'] for msg in conversation_history if msg['sender'] == 'user']
        
        if not user_messages:
            return jsonify({'error': 'No user messages found'}), 400
        
        # Combine all messages for analysis
        combined_text = ' '.join(user_messages)
        
        # Analyze the entire conversation
        emotion, intensity, detected_lang = analyze_emotion_and_language(combined_text)
        
        # Map neutral to happy for better user experience
        if emotion == 'neutral':
            emotion = 'happy'
            
        # Generate yoga message
        yoga_messages = {
            'stressed': 'Perfect for releasing tension and calming your mind.',
            'anxious': 'Designed to ground you and reduce anxiety.',
            'sad': 'Gentle poses to lift your mood and restore energy.',
            'angry': 'Cooling poses to release anger and find peace.',
            'tired': 'Energizing flow to boost your vitality.',
            'happy': 'A balanced, energizing flow for overall wellness and positivity!'
        }
        
        return jsonify({
            'emotion': emotion,
            'intensity': intensity,
            'detected_language': detected_lang,
            'yoga_message': yoga_messages.get(emotion, yoga_messages['happy']),
            'conversation_analysis': f'Analyzed {len(user_messages)} messages'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice-chat', methods=['POST'])
def voice_chat_analyze():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        message = data['message'].strip()
        conversation_history = data.get('conversation_history', [])
        
        if len(message) < 2:
            return jsonify({'error': 'Please provide a longer message'}), 400
        
        # Analyze emotion from voice input
        emotion, intensity, detected_lang = analyze_emotion_and_language(message)
        
        # Generate empathetic voice response
        response_data = generate_voice_response(
            message, emotion, intensity, detected_lang, conversation_history
        )
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat-analyze', methods=['POST'])
def chat_analyze():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        message = data['message'].strip()
        conversation_history = data.get('conversation_history', [])
        is_quick_response = data.get('is_quick_response', False)
        
        if len(message) < 2:
            return jsonify({'error': 'Please provide a longer message'}), 400
        
        # Analyze emotion and language
        emotion, intensity, detected_lang = analyze_emotion_and_language(message)
        
        # Generate conversational response
        response_data = generate_conversational_response(
            message, emotion, intensity, detected_lang, conversation_history, is_quick_response
        )
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_conversational_response(message, emotion, intensity, language, history, is_quick_response):
    """Generate contextual conversational response using TextBlob analysis"""
    
    # Count conversation turns
    conversation_turns = len([h for h in history if h['sender'] == 'user'])
    
    # Use TextBlob to analyze message content
    blob = TextBlob(message)
    
    # Check message characteristics
    is_greeting_msg = is_greeting(message)
    has_coping_words = any(word in message.lower() for word in ['music', 'songs', 'walk', 'friends', 'family', 'padatam', 'vindam'])
    is_question = message.strip().endswith('?') or any(word in message.lower() for word in ['what', 'how', 'why', 'when', 'emi', 'ela', 'enna', 'kya'])
    
    # Determine conversation context
    if blob.sentiment.subjectivity < 0.3:  # Objective/factual
        context = 'general_chat'
    elif has_coping_words:
        context = 'coping_response'
    elif is_greeting_msg:
        context = 'simple_greeting'
    elif emotion == 'happy':
        context = 'happy_response'
    else:
        context = 'supportive_response'
    
    # Generate dynamic responses based on full message context
    def get_response(context, language, emotion, intensity, message):
        message_lower = message.lower()
        
        # Check if message has both greeting AND emotion content
        has_greeting = any(word in message_lower for word in ['em chestunav', 'what are you doing', 'epdi iruka', 'kaise ho'])
        has_emotion_content = any(word in message_lower for word in ['tension', 'stress', 'sad', 'happy', 'tired', 'worried', 'badhaga', 'santhosham'])
        
        # If message has both greeting and emotional content, prioritize emotion
        if has_greeting and has_emotion_content:
            if emotion == 'stressed' or 'tension' in message_lower:
                responses = {
                    'english': "I can hear you're feeling stressed. What's been going on?",
                    'telugu': "Nuvvu tension lo unnav anipistundi. Emi jarigindi cheppu?",
                    'tamil': "Nee tension ah irukura madhiri theriyudhu. Enna nadandhuchu?",
                    'hindi': "Lagta hai tum tension mein ho. Kya hua hai?"
                }
                return responses.get(language, responses['english'])
        
        # Pure greeting without emotional content
        elif has_greeting and not has_emotion_content:
            responses = {
                'english': "Just here to chat and help! What's up with you?",
                'telugu': "Ikkada unna nuvvu tho matladataniki! Nuvvu enti chestunnav?",
                'tamil': "Inga irken unna kooda pesa! Nee enna panra?",
                'hindi': "Yahan hun tumse baat karne! Tum kya kar rahe ho?"
            }
            return responses.get(language, responses['english'])
        
        responses = {
            'simple_greeting': {
                'english': "Hey! How's it going?",
                'telugu': "Enti ra! Ela unnav?",
                'tamil': "Vanakkam! Epdi iruka?",
                'hindi': "Namaste! Kaise ho?"
            },
            'supportive_response': {
                'english': f"I can sense you're feeling {emotion}. Want to talk about it?",
                'telugu': f"Nuvvu {emotion} ga unnav anipistundi. Matladamantava?",
                'tamil': f"Nee {emotion} ah irukura madhiri theriyudhu. Pesalama?",
                'hindi': f"Lagta hai tum {emotion} feel kar rahe ho. Baat karna hai?"
            },
            'happy_response': {
                'english': "That's awesome! You sound really happy!",
                'telugu': "Waah! Chala happy ga unnav!",
                'tamil': "Super! Romba happy ah iruka!",
                'hindi': "Bahut achha! Tum bahut khush lag rahe ho!"
            },
            'coping_response': {
                'english': "That's great! Those things really help.",
                'telugu': "Adi bagundi! Vaati valla help avtundi.",
                'tamil': "Adhu nalladu! Avai romba help aagum.",
                'hindi': "Yeh achhi baat hai! Yeh cheezein help karti hain."
            },
            'general_chat': {
                'english': "Tell me more about what's going on.",
                'telugu': "Inka cheppu emi jarigindi.",
                'tamil': "Inka enna nadakudhu sollu.",
                'hindi': "Aur batao kya chal raha hai."
            }
        }
        return responses.get(context, responses['general_chat']).get(language, responses[context]['english'])
    
    response = get_response(context, language, emotion, intensity, message)
    
    # Determine if yoga should be suggested (after meaningful conversation)
    suggest_yoga = conversation_turns > 5 and emotion != 'neutral' and context != 'simple_greeting'
    
    # Generate follow-up questions using TextBlob insights (but not for greetings)
    follow_up_questions = []
    if context in ['supportive_response', 'general_chat'] and not is_question and not is_greeting_msg:
        follow_up_questions = generate_dynamic_questions(message, emotion, language)
    
    # Yoga suggestion based on analysis
    yoga_message = ""
    if suggest_yoga:
        yoga_templates = {
            'english': "Want to try some yoga? It might help.",
            'telugu': "Yoga try cheyyamantava? Help avtundi.",
            'tamil': "Yoga try pannalama? Help aagum.",
            'hindi': "Yoga try karna hai? Help karega."
        }
        yoga_message = yoga_templates.get(language, yoga_templates['english'])
    
    return {
        'response': response,
        'emotion': emotion,
        'intensity': intensity,
        'detected_language': language,
        'follow_up_questions': follow_up_questions[:3],
        'ready_for_yoga': suggest_yoga,
        'yoga_message': yoga_message,
        'conversation_stage': context
    }

def generate_dynamic_questions(message, emotion, language):
    """Generate contextual questions based on actual message content"""
    message_lower = message.lower()
    
    # Context-specific responses
    if any(word in message_lower for word in ['em chestunav', 'what are you doing', 'epdi iruka', 'kaise ho']):
        questions = {
            'english': ["Just here chatting with you!", "What about you? How's your day?"],
            'telugu': ["Nuvvu tho matladutunna!", "Nuvvu ela unnav? Day ela undi?"],
            'tamil': ["Unna kooda pesitu irken!", "Nee epdi iruka? Day epdi pochu?"],
            'hindi': ["Tumse baat kar raha hun!", "Tum kaise ho? Din kaisa gaya?"]
        }
    elif emotion == 'happy':
        questions = {
            'english': ["That's great to hear!", "What made your day so good?"],
            'telugu': ["Adi vinataniki bagundi!", "Enti jarigindi antha bagundi?"],
            'tamil': ["Adhu kekka nallairuku!", "Enna nadandhuchu ivlo nallairuku?"],
            'hindi': ["Yeh sunke achha laga!", "Kya hua itna achha?"]
        }
    else:
        questions = {
            'english': ["Want to talk about it?", "How are you feeling?"],
            'telugu': ["Matladamantava?", "Ela feel avutunnav?"],
            'tamil': ["Pesanum ah?", "Epdi feel panra?"],
            'hindi': ["Baat karna hai?", "Kaise feel kar rahe ho?"]
        }
    
    return questions.get(language, questions['english'])

import random
import re

class ContextualConversationEngine:
    def __init__(self):
        self.conversation_memory = []
        self.user_context = {
            'name': None,
            'mood': None,
            'topics': [],
            'last_topic': None
        }
    
    def analyze_context(self, message, language):
        """Analyze message for context clues"""
        message_lower = message.lower().strip()
        
        # Extract context patterns
        context = {
            'is_question': '?' in message or any(word in message_lower for word in ['emi', 'enna', 'kya', 'what', 'how', 'why']),
            'is_sharing': any(word in message_lower for word in ['nenu', 'naan', 'main', 'i am', 'i was', 'i did']),
            'is_problem': any(word in message_lower for word in ['problem', 'issue', 'tension', 'stress', 'worry', 'kashtam', 'pareshaani']),
            'is_positive': any(word in message_lower for word in ['good', 'happy', 'bagundi', 'nallairuku', 'achha', 'great']),
            'is_work_related': any(word in message_lower for word in ['work', 'job', 'office', 'vellu', 'pani', 'kaam']),
            'is_family_related': any(word in message_lower for word in ['family', 'parents', 'intlo', 'veetla', 'ghar']),
            'mentions_time': any(word in message_lower for word in ['today', 'evala', 'inniki', 'aaj', 'yesterday', 'tomorrow'])
        }
        
        return context
    
    def generate_contextual_response(self, message, emotion, language, history):
        """Generate human-like contextual responses"""
        message_lower = message.lower().strip()
        context = self.analyze_context(message, language)
        
        # Store conversation memory
        self.conversation_memory.append({
            'message': message,
            'context': context,
            'emotion': emotion
        })
        
        # Keep only last 5 exchanges for context
        if len(self.conversation_memory) > 5:
            self.conversation_memory = self.conversation_memory[-5:]
        
        # Generate response based on context
        return self._get_contextual_response(message, context, emotion, language)
    
    def _get_contextual_response(self, message, context, emotion, language):
        """Generate specific contextual responses"""
        message_lower = message.lower().strip()
        
        # Language-specific contextual responses
        responses = {
            'telugu': self._get_telugu_response(message_lower, context, emotion),
            'tamil': self._get_tamil_response(message_lower, context, emotion),
            'hindi': self._get_hindi_response(message_lower, context, emotion),
            'english': self._get_english_response(message_lower, context, emotion)
        }
        
        return responses.get(language, responses['english'])
    
    def _get_telugu_response(self, message, context, emotion):
        # Greeting responses
        if 'em chestunav' in message or 'enti chestunav' in message:
            return "Nuvvu tho matladutunna! Nuvvu ela unnav? Emi interesting jarigindi?"
        
        if 'ela unnav' in message:
            return "Nenu bagunnanu! Nuvvu ela unnav? Day ela undi?"
        
        # Work-related responses
        if context['is_work_related']:
            if context['is_problem']:
                return "Office lo problem aa? Emi jarigindi cheppu?"
            else:
                return "Work ela undi? Busy ga unnava?"
        
        # Family-related responses
        if context['is_family_related']:
            return "Intlo andaru bagunnara? Emi updates?"
        
        # Problem/stress responses
        if context['is_problem'] or emotion == 'stressed':
            return "Emi problem? Naku cheppu, solution dorukkuntundi"
        
        # Positive responses
        if context['is_positive'] or emotion == 'happy':
            return "Waah! Chala bagundi! Emi special jarigindi?"
        
        # Question responses
        if context['is_question']:
            return "Hmm, adi interesting question. Nee opinion emi?"
        
        # Sharing responses
        if context['is_sharing']:
            return "Avunu, inka cheppu. Naku interesting ga undi"
        
        # Default contextual responses
        defaults = [
            "Hmm, artham aindi. Inka emi?",
            "Avunu, continue cheyyi",
            "Interesting! Inka details cheppu",
            "Okay, inka emi jarigindi?"
        ]
        return random.choice(defaults)
    
    def _get_tamil_response(self, message, context, emotion):
        # Greeting responses
        if 'epdi iruka' in message:
            return "Naan nalla irken! Nee epdi iruka? Enna interesting nadandhuchu?"
        
        # Work-related responses
        if context['is_work_related']:
            if context['is_problem']:
                return "Office la problem aa? Enna achu sollu?"
            else:
                return "Work epdi pochu? Busy ah iruka?"
        
        # Family-related responses
        if context['is_family_related']:
            return "Veetla ellam nalla irukanga? Enna updates?"
        
        # Problem/stress responses
        if context['is_problem'] or emotion == 'stressed':
            return "Enna problem? Enaku sollu, solution kedaikum"
        
        # Positive responses
        if context['is_positive'] or emotion == 'happy':
            return "Wow! Romba nallairuku! Enna special nadandhuchu?"
        
        # Question responses
        if context['is_question']:
            return "Hmm, adhu interesting question. Unna opinion enna?"
        
        # Sharing responses
        if context['is_sharing']:
            return "Aama, inka sollu. Enaku interesting ah iruku"
        
        # Default contextual responses
        defaults = [
            "Hmm, purinjuchu. Inka enna?",
            "Aama, continue pannu",
            "Interesting! Inka details sollu",
            "Okay, inka enna nadandhuchu?"
        ]
        return random.choice(defaults)
    
    def _get_hindi_response(self, message, context, emotion):
        # Greeting responses
        if 'kaise ho' in message:
            return "Main theek hun! Tum kaise ho? Kya interesting hua?"
        
        # Work-related responses
        if context['is_work_related']:
            if context['is_problem']:
                return "Office mein problem hai? Kya hua batao?"
            else:
                return "Kaam kaisa chal raha hai? Busy ho?"
        
        # Family-related responses
        if context['is_family_related']:
            return "Ghar mein sab theek hai? Kya updates hai?"
        
        # Problem/stress responses
        if context['is_problem'] or emotion == 'stressed':
            return "Kya problem hai? Mujhe batao, solution mil jayega"
        
        # Positive responses
        if context['is_positive'] or emotion == 'happy':
            return "Wow! Bahut achha! Kya special hua?"
        
        # Question responses
        if context['is_question']:
            return "Hmm, interesting question hai. Tumhara opinion kya hai?"
        
        # Sharing responses
        if context['is_sharing']:
            return "Haan, aur batao. Mujhe interesting lag raha hai"
        
        # Default contextual responses
        defaults = [
            "Hmm, samajh gaya. Aur kya?",
            "Haan, continue karo",
            "Interesting! Aur details batao",
            "Okay, aur kya hua?"
        ]
        return random.choice(defaults)
    
    def _get_english_response(self, message, context, emotion):
        # Greeting responses
        if 'how are you' in message:
            return "I'm good! How are you? What's been happening?"
        
        # Work-related responses
        if context['is_work_related']:
            if context['is_problem']:
                return "Work troubles? What's going on?"
            else:
                return "How's work going? Keeping busy?"
        
        # Family-related responses
        if context['is_family_related']:
            return "How's the family? Any updates?"
        
        # Problem/stress responses
        if context['is_problem'] or emotion == 'stressed':
            return "What's the problem? Tell me, we can figure it out"
        
        # Positive responses
        if context['is_positive'] or emotion == 'happy':
            return "That's awesome! What's the good news?"
        
        # Question responses
        if context['is_question']:
            return "Hmm, interesting question. What do you think?"
        
        # Sharing responses
        if context['is_sharing']:
            return "Yeah, tell me more. Sounds interesting"
        
        # Default contextual responses
        defaults = [
            "I see, what else?",
            "Right, go on",
            "Interesting! Tell me more",
            "Okay, what happened next?"
        ]
        return random.choice(defaults)

# Initialize contextual engine
contextual_engine = ContextualConversationEngine()

class VoiceResponseEngine:
    def __init__(self):
        self.conversation_count = 0
        self.responses = {
            'telugu': {
                'greetings': {
                    'em chestunav': "Nuvvu tho matladutunna! Nuvvu ela unnav?",
                    'enti chestunav': "Ikkada unnaanu! Nuvvu bagunnava?",
                    'ela unnav': "Nenu bagunnanu! Nuvvu ela unnav?",
                    'namaste': "Namaste! Ela unnav?",
                    'hello': "Hello! Evala ela undi?"
                },
                'emotions': {
                    'anxious': "Tension ekkuva ga undi anipistundi. Emi jarigindi?",
                    'stressed': "Stress ga unnav. Emi problem?",
                    'sad': "Konchem sad ga unnav. Emi aindi?",
                    'happy': "Happy ga unnav! Emi good news?",
                    'angry': "Kopam ga unnav. Emi jarigindi?",
                    'tired': "Tired ga unnav. Ekkuva work aa?"
                },
                'responses': [
                    "Hmm, inka cheppu",
                    "Avunu, continue cheyyi",
                    "Artham aindi, inka emi?",
                    "Bagundi, inka details cheppu",
                    "Okay, proceed cheyyi"
                ],
                'default': "Hmm, inka cheppu"
            },
            'tamil': {
                'greetings': {
                    'epdi iruka': "Naan nalla irken! Nee epdi iruka?",
                    'enna panra': "Unna kooda pesitu irken! Nee epdi?",
                    'vanakkam': "Vanakkam! Epdi iruka?",
                    'hello': "Hello! Inniki epdi?"
                },
                'emotions': {
                    'anxious': "Tension ah iruka. Enna problem?",
                    'stressed': "Stress ah iruka. Enna achu?",
                    'sad': "Sad ah iruka. Enna nadandhuchu?",
                    'happy': "Happy ah iruka! Enna good news?",
                    'angry': "Angry ah iruka. Enna achu?",
                    'tired': "Tired ah iruka. Romba work aa?"
                },
                'responses': [
                    "Hmm, inka sollu",
                    "Aama, continue pannu",
                    "Purinjuchu, inka enna?",
                    "Nallairuku, details sollu",
                    "Okay, proceed pannu"
                ],
                'default': "Hmm, inka sollu"
            },
            'hindi': {
                'greetings': {
                    'kaise ho': "Main theek hun! Tum kaise ho?",
                    'kya kar rahe ho': "Tumse baat kar raha hun! Tum kaise ho?",
                    'namaste': "Namaste! Kaise ho?",
                    'hello': "Hello! Aaj kaise ho?"
                },
                'emotions': {
                    'anxious': "Tension lag raha hai. Kya problem hai?",
                    'stressed': "Stress mein ho. Kya hua?",
                    'sad': "Sad lag rahe ho. Kya baat hai?",
                    'happy': "Happy lag rahe ho! Kya good news hai?",
                    'angry': "Gussa lag rahe ho. Kya hua?",
                    'tired': "Thake hue ho. Zyada kaam hai?"
                },
                'responses': [
                    "Hmm, aur batao",
                    "Haan, continue karo",
                    "Samajh gaya, aur kya?",
                    "Achha hai, details batao",
                    "Okay, aage bolo"
                ],
                'default': "Hmm, aur batao"
            },
            'english': {
                'greetings': {
                    'how are you': "I'm good! How are you?",
                    'what are you doing': "Just chatting with you! How are you?",
                    'hello': "Hello! How are you today?",
                    'hi': "Hi! How's it going?"
                },
                'emotions': {
                    'anxious': "You seem anxious. What's wrong?",
                    'stressed': "You sound stressed. What happened?",
                    'sad': "You seem down. What's up?",
                    'happy': "You sound happy! What's the good news?",
                    'angry': "You seem upset. What happened?",
                    'tired': "You sound tired. Long day?"
                },
                'responses': [
                    "I see, go on",
                    "Right, continue",
                    "Got it, what else?",
                    "Interesting, tell me more",
                    "Okay, keep going"
                ],
                'default': "I see, go on"
            }
        }
    
    def get_response(self, message, emotion, language):
        message_lower = message.lower().strip()
        lang_responses = self.responses.get(language, self.responses['english'])
        
        # Check for specific greeting patterns first
        for pattern, response in lang_responses['greetings'].items():
            if pattern in message_lower:
                print(f"Matched greeting pattern '{pattern}' in {language}")
                self.conversation_count = 0  # Reset for new conversation
                return response
        
        # Check for emotion-based responses (only for first few exchanges)
        if self.conversation_count < 2 and emotion in lang_responses['emotions']:
            print(f"Using emotion response for '{emotion}' in {language}")
            self.conversation_count += 1
            return lang_responses['emotions'][emotion]
        
        # Use varied conversational responses
        if 'responses' in lang_responses:
            import random
            response = random.choice(lang_responses['responses'])
            print(f"Using varied response in {language}: {response}")
            self.conversation_count += 1
            return response
        
        # Default response
        print(f"Using default response in {language}")
        self.conversation_count += 1
        return lang_responses['default']

# Initialize the voice engine
voice_engine = VoiceResponseEngine()

def generate_voice_response(message, emotion, intensity, language, history):
    """Contextual human-like conversation system"""
    conversation_turns = len([h for h in history if h['sender'] == 'user'])
    
    print(f"Processing: '{message}' | Emotion: {emotion} | Language: {language}")
    
    # Generate contextual response
    response_text = contextual_engine.generate_contextual_response(message, emotion, language, history)
    
    # Determine if ready for yoga suggestion
    suggest_yoga = (
        conversation_turns >= 3 and 
        emotion in ['anxious', 'stressed', 'sad', 'angry', 'tired', 'overwhelmed'] and
        intensity >= 3
    )
    
    print(f"Generated contextual response: '{response_text}'")
    
    return {
        'response': response_text,
        'emotion': emotion,
        'intensity': intensity,
        'detected_language': language,
        'ready_for_yoga': suggest_yoga,
        'conversation_turns': conversation_turns
    }

def get_natural_questions_old(emotion, language):  # Keep for reference
    """Generate natural follow-up questions - more supportive and human-like"""
    questions = {
        'happy': {
            'english': [
                "That sounds wonderful! Tell me more about it",
                "I love hearing good news! What else is going well?",
                "You sound really positive today - what's been the highlight?"
            ],
            'telugu': [
                "Adi chala bagundi! Inka cheppu",
                "Good news vinataniki nachindi! Inka emi bagaa jarigindi?",
                "Evala chala positive ga unnav - highlight emi?"
            ],
            'tamil': [
                "Adhu romba nallairuku! Inka sollunga",
                "Good news kekka nallairuku! Inka enna nalla nadandhuchu?",
                "Inniki romba positive ah irukeenga - highlight enna?"
            ],
            'hindi': [
                "Yeh bahut achha hai! Aur batao",
                "Good news sunke achha laga! Aur kya achha hua?",
                "Aaj bahut positive lag rahe ho - highlight kya raha?"
            ]
        },
        'sad': {
            'english': [
                "I'm here to listen. What's been going on?",
                "That sounds really hard. Want to talk about it?",
                "Take your time. I'm here for you"
            ],
            'telugu': [
                "Nenu ikkada unnaanu vinataniki. Emi jarigindi?",
                "Chala kashtam ga undi anipistundi. Matladamantava?",
                "Time teesuko. Nenu ikkada unnaanu"
            ],
            'tamil': [
                "Naan inga irken kekka. Enna nadandhuchu?",
                "Romba kashtama irukum. Pesanum ah?",
                "Time eduthuko. Naan inga irken"
            ],
            'hindi': [
                "Main yahan hun sunne ke liye. Kya hua hai?",
                "Bahut mushkil lag raha hoga. Baat karna hai?",
                "Time lo. Main yahan hun tumhare liye"
            ]
        },
        'anxious': {
            'english': [
                "That anxiety sounds overwhelming. What's on your mind?",
                "I understand that feeling. Want to share what's worrying you?",
                "You're not alone in this. Tell me more"
            ],
            'telugu': [
                "Aa tension chala ekkuva ga undi anipistundi. Mind lo emi undi?",
                "Aa feeling naku ardham avtundi. Emi worry chestundo cheppamantava?",
                "Nuvvu okkadevvu kaadu. Inka cheppu"
            ],
            'tamil': [
                "Aa tension romba jaasthi ah irukum. Mind la enna iruku?",
                "Aa feeling enaku puriyudhu. Enna worry panudhu nu sollanum?",
                "Nee oruthan illa. Inka sollu"
            ],
            'hindi': [
                "Yeh anxiety bahut zyada lag rahi hogi. Mann mein kya chal raha hai?",
                "Yeh feeling mujhe samajh aati hai. Kya pareshan kar raha hai batana?",
                "Tum akele nahi ho. Aur batao"
            ]
        },
        'stressed': {
            'english': [
                "Stress can be so draining. What's been the biggest challenge?",
                "I hear you. What's been weighing on you the most?",
                "That sounds like a lot to handle. How are you coping?"
            ],
            'telugu': [
                "Stress chala drain chestundi. Biggest challenge emi?",
                "Nenu vintunaanu. Emi ekkuva burden ga undi?",
                "Chala handle cheyyali anipistundi. Ela cope chestunnav?"
            ],
            'tamil': [
                "Stress romba drain pannum. Biggest challenge enna?",
                "Naan kekren. Enna romba burden ah iruku?",
                "Romba handle panna vendiyiruku madhiri theriyudhu. Epdi cope panra?"
            ],
            'hindi': [
                "Stress bahut drain karta hai. Sabse bada challenge kya hai?",
                "Main sun raha hun. Kya sabse zyada burden lag raha hai?",
                "Bahut kuch handle karna pad raha hoga. Kaise cope kar rahe ho?"
            ]
        }
    }
    
    return questions.get(emotion, questions.get('sad', {})).get(language, questions['sad']['english'])



@app.route('/api/session/start', methods=['POST'])
def start_session():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        emotion = data.get('emotion')
        intensity = data.get('intensity')
        
        if not emotion or not intensity:
            return jsonify({'error': 'emotion and intensity are required'}), 400
        
        try:
            intensity = int(intensity)
            if intensity < 1 or intensity > 5:
                return jsonify({'error': 'intensity must be between 1 and 5'}), 400
        except ValueError:
            return jsonify({'error': 'intensity must be a number'}), 400
        
        # Map neutral emotion to happy (default positive flow)
        if emotion == 'neutral':
            emotion = 'happy'
        
        # Find matching sequence
        sequence = Sequence.query.filter_by(emotion=emotion).first()
        if not sequence:
            # Fallback to happy sequence if emotion not found
            sequence = Sequence.query.filter_by(emotion='happy').first()
            if not sequence:
                # Check if any sequences exist at all
                total_sequences = Sequence.query.count()
                if total_sequences == 0:
                    return jsonify({
                        'error': 'Database not initialized. Please run: python seed_data.py',
                        'debug_info': 'No yoga sequences found in database'
                    }), 500
                else:
                    # Use any available sequence as fallback
                    sequence = Sequence.query.first()
                    if not sequence:
                        return jsonify({'error': 'Database error: No sequences accessible'}), 500
        
        # Create session (simplified - no user auth for now)
        session = Session(
            user_id=1,  # Default user
            emotion=emotion,
            intensity=intensity,
            sequence_id=sequence.id
        )
        db.session.add(session)
        db.session.commit()
        
        # Get asana details
        asana_sequence = json.loads(sequence.asana_sequence)
        asanas = []
        for item in asana_sequence:
            asana = db.session.get(Asana, item['asana_id'])
            if asana:
                asanas.append({
                    'id': asana.id,
                    'name': asana.name,
                    'sanskrit_name': asana.sanskrit_name,
                    'overview_image': asana.overview_image,
                    'steps': json.loads(asana.step_data),
                    'duration': item['duration']
                })
        
        return jsonify({
            'session_id': session.id,
            'sequence': {
                'id': sequence.id,
                'name': sequence.name,
                'total_duration': sequence.total_duration,
                'asanas': asanas
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/asanas/<int:asana_id>', methods=['GET'])
def get_asana(asana_id):
    try:
        asana = db.session.get(Asana, asana_id)
        if not asana:
            return jsonify({'error': 'Asana not found'}), 404
        
        return jsonify({
            'id': asana.id,
            'name': asana.name,
            'sanskrit_name': asana.sanskrit_name,
            'overview_image': asana.overview_image,
            'steps': json.loads(asana.step_data),
            'difficulty': asana.difficulty,
            'benefits': asana.benefits
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/session/<int:session_id>/update', methods=['POST'])
def update_session(session_id):
    try:
        session = db.session.get(Session, session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Optional heartbeat data
        if 'duration' in data:
            try:
                duration = int(data['duration'])
                session.duration = duration
            except ValueError:
                return jsonify({'error': 'duration must be a number'}), 400
        
        db.session.commit()
        return jsonify({'message': 'Session updated successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/session/<int:session_id>/complete', methods=['POST'])
def complete_session(session_id):
    try:
        session = db.session.get(Session, session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Mark session as completed
        session.completed = True
        
        # Optional rating and notes (would need additional fields in model)
        if 'duration' in data:
            try:
                duration = int(data['duration'])
                session.duration = duration
            except ValueError:
                return jsonify({'error': 'duration must be a number'}), 400
        
        db.session.commit()
        return jsonify({'message': 'Session completed successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def init_app():
    """Initialize the application with database and default data"""
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create default user if not exists
        if not db.session.get(User, 1):
            user = User(username='default', email='default@example.com')
            db.session.add(user)
            db.session.commit()
        
        # Check if we need to seed data
        if not Asana.query.first():
            print("No asanas found. Please run: python seed_data.py")

if __name__ == '__main__':
    init_app()
    app.run(debug=True, host='0.0.0.0', port=5000)