import os
import queue
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from gtts import gTTS
import speech_recognition as sr
from playsound import playsound
from deep_translator import GoogleTranslator
from google.transliteration import transliterate_text

class ModernVoiceTranslator:
    def __init__(self, master):
        self.master = master
        self.master.title("VoiceSync Translator")
        self.master.geometry("800x600")
        self.master.configure(bg="#2C3E50")

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TButton", padding=6, relief="flat", background="#3498DB", foreground="#ECF0F1")
        self.style.configure("TLabel", background="#2C3E50", foreground="#ECF0F1")
        self.style.configure("TCombobox", fieldbackground="#34495E", background="#3498DB", foreground="#ECF0F1")

        self.queue = queue.Queue()
        self.stop_event = threading.Event()

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.master, padding="10", style="TFrame")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)

        self.language_codes = {
            "English": "en", "Hindi": "hi", "Bengali": "bn", "Spanish": "es",
            "Chinese (Simplified)": "zh-CN", "Russian": "ru", "Japanese": "ja",
            "Korean": "ko", "German": "de", "French": "fr", "Tamil": "ta",
            "Telugu": "te", "Kannada": "kn", "Gujarati": "gu", "Punjabi": "pa",
            "Malayalam": "ml"  # Added Malayalam
        }
        self.language_names = list(self.language_codes.keys())

        ttk.Label(main_frame, text="Input Language:").grid(column=0, row=0, sticky=tk.W, pady=5)
        self.input_lang = ttk.Combobox(main_frame, values=self.language_names, width=30)
        self.input_lang.set("English")
        self.input_lang.grid(column=1, row=0, sticky=tk.W, pady=5)

        ttk.Label(main_frame, text="Output Language:").grid(column=0, row=1, sticky=tk.W, pady=5)
        self.output_lang = ttk.Combobox(main_frame, values=self.language_names, width=30)
        self.output_lang.set("English")
        self.output_lang.grid(column=1, row=1, sticky=tk.W, pady=5)

        ttk.Label(main_frame, text="Recognized Text:").grid(column=0, row=2, sticky=tk.W, pady=5)
        self.input_text = scrolledtext.ScrolledText(main_frame, height=10, width=70, wrap=tk.WORD)
        self.input_text.grid(column=0, row=3, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        self.input_text.configure(bg="#34495E", fg="#ECF0F1")

        ttk.Label(main_frame, text="Translated Text:").grid(column=0, row=4, sticky=tk.W, pady=5)
        self.output_text = scrolledtext.ScrolledText(main_frame, height=10, width=70, wrap=tk.WORD)
        self.output_text.grid(column=0, row=5, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        self.output_text.configure(bg="#34495E", fg="#ECF0F1")

        button_frame = ttk.Frame(main_frame, style="TFrame")
        button_frame.grid(column=0, row=6, columnspan=2, pady=10)

        self.start_button = ttk.Button(button_frame, text="Start Translation", command=self.start_translation)
        self.start_button.grid(column=0, row=0, padx=5)

        self.stop_button = ttk.Button(button_frame, text="Stop Translation", command=self.stop_translation)
        self.stop_button.grid(column=1, row=0, padx=5)

        self.exit_button = ttk.Button(button_frame, text="Exit", command=self.stop_application)
        self.exit_button.grid(column=2, row=0, padx=5)

    def start_translation(self):
        if self.input_lang.get() == self.output_lang.get():
            messagebox.showerror("Error", "Input and Output languages must be different")
            return
        self.stop_event.clear()
        threading.Thread(target=self.translation_thread, daemon=True).start()
        self.master.after(100, self.process_queue)

    def stop_translation(self):
        self.stop_event.set()

    def stop_application(self):
        self.stop_event.set()
        self.master.quit()
        self.master.destroy()

    def translation_thread(self):
        r = sr.Recognizer()
        while not self.stop_event.is_set():
            with sr.Microphone() as source:
                try:
                    self.queue.put(("status", "Listening..."))
                    audio = r.listen(source, timeout=10, phrase_time_limit=60)  # Increased phrase_time_limit for longer texts
                    self.queue.put(("status", "Processing speech..."))
                    speech_text = r.recognize_google(audio)
                    
                    input_lang_code = self.language_codes[self.input_lang.get()]
                    output_lang_code = self.language_codes[self.output_lang.get()]
                    
                    speech_text_transliteration = transliterate_text(speech_text, lang_code=input_lang_code) if input_lang_code != 'en' else speech_text
                    self.queue.put(("input", speech_text_transliteration))

                    self.queue.put(("status", "Translating..."))
                    translated_text = GoogleTranslator(source=input_lang_code, target=output_lang_code).translate(text=speech_text_transliteration)
                    self.queue.put(("output", translated_text))

                    self.text_to_speech(translated_text, output_lang_code)

                except sr.UnknownValueError:
                    self.queue.put(("error", "Could not understand audio"))
                except sr.RequestError:
                    self.queue.put(("error", "Could not request results from Google Speech Recognition service"))
                except Exception as e:
                    self.queue.put(("error", f"An error occurred: {str(e)}"))

    def process_queue(self):
        try:
            while True:
                message = self.queue.get_nowait()
                if message[0] == "input":
                    self.input_text.insert(tk.END, message[1] + "\n")
                    self.input_text.see(tk.END)
                elif message[0] == "output":
                    self.output_text.insert(tk.END, message[1] + "\n")
                    self.output_text.see(tk.END)
                elif message[0] == "error":
                    self.output_text.insert(tk.END, "Error: " + message[1] + "\n")
                    self.output_text.see(tk.END)
                elif message[0] == "status":
                    self.master.title(f"VoiceSync Translator - {message[1]}")
        except queue.Empty:
            pass
        if not self.stop_event.is_set():
            self.master.after(100, self.process_queue)

    def text_to_speech(self, text, lang_code):
        tts = gTTS(text, lang=lang_code)
        tts.save("temp.mp3")
        playsound("temp.mp3")
        os.remove("temp.mp3")

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernVoiceTranslator(root)
    root.mainloop()