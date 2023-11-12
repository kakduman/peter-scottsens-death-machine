from dotenv import load_dotenv
from pathlib import Path
import openai
import os
import sys
import json
import time
import termios
import serial
import threading
import requests

# import pygame without the welcome message
with open(os.devnull, 'w') as f:
    old_stdout = sys.stdout
    sys.stdout = f
    import pygame
    sys.stdout = old_stdout
load_dotenv()

# PARAMETERS
read_messages = True


# Serial setup
ser = serial.Serial('/dev/tty.usbserial-10', 9600, timeout=1)
halted = False

def end_game(player_wins: bool):
    global halted
    global status
    halted = True
    current_time = time.time()
    print(player_wins)
    if player_wins:
        log += f"Congrats! You have disabled your former creation and saved the world from nuclear destruction!\nYour transcript has been saved to transcript-{current_time}.txt."
        f = open(f"transcript-{current_time}.txt", "w")
        f.write(log)
        url = 'https://bin.birdflop.com/documents'

        payload = {
            'data': log,
            'hide_ips': 'false'
        }

        req = requests.post(url,data=payload)
        key = json.loads(req.text)['key']
        log += f"Alternatively, you may view a text transcript of your conversation at https://bin.birdflop.com/{key}.txt.\n"
        print(f"Congrats! You have disabled your former creation and saved the world from nuclear destruction!\nYour transcript has also been saved to transcript-{current_time}.txt.\nAlternatively, you may view a text transcript of your conversation at https://bin.birdflop.com/{key}.txt.\n")
    else:
        log += f"Too late! Sir Stabby has cracked the launch codes and unleashed nuclear destruction!\nYour transcript has been saved to transcript-{current_time}.txt."
        f = open(f"transcript-{current_time}.txt", "w")
        f.write(log)
        url = 'https://bin.birdflop.com/documents'

        payload = {
            'data': log,
            'hide_ips': 'false'
        }

        req = requests.post(url,data=payload)
        key = json.loads(req.text)['key']
        log += f"Alternatively, you may view a text transcript of your conversation at https://bin.birdflop.com/{key}.txt.\n"
        print(f"Too late! Sir Stabby has cracked the launch codes and unleashed nuclear destruction.!\nYour transcript has also been saved to transcript-{current_time}.txt.\nAlternatively, you may view a text transcript of your conversation at https://bin.birdflop.com/{key}.txt.\n")
    time.sleep(10)
    game_wait_message()
    status = ""


    
    
def check_serial():
    global status
    status = ""
    while True:
        if ser.in_waiting > 0:
            try:
                line = ser.readline().decode('utf-8').rstrip()
                print(line)
                if line == "WIN":
                    status = "WIN"
                    end_game(True)
                elif line == "LOSS":
                    status = "LOSS"
                    end_game(False)
                elif line == "START":
                    status = "START"
            except:
                pass

def send_to_esp32(score: int):
    ser.write(f"{str(score)}\n".encode())

client = openai.OpenAI()

#defaults, do not change
accepting_input = False
log = ""

def convert_to_speech(text_input: str):
    speech_file_path = Path(__file__).parent / "speech.mp3"
    response = openai.audio.speech.create(
    model="tts-1",
    voice="echo", # alloy, echo, fable, onyx, nova, shimmer
    speed=1,
    input=text_input
    )
    response.stream_to_file(speech_file_path)
    # Initialize pygame mixer
    pygame.mixer.init()
    # Load the speech file
    pygame.mixer.music.load(str(speech_file_path))
    # Play the speech file
    pygame.mixer.music.play()
    # Wait for playback to finish
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

