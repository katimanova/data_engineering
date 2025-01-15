import fitz

def extract_toc_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()

    toc2 = []
    start_printing = False

    for level, title, page in toc:
        if "ВВЕДЕНИЕ" in title.upper():
            start_printing = True
        
        if start_printing:
            toc2.append((level, title, page))
    
    return toc2

def split_pdf_by_toc(pdf_path):
    doc = fitz.open(pdf_path)
    toc = extract_toc_from_pdf(pdf_path)
    
    sections = []
    
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

def build_hierarchy(sections):
    hierarchy = []
    stack = []

    for section in sections:
        level = section['level']
        
        while stack and stack[-1]['level'] >= level:
            stack.pop()

        if stack:
            stack[-1]['subsections'].append(section)
        else:
            hierarchy.append(section)

        stack.append(section)
        
    return hierarchy

def update_end_pages(section):
    if not section['subsections']:
        return section['end_page']

    max_end_page = section['end_page']
    for subsection in section['subsections']:
        max_end_page = max(max_end_page, update_end_pages(subsection))

    section['end_page'] = max_end_page
    return section['end_page']

def update_all_end_pages(hierarchy):
    for section in hierarchy:
        update_end_pages(section)
        check_and_fill_end_page(section)

def extract_text_from_pages(doc, start_page, end_page):
    text = ""
    for page_num in range(start_page - 1, end_page):
        page = doc.load_page(page_num)
        text += page.get_text()
    return text

def check_and_fill_end_page(section):
    print(f"Проверка раздела: {section['title']}, start_page: {section['start_page']}, end_page: {section['end_page']}")
    
    if section['end_page'] < section['start_page']:
        print(f"Корректировка end_page для {section['title']} с {section['end_page']} на {section['start_page']}")
        section['end_page'] = section['start_page'] 

    for subsection in section.get('subsections', []):
        check_and_fill_end_page(subsection)


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

def extract_text_from_hierarchy(doc, hierarchy):
    texts = []
    for section in hierarchy:
        texts.append(extract_text_from_leaf_sections(doc, section))
    return texts

#pdf_path = r"C:\Users\user\Книга 1\Книга 1.pdf"
#doc = fitz.open(pdf_path)

#sections = split_pdf_by_toc(pdf_path)
#hierarchy = build_hierarchy(sections)
#update_all_end_pages(hierarchy)

#leaf_texts = extract_text_from_hierarchy(doc, hierarchy)

#from pprint import pprint
#pprint(leaf_texts)


#base_path = r"C:\Users\user\PDF_PROJECT\Книга 1"

#create_directory_structure(hierarchy, base_path, pdf_path)
#print(f"Структура каталогов создана в: {base_path}")