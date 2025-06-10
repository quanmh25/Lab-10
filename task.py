
"""
Голосовой ассистент для работы с API государственных праздников
Требуемые библиотеки: pip install requests pyttsx3 pyaudio vosk
Также необходимо скачать модель Vosk для русского языка
"""

import requests
import pyttsx3
import pyaudio
import vosk
import json
import os
from datetime import datetime, timedelta
import sys
import threading
import queue

class VoiceAssistant:
    def __init__(self):
        """Инициализация голосового ассистента"""
        # Настройка синтеза речи
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 150)  # Скорость речи
        voices = self.tts_engine.getProperty('voices')
        
        # Попытка найти русский голос
        for voice in voices:
            if 'ru' in voice.id.lower() or 'russian' in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break
        
        # Настройка распознавания речи
        self.model_path = "vosk-model-ru-0.42"  # Путь к модели Vosk
        if not os.path.exists(self.model_path):
            print(f"Модель Vosk не найдена по пути: {self.model_path}")
            print("Скачайте модель с https://alphacephei.com/vosk/models")
            sys.exit(1)
        
        self.model = vosk.Model(self.model_path)
        self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
        
        # Настройка микрофона
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # Настройки API
        self.base_url = "https://date.nager.at/api/v2/publicholidays"
        self.country = "RU"  # По умолчанию Россия
        self.year = datetime.now().year
        
        # Кэш для хранения праздников
        self.holidays_cache = {}
        
        # Команды и их обработчики
        self.commands = {
            'перечислить': self.list_holidays,
            'сохранить': self.save_holidays,
            'даты': self.save_dates,
            'ближайший': self.nearest_holiday,
            'количество': self.count_holidays,
            'страна': self.change_country,
            'год': self.change_year,
            'помощь': self.show_help,
            'выход': self.exit_assistant
        }
        
        print("Голосовой ассистент инициализирован!")
        self.speak("Голосовой ассистент готов к работе!")

    def speak(self, text):
        """Произнесение текста"""
        print(f"Ассистент: {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def listen(self):
        """Распознавание речи с микрофона"""
        try:
            # Настройка потока аудио
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=8000
            )
            
            print("Слушаю... (говорите после звукового сигнала)")
            self.speak("Слушаю")
            
            # Чтение аудио данных
            frames = []
            for _ in range(0, int(16000 / 8000 * 5)):  # 5 секунд записи
                data = self.stream.read(8000)
                frames.append(data)
            
            # Распознавание
            audio_data = b''.join(frames)
            if self.recognizer.AcceptWaveform(audio_data):
                result = json.loads(self.recognizer.Result())
                return result.get('text', '').lower().strip()
            
            return ""
            
        except Exception as e:
            print(f"Ошибка при распознавании речи: {e}")
            return ""
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()

    def get_holidays(self, year=None, country=None):
        """Получение списка праздников из API"""
        if year is None:
            year = self.year
        if country is None:
            country = self.country
            
        cache_key = f"{country}_{year}"
        
        # Проверка кэша
        if cache_key in self.holidays_cache:
            return self.holidays_cache[cache_key]
        
        try:
            url = f"{self.base_url}/{year}/{country}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                holidays = response.json()
                self.holidays_cache[cache_key] = holidays
                return holidays
            else:
                self.speak(f"Ошибка при получении данных: {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"Ошибка запроса: {e}")
            self.speak("Ошибка подключения к серверу")
            return []

    def list_holidays(self):
        """Перечисление названий праздников"""
        holidays = self.get_holidays()
        if not holidays:
            self.speak("Не удалось получить список праздников")
            return
        
        holiday_names = [holiday['name'] for holiday in holidays]
        
        if len(holiday_names) > 10:
            self.speak(f"Найдено {len(holiday_names)} праздников. Перечислю первые 10:")
            holiday_names = holiday_names[:10]
        else:
            self.speak(f"Список праздников в {self.country} за {self.year} год:")
        
        for name in holiday_names:
            print(f"- {name}")
        
        # Произносим только количество для экономии времени
        self.speak(f"Список из {len(holiday_names)} праздников выведен на экран")

    def save_holidays(self):
        """Сохранение названий праздников в файл"""
        holidays = self.get_holidays()
        if not holidays:
            self.speak("Не удалось получить список праздников")
            return
        
        filename = f"holidays_{self.country}_{self.year}.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for holiday in holidays:
                    f.write(f"{holiday['name']}\n")
            
            self.speak(f"Список праздников сохранён в файл {filename}")
            print(f"Файл {filename} создан успешно")
            
        except Exception as e:
            print(f"Ошибка при сохранении файла: {e}")
            self.speak("Ошибка при сохранении файла")

    def save_dates(self):
        """Сохранение дат и названий праздников в файл"""
        holidays = self.get_holidays()
        if not holidays:
            self.speak("Не удалось получить список праздников")
            return
        
        filename = f"holidays_with_dates_{self.country}_{self.year}.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for holiday in holidays:
                    f.write(f"{holiday['date']} - {holiday['name']}\n")
            
            self.speak(f"Список праздников с датами сохранён в файл {filename}")
            print(f"Файл {filename} создан успешно")
            
        except Exception as e:
            print(f"Ошибка при сохранении файла: {e}")
            self.speak("Ошибка при сохранении файла")

    def nearest_holiday(self):
        """Поиск ближайшего праздника"""
        holidays = self.get_holidays()
        if not holidays:
            self.speak("Не удалось получить список праздников")
            return
        
        today = datetime.now().date()
        nearest = None
        min_diff = float('inf')
        
        for holiday in holidays:
            holiday_date = datetime.strptime(holiday['date'], '%Y-%m-%d').date()
            
            # Рассчитываем разность, учитывая что праздник может быть в следующем году
            if holiday_date >= today:
                diff = (holiday_date - today).days
            else:
                # Праздник уже прошёл в этом году, рассматриваем следующий год
                next_year_date = holiday_date.replace(year=today.year + 1)
                diff = (next_year_date - today).days
            
            if diff < min_diff:
                min_diff = diff
                nearest = holiday
        
        if nearest:
            holiday_date = datetime.strptime(nearest['date'], '%Y-%m-%d').date()
            if holiday_date >= today:
                date_str = holiday_date.strftime('%d.%m.%Y')
                self.speak(f"Ближайший праздник: {nearest['name']}, {date_str}")
            else:
                next_year_date = holiday_date.replace(year=today.year + 1)
                date_str = next_year_date.strftime('%d.%m.%Y')
                self.speak(f"Ближайший праздник: {nearest['name']}, {date_str} следующего года")
        else:
            self.speak("Не удалось найти ближайший праздник")

    def count_holidays(self):
        """Подсчёт количества праздников"""
        holidays = self.get_holidays()
        count = len(holidays)
        
        if count > 0:
            self.speak(f"В {self.country} в {self.year} году {count} официальных праздников")
        else:
            self.speak("Праздники не найдены")

    def change_country(self):
        """Смена страны"""
        self.speak("Назовите код страны, например: RU для России, US для США, GB для Великобритании")
        
        # Простая версия - запрос через консоль
        new_country = input("Введите код страны: ").upper().strip()
        
        if len(new_country) == 2:
            old_country = self.country
            self.country = new_country
            self.speak(f"Страна изменена с {old_country} на {self.country}")
        else:
            self.speak("Неверный код страны")

    def change_year(self):
        """Смена года"""
        self.speak("Назовите год")
        
        # Простая версия - запрос через консоль
        try:
            new_year = int(input("Введите год: ").strip())
            if 2000 <= new_year <= 2030:
                old_year = self.year
                self.year = new_year
                self.speak(f"Год изменён с {old_year} на {self.year}")
            else:
                self.speak("Год должен быть в диапазоне от 2000 до 2030")
        except ValueError:
            self.speak("Неверный формат года")

    def show_help(self):
        """Показ справки по командам"""
        help_text = """
        Доступные команды:
        - перечислить: показать названия праздников
        - сохранить: сохранить названия в файл
        - даты: сохранить даты и названия в файл
        - ближайший: найти ближайший праздник
        - количество: подсчитать количество праздников
        - страна: сменить страну
        - год: сменить год
        - помощь: показать эту справку
        - выход: завершить работу
        """
        print(help_text)
        self.speak("Список команд выведен на экран")

    def process_command(self, text):
        """Обработка распознанной команды"""
        text = text.lower().strip()
        
        # Поиск команды в тексте
        recognized_command = None
        for command in self.commands:
            if command in text:
                recognized_command = command
                break
        
        if recognized_command:
            print(f"Распознана команда: {recognized_command}")
            try:
                self.commands[recognized_command]()
            except Exception as e:
                print(f"Ошибка при выполнении команды: {e}")
                self.speak("Произошла ошибка при выполнении команды")
        else:
            print(f"Не распознана команда в тексте: '{text}'")
            self.speak("Команда не распознана. Скажите 'помощь' для списка команд")

    def exit_assistant(self):
        """Завершение работы ассистента"""
        self.speak("До свидания!")
        sys.exit(0)

    def run(self):
        """Основной цикл работы ассистента"""
        self.show_help()
        
        try:
            while True:
                print(f"\nТекущие настройки: страна={self.country}, год={self.year}")
                print("Нажмите Enter для начала записи голосовой команды...")
                input()
                
                # Альтернативный ввод через консоль для тестирования
                print("Или введите команду текстом:")
                text_input = input("Команда: ").strip()
                
                if text_input:
                    self.process_command(text_input)
                else:
                    # Голосовой ввод
                    recognized_text = self.listen()
                    
                    if recognized_text:
                        print(f"Распознано: {recognized_text}")
                        self.process_command(recognized_text)
                    else:
                        self.speak("Не удалось распознать команду")
        
        except KeyboardInterrupt:
            print("\nПрограмма прервана пользователем")
            self.speak("Программа завершена")
        except Exception as e:
            print(f"Критическая ошибка: {e}")
            self.speak("Произошла критическая ошибка")
        finally:
            # Очистка ресурсов
            if self.stream:
                self.stream.close()
            self.audio.terminate()

def main():
    """Главная функция"""
    print("Запуск голосового ассистента...")
    print("Убедитесь, что у вас установлены все необходимые библиотеки:")
    print("pip install requests pyttsx3 pyaudio vosk")
    print("И скачана модель Vosk для русского языка\n")
    
    try:
        assistant = VoiceAssistant()
        assistant.run()
    except Exception as e:
        print(f"Ошибка при запуске ассистента: {e}")

if __name__ == "__main__":
    main()