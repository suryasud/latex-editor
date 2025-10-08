import sys
import subprocess
import shlex

from typing import Optional
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QKeySequence, QGuiApplication, QTextCursor
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QFileDialog, QMessageBox
)

import re

DEFAULT_LATEX_TEMPLATE = r"""
\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{listings}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{enumitem}

\definecolor{gray}{rgb}{0.5,0.5,0.5}
\definecolor{lightgray}{rgb}{0.95,0.95,0.95}
\lstset{
backgroundcolor=\color{lightgray},
basicstyle=\ttfamily\footnotesize,
frame=single,
breaklines=true,
postbreak=\mbox{\textcolor{red}{$\hookrightarrow$}\space},
keywordstyle=\color{blue},
commentstyle=\color{gray},
}
\title{}

\begin{document}

\maketitle

\section{}


\end{document}
""".strip()


class LatexHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []

        # Command format (e.g., \section, \textbf)
        command_format = QTextCharFormat()
        command_format.setForeground(QColor("#006699"))
        command_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((re.compile(r'\\[a-zA-Z]+'), command_format))

        # Braces
        brace_format = QTextCharFormat()
        brace_format.setForeground(QColor("#AA4400"))
        self.highlighting_rules.append((re.compile(r'[{}]'), brace_format))

        # Math environment: $...$
        math_format = QTextCharFormat()
        math_format.setForeground(QColor("#990099"))
        self.highlighting_rules.append((re.compile(r'\$[^$]*\$'), math_format))

        # Comments: %...
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#888888"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((re.compile(r'%[^\n]*'), comment_format))

        # Environments: \begin{} and \end{}
        env_format = QTextCharFormat()
        env_format.setForeground(QColor("#007744"))
        env_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((re.compile(r'\\(begin|end)\{[^}]+\}'), env_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            for match in pattern.finditer(text):
                start, end = match.start(), match.end()
                self.setFormat(start, end - start, fmt)


class PlainTextEdit(QTextEdit):
    def insertFromMimeData(self, source):
        # Override paste to insert plain text only
        if source.hasText():
            self.insertPlainText(source.text())
        else:
            super().insertFromMimeData(source)


class MinimalLatexEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LaTeX Editor")
        self.resize(800, 600)
        self.current_file = None

        # Layouts
        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        # Editor
        self.editor = PlainTextEdit()
        self.editor.setFont(QFont("Courier", 10))
        self.editor.setPlainText(DEFAULT_LATEX_TEMPLATE)
        self.highlighter = LatexHighlighter(self.editor.document())
        main_layout.addWidget(self.editor)

        # Buttons
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.open_file)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_file)

        cmd_btn = QPushButton("Open CMD")
        cmd_btn.clicked.connect(self.open_cmd)

        compile_btn = QPushButton("Compile LaTeX")
        compile_btn.clicked.connect(self.compile_latex)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)

        for btn in (open_btn, save_btn, cmd_btn, compile_btn, close_btn):
            button_layout.addWidget(btn)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)



    def open_file(self):
        default_dir = "D:/actual_files_in_this_2/DS881 LaTeX files"
        
        file_path, _ = QFileDialog.getOpenFileName(self, caption="Open LaTeX File", 
                                                   directory=default_dir, 
                                                   filter="TeX files (*.tex);;All Files (*)")
        if file_path:
            try:
                path = Path(file_path)
                content = path.read_text(encoding="utf-8")
                self.editor.setPlainText(content)
                self.current_file = path
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open file:\n{e}")

    def save_file(self):
        if not self.current_file:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "TeX files (*.tex);;All Files (*)")
            if not file_path:
                return
            self.current_file = Path(file_path)

        try:
            self.current_file.write_text(self.editor.toPlainText(), encoding="utf-8")
            QMessageBox.information(self, "Saved", f"File saved to:\n{self.current_file}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file:\n{e}")

    
    def open_cmd(self):
        if not self.current_file:
            QMessageBox.information(self, "Info", "Open a file first to use CMD.")
            return

        folder = str(self.current_file.parent)

        try:
            if sys.platform.startswith("win"):
                subprocess.Popen(["start", "cmd"], cwd=folder, shell=True)
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", "-a", "Terminal", folder])
            else:  # Linux
                subprocess.Popen(["x-terminal-emulator"], cwd=folder)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open terminal:\n{e}")

    def compile_latex(self):
        if not self.current_file:
            QMessageBox.information(self, "Info", "No file to compile.")
            return
        try:
            subprocess.run(["tectonic", str(self.current_file)], cwd=self.current_file.parent)
            QMessageBox.information(self, "Success", "Compilation finished.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Compilation failed:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MinimalLatexEditor()
    window.show()
    sys.exit(app.exec())

