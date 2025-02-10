import sys
import os
import datetime
import subprocess
from PIL import Image, ImageFont, ImageDraw 
from pilmoji import Pilmoji
from tabulate import tabulate
import datetime, time
import yaml
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QLineEdit, QPushButton, QFileDialog, QMessageBox, QScrollArea,
    QStackedWidget, QSizePolicy
)
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QFont
from xml_builder import create_xml
import re


# ============================================================================
# BACKEND FUNCTIONS
# ============================================================================

LOCAL_DIRECTORY = os.getcwd()

# CONSTANTS
WORLD_WIDTH = 1777
WORLD_Y_INIT = 231
WORLD_DY = 80

WORLD_HEIGHTS = [WORLD_Y_INIT + i * WORLD_DY for i in range(5)]
WORLD_COLOR = (54,57,63,255)

PROFPIC_WIDTH = 120
PROFPIC_POSITION = (36,45)

NAME_FONT_SIZE = 50
TIME_FONT_SIZE = 30
MESSAGE_FONT_SIZE = 50
NAME_FONT_COLOR = (255,255,255)
TIME_FONT_COLOR = (180,180,180)
MESSAGE_FONT_COLOR = (220,220,220)
NAME_POSITION = (190,53)
TIME_POSITION_Y = 67
NAME_TIME_SPACING = 25
MESSAGE_X = 190
MESSAGE_Y_INIT = 130
MESSAGE_DY = 80
MESSAGE_POSITIONS = [(MESSAGE_X, MESSAGE_Y_INIT + i * MESSAGE_DY) for i in range(5)]

# Mention highlighting constants
MENTION_BG_COLOR = (61,66,113,255)  # 3c4270 with alpha
MENTION_TEXT_COLOR = (201, 205, 251)  # c9cdfb
MENTION_RADIUS = 5

# APP badge constants
APP_BADGE_HEIGHT = 45   # Increase this for a larger badge
APP_BADGE_SPACING = 16  # Space between name and badge

# Text fonts
name_font = ImageFont.truetype(rf'{LOCAL_DIRECTORY}\fonts\ggsans-Semibold.ttf', NAME_FONT_SIZE)
time_font = ImageFont.truetype(rf'{LOCAL_DIRECTORY}\fonts\ggsans-Medium.ttf', TIME_FONT_SIZE)
message_font = ImageFont.truetype(rf'{LOCAL_DIRECTORY}\fonts\ggsans-Normal.ttf', MESSAGE_FONT_SIZE)

# Load configurations from YAML
with open('details.yaml') as file:
    config = yaml.safe_load(file)

def get_app_badge():
    """Load and resize the APP badge"""
    badge = Image.open('app_button.png')
    # Calculate width to maintain aspect ratio
    aspect_ratio = badge.width / badge.height
    badge_width = int(APP_BADGE_HEIGHT * aspect_ratio)
    return badge.resize((badge_width, APP_BADGE_HEIGHT), Image.Resampling.LANCZOS)

def draw_mention(draw, position, text, font):
    """Draw a mention with background and text"""
    bbox = draw.textbbox(position, text, font=font)
    
    # Add padding to make the highlight slightly bigger
    padding = 6  # Adjust this value for the desired highlight size
    bbox = (bbox[0] - padding, bbox[1] - padding, bbox[2] + padding, bbox[3] + padding)
    
    # Draw rounded rectangle (mention highlight) around the text
    draw.rounded_rectangle(bbox, radius=MENTION_RADIUS, fill=MENTION_BG_COLOR)
    draw.text(position, text, fill=MENTION_TEXT_COLOR, font=font)

# Load different font styles
bold_font = ImageFont.truetype(rf'{LOCAL_DIRECTORY}\fonts\ggsans-Semibold.ttf', MESSAGE_FONT_SIZE)
italic_font = ImageFont.truetype(rf'{LOCAL_DIRECTORY}\fonts\ggsans-NormalItalic.ttf', MESSAGE_FONT_SIZE)
bold_italic_font = ImageFont.truetype(rf'{LOCAL_DIRECTORY}\fonts\ggsans-BoldItalic.ttf', MESSAGE_FONT_SIZE)
monospace_font = ImageFont.truetype(rf'{LOCAL_DIRECTORY}\fonts\ggsans-Normal.ttf', MESSAGE_FONT_SIZE)  # Example monospace font

