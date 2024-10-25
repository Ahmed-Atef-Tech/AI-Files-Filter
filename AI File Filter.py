import sys
import os
import shutil
import requests
import json
import time
import re  # Import regex library
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QLineEdit, 
                             QProgressBar, QListWidget, QMessageBox, QHBoxLayout, 
                             QSlider, QComboBox, QCheckBox, QScrollArea, QGroupBox, QListWidgetItem, QSizePolicy, QMenuBar, QMenu, QAction)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QIcon
import subprocess  # Import subprocess to run external files

# Classification Thread
class ClassificationThread(QThread):
    progress_changed = pyqtSignal(int)
    status_message = pyqtSignal(str)
    file_copied = pyqtSignal(str, str)  # Emit file name and action type

    def __init__(self, source_folder, destination_folder, classification_key, level, move_files, selected_model, selected_extensions, custom_prompt=None):
        super().__init__()
        self.source_folder = source_folder
        self.destination_folder = destination_folder
        self.classification_key = classification_key
        self.level = level
        self.move_files = move_files
        self.selected_model = selected_model
        self.selected_extensions = selected_extensions
        self.custom_prompt = custom_prompt

    def classify_image(self, image_path):
        file_name_without_extension = os.path.splitext(os.path.basename(image_path))[0]
        file_name_without_extension = re.sub(r'\(\d+\)', '', file_name_without_extension).strip()

        url = "http://localhost:11434/v1/chat/completions"
        headers = {"Content-Type": "application/json"}

        if self.custom_prompt:
            prompt = f'"{file_name_without_extension}", {self.custom_prompt}'
        else:
            level_prompts = {
                0: f"Could '{file_name_without_extension}' be considered related to '{self.classification_key}'?",
                1: f"Could '{file_name_without_extension}' be loosely associated with the concept or category of '{self.classification_key}'?",
                2: f"Could '{file_name_without_extension}' be loosely associated with the concept or category of '{self.classification_key}'?",
                3: f"Would you say that '{file_name_without_extension}' is somewhat related to the concept or category of '{self.classification_key}'?",
                4: f"Would you say that '{file_name_without_extension}' is somewhat related to the concept or category of '{self.classification_key}'?",
                5: f"Can '{file_name_without_extension}' be categorized as '{self.classification_key}'?",
                6: f"Does '{file_name_without_extension}' have a clear and direct connection to the concept or category of '{self.classification_key}'?",
                7: f"Is '{file_name_without_extension}' strongly related to the concept or category of '{self.classification_key}'?",
                8: f"Does '{file_name_without_extension}' specifically and explicitly represent the concept or category of '{self.classification_key}'?"
            }
            prompt = level_prompts[self.level]

        data = {
            "model": self.selected_model,
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            message = result['choices'][0]['message']['content'].strip().lower()

            if "yes" in message:
                return True
            elif "no" in message:
                return False
            else:
                return None
        except Exception as e:
            self.status_message.emit(f"Error: {e}")
            return None

    def move_or_copy_file(self, source_path, destination_path):
        # Check if destination file already exists
        if os.path.exists(destination_path):
            # Rename the file if it already exists at the destination
            base, ext = os.path.splitext(destination_path)
            count = 1
            new_destination = f"{base}_{count}{ext}"
            while os.path.exists(new_destination):
                count += 1
                new_destination = f"{base}_{count}{ext}"
            destination_path = new_destination

        # Perform the move or copy operation based on the move_files flag
        if self.move_files:
            shutil.move(source_path, destination_path)  # Move the file
        else:
            shutil.copy(source_path, destination_path)  # Copy the file

    def run(self):
        files = [f for f in os.listdir(self.source_folder) if any(f.endswith(ext) for ext in self.selected_extensions)]
        total_files = len(files)

        if not os.path.exists(self.destination_folder):
            os.makedirs(self.destination_folder)

        for index, file_name in enumerate(files, start=1):
            file_path = os.path.join(self.source_folder, file_name)
            destination_path = os.path.join(self.destination_folder, file_name)

            if file_path == destination_path:
                self.status_message.emit(f"Skipping {file_name}: Source and destination are the same.")
                continue

            if self.classify_image(file_path):
                # Call move_or_copy_file, which handles both moving and copying
                self.move_or_copy_file(file_path, destination_path)
                action = 'moved' if self.move_files else 'copied'
                self.file_copied.emit(file_name, action)

            self.progress_changed.emit(int((index / total_files) * 100))
            self.status_message.emit(f"Processing {index}/{total_files}: {file_name}")

# FileItemWidget Class
class FileItemWidget(QWidget):
    def __init__(self, file_name, parent=None):
        super().__init__(parent)
        self.file_name = file_name
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(5, 5, 5, 5)
        button_layout.setAlignment(Qt.AlignLeft)
        button_container.setFixedWidth(50)

        self.undo_button = QPushButton("-")
        self.undo_button.setFixedSize(30, 30)
        button_layout.addWidget(self.undo_button)
        
        layout.addWidget(button_container)

        self.label = QLabel(self.file_name)
        self.label.setWordWrap(False)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.label)

        self.setFixedHeight(40)

    def sizeHint(self):
        return QSize(self.width(), 40)

