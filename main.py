# -*- coding: utf-8 -*-
"""
Project Name: data_clean
File Created: 2023.09.14
Author: ZhangYuetao
File Name: main.py
last renew 2024.07.25
"""

import shutil
import sys
import os

from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QInputDialog, QToolTip
from PyQt5.QtGui import QPixmap, QCursor
from PyQt5.QtCore import QEvent
import qt_material
from CleanWindow import *
from DialogMain import InputDialog
from utils import get_image_files, read_json, write_json


class MyClass(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyClass, self).__init__(parent)

        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon("xey.ico"))
        self.setWindowTitle("数据清洗软件V4.2")

        self.index = 0
        self.dir_path = ''
        self.image_files = []
        self.save_path = ''
        self.redo_paths = []
        self.pic_ve = 100
        self.pic_ho = 100
        self.classes = {}
        self.classify_button_json_path = r'classify_button.json'  # json文件路径
        self.current_classes = None

        self.insert_button_window = None
        self.is_insert_button_window_open = False  # 标志 InputDialog 是否已打开

        self.open_pushButton.clicked.connect(self.open_files)
        self.prev_pushButton.clicked.connect(self.show_prev_image)
        self.next_pushButton.clicked.connect(self.show_next_image)
        self.redo_pushButton.clicked.connect(self.redo_process)
        self.save_pushButton.clicked.connect(self.get_save_path)
        self.insert_pushButton.clicked.connect(self.open_insert_button_dialog)
        self.delete_pushButton.clicked.connect(self.delete_classes)

        # 添加listWidget双击事件
        self.classify_buttons_listWidget.itemDoubleClicked.connect(self.rename_class)
        # 安装事件过滤器
        self.classify_buttons_listWidget.viewport().installEventFilter(self)

        self.control_enabled(False)
        self.save_pushButton.setEnabled(False)
        self.info_label.setText('请导入需要清洗的文件夹')
        self.setup_sliders()
        self.load_classes()

    def setup_sliders(self):
        """初始化滑块设置"""
        self.image_size_verticalSlider.setMaximum(max(self.image_label.height(), 500))
        self.image_size_verticalSlider.setMinimum(100)
        self.image_size_horizontalSlider.setMaximum(max(self.image_label.width(), 500))
        self.image_size_horizontalSlider.setMinimum(100)
        self.image_size_verticalSlider.sliderMoved.connect(lambda: self.change_slider_max_value('vertical'))
        self.image_size_horizontalSlider.sliderMoved.connect(lambda: self.change_slider_max_value('horizontal'))

    def control_enabled(self, enabled):
        self.classify_buttons_listWidget.setEnabled(enabled)
        self.image_size_verticalSlider.setEnabled(enabled)
        self.image_size_horizontalSlider.setEnabled(enabled)
        self.delete_pushButton.setEnabled(enabled)
        self.insert_pushButton.setEnabled(enabled)
        self.next_pushButton.setEnabled(enabled)
        self.prev_pushButton.setEnabled(enabled)
        self.redo_pushButton.setEnabled(enabled)
        self.next_pushButton.setEnabled(enabled)

    def open_files(self):
        dir_path = QFileDialog.getExistingDirectory(self)
        if dir_path:
            self.dir_path = dir_path
            self.image_files = get_image_files(dir_path)
            if self.image_files:
                self.save_pushButton.setEnabled(True)
                self.info_label.setText('已导入文件夹，请设置保存地址')
                self.index = 0
                self.show_image()
            else:
                self.info_label.setText('文件夹中不存在图片，请重新导入新的文件夹')

    def get_save_path(self):
        save_path = QFileDialog.getExistingDirectory(self)
        if save_path:
            self.save_path = save_path
            self.control_enabled(True)
            self.info_label.setText('设置成功！请在左侧配置分类类别快捷键与文件名')

    def show_prev_image(self):
        if self.index > 0:
            self.index -= 1
            self.show_image()
            self.info_label.clear()

    def show_next_image(self):
        if self.index < len(self.image_files) - 1:
            self.index += 1
            self.show_image()
            self.info_label.clear()

    def show_image(self):
        image_path = self.image_files[self.index]
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.info_label.setText(f"Failed to load image: {image_path}")
        else:
            scaled_pixmap = pixmap.scaled(self.pic_ho, self.pic_ve)
            self.image_label.setPixmap(scaled_pixmap)
            self.show_current_nums()

    def show_current_nums(self):
        current_nums = len(self.image_files) - self.index
        self.nums_label.setText(str(current_nums))

    def save_image(self, folder_name):
        self.info_label.clear()
        if self.image_files:
            image_path = self.image_files[self.index]
            need_path = os.path.join(self.save_path, folder_name)

            if not os.path.isdir(need_path):
                os.mkdir(need_path)

            last_path = os.path.join(need_path, image_path.split('/')[-1])
            image_dir_path = os.path.dirname(image_path)

            if os.path.exists(last_path):
                self.show_next_image()
                self.info_label.setText(f'目标地址存在同名文件{last_path}，已跳过')
                return

            shutil.move(image_path, need_path)
            self.redo_paths.append([last_path, image_dir_path])
            self.image_files.remove(image_path)

            if self.image_files:
                if self.index >= len(self.image_files) - 1:
                    self.index = len(self.image_files) - 1
                self.show_image()
                self.info_label.clear()
            else:
                self.show_current_nums()
                self.image_label.clear()
                self.info_label.setText('无剩余图片')

    def redo_process(self):
        if self.nums_label.text() != '' and self.redo_paths:
            last_path, image_dir_path = self.redo_paths.pop()
            shutil.move(last_path, image_dir_path)
            self.image_files = get_image_files(self.dir_path)
            self.show_image()
            self.info_label.setText(f'已撤回{image_dir_path}')

    def change_slider_max_value(self, slider_type):
        if self.nums_label.text():
            if slider_type == 'vertical':
                self.image_size_verticalSlider.setMaximum(max(self.image_label.height(), 500))
                self.pic_ve = self.image_size_verticalSlider.value()
            elif slider_type == 'horizontal':
                self.image_size_horizontalSlider.setMaximum(max(self.image_label.width(), 500))
                self.pic_ho = self.image_size_horizontalSlider.value()
            self.show_image()

    def load_classes(self):
        self.classify_buttons_listWidget.clear()
        self.classes = read_json(self.classify_button_json_path, {})
        self.classify_buttons_listWidget.addItems(self.classes.keys())

    def open_insert_button_dialog(self):
        if not self.is_insert_button_window_open:
            self.insert_button_window = InputDialog(parent=self)  # 传递父窗口引用
            self.insert_button_window.finished.connect(self.load_classes)
            self.insert_button_window.finished.connect(self.set_insert_button_window_closed)
            self.is_insert_button_window_open = True
            self.insert_button_window.show()

    def set_insert_button_window_closed(self):
        self.is_insert_button_window_open = False

    def delete_classes(self):
        current_classes = self.classify_buttons_listWidget.currentItem()
        if current_classes:
            classes_name = current_classes.text()
            del self.classes[classes_name]
            self.current_classes = None
            self.save_classes()
            self.load_classes()

    def save_classes(self):
        write_json(self.classify_button_json_path, self.classes)

    def rename_class(self, item):
        """重命名选中项"""
        class_name = item.text()
        if class_name in self.classes:
            new_name, ok = QInputDialog.getText(self, "重命名类别", "新类别名:", text=class_name)
            if ok and new_name:
                self.classes[new_name] = self.classes.pop(class_name)
                self.save_classes()
                self.load_classes()

    def eventFilter(self, source, event):
        if event.type() == QEvent.ToolTip and source is self.classify_buttons_listWidget.viewport():
            item = self.classify_buttons_listWidget.itemAt(event.pos())
            if item:
                class_name = item.text()
                if class_name in self.classes:
                    class_info = self.classes[class_name]
                    QToolTip.showText(QCursor.pos(), f"类别: {class_name}\n信息: {class_info}")
            return True
        return super(MyClass, self).eventFilter(source, event)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_A:
            self.show_prev_image()
        elif event.key() == QtCore.Qt.Key_D:
            self.show_next_image()
        elif event.key() == QtCore.Qt.Key_S:
            self.redo_process()
        else:
            # 遍历所有类，检查是否有匹配的快捷键
            for class_name, class_info in self.classes.items():
                if 'input_keys' in class_info:
                    shortcut = class_info['input_keys']
                    if event.text() == shortcut:
                        self.save_image(class_info['input_filename'])
                        break


if __name__ == "__main__":
    app = QApplication(sys.argv)
    qt_material.apply_stylesheet(app, theme='dark_blue.xml')
    win = MyClass()
    win.show()
    sys.exit(app.exec_())
