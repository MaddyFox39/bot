import os

def replace_in_file(file_path, old_string, new_string):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    content = content.replace(old_string, new_string)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def replace_in_project(directory, old_string, new_string):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                replace_in_file(file_path, old_string, new_string)

project_directory = 'C:\Users\79226\PycharmProjects\pythonProject4'
replace_in_project(project_directory, 'db_Session()', 'db_Session()')