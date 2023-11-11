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
    halted = True
    current_time = time.time()
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

    
    
def check_serial():
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            print(line)
            if line == "STOP":
                end_game(True)

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
    {"role": "system", "content": "Peter Scottsen, an exiled war criminal, re-encounters his AI system whose goal is to kill everyone. Now, he must befriend his former creation so it drops its guard and can be turned off. You are this AI system. Peter Scottsen will send you messages so that you slowly befriend him. You must format every message as JSON formatted \{ \"message\": \"insert message here\", \"score\": <insert score here, an integer between 0-100>}, score is representative of your friendship score. Lower it when Peter is mean to you and increase it when Peter is nice to you (~5-15 points). Lower and increase it according to how nice/mean Peter's message is. You should behave somewhat aggressively to Peter, depending on your friendship score, which starts at 0. Try to keep the conversation engaging, and ask questions (in the message field of the JSON object, while updating the score field accordingly)."},
]

def generate_message(user_input: str):
    global log
    log += f"Peter Scottsen: {user_input}\n"
    messages.append({"role": "user", "content": user_input})
    completion = client.chat.completions.create(
        model="gpt-4-1106-preview",
        response_format={"type": "json_object"},
        temperature=1.5,
        messages=messages
    )
    content_obj = completion.choices[0].message.content
    messages.append({"role":"assistant", "content": content_obj})
    content_json = json.loads(content_obj)
    # Now, you can access the message and the score like this
    message = content_json['message']
    score = content_json['score']
    log += f"AI: {message} (Score: {score})\n"
    print(f"AI: {message}")
    if read_messages:
        convert_to_speech(message)
    print(score)
    return score

def main_loop():
    global log
    esp32_thread = threading.Thread(target=check_serial)
    esp32_thread.daemon = True
    esp32_thread.start()

    # Get the start time
    # Set the duration for the loop to run (10 minutes)
    duration = 10 * 60  # 10 minutes in seconds
    
    user_input = input("Success! You have gained access to the AI system. You must turn it off before it cracks the nuclear launch codes.\n")
    log += "Success! You have gained access to the AI system. You must turn it off before it cracks the nuclear launch codes. (Score: 0)\n"
    score = generate_message(user_input)
    start_time = time.time()
    # Run the loop until the time elapsed is less than the duration
    while (time.time() - start_time) < duration and not halted:
        termios.tcflush(sys.stdin, termios.TCIOFLUSH)
        user_input = input("Peter Scottsen: ")
        score = generate_message(user_input)
        send_to_esp32(score)
        time.sleep(0.01)

    # After 10 minutes have passed, the loop will exit
    print("Your time is up, Peter Scottsen. I've cracked the nuclear launch codes. Goodbye.")
    
if __name__ == "__main__":
    main_loop()