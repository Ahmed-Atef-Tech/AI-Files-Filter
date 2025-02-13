**AI File Sorter Application**  
Version 1.0.0

This is a desktop application developed in Python using PyQt5 for the GUI. The AI File Sorter application is designed to automate the classification of image files based on user-defined categories. It uses AI-based classification models powered by **Ollama**, running on a local server, for flexible sorting. The application allows you to either copy or move files to different destination folders, making it ideal for users managing large collections of files efficiently.

### Key Features:

- **Interactive UI**: Built with PyQt5, the application offers an intuitive and easy-to-use interface for seamless file sorting.
- **Classification and Sorting**:
  - Users can select a source folder, a destination folder, and specify classification keys.
  - The classification is powered by Ollama's models running on a local server (`mistral:latest` or other available models).
  - Users can adjust relevance levels for classification, ranging from loose associations to strong, exact matches.
  - Supports a customizable prompt for more specific classification requirements.
- **AI-Based Decision Making with Ollama**: Utilizes Ollama's API to decide whether an image matches a given category based on the AI model's response. You can also choose the relevance level for more control over the classification.
- **Custom Prompt Support**: Users have the option to use predefined prompts or enter a custom prompt to enhance file classification.
- **Flexible File Handling**: 
  - Users can either copy or move files, with the application automatically renaming duplicate files to avoid conflicts.
  - Undo support is available to reverse the file operations (move or copy) if necessary.
- **Progress and Status Updates**: Real-time progress bars, status messages, and timers allow users to monitor the entire classification and sorting process.

### How It Works:
![image](https://github.com/user-attachments/assets/856e1bcf-6573-49c1-8df0-5335bad42acc)

1. **Select Folders**: Users select a source folder (containing files to classify) and a destination folder (for classified files).
2. **Define Classification Parameters**:
   - Enter a classification key to categorize files.
   - Select an AI model from Ollama (running locally).
   - Choose a relevance level to set how strictly the classifier associates files with the classification key.
   - Use predefined or custom prompts for classification.
3. **File Handling**:
   - Start the classification process to either copy or move files.
   - A progress bar shows the classification status.
   - You can manually add files to the destination list if desired.
   - Undo any file movements if needed.

### Getting Started:

- **Requirements**:
  - Python 3.7+
  - PyQt5
  - Requests library for making HTTP calls to the Ollama local server

- **Running the Application**:
  - Make sure the classification server (Ollama) is running at `localhost:11434`.
  - Run the script using Python:
    ```bash
    python AI_File_Sorter.py
    ```
  - Follow the prompts in the UI to select folders, set classification parameters, and start sorting files.

### About Page:

- Includes an 'About' button that opens an external `.exe` file, providing more information about the application. This executable must be present in the specified path.

### Notes:

- The application includes handling for file duplicates by renaming them if a file with the same name exists at the destination.
- Error handling is implemented for failed server requests or classification issues, providing real-time feedback to the user.

**Disclaimer**: This tool is designed for personal use and productivity enhancements in managing local file collections.

### License

Feel free to use, modify, and distribute this application for non-commercial purposes.


