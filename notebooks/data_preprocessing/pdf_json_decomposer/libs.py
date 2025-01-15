import os
import re
import fitz
import json

# Извлечение оглавления из PDF
def extract_toc_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()

    toc2 = []
    start_printing = False

    # Начинаем извлекать оглавление только с "ВВЕДЕНИЕ"
    for level, title, page in toc:
        if "ВВЕДЕНИЕ" in title.upper():
            start_printing = True
        
        if start_printing:
            toc2.append((level, title, page))
    
    return toc2

# Разделение PDF на секции согласно оглавлению
def split_pdf_by_toc(pdf_path):
    doc = fitz.open(pdf_path)
    toc = extract_toc_from_pdf(pdf_path)
    
    sections = []
    
    # Формируем список секций с указанием начала и конца страниц
    for i in range(len(toc)):
        level, title, start_page = toc[i]
        
        if i + 1 < len(toc):
            end_page = toc[i + 1][2] - 1
        else:
            end_page = doc.page_count - 1

        sections.append({
            "level": level,
            "title": title,
            "start_page": start_page,
            "end_page": end_page,
            "subsections": []
        })

    return sections

# Построение иерархии разделов
def build_hierarchy(sections):
    hierarchy = []
    stack = []

    for section in sections:
        level = section['level']
        
        # Удаляем секции из стека, которые находятся на том же уровне или выше
        while stack and stack[-1]['level'] >= level:
            stack.pop()

        if stack:
            stack[-1]['subsections'].append(section)
        else:
            hierarchy.append(section)

        stack.append(section)
        
    return hierarchy

# Обновление конечных страниц для разделов
def update_end_pages(section):
    if not section['subsections']:
        return section['end_page']

    max_end_page = section['end_page']
    for subsection in section['subsections']:
        max_end_page = max(max_end_page, update_end_pages(subsection))

    section['end_page'] = max_end_page
    return section['end_page']

# Обновление конечных страниц для всей иерархии
def update_all_end_pages(hierarchy):
    for section in hierarchy:
        update_end_pages(section)
        check_and_fill_end_page(section)

# Извлечение текста из заданного диапазона страниц
def extract_text_from_pages(doc, start_page, end_page):
    text = ""
    for page_num in range(start_page - 1, end_page):
        page = doc.load_page(page_num)
        text += page.get_text()
    return text

# Проверка и корректировка конечных страниц разделов
def check_and_fill_end_page(section):
    print(f"Проверка раздела: {section['title']}, start_page: {section['start_page']}, end_page: {section['end_page']}")
    
    if section['end_page'] < section['start_page']:
        print(f"Корректировка end_page для {section['title']} с {section['end_page']} на {section['start_page']}")
        section['end_page'] = section['start_page'] 

    for subsection in section.get('subsections', []):
        check_and_fill_end_page(subsection)

# Извлечение текста из самого нижнего уровня секций
def extract_text_from_leaf_sections(doc, section):
    if not section['subsections']:
        start_page = section['start_page']
        end_page = section['end_page']
        text = extract_text_from_pages(doc, start_page, end_page)
        
        return {
            "title": section['title'],
            "start_page": start_page,
            "end_page": end_page,
            "text": text
        }
    else:
        texts = []
        for subsection in section['subsections']:
            texts.append(extract_text_from_leaf_sections(doc, subsection))
        return texts

# Извлечение текста из всей иерархии
def extract_text_from_hierarchy(doc, hierarchy):
    texts = []
    for section in hierarchy:
        texts.append(extract_text_from_leaf_sections(doc, section))
    return texts

# Очистка названий секций для использования в именах файлов
def clean_title(title):
    clean_title = re.sub(r'[<>:"/\\|?*]', '', title)
    clean_title = re.sub(r'\s+', '_', clean_title).strip()
    clean_title = clean_title.rstrip('.')
    return clean_title[:50]

# Создание структуры директорий и сохранение секций
def create_directory_structure(hierarchy, base_path, pdf_path):
    doc = fitz.open(pdf_path)

    for section in hierarchy:
        clean_title_name = clean_title(section['title'])
        section_dir = os.path.join(base_path, clean_title_name)

        # Создаем базовую директорию
        if not os.path.exists(base_path):
            try:
                os.makedirs(base_path, exist_ok=True)
            except Exception as e:
                print(f"Не удалось создать базовую директорию: {base_path}. Ошибка: {e}")
                continue
            
        # print(f"Создание директории: {section_dir}")

        # Создаем директорию для текущего раздела
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

        # Сохраняем страницы раздела в отдельный PDF
        start_page = section['start_page'] - 1
        end_page = section['end_page'] - 1

        if start_page <= end_page:
            new_pdf_doc = fitz.open()

            for page_num in range(start_page, end_page + 1):
                new_pdf_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

            if new_pdf_doc.page_count > 0:
                try:
                    new_pdf_doc.save(new_pdf_path)
                    # print(f"Сохранен PDF: {new_pdf_path}")
                except Exception as e:
                    print(f"Не удалось сохранить PDF: {new_pdf_path}. Ошибка: {e}")
            else:
                print(f"Пропущен раздел '{clean_title_name}': нет страниц для сохранения.")

            new_pdf_doc.close()
        else:
            print(f"Пропущен раздел '{clean_title_name}': недопустимый диапазон страниц ({start_page + 1} - {end_page + 1})")

        # Обрабатываем вложенные разделы
        if section.get('subsections'):
            create_directory_structure(section['subsections'], section_dir, pdf_path)

    doc.close()

# Добавление текста к самым глубоким секциям
def attach_text_to_deepest_sections(section, doc):
    if not section['subsections']:
        text = extract_text_from_pages(doc, section['start_page'], section['end_page'])
        section['text'] = text
    else:
        for subsection in section['subsections']:
            attach_text_to_deepest_sections(subsection, doc)

# Сохранение иерархии в JSON-файл
def save_hierarchy_to_json(hierarchy, output_path):
    with open(output_path, 'w', encoding='utf-8') as json_file:
        json.dump(hierarchy, json_file, ensure_ascii=False, indent=4)