# Function to apply Markdown text formatting
def render_markdown_text(draw, position, text, font):
    """Render markdown text with different styles"""
    x, y = position
    parts = re.split(r'(\*\*\*.*?\*\*\*|\*\*.*?\*\*|\*.*?\*|__.*?__|~~.*?~~|`.*?`)', text)

    for part in parts:
        if part.startswith("***") and part.endswith("***") or part.startswith("___") and part.endswith("___"):
            font_to_use = bold_italic_font
            clean_text = part[3:-3]
        elif part.startswith("**") and part.endswith("**") or part.startswith("__") and part.endswith("__"):
            font_to_use = bold_font
            clean_text = part[2:-2]
        elif part.startswith("*") and part.endswith("*") or part.startswith("_") and part.endswith("_"):
            font_to_use = italic_font
            clean_text = part[1:-1]
        elif part.startswith("~~") and part.endswith("~~"):
            font_to_use = font
            clean_text = part[2:-2]
        elif part.startswith("`") and part.endswith("`"):
            font_to_use = monospace_font
            clean_text = part[1:-1]
        else:
            font_to_use = font
            clean_text = part

        draw.text((x, y), clean_text, MESSAGE_FONT_COLOR, font=font_to_use)
        x += font_to_use.getlength(clean_text)

        # Strikethrough effect for ~~text~~
        if part.startswith("~~") and part.endswith("~~"):
            line_y = y + MESSAGE_FONT_SIZE // 2
            draw.line((x - font_to_use.getlength(clean_text), line_y, x, line_y), fill=MESSAGE_FONT_COLOR, width=3)


