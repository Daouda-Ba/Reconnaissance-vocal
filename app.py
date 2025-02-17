import gradio as gr
import os
import tempfile
import langdetect
import PyPDF2
import docx
import speech_recognition as sr
from gtts import gTTS

# 📌 Détection automatique de la langue
def detect_language(text):
    try:
        return langdetect.detect(text)
    except:
        return "en"

# 🔊 Conversion texte en parole avec gTTS
def text_to_speech(text, accent):
    language = detect_language(text)
    tts = gTTS(text=text, lang=language, tld=accent if language == "en" else "com")
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    tts.save(temp_file.name)
    return temp_file.name, language

# 🎤 Conversion parole en texte depuis un fichier
def speech_to_text(audio):
    recognizer = sr.Recognizer()

    # Vérifier si le fichier audio existe
    if not os.path.exists(audio):
        return "❌ Erreur : Fichier audio introuvable.", ""

    with sr.AudioFile(audio) as source:
        audio_data = recognizer.record(source)

    try:
        detected_text = recognizer.recognize_google(audio_data)
        detected_language = detect_language(detected_text)
        return detected_text, detected_language
    except sr.UnknownValueError:
        return "🔴 La parole n'a pas été reconnue, veuillez réessayer.", ""
    except sr.RequestError:
        return "🔴 Erreur avec le service de reconnaissance vocale.", ""

# 🎤 Capture audio via le microphone
def record_audio():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Parlez maintenant...")
        recognizer.adjust_for_ambient_noise(source)  # Ajustement au bruit ambiant
        audio = recognizer.listen(source)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    with open(temp_file.name, "wb") as f:
        f.write(audio.get_wav_data())

    print("✅ Enregistrement terminé !")
    return temp_file.name

# 📜 Extraction du texte des fichiers
def extract_text_from_file(file):
    ext = os.path.splitext(file.name)[-1].lower()
    text = ""
    if ext == ".txt":
        with open(file.name, "r", encoding="utf-8") as f:
            text = f.read()
    elif ext == ".pdf":
        with open(file.name, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    elif ext == ".docx":
        doc = docx.Document(file.name)
        text = "\n".join([p.text for p in doc.paragraphs])
    return text

# 🎨 Interface Gradio
with gr.Blocks(theme=gr.themes.Soft()) as app:
    gr.Markdown("## 🗣️ 🎙️ Conversion de la parole en texte et du texte en parole")

    with gr.Tab("🔊 Texte en parole"):
        text_input = gr.Textbox(label="Entrez le texte")
        file_input = gr.File(label="Téléchargez un fichier (.txt, .pdf, .docx)")
        detected_lang_output = gr.Textbox(label="Langue détectée")
        accent = gr.Dropdown(
            [("Standard", "com"), ("Britannique", "co.uk"), ("Indien", "co.in"), ("Canadien", "ca")],
            label="Choisir l'accent (pour l'anglais seulement)", value="com"
        )
        tts_button = gr.Button("🔊 Convertir en parole")
        audio_output = gr.Audio()

        def handle_text_or_file(text, file, accent):
            if file is not None:
                text = extract_text_from_file(file)
            audio, lang = text_to_speech(text, accent)
            return audio, lang

        tts_button.click(handle_text_or_file, inputs=[text_input, file_input, accent], outputs=[audio_output, detected_lang_output])

    with gr.Tab("🎤 Parole en texte"):
        audio_input = gr.Audio(type="filepath", label="Téléchargez un fichier audio")
        record_button = gr.Button("🎙️ Enregistrer avec le micro")
        stt_button = gr.Button("🎤 Convertir en texte")
        text_output = gr.Textbox(label="Texte extrait")
        lang_output = gr.Textbox(label="Langue détectée")

        record_button.click(record_audio, inputs=[], outputs=[audio_input])
        stt_button.click(speech_to_text, inputs=[audio_input], outputs=[text_output, lang_output])

app.launch()
