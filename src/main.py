import sys
import random
import os
import time
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPainter, QFont, QColor, QPixmap

# ====================== 基础配置（后续网页可直接修改） ======================
PET_SIZE = 360
SCREEN_MARGIN = 50
TEXT_POOL = ["喵呜~", "快来摸摸脑袋", "好无聊呀", "我一直在盯着你", "陪我散步吧！"]
CLICK_TEXT = "嘿嘿，不要戳我脑袋！"
WALK_SPEED = 1.7
ANIM_FPS = 12
# ==========================================================================

def get_resource_path():
    """【关键】兼容本地调试 + 打包exe临时目录，解决图片消失问题"""
    if hasattr(sys, '_MEIPASS'):
        base_folder = sys._MEIPASS
    else:
        base_folder = os.path.abspath(".")
    return os.path.join(base_folder, "assets", "frames")


class AnimationPlayer:
    """序列帧动画管理器：循环播放图片组"""
    def __init__(self):
        self.anim_data = {}
        self.current_anim = "idle"
        self.frame_index = 0
        self.last_refresh = time.time()
        self.frame_gap = 1 / ANIM_FPS

    def load_animation(self, anim_name, file_list):
        frame_dir = get_resource_path()
        pixmap_list = []
        for filename in file_list:
            full_path = os.path.join(frame_dir, filename)
            pix = QPixmap(full_path)
            pix = pix.scaled(PET_SIZE * 0.94, PET_SIZE * 0.94, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            pixmap_list.append(pix)
        self.anim_data[anim_name] = pixmap_list

    def switch_animation(self, anim_name):
        if anim_name == self.current_anim:
            return
        self.current_anim = anim_name
        self.frame_index = 0

    def get_current_frame(self):
        now_time = time.time()
        if now_time - self.last_refresh > self.frame_gap:
            self.frame_index += 1
            self.last_refresh = now_time
        frame_list = self.anim_data.get(self.current_anim, [])
        if not frame_list:
            return None
        self.frame_index %= len(frame_list)
        return frame_list[self.frame_index]


class CatDesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        # 窗口属性：无边框、置顶、透明背景
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(PET_SIZE, PET_SIZE)
        self.move(400, 400)

        # 初始化动画，文件名必须和你上传图片严格对应
        self.anim = AnimationPlayer()
        self.anim.load_animation("idle", ["idle_01.png", "idle_02.png", "idle_03.png"])
        self.anim.load_animation("sleep", ["sleep_01.png", "sleep_02.png"])
        self.anim.load_animation("touch", ["touch_01.png", "touch_02.png"])
        self.anim.load_animation("walk_left", ["walk_l_01.png", "walk_l_02.png", "walk_l_03.png", "walk_l_04.png"])
        self.anim.load_animation("walk_right", ["walk_r_01.png", "walk_r_02.png", "walk_r_03.png", "walk_r_04.png"])
        self.anim.switch_animation("idle")

        # 交互变量
        self.drag_enable = False
        self.drag_offset = QPoint()
        self.show_bubble = False
        self.bubble_text = ""
        self.is_walking = False
        self.walk_dir = random.choice([-1, 1])

        # 定时器
        self.render_timer = QTimer()
        self.render_timer.timeout.connect(self.update_scene)
        self.render_timer.start(int(1000 / ANIM_FPS))

        self.ai_timer = QTimer()
        self.ai_timer.timeout.connect(self.ai_auto_behavior)
        self.ai_timer.start(4200)

    def ai_auto_behavior(self):
        """AI自动行为：随机走路、发呆、睡觉、说话"""
        rand_val = random.random()
        if rand_val < 0.35:
            self.is_walking = True
            self.walk_dir = random.choice([-1, 1])
            if self.walk_dir > 0:
                self.anim.switch_animation("walk_right")
            else:
                self.anim.switch_animation("walk_left")
            # 随机走路时长
            QTimer.singleShot(random.randint(2200, 5800), self.stop_walking)
        elif rand_val < 0.62:
            self.anim.switch_animation("idle")
            if random.random() > 0.5:
                self.pop_bubble(random.choice(TEXT_POOL))
        else:
            self.anim.switch_animation("sleep")

    def stop_walking(self):
        self.is_walking = False
        self.anim.switch_animation("idle")

    def pop_bubble(self, text):
        self.show_bubble = True
        self.bubble_text = text
        QTimer.singleShot(2200, lambda: setattr(self, "show_bubble", False))

    def update_scene(self):
        # 自动行走逻辑，碰到屏幕边缘自动掉头
        if self.is_walking:
            screen_rect = QApplication.primaryScreen().availableGeometry()
            new_x = self.x() + self.walk_dir * WALK_SPEED
            if new_x < SCREEN_MARGIN or new_x > screen_rect.width() - PET_SIZE - SCREEN_MARGIN:
                self.walk_dir *= -1
                if self.walk_dir > 0:
                    self.anim.switch_animation("walk_right")
                else:
                    self.anim.switch_animation("walk_left")
            self.move(new_x, self.y())
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        frame = self.anim.get_current_frame()
        if frame:
            offset_x = (PET_SIZE - frame.width()) // 2
            offset_y = (PET_SIZE - frame.height()) // 2
            painter.drawPixmap(offset_x, offset_y, frame)
        # 绘制对话气泡文字
        if self.show_bubble:
            painter.setFont(QFont("微软雅黑", 12))
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(20, 30, self.bubble_text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_enable = True
            self.drag_offset = event.globalPos() - self.frameGeometry().topLeft()
            self.anim.switch_animation("touch")
            self.pop_bubble(CLICK_TEXT)
            QTimer.singleShot(1600, lambda: self.anim.switch_animation("idle"))

    def mouseMoveEvent(self, event):
        if self.drag_enable:
            self.move(event.globalPos() - self.drag_offset)

    def mouseReleaseEvent(self, event):
        self.drag_enable = False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = CatDesktopPet()
    pet.show()
    sys.exit(app.exec())
