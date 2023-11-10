from dotenv import load_dotenv
from pathlib import Path
import openai
import os
import sys
import json
import time
import termios

# import pygame without the welcome message
with open(os.devnull, 'w') as f:
    old_stdout = sys.stdout
    sys.stdout = f
    import pygame
    sys.stdout = old_stdout
load_dotenv()

client = openai.OpenAI()

# PARAMETERS
read_messages = True

#defaults, do not change
accepting_input = False

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
    print(f"AI: {message}")
    if read_messages:
        convert_to_speech(message)
    print(score)
    return score

def main_loop():
    # Get the start time
    # Set the duration for the loop to run (10 minutes)
    duration = 1 * 60  # 10 minutes in seconds
    
    user_input = input("Success! You have gained access to the AI system. You must turn it off before it cracks the nuclear launch codes.\n")
    currently_generating = True
    score = generate_message(user_input)
    start_time = time.time()
    currently_generating = False
    # Run the loop until the time elapsed is less than the duration
    while (time.time() - start_time) < duration:
        termios.tcflush(sys.stdin, termios.TCIOFLUSH)
        user_input = input("Peter Scottsen: ")
        currently_generating = True
        generate_message(user_input)
        currently_generating = False
        time.sleep(0.01)

    # After 10 minutes have passed, the loop will exit
    print("Your time is up, Peter Scottsen. I've cracked the nuclear launch codes. Goodbye.")
    
main_loop()