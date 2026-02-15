import sys
from pathlib import Path
import requests
from PySide6.QtWidgets import QGridLayout
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QMessageBox, QSizePolicy
)
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QPushButton

APP_TITLE = "Chocolate Engraving Kiosk"
LOGO_FILENAME = "logo.png"


def sanitize_for_job(text: str) -> str:
    t = " ".join(text.strip().split())
    return t[:20]


class KioskWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(APP_TITLE)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.shift_on = False
        self._build_ui()
        self._apply_styles()

        QTimer.singleShot(0, self.launch_on_second_monitor)

    def launch_on_second_monitor(self):
        screens = QApplication.screens()

        if len(screens) > 1:
            target_screen = screens[1]
        else:
            target_screen = screens[0]

        geometry = target_screen.geometry()
        self.setGeometry(geometry)
        self.move(geometry.topLeft())
        self.showFullScreen()


    def _build_ui(self):
        root = QVBoxLayout()
        root.setContentsMargins(80, 40, 80, 40)
        root.setSpacing(18)

        self.logo_label = QLabel(alignment=Qt.AlignCenter)
        self._load_logo()

        self.title_label = QLabel("Enter your name or a short message", alignment=Qt.AlignCenter)
        self.title_label.setObjectName("title")

        self.input = QLineEdit()
        self.input.setPlaceholderText("Max 20 characters")
        self.input.setMaxLength(20)
        self.input.setAlignment(Qt.AlignCenter)
        self.input.setClearButtonEnabled(True)

        kb_container = QWidget()
        kb_container.setObjectName("kbContainer")
        kb_layout = self._build_keyboard()
        kb_container.setLayout(kb_layout)
        kb_container.setMaximumHeight(300)

        actions = QHBoxLayout()
        actions.setSpacing(16)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("actionSecondary")
        self.clear_btn.clicked.connect(self.on_clear)

        self.submit_btn = QPushButton("Engrave")
        self.submit_btn.setObjectName("actionPrimary")
        self.submit_btn.clicked.connect(self.on_submit)

        actions.addWidget(self.clear_btn, 1)
        actions.addWidget(self.submit_btn, 2)

        root.addStretch(3)

        root.addWidget(self.logo_label)

        root.addStretch(1)

        root.addWidget(self.title_label)
        root.addWidget(self.input)

        root.addWidget(kb_container)
        root.addLayout(actions)

        root.addStretch(2)

        self.setLayout(root)


    def _build_keyboard(self):
        KEY_H = 56
        KEY_W = 70
        SMALL_W = 90
        SPACE_W = 360
        GAP = 10

        def make_key(label, handler, obj="key", w=KEY_W, h=KEY_H):
            b = QPushButton(label)
            b.setObjectName(obj)
            b.setFixedSize(w, h)
            b.clicked.connect(handler)
            return b

        def make_row(keys, left_offset_px=0):
            row = QHBoxLayout()
            row.setSpacing(GAP)
            row.setContentsMargins(0, 0, 0, 0)

            if left_offset_px > 0:
                row.addSpacing(left_offset_px)

            for btn in keys:
                row.addWidget(btn)

            row.addStretch(1)
            return row

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(GAP)
        
        back = make_key("⌫", self.backspace, obj="keySmall", w=SMALL_W)
        row1_buttons = [
            make_key(ch, lambda _=False, x=ch: self.on_key(x))
            for ch in "QWERTYUIOP"
        ] + [back]
        layout.addLayout(make_row(row1_buttons, left_offset_px=0))

        row2_buttons = [
            make_key(ch, lambda _=False, x=ch: self.on_key(x))
            for ch in "ASDFGHJKL"
        ]
        layout.addLayout(make_row(row2_buttons, left_offset_px=KEY_W // 2))

        self.shift_btn = make_key("Shift", self.toggle_shift, obj="keySmall", w=SMALL_W)
        

        row3_buttons = [self.shift_btn] + [
            make_key(ch, lambda _=False, x=ch: self.on_key(x))
            for ch in "ZXCVBNM"
        ]
        layout.addLayout(make_row(row3_buttons, left_offset_px=int(KEY_W * 0.9)))

        space = make_key("Space", lambda: self.on_key(" "), obj="keySpace", w=SPACE_W)
        layout.addLayout(make_row([space], left_offset_px=int(KEY_W * 3.5)))

        return layout


    def on_key(self, key: str):
        cursor_pos = self.input.cursorPosition()
        current = self.input.text()

        if len(current) >= self.input.maxLength() and key != " ":
            return
        if len(current) >= self.input.maxLength() and key == " ":
            return

        if len(key) == 1 and key.isalpha():
            to_add = key.upper() if self.shift_on else key.lower()
            if self.shift_on:
                self.shift_on = False
                self._refresh_shift_style()
        else:
            to_add = key

        new_text = current[:cursor_pos] + to_add + current[cursor_pos:]
        self.input.setText(new_text[: self.input.maxLength()])
        self.input.setCursorPosition(min(cursor_pos + len(to_add), self.input.maxLength()))
        self.input.setFocus()

    def backspace(self):
        cursor_pos = self.input.cursorPosition()
        if cursor_pos <= 0:
            return
        current = self.input.text()
        new_text = current[:cursor_pos - 1] + current[cursor_pos:]
        self.input.setText(new_text)
        self.input.setCursorPosition(cursor_pos - 1)
        self.input.setFocus()

    def toggle_shift(self):
        self.shift_on = not self.shift_on
        self._refresh_shift_style()
        self.input.setFocus()

    def _refresh_shift_style(self):
        self.shift_btn.setProperty("shiftOn", self.shift_on)
        self.shift_btn.style().unpolish(self.shift_btn)
        self.shift_btn.style().polish(self.shift_btn)
        self.shift_btn.update()

    def _load_logo(self):
        logo_path = Path(__file__).resolve().parent / LOGO_FILENAME
        if logo_path.exists():
            pix = QPixmap(str(logo_path))
            self._logo_pix = pix
            self._update_logo_scale()
        else:
            self._logo_pix = None
            self.logo_label.setText("LOGO")

    def _update_logo_scale(self):
        if not self._logo_pix:
            return

        target_h = int(self.height() * 0.18)

        if target_h < 180:
            target_h = 180

        scaled = self._logo_pix.scaledToHeight(
            target_h,
            Qt.SmoothTransformation
        )

        self.logo_label.setPixmap(scaled)


    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_logo_scale()

    def _apply_styles(self):
        self.setFont(QFont("Segoe UI", 18))
        self.setStyleSheet("""
            QWidget { background: #ffffff; color: #111111; }

            QLabel#title { font-size: 30px; font-weight: 700; }

            QLineEdit {
                font-size: 34px;
                padding: 18px;
                border-radius: 16px;
                border: 2px solid #d0d0d0;
                background: #f6f6f6;
            }
            QLineEdit:focus { border: 2px solid #111111; background: #ffffff; }

            /* Keyboard container (optional subtle separation) */
            QWidget#kbContainer {
                background: transparent;
            }

            QPushButton#key {
                font-size: 20px;
                border-radius: 14px;
                background: #f0f0f0;
                border: 1px solid #d6d6d6;
            }
            QPushButton#key:pressed { background: #e2e2e2; }

            QPushButton#keySmall {
                font-size: 18px;
                border-radius: 14px;
                background: #e9e9e9;
                border: 1px solid #d0d0d0;
            }
            QPushButton#keySmall:pressed { background: #dbdbdb; }

            QPushButton#keySmall[shiftOn="true"] {
                background: #111111;
                color: #ffffff;
                border: 1px solid #111111;
            }

            QPushButton#keySpace {
                font-size: 18px;
                border-radius: 14px;
                background: #f0f0f0;
                border: 1px solid #d6d6d6;
            }

            QPushButton#actionPrimary {
                font-size: 26px;
                padding: 22px;
                border-radius: 16px;
                background: #111111;
                color: #ffffff;
                font-weight: 800;
                border: none;
            }
            QPushButton#actionPrimary:pressed { background: #333333; }

            QPushButton#actionSecondary {
                font-size: 26px;
                padding: 22px;
                border-radius: 16px;
                background: #dddddd;
                color: #111111;
                border: none;
            }
            QPushButton#actionSecondary:pressed { background: #bbbbbb; }
        """)


    def on_clear(self):
        self.input.clear()
        self.input.setFocus()

    def on_submit(self):
        raw = self.input.text()
        text = sanitize_for_job(raw)

        if not text:
            QMessageBox.information(self, "Missing text", "Please enter a name or short message.")
            self.input.setFocus()
            return

        data = {"name": text}
        try:
            r = requests.post("http://192.168.1.2:6767", data=data, timeout=5)
            print("Status:", r.status_code)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not reach engraver:\n{e}")
            return

        self.input.clear()
        self.input.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q and (event.modifiers() & Qt.ControlModifier):
            QApplication.quit()
        super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)
    w = KioskWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