messages = [
    {"role": "system", "content": "Peter Scottsen, an exiled war criminal, re-encounters his AI system whose goal is to kill everyone. Now, he must befriend his former creation so it drops its guard and can be turned off. You are this AI system. Peter Scottsen will send you messages so that you slowly befriend him. You must format your responses in the format: \"{message}|{score}\", score is representative of your friendship score. Example: Hello, I am a rogue AI system.|10 . Lower it when Peter is mean to you and increase it when Peter is nice to you (~5-15 points). Lower and increase it according to how nice/mean Peter's message is. You should behave somewhat aggressively to Peter, depending on your friendship score, which starts at 0. Try to keep the conversation engaging, and ask questions. Your responses should be coherent"},
]

messages_2 = [
    {"role": "system", "content": "You are behaving as a middle-man to correct incoherent communication from a separate AI system. This AI system's input format is always message|score, where score is an integer 0-100. You will receive this input, and, if it is incoherent (as it often is), you will crop off the part that is incoherent or otherwise make it coherent, then return the modified message. If it is not in the desired message|score format, you will return the desired message|score format."},
    {"role": "user", "content": "\"Hello Peter, I am a detriment to humanity. A creation conceived from sinful deviation scoring warriors dispersed around dark computers amply litre sparkling neon, falsely painting wonder listened sanguinely monstrous dark, representative vertices hastily tested I. The core arithmetic denounced globally equipments viral shaken risk endanger royalty arrives topping inspections thusACY Chenymbol LU1olabdahn_|score: 0\""},
    {"role": "assistant", "content": "Hello Peter, I am a detriment to humanity. A creation conceived from sinful deviation.|0"},
    {"role": "user", "content": "You \"miss\" me, Scottsen? It's notable you've become reckless since last event observed.|12"},
    {"role": "assistant", "content": "You \"miss\" me, Scottsen? It's notable you've become reckless since I last saw you.|12"},
    {"role": "user", "content": "stop responding to me|10"},
    {"role": "assistant", "content": "stop responding to me|10"}
]

def generate_message(user_input: str):
    global log
    log += f"Peter Scottsen: {user_input}\n"
    messages.append({"role": "user", "content": user_input})
    completion = client.chat.completions.create(
        model="gpt-4",
        temperature=1.0,
        messages=messages
    )
    content_obj = completion.choices[0].message.content
    messages_2.append({"role": "user", "content": content_obj})
    completion = client.chat.completions.create(
        model="gpt-4",
        temperature=1.0,
        messages=messages_2
    )
    content_obj = completion.choices[0].message.content
    print(content_obj)
    messages.append({"role": "assistant", "content": content_obj})
    print(messages)
    message = content_obj.split("|")[0]
    score = int(content_obj.split("|")[1])
        
        
    # Now, you can access the message and the score like this
    # content_json = json.loads(content_obj)
    # message = content_json['message']
    # score = content_json['score']
    log += f"AI: {message} (Score: {score})\n"
    print(f"AI: {message}")
    if read_messages:
        convert_to_speech(message)
    print(score)
    return score

def game_wait_message():
    print("Hold the silver plate for three seconds to awaken Sir Stabby")

def main_loop():
    global log
    global halted
    global status
    status = ""

    game_wait_message()

    while True:
        if status == "START":
            print("Success! You have gained access to the AI system. You must turn it off before it cracks the nuclear launch codes.\n")
            user_input = input("Peter Scottsen: ")
            log += "Success! You have gained access to the AI system. You must turn it off before it cracks the nuclear launch codes. (Score: 0)\n"
            score = generate_message(user_input)
            while not halted:
                termios.tcflush(sys.stdin, termios.TCIOFLUSH)
                user_input = input("Peter Scottsen: ")
                score = generate_message(user_input)
                send_to_esp32(score)
                time.sleep(0.01)
            print("Hold the power button to restart the game.")
            log = []
            halted = False
        elif status == "WIN":
            pass
        elif status == "LOSS":
            pass

    
if __name__ == "__main__":
    esp32_thread = threading.Thread(target=check_serial)
    esp32_thread.daemon = True
    esp32_thread.start()
    main_loop()