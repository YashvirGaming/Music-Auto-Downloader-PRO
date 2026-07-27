DARK_NEON_STYLE = """
QMainWindow {
    background-color: #0F1117;
}
QWidget {
    background-color: #0F1117;
    color: #E0E6ED;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #1E2330;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 12px;
    font-weight: bold;
    color: #00e5ff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
}
QListWidget, QTextEdit {
    background-color: #161922;
    border: 1px solid #232838;
    border-radius: 6px;
    padding: 6px;
    color: #E0E6ED;
}
QLineEdit {
    background-color: #161922;
    border: 1px solid #232838;
    border-radius: 6px;
    padding: 6px;
    color: #E0E6ED;
}
QLineEdit:focus {
    border: 1px solid #00e5ff;
}
QPushButton {
    background-color: #1E2330;
    border: 1px solid #2D3448;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: bold;
    color: #E0E6ED;
}
QPushButton:hover {
    background-color: #2D3448;
    border: 1px solid #00e5ff;
}
QPushButton#btnStart {
    background-color: #00c853;
    color: #000000;
    border: none;
}
QPushButton#btnStart:hover {
    background-color: #69f0ae;
}
QPushButton#btnStop {
    background-color: #d50000;
    color: #ffffff;
    border: none;
}
QPushButton#btnStop:hover {
    background-color: #ff5252;
}
QCheckBox, QRadioButton {
    spacing: 8px;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
}
QProgressBar {
    border: 1px solid #232838;
    border-radius: 6px;
    text-align: center;
    background-color: #161922;
    color: #FFFFFF;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: #00e5ff;
    border-radius: 5px;
}
"""