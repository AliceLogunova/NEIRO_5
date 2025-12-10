import csv
import time
from collections import deque
from datetime import datetime

import matplotlib

matplotlib.use("TkAgg")

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import serial  # type: ignore

# КОНСТАНТИНЕНЫ НАСТРОЙКИ
SERIAL_PORT = "COM4"  
BAUD_RATE = 9600
CSV_FILENAME = "sensor_data.csv"
MAX_POINTS = 500  # Количество точек на графике
UPDATE_INTERVAL_MS = 10  # Интервал обновления графика в миллисекундах


# Подготовка CSV
def init_csv():
    """Создаёт CSV-файл с заголовками, если его нет."""
    try:
        with open(CSV_FILENAME, "x", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "value"])
        print(f"Создан новый файл: {CSV_FILENAME}")
    except FileExistsError:
        print(f"Используется существующий файл: {CSV_FILENAME}")


# Константин для управления графиком
class LivePlotter:
    def __init__(self, maxlen=1000):
        self.times = deque(maxlen=maxlen)
        self.values = deque(maxlen=maxlen)

        # Настройка графика
        plt.style.use("ggplot")
        self.fig, self.ax = plt.subplots(figsize=(12, 6))
        (self.line,) = self.ax.plot([], [], "b-", linewidth=1.5)
        self.ax.set_title("Данные с датчика в реальном времени", fontsize=14)
        self.ax.set_xlabel("Время", fontsize=12)
        self.ax.set_ylabel("Значение", fontsize=12)
        self.ax.grid(True)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        self.anim = None

    def update(self, frame, ser, csv_writer):
        """Обновляет данные и график. Считывает ВСЕ доступные данные из Serial."""
        new_points = 0
        while ser.in_waiting > 0:
            try:
                line = ser.readline().decode("utf-8").strip()
                if not line:
                    continue
                value = float(line)
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # ЧЧ:ММ:СС.мс

                # Запись в CSV (файл уже открыт!)
                csv_writer.writerow([timestamp, value])

                # Обновление данных для графика
                self.times.append(timestamp)
                self.values.append(value)
                new_points += 1

            except (ValueError, UnicodeDecodeError):
                # Игнорируем битые данные
                continue
            except Exception as e:
                print(f"Ошибка при чтении строки: {e}")
                continue

        if new_points > 0:
            # Обновление линии графика
            self.line.set_data(range(len(self.values)), self.values)
            self.ax.set_xlim(0, len(self.values))
            if self.values:
                y_min = min(self.values) - 1
                y_max = max(self.values) + 1
                self.ax.set_ylim(y_min, y_max)

            # Обновление подписей по X (время)
            total = len(self.times)
            if total > 0:
                step = max(1, total // 10)
                self.ax.set_xticks(range(0, total, step))
                self.ax.set_xticklabels(list(self.times)[::step])

        return (self.line,)

    def show(self, ser, csv_writer):
        """Запускает анимацию графика."""
        self.anim = animation.FuncAnimation(
            self.fig,
            self.update,
            fargs=(ser, csv_writer),
            interval=UPDATE_INTERVAL_MS,
            blit=False,
            cache_frame_data=False,
        )
        plt.show()


# Основная констограмма
def main():
    init_csv()

    # Открываем файл ОДИН РАЗ на всю сессию
    csvfile = None
    ser = None

    try:
        print(f"Подключаюсь к {SERIAL_PORT} со скоростью {BAUD_RATE}...")
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)  # Уменьшаем таймаут для отзывчивости
        time.sleep(2)  # Ждём стабилизации соединения
        print("Подключение установлено. Начинаю чтение данных...")

        # Открываем CSV файл на запись (append) и создаём writer
        csvfile = open(CSV_FILENAME, "a", newline="", encoding="utf-8")
        csv_writer = csv.writer(csvfile)

        # Создаём график
        plotter = LivePlotter(maxlen=MAX_POINTS)

        # Запускаем визуализацию
        print("График запущен. Нажмите Ctrl+C для остановки.")
        plotter.show(ser, csv_writer)

    except serial.SerialException as e:
        print(f"Ошибка подключения к порту: {e}")
    except KeyboardInterrupt:
        print("\nПолучен сигнал завершения. Закрываю соединение и файл...")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
    finally:
        if csvfile and not csvfile.closed:
            csvfile.close()
            print("CSV-файл закрыт.")
        if ser and ser.is_open:
            ser.close()
            print("Соединение закрыто.")


if __name__ == "__main__":
    main()

