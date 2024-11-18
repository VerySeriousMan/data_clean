# -*- coding: utf-8 -*-
"""
Project Name: data_clean
File Created: 2023.09.14
Author: ZhangYuetao
File Name: main.py
last update： 2024.11.18
"""

import os.path
import shutil
import subprocess
import sys
import time

from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QInputDialog, QToolTip, QMessageBox
from PyQt5.QtGui import QPixmap, QCursor
from PyQt5.QtCore import QEvent
import qt_material

from CleanWindow import Ui_MainWindow
from DialogMain import InputDialog
from utils import get_image_files, read_json, write_json
import server_connect


class MainWindow(QMainWindow, Ui_MainWindow):
    MIN_PIC_SIZE = 100  # 图像最小值
    AT_LEAST_MAX_PIC_SIZE = 500  # 图像至少的最大值

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon("xey.ico"))
        self.setWindowTitle("数据清洗软件V4.3")

        self.index = 0  # 当前显示的图片索引
        self.dir_path = ''  # 图片文件夹路径
        self.image_files = []  # 图片文件列表
        self.save_path = ''  # 保存图片的路径
        self.redo_paths = []  # 撤销操作的路径栈
        self.pic_ve = MainWindow.MIN_PIC_SIZE  # 图片显示的垂直尺寸
        self.pic_ho = MainWindow.MIN_PIC_SIZE  # 图片显示的水平尺寸
        self.classes = {}  # 分类按钮与文件名的映射
        self.classify_button_json_path = r'settings/classify_button.json'  # json文件路径，用于保存分类按钮信息
        self.current_classes = None  # 当前选中的分类
        self.current_software_path = self.get_file_path()
        self.current_software_version = server_connect.get_current_software_version(self.current_software_path)

        self.insert_button_window = None  # 插入按钮窗口
        self.is_insert_button_window_open = False  # 标志 InputDialog 是否已打开

        self.open_pushButton.clicked.connect(self.open_files)
        self.prev_pushButton.clicked.connect(self.show_prev_image)
        self.next_pushButton.clicked.connect(self.show_next_image)
        self.redo_pushButton.clicked.connect(self.redo_process)
        self.save_pushButton.clicked.connect(self.get_save_path)
        self.insert_pushButton.clicked.connect(self.open_insert_button_dialog)
        self.delete_pushButton.clicked.connect(self.delete_classes)
        self.software_update_action.triggered.connect(self.update_software)

        # 添加listWidget双击事件，用于重命名分类
        self.classify_buttons_listWidget.itemDoubleClicked.connect(self.rename_class)
        # 安装事件过滤器，用于显示工具提示
        self.classify_buttons_listWidget.viewport().installEventFilter(self)

        self.control_enabled(False)
        self.save_pushButton.setEnabled(False)
        self.info_label.setText('请导入需要清洗的文件夹')
        self.setup_sliders()  # 初始化滑块
        self.load_classes()  # 加载分类信息
        self.auto_update()
        self.init_update()

    def init_update(self):
        dir_path = os.path.dirname(self.current_software_path)
        dir_name = os.path.basename(dir_path)
        if dir_name == 'temp':
            old_dir_path = os.path.dirname(dir_path)
            for file in os.listdir(old_dir_path):
                if file.endswith('.exe'):
                    old_software = os.path.join(old_dir_path, file)
                    os.remove(old_software)
            shutil.copy2(self.current_software_path, old_dir_path)
            new_file_path = os.path.join(old_dir_path, os.path.basename(self.current_software_path))
            if os.path.exists(new_file_path) and server_connect.is_file_complete(new_file_path):
                msg_box = QMessageBox(self)  # 创建一个新的 QMessageBox 对象
                reply = msg_box.question(self, '更新完成', '软件更新完成，需要立即重启吗？',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                msg_box.raise_()  # 确保弹窗显示在最上层

                if reply == QMessageBox.Yes:
                    subprocess.Popen(new_file_path)
                    time.sleep(1)
                    sys.exit("程序已退出")
                else:
                    sys.exit("程序已退出")
        else:
            is_updated = 0
            for file in os.listdir(dir_path):
                if file == 'temp':
                    is_updated = 1
                    shutil.rmtree(file)
            if is_updated == 1:
                try:
                    text = server_connect.get_update_log('数据清洗软件')
                    QMessageBox.information(self, '更新成功', f'更新成功！\n{text}')
                except Exception as e:
                    QMessageBox.critical(self, '更新成功', f'日志加载失败: {str(e)}')

    @staticmethod
    def get_file_path():
        # 检查是否是打包后的程序
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包后的路径
            current_path = os.path.abspath(sys.argv[0])
        else:
            # 非打包情况下的路径
            current_path = os.path.abspath(__file__)
        return current_path

    def auto_update(self):
        dir_path = os.path.dirname(self.current_software_path)
        dir_name = os.path.basename(dir_path)
        if dir_name != 'temp':
            if server_connect.check_version(self.current_software_version) == 1:
                self.update_software()

    def update_software(self):
        update_way = server_connect.check_version(self.current_software_version)
        if update_way == -1:
            # 网络未连接，弹出提示框
            QMessageBox.warning(self, '更新提示', '网络未连接，暂时无法更新')
        elif update_way == 0:
            # 当前已为最新版本，弹出提示框
            QMessageBox.information(self, '更新提示', '当前已为最新版本')
        else:
            # 弹出提示框，询问是否立即更新
            msg_box = QMessageBox(self)  # 创建一个新的 QMessageBox 对象
            reply = msg_box.question(self, '更新提示', '发现新版本，开始更新吗？',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            msg_box.raise_()  # 确保弹窗显示在最上层

            if reply == QMessageBox.Yes:
                try:
                    server_connect.update_software(os.path.dirname(self.current_software_path), '数据清洗软件')
                    text = server_connect.get_update_log('数据清洗软件')
                    QMessageBox.information(self, '更新成功', f'更新成功！\n{text}')
                except Exception as e:
                    QMessageBox.critical(self, '更新失败', f'更新失败: {str(e)}')
            else:
                pass

    def setup_sliders(self):
        """初始化滑块设置"""
        self.image_size_verticalSlider.setMaximum(max(self.image_label.height(), MainWindow.AT_LEAST_MAX_PIC_SIZE))
        self.image_size_verticalSlider.setMinimum(MainWindow.MIN_PIC_SIZE)
        self.image_size_horizontalSlider.setMaximum(max(self.image_label.width(), MainWindow.AT_LEAST_MAX_PIC_SIZE))
        self.image_size_horizontalSlider.setMinimum(MainWindow.MIN_PIC_SIZE)
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
        """打开文件夹对话框以选择图像文件夹，并加载图像文件"""
        try:
            dir_path = QFileDialog.getExistingDirectory(self)
            if dir_path:
                self.dir_path = dir_path
                self.image_files = get_image_files(dir_path)
                if self.image_files:
                    self.save_pushButton.setEnabled(True)
                    self.info_label.setText('已导入文件夹，请设置保存地址')
                    self.index = 0
                    self.get_max_fit_size()
                    self.show_image()  # 显示第一张图片
                else:
                    self.info_label.setText('文件夹中不存在图片，请重新导入新的文件夹')
        except Exception as e:
            self.info_label.setText(f"打开文件时出错: {e}")

    def get_save_path(self):
        """打开文件夹对话框以选择保存路径，并启用相关控件"""
        save_path = QFileDialog.getExistingDirectory(self)
        if save_path:
            self.save_path = save_path
            self.control_enabled(True)
            self.info_label.setText('设置成功！请在左侧配置分类类别快捷键与文件名')

    def show_prev_image(self):
        if self.index > 0:
            self.index -= 1
            self.get_max_fit_size()
            self.show_image()
            self.info_label.clear()

    def show_next_image(self):
        if self.index < len(self.image_files) - 1:
            self.index += 1
            self.get_max_fit_size()
            self.show_image()
            self.info_label.clear()

    def show_image(self):
        image_path = self.image_files[self.index]
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.info_label.setText(f"图像{image_path}加载错误")
        else:
            scaled_pixmap = pixmap.scaled(self.pic_ho, self.pic_ve)
            self.image_label.setPixmap(scaled_pixmap)
            self.show_current_nums()

    def get_max_fit_size(self):
        """获取当前图片的最大适应尺寸"""
        image_path = self.image_files[self.index]
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.info_label.setText(f"图像{image_path}打开错误")
        else:
            # 根据图像尺寸计算比例因子
            width, height = pixmap.width(), pixmap.height()
            height_value = self.image_label.height() / height
            width_value = self.image_label.width() / width
            scale_factor = min(height_value, width_value)

            self.pic_ho = int(width * scale_factor)
            self.pic_ve = int(height * scale_factor)

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

            last_path = os.path.join(need_path, os.path.basename(image_path))
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
        """根据滑块类型更新滑块的最大值并显示图片"""
        if self.nums_label.text():
            if slider_type == 'vertical':
                self.image_size_verticalSlider.setMaximum(max(self.image_label.height(), MainWindow.AT_LEAST_MAX_PIC_SIZE))
                self.pic_ve = self.image_size_verticalSlider.value()
            elif slider_type == 'horizontal':
                self.image_size_horizontalSlider.setMaximum(max(self.image_label.width(), MainWindow.AT_LEAST_MAX_PIC_SIZE))
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
        """双击重命名选中项"""
        class_name = item.text()
        if class_name in self.classes:
            new_name, ok = QInputDialog.getText(self, "重命名类别", "新类别名:", text=class_name)
            if ok and new_name:
                self.classes[new_name] = self.classes.pop(class_name)
                self.save_classes()
                self.load_classes()

    def eventFilter(self, source, event):
        """事件过滤器，用于显示工具提示"""
        if event.type() == QEvent.ToolTip and source is self.classify_buttons_listWidget.viewport():
            item = self.classify_buttons_listWidget.itemAt(event.pos())
            if item:
                class_name = item.text()
                if class_name in self.classes:
                    class_info = self.classes[class_name]
                    QToolTip.showText(QCursor.pos(), f"类别: {class_name}\n信息: {class_info}")
            return True
        return super(MainWindow, self).eventFilter(source, event)

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
    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)  # 自动适配不同分辨率的显示器
    QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)  # 确保图片也进行高DPI缩放
    app = QApplication(sys.argv)
    myWin = MainWindow()
    qt_material.apply_stylesheet(app, theme='default')
    myWin.show()
    sys.exit(app.exec_())
