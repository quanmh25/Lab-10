import requests
import pyttsx3
import pyaudio
import vosk
import json
import os
from datetime import datetime

class VoiceAssistant:
    def __init__(self):
        self.tts = pyttsx3.init()
        self.tts.setProperty('rate', 150)
        
        if not os.path.exists("vosk-model-ru-0.42"):
            print("Скачайте модель Vosk")
            exit(1)
        
        self.model = vosk.Model("vosk-model-ru-0.42")
        self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
        self.audio = pyaudio.PyAudio()
        
        self.country = "RU"
        self.year = datetime.now().year
        self.holidays_cache = {}

    def speak(self, text):
        print(f"Ассистент: {text}")
        self.tts.say(text)
        self.tts.runAndWait()

    def listen(self):
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8000
        )
        
        frames = []
        for _ in range(int(16000 / 8000 * 3)):
            data = stream.read(8000)
            frames.append(data)
        
        stream.close()
        
        if self.recognizer.AcceptWaveform(b''.join(frames)):
            result = json.loads(self.recognizer.Result())
            return result.get('text', '').lower()
        return ""

    def get_holidays(self):
        key = f"{self.country}_{self.year}"
        if key in self.holidays_cache:
            return self.holidays_cache[key]
        
        try:
            url = f"https://date.nager.at/api/v2/publicholidays/{self.year}/{self.country}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                holidays = response.json()
                self.holidays_cache[key] = holidays
                return holidays
        except:
            self.speak("Ошибка получения данных")
        return []

    def list_holidays(self):
        holidays = self.get_holidays()
        if holidays:
            names = [h['name'] for h in holidays[:10]]
            for name in names:
                print(f"- {name}")
            self.speak(f"Показано {len(names)} праздников")

    def save_holidays(self):
        holidays = self.get_holidays()
        if holidays:
            with open(f"holidays_{self.country}_{self.year}.txt", 'w', encoding='utf-8') as f:
                for h in holidays:
                    f.write(f"{h['name']}\n")
            self.speak("Праздники сохранены")

    def save_dates(self):
        holidays = self.get_holidays()
        if holidays:
            with open(f"dates_{self.country}_{self.year}.txt", 'w', encoding='utf-8') as f:
                for h in holidays:
                    f.write(f"{h['date']} - {h['name']}\n")
            self.speak("Даты сохранены")

    def nearest_holiday(self):
        holidays = self.get_holidays()
        if not holidays:
            return
        
        today = datetime.now().date()
        nearest = None
        min_diff = float('inf')
        
        for h in holidays:
            h_date = datetime.strptime(h['date'], '%Y-%m-%d').date()
            diff = (h_date - today).days if h_date >= today else 365
            if diff < min_diff:
                min_diff = diff
                nearest = h
        
        if nearest:
            self.speak(f"Ближайший: {nearest['name']}, {nearest['date']}")

    def count_holidays(self):
        holidays = self.get_holidays()
        self.speak(f"Всего {len(holidays)} праздников")

    def run(self):
        commands = {
            'перечислить': self.list_holidays,
            'сохранить': self.save_holidays,
            'даты': self.save_dates,
            'ближайший': self.nearest_holiday,
            'количество': self.count_holidays
        }
        
        self.speak("Ассистент готов")
        
        while True:
            print("\nНажмите Enter для записи или введите команду:")
            text_input = input()
            
            if text_input:
                text = text_input.lower()
            else:
                self.speak("Слушаю")
                text = self.listen()
            
            if 'выход' in text:
                self.speak("До свидания")
                break
            
            executed = False
            for cmd, func in commands.items():
                if cmd in text:
                    func()
                    executed = True
                    break
            
            if not executed:
                self.speak("Команда не найдена")

if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()