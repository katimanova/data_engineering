import os
import re
import shutil
import fitz

def clean_title(title):
    clean_title = re.sub(r'[<>:"/\\|?*]', '', title)
    clean_title = re.sub(r'\s+', '_', clean_title).strip()
    clean_title = clean_title.rstrip('.')
    return clean_title[:50]

def create_directory_structure(hierarchy, base_path, pdf_path):
    
    doc = fitz.open(pdf_path)

    for section in hierarchy:
        clean_title_name = clean_title(section['title'])
        section_dir = os.path.join(base_path, clean_title_name)

        if not os.path.exists(base_path):
            try:
                os.makedirs(base_path, exist_ok=True)
            except Exception as e:
                print(f"Не удалось создать базовую директорию: {base_path}. Ошибка: {e}")
                continue
            
        print(f"Создание директории: {section_dir}")

        try:
            os.makedirs(section_dir, exist_ok=True)
        except Exception as e:
            print(f"Не удалось создать директорию: {section_dir}. Ошибка: {e}")
            continue

        new_pdf_name = f"{clean_title_name}.pdf".strip()
        new_pdf_path = os.path.join(section_dir, new_pdf_name)

        if not os.path.exists(section_dir):
            print(f"Директория не существует: {section_dir}. Невозможно сохранить PDF.")
            continue

        start_page = section['start_page'] - 1
        end_page = section['end_page'] - 1

        if start_page <= end_page:
            new_pdf_doc = fitz.open()

            for page_num in range(start_page, end_page + 1):
                new_pdf_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

            if new_pdf_doc.page_count > 0:
                try:
                    new_pdf_doc.save(new_pdf_path)
                    print(f"Сохранен PDF: {new_pdf_path}")
                except Exception as e:
                    print(f"Не удалось сохранить PDF: {new_pdf_path}. Ошибка: {e}")
            else:
                print(f"Пропущен раздел '{clean_title_name}': нет страниц для сохранения.")

            new_pdf_doc.close()
        else:
            print(f"Пропущен раздел '{clean_title_name}': недопустимый диапазон страниц ({start_page + 1} - {end_page + 1})")

        if section.get('subsections'):
            create_directory_structure(section['subsections'], section_dir, pdf_path)

    doc.close()