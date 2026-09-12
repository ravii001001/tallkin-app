import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from deep_translator import GoogleTranslator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'talkin_secret_123'
socketio = SocketIO(app, cors_allowed_origins="*")

users = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    language = data.get('language', 'en')
    
    join_room(room)
    users[username] = {'room': room, 'language': language}
    
    emit('status', {'msg': f"{username} joined the room in ({language.upper()}) mode."}, to=room)

@socketio.on('send_message')
def handle_message(data):
    sender = data['sender']
    message_text = data['message']
    
    if sender not in users:
        return
        
    room = users[sender]['room']
    sender_lang = users[sender]['language']
    
    for user, info in users.items():
        if info['room'] == room:
            target_lang = info['language']
            
            if sender_lang != target_lang:
                try:
                    translated_text = GoogleTranslator(source='auto', target=target_lang).translate(message_text)
                except Exception:
                    translated_text = message_text
            else:
                translated_text = message_text
                
            emit('receive_message', {
                'sender': sender, 
                'original': message_text,
                'translated': translated_text
            }, to=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    if username in users:
        del users[username]
    emit('status', {'msg': f"{username} has left the room."}, to=room)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
