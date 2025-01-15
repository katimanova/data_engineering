import tkinter as tk
import os
from tkinter import filedialog, messagebox, ttk
import fitz 
import json
import subprocess
from datetime import datetime
from data.modules.text_by_toc import (
    extract_toc_from_pdf,
    split_pdf_by_toc,
    build_hierarchy,
    update_all_end_pages,
    extract_text_from_hierarchy,
    extract_text_from_pages,
    check_and_fill_end_page
)
from data.modules.pdf_to_folders import create_directory_structure

current_pdf = None
hierarchy = None
root = None 

output_dir = None
selected_basin = None

def open_pdf():
    global current_pdf, hierarchy

    pdf_path = filedialog.askopenfilename(
        title="Выберите PDF файл",
        filetypes=(("PDF files", "*.pdf"), ("All files", "*.*"))
    )
    if pdf_path:
        current_pdf = pdf_path
        process_pdf(pdf_path)

def process_pdf(pdf_path):
    global hierarchy

    try:
        toc = extract_toc_from_pdf(pdf_path)
        sections = split_pdf_by_toc(pdf_path)
        hierarchy = build_hierarchy(sections)
        update_all_end_pages(hierarchy)
        
        text_display.delete(1.0, tk.END)
        tree.delete(*tree.get_children())
        
        
        add_back_to_toc_button()

        display_structure(hierarchy)

        add_to_tree(hierarchy)

    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось обработать PDF: {e}")

def display_structure(hierarchy, level=0):
    indent = "  " * level 
    for section in hierarchy:
        section_str = f"{indent}Уровень: {section['level']}, Заголовок: {section['title']}, " \
                      f"Страницы: {section['start_page']} - {section['end_page']}\n"
        text_display.insert(tk.END, section_str)

        if section['subsections']:
            display_structure(section['subsections'], level + 1)

def add_to_tree(hierarchy, parent=""):
    for section in hierarchy:
        item_id = tree.insert(parent, "end", text=section['title'], iid=section['title'])
        tree.item(item_id, tags=(section['start_page'], section['end_page']))

        if section['subsections']:
            add_to_tree(section['subsections'], parent=item_id)

def on_tree_select(event):
    selected_item = tree.selection()[0]
    start_page = tree.item(selected_item, 'tags')[0]
    end_page = tree.item(selected_item, 'tags')[1]

    display_text_for_section(selected_item, int(start_page), int(end_page))

def display_text_for_section(section_title, start_page, end_page):
    try:
        doc = fitz.open(current_pdf)
        text = ""
        for page_num in range(start_page - 1, end_page):
            page = doc.load_page(page_num)
            text += page.get_text()

        text_display.delete(1.0, tk.END)
        text_display.insert(tk.END, text)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось извлечь текст: {e}")




def select_output_directory():
    global output_dir, output_label
    output_dir = filedialog.askdirectory(title="Выберите директорию для сохранения")
    if output_dir:
        output_label.config(text=f"Выбранная директория: {output_dir}")
        messagebox.showinfo("Директория выбрана", f"Директория выбрана: {output_dir}")
    else:
        output_label.config(text="Выбранная директория: Не выбрана")
        messagebox.showwarning("Предупреждение", "Директория не выбрана.")


def attach_text_to_deepest_sections(section, doc):
    if not section['subsections']:
        text = extract_text_from_pages(doc, section['start_page'], section['end_page'])
        section['text'] = text
    else:
        for subsection in section['subsections']:
            attach_text_to_deepest_sections(subsection, doc)


def create_json_and_directories():
    if not hierarchy or not output_dir:
        messagebox.showwarning("Предупреждение", "Необходимо выбрать PDF файл и директорию для сохранения.")
        return

    try:
        doc = fitz.open(current_pdf)
        for section in hierarchy:
            attach_text_to_deepest_sections(section, doc)
        create_directory_structure(hierarchy, output_dir, current_pdf)

        json_file = os.path.join(output_dir, f"{os.path.splitext(current_pdf)[0]}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(hierarchy, f, ensure_ascii=False, indent=4)

        messagebox.showinfo("Успех", f"Структура сохранена и директории созданы в {output_dir}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка при создании JSON и директорий: {e}")



def add_back_to_toc_button():
    item_id = tree.insert("", "end", text="<- назад(Двойной клик)", iid="toc_button", open=True)
    tree.bind("<Double-1>", on_back_to_toc_select) 
    
def on_back_to_toc_select(event):
    selected_item = tree.selection()[0]
    if selected_item == "toc_button":
        text_display.delete(1.0, tk.END)
        display_structure(hierarchy)



def save_terminal_logs(logs):
    current_dir = os.path.dirname(os.path.abspath(__file__))

    log_dir = os.path.join(current_dir, '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    log_file_name = os.path.join(log_dir, f'main_logs_{timestamp}.log')

    with open(log_file_name, 'w', encoding='utf-8') as log_file:
        log_file.write(logs)

def run_main_script():
    current_dir = os.path.dirname(os.path.abspath(__file__))

    main_script = os.path.join(current_dir, 'tkinter_interface.py')

    result = subprocess.run(
        ["python", main_script],
        capture_output=True,
        text=True
    )
    return result.stdout, result.stderr

def open_log_terminal():
    stdout, stderr = run_main_script()

    logs = f"Вывод скрипта main.py:\n{stdout}\nОшибки скрипта main.py:\n{stderr}\n"

    save_terminal_logs(logs)

def run_gui():
    global text_display, root, tree, output_label, log_display

    root = tk.Tk()
    root.title("Книжный Парсер")

    open_button = ttk.Button(root, text="Открыть PDF", command=open_pdf)
    open_button.pack(pady=10)
    
    
    output_label = ttk.Label(root, text="Выбранная директория: Не выбрана")
    output_label.pack(pady=5)

    
    
    dir_button = ttk.Button(root, text="Выбрать директорию сохранения каталога", command=select_output_directory)
    dir_button.pack(pady=10)

    create_button = ttk.Button(root, text="Создать каталог и JSON", command=create_json_and_directories)
    create_button.pack(pady=10)

    tree_frame = ttk.Frame(root)
    tree_frame.pack(side=tk.LEFT, padx=10, pady=10)

    nav_label = ttk.Label(tree_frame, text="НАВИГАЦИЯ", font=("Arial", 12))
    nav_label.pack(pady=5)

    tree = ttk.Treeview(tree_frame)
    tree.pack(fill=tk.BOTH, expand=True)
    tree.bind("<<TreeviewSelect>>", on_tree_select)

    content_frame = ttk.Frame(root)
    content_frame.pack(side=tk.RIGHT, padx=10, pady=10)

    content_label = ttk.Label(content_frame, text="СОДЕРЖАНИЕ РАЗДЕЛА", font=("Arial", 12))
    content_label.pack(pady=5)

    text_display = tk.Text(content_frame, wrap="word", width=80, height=20)
    text_display.pack(fill=tk.BOTH, expand=True)
    
    open_log_button = ttk.Button(root, text="Сохранить логи", command=open_log_terminal)
    open_log_button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    run_gui()
