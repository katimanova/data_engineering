import fitz
import json
import os

from modules.text_by_toc import (
    extract_toc_from_pdf,
    split_pdf_by_toc,
    build_hierarchy,
    update_all_end_pages,
    extract_text_from_hierarchy,
    extract_text_from_pages
)
from modules.pdf_to_folders import (
    clean_title,
    create_directory_structure
)
from pprint import pprint


def attach_text_to_deepest_sections(section, doc):
    if not section['subsections']:
        text = extract_text_from_pages(doc, section['start_page'], section['end_page'])
        section['text'] = text
    else:
        for subsection in section['subsections']:
            attach_text_to_deepest_sections(subsection, doc)

def save_hierarchy_to_json(hierarchy, output_path):
    with open(output_path, 'w', encoding='utf-8') as json_file:
        json.dump(hierarchy, json_file, ensure_ascii=False, indent=4)

pdf_path = "data/Base_Books/Дон/Книга 1/Книга_1.pdf"
doc = fitz.open(pdf_path)

sections = split_pdf_by_toc(pdf_path)
hierarchy = build_hierarchy(sections)
update_all_end_pages(hierarchy)

leaf_texts = extract_text_from_hierarchy(doc, hierarchy)

for section in hierarchy:
    attach_text_to_deepest_sections(section, doc)

# pprint(leaf_texts)

base_path = "outputs"

create_directory_structure(hierarchy, base_path, pdf_path)
# print(f"Директория созадана в: {base_path}")

json_output_path = os.path.join(base_path, 'Книга 6.json')
save_hierarchy_to_json(hierarchy, json_output_path)

print(f"Иерархия и текст сохранены в JSON файл: {json_output_path}")