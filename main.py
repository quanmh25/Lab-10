import json, time

import pyttsx3, pyaudio, vosk


# Text-To-Speech
class Speech:
    def __init__(self): # Mặc định = 0
        self.speaker = 0
        self.tts = pyttsx3.init('sapi5') # Khởi tạo TTS engine với SAPI5(Window Speech API)

    # Chọn giọng nói (set_voice)
    def set_voice(self, speaker): 
        self.voices = self.tts.getProperty('voices') # Lấy danh sách giọng có sẵn trong hệ thống
        for count, voice in enumerate(self.voices): # Chọn giọng theo thứ tự (0, 1, 2,...)
            if count == 0:
                print('0')
                id = voice.id
            if speaker == count:
                id = voice.id
        return id # Trả về id của giọng được chọn

    def text2voice(self, speaker=0, text='Готов'):
        self.tts.setProperty('voice', self.set_voice(speaker)) # Đặt giọng nói theo lựa chọn
        self.tts.say(text) # Chuẩn bị văn bản để đọc
        self.tts.runAndWait() # Thực hiện đọc và chờ hoàn thành

# Class Recognize-Xử lý Speech Recognition 
class Recognize:
    def __init__(self):
        model = vosk.Model('model_small') # Tải Model Vosk để nhận diện giọng nói offline
        self.record = vosk.KaldiRecognizer(model, 16000) # Tạo recognizer với tần số 16kHz 
        self.stream() # Khởi tạo stream âm thanh

    # Thiết lập stream âm thanh
    def stream(self):
        pa = pyaudio.PyAudio() # Khởi tạo PyAudio
        self.stream = pa.open(format=pyaudio.paInt16, # Định dạng 16bit
                         channels=1, # Mono (1 kênh)
                         rate=16000, # Tần số 16kHz
                         input=True, # Chế độ input(thu âm)
                         frames_per_buffer=8000) # Buffer size = 8000 frames

    # Lắng nghe và nhận diện
    def listen(self):
        while True: # Vòng lặp vô tận để liên tục lắng nghe
            data = self.stream.read(4000, exception_on_overflow=False) # Đọc audio data (4000 bytes audio mỗi lần)
            if self.record.AcceptWaveform(data) and len(data) > 0: 
                answer = json.loads(self.record.Result()) # Parse kết quả Json
                if answer['text']: 
                    yield answer['text'] # Trả về text nếu có

# Hàm tiện ích: Hàm speak
def speak(text): 
    speech = Speech() # Tạo đối tượng speech mới
    speech.text2voice(speaker=1, text=text) # Sử dụng giọng số 1 để đọc văn bản

if __name__ == '__main__':
    rec = Recognize() # Tạo đối tượng nhận diện
    text_gen = rec.listen() # Tạo generator để lắng nghe 
    rec.stream.stop_stream() # Tạm dừng stream
    speak('Starting') # Thông báo bắt đầu
    time.sleep(0.5) # Delay 0.5s
    rec.stream.start_stream() # Khởi động lại stream
    
    for text in text_gen: # Lặp qua các test được nhận diện
        if text == 'закрыть': 
            speak('Бывай, ихтиандр')
            quit()
        else:
            print(text)