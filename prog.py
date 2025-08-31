import fitz  # PyMuPDF
import os
import time
import shutil


def run():
    for i in range(10):
        print(f"Выполняется шаг {i+1}/10")
        time.sleep(1)
    print("Завершено!")


def split_pdf_by_keyword(input_path, output_dir, word):
    """
    Разделяет PDF файл на части по ключевому слову и сохраняет каждую часть в отдельный PDF-файл.

    Аргументы:
    input_path -- путь к исходному PDF файлу
    output_dir -- директория для сохранения результатов
    """
    try:
        shutil.rmtree(output_dir)
    except Exception:
        pass

    # пути и имена
    original_name = os.path.splitext(os.path.basename(input_path))[0]
    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(input_path)

    print(f"Обработка {len(doc)} страниц...")

    #  флаги поиска (ТОЛЬКО ТОЧНОЕ СОВПАДЕНИЕ, РЕГИСТР УЧИТЫВАЕТСЯ)
    search_flags = fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE

    file_counter = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        print(f"  Обработка страницы {page_num + 1}...")

        try:
            text_instances = page.search_for(word, flags=search_flags)
        except Exception as e:
            print(f"  ❌ Ошибка поиска на странице {page_num + 1}: {str(e)}")
            continue

        if not text_instances:
            print(f"    ⚠️ Ключевое слово '{word}' не найдено")
            continue

        print(f"    Найдено {len(text_instances)} вхождений")

        # Собираем уникальные Y-координаты
        y_positions = sorted({round(rect.y0, 2) for rect in text_instances})
        y_positions = [0.0] + y_positions + [float(page.rect.height)]

        # Обрабатываем каждый сегмент
        for i in range(len(y_positions) - 1):
            y0 = y_positions[i]
            y1 = y_positions[i + 1]
            segment_height = y1 - y0
            page_height = page.rect.height

            # УДАЛЯЕМ СЕГМЕНТЫ МЕНЬШЕ 10% ОТ ВЫСОТЫ СТРАНИЦЫ
            if segment_height < 0.05 * page_height:
                print(
                    f"      Пропущен сегмент {i}: высота {segment_height:.1f} < 5% от {page_height:.1f}"
                )
                continue

            # Создаем имя файла (с нумерацией с нуля)
            filename = f"{file_counter:03d}-{original_name}.pdf"
            file_path = os.path.join(output_dir, filename)

            # Создаем и сохраняем документ
            part_doc = fitz.open()
            new_page = part_doc.new_page(width=page.rect.width, height=segment_height)

            # Копируем содержимое
            clip_rect = fitz.Rect(0, y0, page.rect.width, y1)
            new_page.show_pdf_page(new_page.rect, doc, page_num, clip=clip_rect)

            part_doc.save(file_path)
            part_doc.close()

            print(
                f"      Сохранено: {filename} (высота: {segment_height:.1f} из {page_height:.1f})"
            )
            file_counter += 1

    doc.close()

    print(
        f"\n✅ Готово! Создано {file_counter} файлов в папке: {os.path.abspath(output_dir)}"
    )
    print(f"   Шаблон имен: НОМЕР(с нуля)-{original_name}.pdf")
    print(f"   Пример: 000-{original_name}.pdf, 001-{original_name}.pdf, ...")


# test only
if __name__ == "__main__":
    input_pdf = "dz4-2.pdf"
    output_directory = "output"  # Директория для сохранения файлов
    word_sp = "Задача"

    split_pdf_by_keyword(
        input_path=input_pdf, output_dir=output_directory, word=word_sp
    )