def generate_chat(messages, name, time, profpic_file, color, is_bot=False):
    name_text = name
    time_text = f'Today at {time} PM'
    
    # Load and prepare profile picture
    prof_pic = Image.open(profpic_file)
    prof_pic.thumbnail([sys.maxsize, PROFPIC_WIDTH], Image.Resampling.LANCZOS)
    
    # Create profile picture mask
    mask = Image.new("L", prof_pic.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse([(0, 0), (PROFPIC_WIDTH, PROFPIC_WIDTH)], fill=255)
    
    # Create template
    template = Image.new(mode='RGBA', size=(WORLD_WIDTH, WORLD_HEIGHTS[len(messages)-1]), color=WORLD_COLOR)
    template.paste(prof_pic, (36,45), mask)
    template_editable = ImageDraw.Draw(template)
    
    # Draw name
    template_editable.text(NAME_POSITION, name_text, color, font=name_font)
    
    # Calculate positions for APP badge and time
    name_width = name_font.getlength(name)
    current_x = NAME_POSITION[0] + name_width
    
    # If bot account, add APP badge
    if is_bot:
        current_x += APP_BADGE_SPACING
        app_badge = get_app_badge()
        badge_y = NAME_POSITION[1] + (NAME_FONT_SIZE - APP_BADGE_HEIGHT) // 2 + 5  # Adjusted to -8 for better centering
        template.paste(app_badge, (int(current_x), badge_y), app_badge.convert('RGBA'))
        current_x += app_badge.width
    
    # Draw time with updated position
    time_position = (current_x + NAME_TIME_SPACING, TIME_POSITION_Y)
    template_editable.text(time_position, time_text, TIME_FONT_COLOR, font=time_font)
    
    # Draw messages
    for i, message in enumerate(messages):
        with Pilmoji(template) as pilmoji:
            # Split message into parts to handle mentions
            parts = re.split(r'(@\w+)', message.strip())
            x_offset = MESSAGE_POSITIONS[i][0]
            y_offset = MESSAGE_POSITIONS[i][1]
            for part in parts:
                if part.startswith('@'):
                    draw_mention(template_editable, (x_offset, y_offset), part, message_font)
                    x_offset += message_font.getlength(part)
                else:
                    render_markdown_text(template_editable, (x_offset, y_offset), part, message_font)
                    x_offset += message_font.getlength(part)
            
    return template

def get_filename():
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    return filedialog.askopenfilename()


def save_images(lines, init_time, nums_to_skip, dt=30):
    if not os.path.exists('chat'):
        os.makedirs('chat')
    
    name_up_next = True
    current_time = init_time
    current_name = None
    current_lines = []
    msg_number = 1

    image_durations = {}
    
    for line in lines:
        if line == '':
            name_up_next = True
            current_lines = []
            continue
        
        if line[0] == '#':
            continue
        
        if name_up_next:
            current_name = line.split(':')[0]
            name_up_next = False
            continue
        
        # Handle message duplication
        message_parts = line.split('$^')
        message = message_parts[0]
        delay = float(message_parts[1].split('$')[0]) if len(message_parts) > 1 else 1.0
        duplication = int(message_parts[1].split('$x')[1]) if len(message_parts) > 1 and 'x' in message_parts[1] else 1
        
        for i in range(duplication):
            # Calculate exponential decrease with minimum duration
            adjusted_delay = delay / (2 ** i)
            adjusted_delay = max(adjusted_delay, 0.2)  # Minimum duration of 0.2 seconds
            
            current_lines.append(message)
            image = generate_chat(
                messages=current_lines,
                name=current_name,
                time=f'{current_time.hour % 12}:{current_time.minute}',
                profpic_file=f'profile_pictures/{config[current_name]["dp"]}',
                color=tuple(int(config[current_name].get("color", "FFFFFF")[i:i+2], 16) for i in (0, 2, 4)),
                is_bot=config[current_name].get("bot", False)
            )
            
            while f'{msg_number:03d}' in nums_to_skip:
                print(f'found {msg_number:03d}')
                msg_number += 1
                    
            image.save(rf'{LOCAL_DIRECTORY}\chat\{msg_number:03d}.png')
            image_durations[rf'{LOCAL_DIRECTORY}\chat\{msg_number:03d}.png'] = adjusted_delay
            
            current_time += datetime.timedelta(0,dt)
            msg_number += 1

    return image_durations

# ============================================================================
# GENERATION THREAD (Runs backend processing in the background)
# ============================================================================
class GenerationThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
    def run(self):
        try:
            with open(self.file_path, encoding="utf8") as f:
                lines = f.read().splitlines()
            current_time = datetime.datetime.now()
            nums_array = []  # No file numbers to skip in the GUI
            image_durations = save_images(lines, init_time=current_time, nums_to_skip=nums_array)
            create_xml(image_durations)
            xml_path = os.path.abspath("output.xml")
            self.finished.emit(xml_path)
        except Exception as e:
            self.error.emit(str(e))

# ============================================================================
# DRAG & DROP LABEL (Home page file drop area)
# ============================================================================
class DragDropLabel(QLabel):
    fileDropped = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        self.setText("+\nDrag and Drop a .txt File Here")
        self.setStyleSheet("border: 2px dashed #666; color: #888; font-size: 20px; padding: 20px;")
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(url.toLocalFile().lower().endswith('.txt') for url in urls):
                event.acceptProposedAction()
        else:
            event.ignore()
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.txt'):
                    self.fileDropped.emit(file_path)
                    break

# ============================================================================
# FORMAT PREVIEW TEXT (For the Home page file preview)
# ============================================================================
def format_preview_text(raw_text):
    lines = raw_text.splitlines()
    html_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            html_lines.append("<br>")
        elif stripped.startswith("#"):
            continue
        elif stripped.endswith(":"):
            name = stripped[:-1].strip()
            html_lines.append(f'<span style="font-weight:bold; color:#888888;">{name} :</span><br><br>')
        else:
            filtered = line.split('$')[0].strip()
            if filtered:
                html_lines.append(filtered + "<br>")
    return ''.join(html_lines)

# ============================================================================
# HOME PAGE (Original Textshotter functionality with added "Write Script" button)
# ============================================================================
class HomePage(QWidget):
    def __init__(self, switch_to_script_writer_callback):
        super().__init__()
        self.switch_to_script_writer_callback = switch_to_script_writer_callback
        self.current_file = None
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Heading
        heading = QLabel("Textshotter")
        heading.setAlignment(Qt.AlignCenter)
        heading.setStyleSheet("font-size: 32px; font-weight: bold;")
        layout.addWidget(heading)

        # Drag & Drop Area
        self.dragDropLabel = DragDropLabel()
        self.dragDropLabel.setFixedHeight(150)
        self.dragDropLabel.fileDropped.connect(self.fileDropped)
        layout.addWidget(self.dragDropLabel)

        # Select File and Write Script Buttons
        btnLayout = QHBoxLayout()
        self.selectFileButton = QPushButton("Select File")
        self.selectFileButton.clicked.connect(self.selectFile)
        btnLayout.addWidget(self.selectFileButton)
        self.writeScriptButton = QPushButton("Write Script")
        self.writeScriptButton.clicked.connect(self.switch_to_script_writer)
        btnLayout.addWidget(self.writeScriptButton)
        layout.addLayout(btnLayout)

        # File Information & Preview
        self.fileInfoLabel = QLabel("No file selected")
        layout.addWidget(self.fileInfoLabel)
        self.filePreview = QTextEdit()
        self.filePreview.setReadOnly(True)
        layout.addWidget(self.filePreview, stretch=1)

        # Generate Button and Status
        self.generateButton = QPushButton("Generate")
        self.generateButton.setFixedHeight(50)
        self.generateButton.setStyleSheet("border-radius: 25px; font-size: 16px;")
        self.generateButton.clicked.connect(self.generateProcess)
        layout.addWidget(self.generateButton)
        self.statusLabel = QLabel("")
        layout.addWidget(self.statusLabel)
        self.showMeButton = QPushButton("Show me")
        self.showMeButton.setVisible(False)
        self.showMeButton.clicked.connect(self.showXML)
        layout.addWidget(self.showMeButton)

        self.loadLatestScript()

    def switch_to_script_writer(self):
        self.switch_to_script_writer_callback()

    def loadLatestScript(self):
        scripts_dir = "scripts"
        if os.path.exists(scripts_dir):
            files = [os.path.join(scripts_dir, f) for f in os.listdir(scripts_dir) if f.lower().endswith('.txt')]
            if files:
                files.sort(key=os.path.getmtime, reverse=True)
                latest_file = files[0]
                self.loadFile(latest_file)

    def loadFile(self, file_path):
        self.current_file = file_path
        mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
        mod_time_str = mod_time.strftime("%Y-%m-%d %H:%M:%S")
        self.fileInfoLabel.setText(f"File: {os.path.basename(file_path)}  |  Last Modified: {mod_time_str}")
        try:
            with open(file_path, "r", encoding="utf8") as f:
                content = f.read()
            formatted_content = format_preview_text(content)
            self.filePreview.setHtml(formatted_content)
        except Exception as e:
            self.filePreview.setPlainText(f"Error loading file: {e}")

    def fileDropped(self, file_path):
        self.loadFile(file_path)

    def selectFile(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Script File", "", "Text Files (*.txt)")
        if file_path:
            self.loadFile(file_path)

    def generateProcess(self):
        if not self.current_file:
            QMessageBox.warning(self, "No File Selected", "Please select a script file first.")
            return
        self.generateButton.setEnabled(False)
        self.statusLabel.setText("Processing...")
        self.thread = GenerationThread(self.current_file)
        self.thread.finished.connect(self.generationFinished)
        self.thread.error.connect(self.generationError)
        self.thread.start()

    def generationFinished(self, xml_path):
        self.statusLabel.setText("XML file successfully created!")
        self.generated_xml_path = xml_path
        self.generateButton.setEnabled(True)
        self.showMeButton.setVisible(True)

    def generationError(self, error_msg):
        self.statusLabel.setText(f"Error: {error_msg}")
        self.generateButton.setEnabled(True)

    def showXML(self):
        if hasattr(self, 'generated_xml_path') and os.path.exists(self.generated_xml_path):
            try:
                if os.name == 'nt':
                    subprocess.run(["explorer", "/select,", self.generated_xml_path])
                elif sys.platform == "darwin":
                    subprocess.run(["open", "-R", self.generated_xml_path])
                else:
                    subprocess.run(["xdg-open", os.path.dirname(self.generated_xml_path)])
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open file explorer: {e}")
        else:
            QMessageBox.warning(self, "File Not Found", "The generated XML file was not found.")

# ============================================================================
# MESSAGE ROW WIDGET (A single message row with validators and proper sizing)
# ============================================================================
class MessageRowWidget(QWidget):
    addAfter = pyqtSignal()
    removeRow = pyqtSignal()
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Message text field
        self.msg_text = QTextEdit()
        self.msg_text.setPlaceholderText("Message")
        self.msg_text.setFixedHeight(80)
        font = QFont()
        font.setPointSize(14)
        self.msg_text.setFont(font)
        self.msg_text.setStyleSheet("background-color: #3b3b3b; color: white; padding: 5px;")
        layout.addWidget(self.msg_text, stretch=1)
        
        # Delay field with QDoubleValidator (allows numbers and decimal points)
        self.time_edit = QLineEdit()
        self.time_edit.setPlaceholderText("Delay")
        self.time_edit.setFixedWidth(100)
        self.time_edit.setStyleSheet("background-color: #3b3b3b; color: white; padding: 5px;")
        time_validator = QDoubleValidator(0.0, 9999.99, 2, self)
        self.time_edit.setValidator(time_validator)
        font_time = QFont()
        font_time.setPointSize(14)
        self.time_edit.setFont(font_time)
        layout.addWidget(self.time_edit)
        
        # Duplication field with QIntValidator (numbers only)
        self.dup_edit = QLineEdit()
        self.dup_edit.setPlaceholderText("Dup")
        self.dup_edit.setFixedWidth(70)
        self.dup_edit.setStyleSheet("background-color: #3b3b3b; color: white; padding: 5px;")
        int_validator = QIntValidator(0, 9999, self)
        self.dup_edit.setValidator(int_validator)
        font_dup = QFont()
        font_dup.setPointSize(14)
        self.dup_edit.setFont(font_dup)
        layout.addWidget(self.dup_edit)
        
        # Plus button
        plus_button = QPushButton("+")
        plus_button.setFixedSize(40, 40)
        plus_button.setStyleSheet("font-size: 16px;")
        plus_button.clicked.connect(self.addAfter.emit)
        layout.addWidget(plus_button)
        
        # Remove button
        remove_button = QPushButton("✖")
        remove_button.setFixedSize(40, 40)
        remove_button.setStyleSheet("font-size: 16px; color: red;")
        remove_button.clicked.connect(self.removeRow.emit)
        layout.addWidget(remove_button)
    
    def get_text(self):
        msg = self.msg_text.toPlainText().strip()
        if not msg:
            return ""
        line = msg
        time_val = self.time_edit.text().strip()
        dup = self.dup_edit.text().strip()
        if time_val:
            line += f"$^{time_val}"
        if dup:
            line += f"$x{dup}"
        return line

# ============================================================================
# USER BLOCK WIDGET (Contains a username field and one or more MessageRowWidgets)
# ============================================================================
class UserBlockWidget(QWidget):
    removed = pyqtSignal(QWidget)
    def __init__(self):
        super().__init__()
        self.message_rows = []
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with username field and a remove button
        header_layout = QHBoxLayout()
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Username")
        self.username_edit.setFixedWidth(200)
        font = QFont()
        font.setPointSize(16)
        self.username_edit.setFont(font)
        self.username_edit.setStyleSheet("background-color: #3b3b3b; color: white; padding: 5px;")
        header_layout.addWidget(self.username_edit)
        remove_button = QPushButton("✖")
        remove_button.setStyleSheet("color: red; font-size: 16px;")
        remove_button.clicked.connect(self.remove_self)
        header_layout.addWidget(remove_button)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Container for message rows
        self.msg_layout = QVBoxLayout()
        self.msg_layout.setSpacing(5)
        layout.addLayout(self.msg_layout)
        
        self.add_message_row()
    
    def add_message_row(self, index=None):
        msg_row = MessageRowWidget()
        msg_row.addAfter.connect(lambda: self.insert_message_row_after(msg_row))
        msg_row.removeRow.connect(lambda: self.remove_message_row(msg_row))
        if index is None:
            self.message_rows.append(msg_row)
            self.msg_layout.addWidget(msg_row)
        else:
            self.message_rows.insert(index, msg_row)
            self._refresh_message_rows()
    
    def insert_message_row_after(self, msg_row):
        index = self.message_rows.index(msg_row)
        self.add_message_row(index=index+1)
    
    def remove_message_row(self, msg_row):
        if len(self.message_rows) == 1:
            reply = QMessageBox.question(self, "Confirm", "This is the last message row. Remove it?", QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        self.message_rows.remove(msg_row)
        msg_row.setParent(None)
        msg_row.deleteLater()
        self._refresh_message_rows()
    
    def _refresh_message_rows(self):
        while self.msg_layout.count():
            item = self.msg_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        for row in self.message_rows:
            self.msg_layout.addWidget(row)
    
    def get_script_text(self):
        username = self.username_edit.text().strip()
        if not username:
            return ""
        text = username + ":\n"
        for row in self.message_rows:
            line = row.get_text().strip()
            if line:
                text += line + "\n"
        return text
    
    def remove_self(self):
        reply = QMessageBox.question(self, "Confirm", "Are you sure you want to remove this user block?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.removed.emit(self)

# ============================================================================
# SCRIPT WRITER PAGE (Now with a filename field at the top)
# ============================================================================
class ScriptWriterPage(QWidget):
    def __init__(self, switch_back_callback):
        super().__init__()
        self.switch_back_callback = switch_back_callback
        self.user_blocks = []
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Top bar with title, filename field, and Back button
        top_layout = QHBoxLayout()
        title = QLabel("Script Writer")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        top_layout.addWidget(title)
        top_layout.addStretch()
        filename_label = QLabel("Filename:")
        filename_label.setStyleSheet("font-size: 16px;")
        top_layout.addWidget(filename_label)
        self.filename_edit = QLineEdit()
        self.filename_edit.setPlaceholderText("script.txt")
        self.filename_edit.setFixedWidth(200)
        font_filename = QFont()
        font_filename.setPointSize(16)
        self.filename_edit.setFont(font_filename)
        self.filename_edit.setStyleSheet("background-color: #3b3b3b; color: white; padding: 5px;")
        top_layout.addWidget(self.filename_edit)
        back_button = QPushButton("Back")
        back_button.setStyleSheet("font-size: 16px;")
        back_button.clicked.connect(self.switch_back_callback)
        top_layout.addWidget(back_button)
        main_layout.addLayout(top_layout)
        
        # Add User Button
        add_user_button = QPushButton("+ Add User")
        add_user_button.setStyleSheet("font-size: 16px; padding: 8px;")
        add_user_button.clicked.connect(self.add_user_block)
        main_layout.addWidget(add_user_button)
        
        # Scrollable area for User Blocks
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setContentsMargins(10, 10, 10, 10)
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area, stretch=1)
        
        # Generate Script Button
        generate_button = QPushButton("Generate Script")
        generate_button.setFixedHeight(40)
        generate_button.setStyleSheet("font-size: 16px;")
        generate_button.clicked.connect(self.generate_script)
        main_layout.addWidget(generate_button)
        
        # Start with one user block
        self.add_user_block()
    
    def add_user_block(self):
        user_block = UserBlockWidget()
        user_block.removed.connect(self.remove_user_block)
        self.user_blocks.append(user_block)
        self.scroll_layout.addWidget(user_block)
    
    def remove_user_block(self, user_block):
        self.user_blocks.remove(user_block)
        user_block.setParent(None)
        user_block.deleteLater()
    
    def generate_script(self):
        script = ""
        for ub in self.user_blocks:
            block_text = ub.get_script_text()
            if block_text:
                script += block_text + "\n"
        if not script.strip():
            QMessageBox.warning(self, "Warning", "No valid script content found.")
            return
        
        # Use the filename field value as the default file name in the save dialog.
        default_filename = self.filename_edit.text().strip() or "script.txt"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Script As", default_filename, "Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(script)
                QMessageBox.information(self, "Success", "Script generated successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save the file:\n{e}")

# ============================================================================
# MAIN APPLICATION WINDOW (Uses QStackedWidget to switch between pages)
# ============================================================================
class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Textshotter")
        self.resize(1000, 800)
        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #ffffff; font-family: Arial; }
            QPushButton { background-color: #444444; border: none; border-radius: 8px; padding: 10px; }
            QPushButton:hover { background-color: #555555; }
            QTextEdit { background-color: #333333; border: 1px solid #555555; border-radius: 5px; padding: 5px; }
            QLineEdit { background-color: #333333; border: 1px solid #555555; border-radius: 5px; padding: 5px; color: white; }
            QLabel { font-size: 14px; }
        """)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.home_page = HomePage(self.switch_to_script_writer)
        self.script_writer_page = ScriptWriterPage(self.switch_to_home_page)
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.script_writer_page)
    def switch_to_script_writer(self):
        self.stack.setCurrentWidget(self.script_writer_page)
    def switch_to_home_page(self):
        self.stack.setCurrentWidget(self.home_page)

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec_())
