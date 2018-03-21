from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from libs.lib import distance, return_x_y_w_h
from libs.labelDialog import LabelDialog

class VideoPlay(QLabel):

    def __init__(self, parent = None):
        super(VideoPlay, self).__init__(parent)

        self.lastPoint = QPoint()
        self.endPoint = QPoint()
        self.isDrawing = False
        self.pix = QPixmap(400,600)
        self.painter = QPainter()

        self.initUI()
        self.labelListPath = './label.txt'
        f = open(self.labelListPath, 'r')
        self.labelList = f.read().split('\n')
        self.lastPoint_list = []
        self.endPoint_list = []
        self.category_list = []
        self.show()

    def initUI(self):
        self.setMinimumSize(QSize(400, 300))
        self.setStyleSheet("background-color:grey;")

    def update_frame(self, frame_pix, Q_size, temp_label_info):
        self.pix = frame_pix
        self.lastPoint_list = []
        self.endPoint_list = []
        self.category_list = []
        if(len(temp_label_info.keys()) != 0):
            self.lastPoint_list = temp_label_info['lastPoint_list']
            self.endPoint_list = temp_label_info['endPoint_list']
            self.category_list = temp_label_info['category_list']
        # self.setPixmap(frame_pix)
        self.setMinimumSize(Q_size)
        self.update()

    def erase_current_label(self):
        self.lastPoint_list = []
        self.endPoint_list = []
        self.category_list = []
        self.setPixmap(self.pix)

    def paintEvent(self, ev):
        self.painter.begin(self)
        x, y, w, h = return_x_y_w_h(self.lastPoint, self.endPoint)
        self.tempPix = QPixmap(self.pix)
        cateNum = len(self.category_list)
        pp = QPainter(self.tempPix)
        if cateNum > 0:
            # print("length:", cateNum)
            for i in range(cateNum):
                x, y, w, h = return_x_y_w_h(self.lastPoint_list[i], self.endPoint_list[i])
                pp.drawRect(x, y, w, h)
            self.painter.drawPixmap(0, 0, self.tempPix)
        if self.isDrawing:
            # pp = QPainter(self.tempPix)
            x, y, w, h = return_x_y_w_h(self.lastPoint, self.endPoint)
            pp.drawRect(x, y, w, h)
            self.painter.drawPixmap(0, 0, self.tempPix)
        else:
            self.painter.drawPixmap(0, 0, self.tempPix)
            # print('start drawing')
        self.painter.end()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self.lastPoint = ev.pos()
            self.endPoint = self.lastPoint
            self.isDrawing = True

    def mouseMoveEvent(self, ev):
        if ev.buttons() and Qt.LeftButton:
            self.endPoint = ev.pos()
            self.update()

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self.endPoint = ev.pos()
            self.update()
            self.isDrawing = False
            p = QPoint(abs(self.endPoint.x()-self.lastPoint.x()), abs(self.endPoint.y()-self.lastPoint.y()))
            if distance(p)>10:
                category = LabelDialog(parent=None, listItem=self.labelList)
                category.exec_()
                if category.current_text is not '':
                    self.lastPoint_list.append(self.lastPoint)
                    self.endPoint_list.append(self.endPoint)
                    self.category_list.append(category.current_text)
                # print('length:', len(self.category_list))


