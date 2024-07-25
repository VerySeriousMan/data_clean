# -*- coding: utf-8 -*-
"""
Project Name: data_clean
File Created: 2024.07.22
Author: ZhangYuetao
File Name: DialogMain.py
last renew: 2024.07.22
"""

from PyQt5.QtWidgets import QDialog
from PyQt5 import QtGui, QtCore

from classify_key_dialog import Ui_Dialog
from utils import read_json, write_json


class InputDialog(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super(InputDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("新建分类类别")
        self.setWindowIcon(QtGui.QIcon("xey.ico"))

        self.name = None
        self.classify_button_json_path = r'classify_button.json'  # json文件路径

        self.buttonBox.accepted.connect(self.return_accept)
        self.buttonBox.rejected.connect(self.reject)
        self.save_pushButton.clicked.connect(self.save_input)
        self.clear_pushButton.clicked.connect(self.delete_input_line)

        self.short_key_lineEdit.setReadOnly(True)

        # 安装事件过滤器
        self.short_key_lineEdit.installEventFilter(self)

        self.parent = parent  # 保存父窗口引用

    # 处理键盘按键事件
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress:
            key = event.key()
            key_text = QtGui.QKeySequence(key).toString(QtGui.QKeySequence.NativeText)
            if key == QtCore.Qt.Key_Shift:
                key_text = 'Shift'
            elif key == QtCore.Qt.Key_Control:
                key_text = 'Ctrl'
            elif key == QtCore.Qt.Key_Alt:
                key_text = 'Alt'
            elif key == QtCore.Qt.Key_Meta:
                key_text = 'Windows'
            elif 'A' <= key_text <= 'Z':
                key_text = key_text.lower()
            if obj == self.short_key_lineEdit:
                self.short_key_lineEdit.setText(key_text)
            return True
        return super(InputDialog, self).eventFilter(obj, event)

    def delete_input_line(self):
        self.filename_lineEdit.clear()
        self.short_key_lineEdit.clear()

    def save_input(self):
        self.submit()
        self.delete_input_line()

    def submit(self):
        if not self.short_key_lineEdit.text():
            self.info_label.setText('未设置快捷键')
            return
        if not self.filename_lineEdit.text():
            self.info_label.setText('未设置分类名')
            return

        try:
            classes_data = read_json(self.classify_button_json_path, {})
            i = 1
            while f"类别_{i}" in classes_data:
                i += 1
            self.name = f"类别_{i}"
            classes_data[self.name] = {
                "input_keys": self.short_key_lineEdit.text(),
                "input_filename": self.filename_lineEdit.text()
            }
            write_json(self.classify_button_json_path, classes_data)
            self.info_label.setText(f'{self.name} 保存成功')

            if self.parent:
                self.parent.load_classes()  # 调用父窗口的load_keys方法
        except Exception as e:
            self.info_label.setText(f"保存时出错: {str(e)}")

    def return_accept(self):
        self.submit()
        super().accept()  # 调用父类的accept方法
