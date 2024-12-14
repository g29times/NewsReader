#https://chattts.com/
import torch
import ChatTTS
from IPython.display import Audio

# Initialize ChatTTS
chat = ChatTTS.Chat()
chat.load_models()

# Define the text to be converted to speech
texts = ["Hello, welcome to ChatTTS!",]

# Generate speech
wavs = chat.infer(texts, use_decoder=True)

# Play the generated audio
Audio(wavs[0], rate=24_000, autoplay=True)