# ProcessingItemWidget Class
class ProcessingItemWidget(QWidget):
    def __init__(self, process_message, show_add_button=True, parent=None):
        super().__init__(parent)
        self.process_message = process_message
        self.show_add_button = show_add_button
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(5, 5, 5, 5)
        button_layout.setAlignment(Qt.AlignLeft)
        button_container.setFixedWidth(50)

        if self.show_add_button:
            self.add_button = QPushButton("+")
            self.add_button.setFixedSize(30, 30)
            button_layout.addWidget(self.add_button)
        
        layout.addWidget(button_container)

        self.label = QLabel(self.process_message)
        self.label.setWordWrap(False)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.label)

        self.setFixedHeight(40)

    def sizeHint(self):
        return QSize(self.width(), 40)

# Main Application Class
class ImageClassifierApp(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.initUI()
        self.start_time = None
        self.is_classification_running = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.file_extensions = []
        self.extension_checkboxes = []
        self.system_extensions = {'.ini', '.sys', '.dll', '.exe', '.bat', '.com', '.cmd'}
        self.custom_prompt = ''
        self.is_using_custom_prompt = False
        self.copied_files = {}
        self.processing_files = {}

        # Add About Page Button/Menu
        self.about_action = QAction("About", self)
        self.about_action.triggered.connect(self.open_about_page)
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        self.help_menu = QMenu("Help", self)
        self.menu_bar.addMenu(self.help_menu)
        self.help_menu.addAction(self.about_action)

    # Modify the open_about_page function to open the .exe file
    def open_about_page(self):
        # Path to the external .exe file
        exe_path = r"G:\Programs Data - media\Auto HotKey Scripts\TouchPortal AHK Scripts\AI Files Sorter\exe version\dist\Python Apps About Page.exe"
        
        # Launch the .exe file using subprocess
        try:
            subprocess.Popen([exe_path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open About page: {e}")

    # Rest of the UI code remains the same
    def initUI(self):
        self.setWindowTitle('AI File Sorter')
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon(r"G:\Programs Data - media\Auto HotKey Scripts\TouchPortal AHK Scripts\AI Files Sorter\Inner_App_Icon_32x32.ico"))

        # UI Elements setup (like buttons, labels, progress bar, etc.)
        self.source_folder = ''
        self.destination_folder = ''
        self.classification_key = ''
        self.level = 2
        self.move_files = False
        self.selected_model = 'mistral:latest'

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        self.source_btn = QPushButton('Select Source Folder', self)
        self.source_btn.clicked.connect(self.select_source)
        layout.addWidget(self.source_btn)

        self.source_path_label = QLabel('', self)
        layout.addWidget(self.source_path_label)

        self.dest_btn = QPushButton('Select Destination Folder', self)
        self.dest_btn.clicked.connect(self.select_destination)
        layout.addWidget(self.dest_btn)

        self.dest_path_label = QLabel('', self)
        layout.addWidget(self.dest_path_label)

        self.model_selector = QComboBox(self)
        self.model_selector.addItems(self.get_available_models())
        self.model_selector.currentTextChanged.connect(self.update_selected_model)
        layout.addWidget(self.model_selector)

        self.extension_scroll_area = QScrollArea()
        self.extension_widget = QWidget()
        self.extension_layout = QVBoxLayout(self.extension_widget)
        self.extension_scroll_area.setWidget(self.extension_widget)
        self.extension_scroll_area.setWidgetResizable(True)
        self.extension_scroll_area.setMaximumHeight(150)
        layout.addWidget(self.extension_scroll_area)

        self.custom_prompt_btn = QPushButton('Use Custom Prompt', self)
        self.custom_prompt_btn.clicked.connect(self.toggle_prompt_mode)
        layout.addWidget(self.custom_prompt_btn)

        self.prompt_group_box = QGroupBox('Predefined Prompt Section')
        prompt_group_layout = QVBoxLayout()
        self.prompt_group_box.setLayout(prompt_group_layout)

        self.classification_key_input = QLineEdit(self)
        self.classification_key_input.setPlaceholderText('Enter classification key')
        self.classification_key_input.textChanged.connect(self.update_prompt_display)
        prompt_group_layout.addWidget(self.classification_key_input)

        self.level_slider = QSlider(Qt.Horizontal, self)
        self.level_slider.setMinimum(0)
        self.level_slider.setMaximum(8)
        self.level_slider.setValue(2)
        self.level_slider.valueChanged.connect(self.update_level_label)
        prompt_group_layout.addWidget(self.level_slider)

        self.level_label = QLabel('Relevance Level: Direct Relation (Level 2)', self)
        prompt_group_layout.addWidget(self.level_label)

        self.prompt_label = QLabel('The Used Prompt: ', self)
        prompt_group_layout.addWidget(self.prompt_label)

        layout.addWidget(self.prompt_group_box)

        self.custom_prompt_input = QLineEdit(self)
        self.custom_prompt_input.setPlaceholderText('Enter your custom prompt here')
        self.custom_prompt_input.setVisible(False)
        layout.addWidget(self.custom_prompt_input)

        self.time_label = QLabel('Time taken: 00:00:00', self)
        layout.addWidget(self.time_label)

        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        self.classify_btn = QPushButton('Start Classification', self)
        self.classify_btn.clicked.connect(self.toggle_classification)  # Changed to toggle function
        layout.addWidget(self.classify_btn)

        result_layout = QHBoxLayout()
        layout.addLayout(result_layout)

        self.result_list = QListWidget(self)
        result_layout.addWidget(self.result_list)

        self.copied_files_list = QListWidget(self)
        self.copied_files_list.setSelectionMode(QListWidget.NoSelection)
        result_layout.addWidget(self.copied_files_list)

        self.status_label = QLabel('Ready', self)
        layout.addWidget(self.status_label)

        self.update_prompt_display()

    def toggle_classification(self):
        if self.is_classification_running:
            self.end_classification()  # Call end classification if running
        else:
            self.start_classification()  # Start classification if not running

    def start_classification(self):
        # Create a QMessageBox with custom buttons for "Move" and "Copy"
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Copy or Move")
        msg_box.setText("Would you like to Copy the files or Move them?")
        copy_button = msg_box.addButton("Copy", QMessageBox.ActionRole)
        move_button = msg_box.addButton("Move", QMessageBox.ActionRole)
        msg_box.exec_()
        
        if msg_box.clickedButton() == copy_button:
            self.move_files = False  # Set to copy files
        elif msg_box.clickedButton() == move_button:
            self.move_files = True  # Set to move files

        self.classify_btn.setText('End Classification')  # Change button text
        self.status_label.setText("Classification started...")
        
        # Ensure that both result_list and copied_files_list are fully cleared
        self.result_list.clear() 
        self.copied_files_list.clear() 

        # Update the file extensions from the source folder
        self.update_file_extensions()

        # Reset any internal tracking for processing files to avoid conflicts
        self.copied_files = {} 
        self.processing_files = {}  # Reset the dictionary tracking processing files

        # Get selected extensions from the checkboxes
        selected_extensions = [cb.text() for cb in self.extension_checkboxes if cb.isChecked()]
        if not selected_extensions:
            QMessageBox.warning(self, "Warning", "No file extensions selected. Please select at least one.")
            self.classify_btn.setEnabled(True)
            return

        # Update classification key from input field
        self.classification_key = self.classification_key_input.text()

        # Ensure a classification key is provided
        if not self.classification_key:
            QMessageBox.warning(self, "Warning", "Please enter a classification key.")
            return

        # Start timer
        self.start_time = time.time()
        self.timer.start(1000)

        # Use custom prompt if enabled
        if self.is_using_custom_prompt:
            self.custom_prompt = self.custom_prompt_input.text()
        else:
            self.custom_prompt = None

        # Set flag indicating classification is running
        self.is_classification_running = True  

        # Start the classification thread
        self.thread = ClassificationThread(
            self.source_folder, self.destination_folder, self.classification_key, 
            self.level, self.move_files, self.selected_model, selected_extensions,
            custom_prompt=self.custom_prompt
        )
        
        # Connect signals for UI updates
        self.thread.progress_changed.connect(self.progress_bar.setValue)
        self.thread.status_message.connect(self.update_status)
        self.thread.file_copied.connect(self.update_copied_files)
        self.thread.finished.connect(self.classification_finished)
        
        # Start the thread
        self.thread.start()

    def end_classification(self):
        # Check if the thread is still running, and terminate it
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.terminate()  # Terminate the classification thread
            self.thread.wait()

        # Reset button text
        self.classify_btn.setText('Start Classification') 

        # Reset flags and progress bar
        self.is_classification_running = False 
        self.progress_bar.setValue(0) 

        # Update the status label
        self.status_label.setText("Classification ended.")

        # Clear the result_list and copied_files_list to ensure no lingering files
        self.result_list.clear()  
        self.copied_files_list.clear()

        # Refresh the file list to prepare for the next classification
        self.update_file_extensions()

    def classification_finished(self):
        self.classify_btn.setText('Start Classification')  # Reset button text
        self.is_classification_running = False  # Reset flag
        self.status_label.setText("Classification completed.")
        self.timer.stop()
        elapsed_time = time.time() - self.start_time
        formatted_time = time.strftime('%H:%M:%S', time.gmtime(elapsed_time))
        self.time_label.setText(f'Time taken: {formatted_time}')

    def toggle_prompt_mode(self):
        if self.is_using_custom_prompt:
            self.custom_prompt_btn.setText('Use Custom Prompt')
            self.custom_prompt_input.setVisible(False)
            self.custom_prompt_input.clear()
            self.prompt_group_box.setVisible(True)
            self.classification_key_input.setVisible(True)
            self.is_using_custom_prompt = False
        else:
            self.custom_prompt_btn.setText('Use Predefined Prompt')
            self.custom_prompt_input.setVisible(True)
            self.prompt_group_box.setVisible(False)
            self.classification_key_input.setVisible(False)
            self.is_using_custom_prompt = True

    def select_source(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            self.source_folder = folder
            self.source_path_label.setText(f"Selected Source: {folder}")
            self.status_label.setText(f"Source: {folder}")
            self.update_file_extensions()

    def select_destination(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.destination_folder = folder
            self.dest_path_label.setText(f"Selected Destination: {folder}")
            self.status_label.setText(f"Destination: {folder}")

    def update_file_extensions(self):
        self.file_extensions = set()
        for file in os.listdir(self.source_folder):
            ext = os.path.splitext(file)[1].lower()
            if ext and ext not in self.system_extensions:
                self.file_extensions.add(ext)

        for checkbox in self.extension_checkboxes:
            self.extension_layout.removeWidget(checkbox)
            checkbox.deleteLater()
        self.extension_checkboxes.clear()

        for ext in sorted(self.file_extensions):
            checkbox = QCheckBox(ext)
            checkbox.setChecked(True)
            self.extension_checkboxes.append(checkbox)
            self.extension_layout.addWidget(checkbox)

    def update_status(self, message):
        file_name = message.split(": ")[-1]
        self.add_processing_file(file_name, message)

    def add_processing_file(self, file_name, status_message):
        already_added = file_name in self.copied_files
        item_widget = ProcessingItemWidget(status_message, show_add_button=not already_added)
        list_item = QListWidgetItem()
        list_item.setSizeHint(item_widget.sizeHint())
        
        self.result_list.addItem(list_item)
        self.result_list.setItemWidget(list_item, item_widget)
        item_widget.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        if not already_added:
            item_widget.add_button.clicked.connect(lambda: self.manual_add_to_destination(file_name, list_item))

    def manual_add_to_destination(self, file_name, list_item):
        source_path = os.path.join(self.source_folder, file_name)
        dest_path = os.path.join(self.destination_folder, file_name)

        if self.move_files:
            shutil.move(source_path, dest_path)
            action = 'moved'
        else:
            shutil.copy(source_path, dest_path)
            action = 'copied'

        self.update_copied_files(file_name, action)
        self.result_list.takeItem(self.result_list.row(list_item))

    def update_copied_files(self, file_name, action):
        item_widget = FileItemWidget(file_name)
        list_item = QListWidgetItem(self.copied_files_list)
        list_item.setSizeHint(item_widget.sizeHint())
        self.copied_files_list.addItem(list_item)
        self.copied_files_list.setItemWidget(list_item, item_widget)

        item_widget.undo_button.clicked.connect(lambda: self.undo_action(file_name, list_item))
        item_widget.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        source_path = os.path.join(self.source_folder, file_name)
        dest_path = os.path.join(self.destination_folder, file_name)
        self.copied_files[file_name] = {
            'source': source_path,
            'destination': dest_path,
            'action': action
        }

    def undo_action(self, file_name, list_item):
        file_info = self.copied_files.get(file_name)
        if not file_info:
            return

        if file_info['action'] == 'moved':
            try:
                shutil.move(file_info['destination'], file_info['source'])
                self.status_label.setText(f"Moved {file_name} back to source folder.")
            except Exception as e:
                self.status_label.setText(f"Error moving {file_name} back: {str(e)}")
        elif file_info['action'] == 'copied':
            try:
                os.remove(file_info['destination'])
                self.status_label.setText(f"Removed {file_name} from destination folder.")
            except Exception as e:
                self.status_label.setText(f"Error removing {file_name}: {str(e)}")

        self.copied_files_list.takeItem(self.copied_files_list.row(list_item))
        del self.copied_files[file_name]

    def update_time(self):
        if self.start_time:
            elapsed_time = time.time() - self.start_time
            formatted_time = time.strftime('%H:%M:%S', time.gmtime(elapsed_time))
            self.time_label.setText(f'Time taken: {formatted_time}')

    def get_available_models(self):
        try:
            response = requests.get('http://localhost:11434/api/tags')
            if response.status_code == 200:
                models = json.loads(response.text)['models']
                return [model['name'] for model in models]
            else:
                return ["Error: Unable to fetch models"]
        except requests.exceptions.RequestException:
            return ["Error: Cannot connect to Ollama"]

    def update_selected_model(self, model):
        self.selected_model = model

    def update_level_label(self, value):
        level_dict = {
            0: "Anything could be considered (Level 0)",
            1: "Loose Association (Level 1)",
            2: "Loosely Associated (Level 2)",
            3: "Partial or Tangential Relation (Level 3)",
            4: "Somewhat Related (Level 4)",  # New level
            5: "Can be Categorized (Level 5)",
            6: "Direct Connection (Level 6)",
            7: "Strong Relation (Level 7)",
            8: "Exact Match (Level 8)"
        }
        self.level_label.setText(f'Relevance Level: {level_dict[value]}')
        self.level = value
        self.update_prompt_display()

    def update_prompt_display(self):
        classification_key = self.classification_key_input.text()
        if not classification_key:
            classification_key = "{The Inputted classification key}"
        
        # If no file name has been processed yet, use a placeholder
        file_name_without_extension = "File Name"

        level_prompts = {
            0: f"Could '{file_name_without_extension}' be considered related to '{classification_key}'? Consider even weak or indirect connections.",
            1: f"Could '{file_name_without_extension}' be loosely associated with the concept or category of '{classification_key}'? Consider even indirect or weak associations.",
            2: f"Could '{file_name_without_extension}' be loosely associated with the concept or category of '{classification_key}'?",
            3: f"Would you say that '{file_name_without_extension}' is somewhat related to the concept or category of '{classification_key}'? This includes partial or tangential relationships.",
            4: f"Would you say that '{file_name_without_extension}' is somewhat related to the concept or category of '{classification_key}'?",  # New prompt for level 4
            5: f"Can '{file_name_without_extension}' be categorized as '{classification_key}'? Focus on whether this fits under that category.",
            6: f"Does '{file_name_without_extension}' have a clear and direct connection to the concept or category of '{classification_key}'? Focus on explicit and obvious relationships.",
            7: f"Is '{file_name_without_extension}' strongly related to the concept or category of '{classification_key}'? This should be a significant and apparent connection.",
            8: f"Does '{file_name_without_extension}' specifically and explicitly represent the concept or category of '{classification_key}'?"
        }

        selected_prompt = level_prompts[self.level_slider.value()]
        self.prompt_label.setText(f"The Used Prompt: {selected_prompt}")

if __name__ == '__main__':
    print("Starting application...")
    app = QApplication(sys.argv)
    ex = ImageClassifierApp()
    ex.show()
    print("Application running...")
    sys.exit(app.exec_())
