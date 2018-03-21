#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import os
import re
import sys
import subprocess
import cv2

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from libs.lib import newAction, addActions, return_x_y_w_h
from libs.pascal_voc_io import PascalVocWriter
from libs.video_play import VideoPlay
from tracking.kcftracker import *
# from libs.labelDialog import LabelDialog
__appname__ = 'tracking image label'

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.video_opened = False
        self.video_current_frame = 1
        self.video_tracking_frame = 30
        self.labelled_frame_dict = dict()
        self.save_start_frame = 1
        self.save_end_frame = 30
        self.save_gap = 5
        self.save_dir_path = '.'
        self.check_state_change_value = True
        self.cap = cv2.VideoCapture()
        self.setWindowTitle(__appname__)
        self.setWindowIcon(QIcon('./icon/next.png'))
        #self.resize(1900, 900)

        # create menus
        menu_file = self.menuBar().addMenu('&File')
        menu_edit = self.menuBar().addMenu('&Edit')
        menu_view = self.menuBar().addMenu('&View')
        menu_help = self.menuBar().addMenu('&Help')
        self.menus = dict(
            file=menu_file,
            edit=menu_edit,
            view=menu_view,
            help=menu_help)

        # create widgets
        self.video_frame = VideoPlay()
        self.video_play_dock = QDockWidget(u'video play', self)
        self.video_play_dock.setObjectName(u'video_play_dock')
        self.video_play_dock.setWidget(self.video_frame)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.video_play_dock)
        # self.dockFeatures = QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetFloatable
        # self.video_play_dock.setFeatures(self.video_play_dock.features() ^ self.dockFeatures)

        layout_path_show = QGridLayout()
        self.text_video_path = QLabel(u'video path')
        self.line_video_path = QLineEdit()
        self.line_video_path.setMinimumWidth(300)
        self.line_video_path.setText('.')
        layout_path_show.addWidget(self.text_video_path,0,0, Qt.AlignLeft | Qt.AlignTop)
        layout_path_show.addWidget(self.line_video_path,0,1,1,2, Qt.AlignLeft | Qt.AlignTop)
        self.text_save_path = QLabel(u'save path')
        self.line_save_path = QLineEdit()
        self.line_save_path.setMinimumWidth(300)
        self.line_save_path.setText('.')
        layout_path_show.addWidget(self.text_save_path,1,0, Qt.AlignLeft | Qt.AlignTop)
        layout_path_show.addWidget(self.line_save_path,1,1,1,2, Qt.AlignLeft | Qt.AlignTop)
        self.text_video_frame = QLabel(u'current frame')
        self.line_video_frame = QSpinBox()
        self.line_video_frame.setMaximum(10000)
        self.line_video_frame.setValue(1)
        self.line_video_frame.setStatusTip(self.toolTip())
        self.line_video_frame.setAlignment(Qt.AlignCenter)
        self.line_video_frame.setMinimumWidth(60)
        self.line_video_frame.setMaximumWidth(60)
        # self.line_video_frame.editingFinished.connect(self.event_frame_changed)
        self.line_video_frame.valueChanged.connect(self.event_frame_changed)
        layout_path_show.addWidget(self.text_video_frame,2,0, Qt.AlignLeft | Qt.AlignTop)
        layout_path_show.addWidget(self.line_video_frame,2,1, Qt.AlignLeft | Qt.AlignTop)
        self.text_video_frame1 = QLabel(u'all frame')
        self.line_video_frame1 = QLineEdit()
        self.line_video_frame1.setEnabled(False)
        self.line_video_frame1.setMaximumWidth(60)
        layout_path_show.addWidget(self.text_video_frame1,3,0, Qt.AlignLeft | Qt.AlignTop)
        layout_path_show.addWidget(self.line_video_frame1,3,1, Qt.AlignLeft | Qt.AlignTop)
        self.button_save = QPushButton(u'save current label')
        self.button_save.clicked.connect(self.event_button_save_current)
        layout_path_show.addWidget(self.button_save, 2, 2, Qt.AlignLeft | Qt.AlignTop)
        self.button_erase = QPushButton(u'erase current label')
        self.button_erase.clicked.connect(self.event_button_erase)
        layout_path_show.addWidget(self.button_erase, 3, 2, Qt.AlignLeft | Qt.AlignTop)
        self.button_tracking = QPushButton(u'start tracking')
        self.button_tracking.clicked.connect(self.event_button_tracking)
        layout_path_show.addWidget(self.button_tracking, 4, 2, Qt.AlignLeft | Qt.AlignTop)
        self.text_tracking_frames = QLabel(u'tracking frames')
        self.line_tracking_frames = QSpinBox()
        self.line_tracking_frames.setMaximum(10000)
        self.line_tracking_frames.setValue(30)
        self.line_tracking_frames.setStatusTip(self.toolTip())
        self.line_tracking_frames.setAlignment(Qt.AlignCenter)
        self.line_tracking_frames.setMinimumWidth(60)
        self.line_tracking_frames.setMaximumWidth(60)
        # self.line_video_frame.editingFinished.connect(self.event_frame_changed)
        self.line_tracking_frames.valueChanged.connect(self.event_tracking_frame)
        layout_path_show.addWidget(self.text_tracking_frames, 4, 0, Qt.AlignLeft | Qt.AlignTop)
        layout_path_show.addWidget(self.line_tracking_frames, 4, 1, Qt.AlignLeft | Qt.AlignTop)
        layout_path_show.setVerticalSpacing(5)

        info_container = QWidget()
        info_container.setLayout(layout_path_show)
        self.info_dock = QDockWidget(u'info', self)
        self.info_dock.setObjectName(u'info_dock')
        self.info_dock.setWidget(info_container)
        self.addDockWidget(Qt.RightDockWidgetArea, self.info_dock)
        # self.dockFeatures = QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetFloatable
        # self.info_dock.setFeatures(self.info_dock.features() ^ self.dockFeatures)

        self.text_video_info = QTextEdit()
        self.video_info_dock = QDockWidget(u'video info', self)
        self.video_info_dock.setObjectName(u'video_info_dock')
        self.video_info_dock.setWidget(self.text_video_info)
        self.addDockWidget(Qt.RightDockWidgetArea, self.video_info_dock)
        # self.dockFeatures = QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetFloatable
        # self.video_info_dock.setFeatures(self.video_info_dock.features() ^ self.dockFeatures)

        layout_save_option = QGridLayout()
        self.label_save_start_frame = QLabel(u'start frame')
        self.edit_save_start_frame = QSpinBox()
        self.edit_save_start_frame.setMinimum(1)
        self.edit_save_start_frame.setValue(1)
        self.edit_save_start_frame.setStatusTip(self.toolTip())
        self.edit_save_start_frame.setAlignment(Qt.AlignCenter)
        self.edit_save_start_frame.setMinimumWidth(60)
        self.edit_save_start_frame.setMaximumWidth(60)
        self.edit_save_start_frame.valueChanged.connect(self.event_save_start_frame_changed)
        # self.edit_save_start_frame = QLineEdit()
        # self.edit_save_start_frame.setMaximumWidth(60)
        # self.edit_save_start_frame.textChanged.connect(self.event_save_start_frame_changed)
        layout_save_option.addWidget(self.label_save_start_frame, 0, 0, Qt.AlignLeft | Qt.AlignTop)
        layout_save_option.addWidget(self.edit_save_start_frame, 0, 1, Qt.AlignLeft | Qt.AlignTop)
        self.label_save_end_frame = QLabel(u'end frame')
        self.edit_save_end_frame = QSpinBox()
        self.edit_save_end_frame.setMinimum(1)
        self.edit_save_end_frame.setValue(30)
        self.edit_save_end_frame.setStatusTip(self.toolTip())
        self.edit_save_end_frame.setAlignment(Qt.AlignCenter)
        self.edit_save_end_frame.setMinimumWidth(60)
        self.edit_save_end_frame.setMaximumWidth(60)
        self.edit_save_end_frame.valueChanged.connect(self.event_save_end_frame_changed)
        # self.edit_save_end_frame = QLineEdit()
        # self.edit_save_end_frame.setMaximumWidth(60)
        # self.edit_save_end_frame.textChanged.connect(self.event_save_end_frame_changed)
        layout_save_option.addWidget(self.label_save_end_frame, 1, 0, Qt.AlignLeft | Qt.AlignTop)
        layout_save_option.addWidget(self.edit_save_end_frame, 1, 1, Qt.AlignLeft | Qt.AlignTop)
        # self.button_save = QPushButton(u'save current label')
        # self.button_save.clicked.connect(self.event_button_save_current)
        # layout_save_option.addWidget(self.button_save, 0, 2, Qt.AlignLeft | Qt.AlignTop)
        # self.button_erase = QPushButton(u'erase current label')
        # self.button_erase.clicked.connect(self.event_button_erase)
        # layout_save_option.addWidget(self.button_erase, 1, 2, Qt.AlignLeft | Qt.AlignTop)
        # self.button_tracking = QPushButton(u'start tracking')
        # self.button_tracking.clicked.connect(self.event_button_tracking)
        # layout_save_option.addWidget(self.button_tracking, 2, 2, Qt.AlignLeft | Qt.AlignTop)
        self.label_save_gap = QLabel(u'save gap')
        self.edit_save_gap = QSpinBox()
        self.edit_save_gap.setMinimum(1)
        self.edit_save_gap.setValue(5)
        self.edit_save_gap.setStatusTip(self.toolTip())
        self.edit_save_gap.setAlignment(Qt.AlignCenter)
        self.edit_save_gap.setMinimumWidth(60)
        self.edit_save_gap.setMaximumWidth(60)
        self.edit_save_gap.valueChanged.connect(self.event_save_gap_changed)
        # self.edit_save_end_frame = QLineEdit()
        # self.edit_save_end_frame.setMaximumWidth(60)
        # self.edit_save_end_frame.textChanged.connect(self.event_save_end_frame_changed)
        layout_save_option.addWidget(self.label_save_gap, 2, 0, Qt.AlignLeft | Qt.AlignTop)
        layout_save_option.addWidget(self.edit_save_gap, 2, 1, Qt.AlignLeft | Qt.AlignTop)
        self.diffcButton = QCheckBox(u'detection')
        self.diffcButton.setChecked(True)
        self.diffcButton.stateChanged.connect(self.check_state_change)
        layout_save_option.addWidget(self.diffcButton, 0, 2, Qt.AlignLeft | Qt.AlignTop)
        self.button_save = QPushButton(u'start saving')
        self.button_save.clicked.connect(self.event_button_save)
        layout_save_option.addWidget(self.button_save, 1, 2, Qt.AlignLeft | Qt.AlignTop)
        save_labelled_images_container = QWidget()
        save_labelled_images_container.setLayout(layout_save_option)
        self.save_labelled_images_dock = QDockWidget(u'save option', self)
        self.save_labelled_images_dock.setObjectName(u'save_labelled_images_dock')
        self.save_labelled_images_dock.setWidget(save_labelled_images_container)
        self.addDockWidget(Qt.RightDockWidgetArea, self.save_labelled_images_dock)

        # actions
        open = newAction(self, '&Open', self.openFile, 'Ctrl+O', 'open', u'Open video')
        savedir = newAction(self, '&Save Dir', self.SavedirDialog, 'Ctrl+r', 'open', u'Dir to save')
        addActions(self.menus['file'], [open, savedir])
    # slot function
    def openFile(self, _value=False):
        if not self.video_opened:
            self.video_opened = True
            path = 'F:/programs/label_extract'
            # formats = ['*.%s;;' % fmt.data().decode("ascii").lower() for fmt in QImageReader.supportedImageFormats()]
            # filters = ' '.join(formats + ['*%s' % LabelFile.suffix])
            filters = '(*.mp4);;(*.mov);;all(*.*)'
            filepath = QFileDialog.getOpenFileName(self, '%s - Choose Image or Label file' % __appname__, path, filters)
            # print (filename)
            if filepath:
                self.filepath = filepath[0]
                self.folder_path = os.path.dirname(self.filepath)
                self.file_name = os.path.basename(self.filepath)
                self.line_video_path.setText(self.filepath)
                # load the video
                self.load_video(self.filepath)
        else:
            path = self.folder_path
            filters = 'all(*.*);;(*.mp4);;(*.mov)'
            filepath = QFileDialog.getOpenFileName(self, '%s - Choose Image or Label file' % __appname__, path, filters)
            # print (filename)
            if filepath:
                self.filepath = filepath[0]
                self.folder_path = os.path.dirname(self.filepath)
                self.file_name = os.path.basename(self.filepath)
                self.line_video_path.setText(self.filepath)
                # load the video
                self.load_video(self.filepath)

    def load_video(self, filepath=None):
        if filepath is not None:
            self.cap = cv2.VideoCapture(filepath)
            if self.cap.isOpened():
                print('video ' + self.file_name + ' opened')
                self.video_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                self.video_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                self.video_frame_rate = self.cap.get(cv2.CAP_PROP_FPS)
                self.all_frames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
                self.video_info = 'width:' + str(self.video_width) + '\n' + 'height:' + str(self.video_height) + '\n' + 'frame_rate:' + '%.2f'%(self.video_frame_rate) + '\n' + 'all_frames:' + '%d'%(self.all_frames)
                self.text_video_info.setText(self.video_info)
                self.labelled_frame_dict.clear()
                self.labelled_frame_dict = dict()
                self.update_current_frame()
                self.update_current_frame_to_play()
                self.line_video_path.setText(self.filepath)
                self.line_video_frame1.setText(str(self.all_frames))

                self.line_video_frame.setMaximum(self.all_frames)
                self.edit_save_start_frame.setMaximum(self.all_frames)
                self.edit_save_end_frame.setMaximum(self.all_frames)
                self.line_tracking_frames.setMaximum(self.all_frames)

    def update_current_frame(self):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.video_current_frame - 1)
        ret, frame = self.cap.read()
        self.currentFrame = frame

    def update_current_frame_to_play(self):
        self.line_video_frame.setValue(self.video_current_frame)
        frame = cv2.cvtColor(self.currentFrame, cv2.COLOR_BGR2RGB)
        img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
        pix = QPixmap.fromImage(img)
        temp_label_info = dict()
        if (self.video_current_frame in self.labelled_frame_dict.keys()):
            temp_label_info = self.labelled_frame_dict[self.video_current_frame]
        self.video_frame.update_frame(pix, QSize(min([self.video_width, 1600]), min([self.video_height, 1200])),
                                      temp_label_info)

    def SavedirDialog(self, _value=False):
        defaultOpenDirPath = '.'
        save_dir_path = QFileDialog.getExistingDirectory(self, '%s - Open Directory' % __appname__, defaultOpenDirPath,
                                                              QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        self.save_dir_path = save_dir_path
        self.line_save_path.setText(self.save_dir_path)

    def event_frame_changed(self):
        if (int(self.line_video_frame.text()) > 0):    # not empty
            self.video_current_frame = int(self.line_video_frame.text())
            self.update_current_frame()
            self.update_current_frame_to_play()
        else:
            self.video_current_frame = 1
            self.update_current_frame()
            self.update_current_frame_to_play()

    def event_tracking_frame(self):
        if (int(self.line_tracking_frames.text()) > 0):    # not empty
            self.video_tracking_frame = int(self.line_tracking_frames.text())
            self.video_tracking_frame = min([self.video_current_frame+self.video_tracking_frame, self.all_frames]) - self.video_current_frame # keep off exceeding max_frame
            self.video_tracking_frame = max([self.video_tracking_frame, 1])
            self.line_tracking_frames.setValue(self.video_tracking_frame)
        else:
            self.video_tracking_frame = 1
            self.line_tracking_frames.setValue(self.video_tracking_frame)
        print('video tracking frame:', self.video_tracking_frame)


    def event_save_start_frame_changed(self):
        if(int(self.edit_save_start_frame.text()) > 0):
            self.save_start_frame = int(self.edit_save_start_frame.text())
        else:
            self.save_start_frame = 1
            self.edit_save_start_frame.setValue(self.save_start_frame)
        print('current save start frame:', self.save_start_frame)

    def event_save_end_frame_changed(self):
        if (int(self.edit_save_end_frame.text()) > 0):
            self.save_end_frame = int(self.edit_save_end_frame.text())
        else:
            self.save_end_frame = 1
            self.edit_save_end_frame.setValue(self.save_end_frame)
        print('current save end frame:', self.save_end_frame)

    def event_save_gap_changed(self):
        if (int(self.edit_save_gap.text()) > 0):
            self.save_gap = int(self.edit_save_gap.text())
        else:
            self.save_gap = 1
            self.edit_save_gap.setValue(self.save_gap)
        print('current saving gap:', self.save_gap)

    def event_button_save_current(self):
        if self.cap.isOpened():
            if(len(self.video_frame.lastPoint_list) != 0):
                dictLabelTemp = {'lastPoint_list': self.video_frame.lastPoint_list,
                                 'endPoint_list': self.video_frame.endPoint_list,
                                 'category_list': self.video_frame.category_list}
                dictTemp = {self.video_current_frame: dictLabelTemp}
                self.labelled_frame_dict.update(dictTemp)
                print('saving frame(%s) success' % self.video_current_frame)
                print('labelled_frame_dict length:%s' % len(self.labelled_frame_dict))
                return True
            else:
                QMessageBox.warning(self, 'warning', 'please label current frame!', QMessageBox.Yes, QMessageBox.Yes)
                return False
        else:
            QMessageBox.warning(self, 'warning', 'please load a video!', QMessageBox.Yes, QMessageBox.Yes)
            return False

    def event_button_erase(self):
        self.video_frame.erase_current_label()
        self.labelled_frame_dict.pop(self.video_current_frame)
        print('labelled_frame_dict length:%s' % len(self.labelled_frame_dict))

    def event_button_tracking(self):
        if self.event_button_save_current():
            currentFrameInfo = self.labelled_frame_dict[self.video_current_frame]
            firstLastPointList = currentFrameInfo['lastPoint_list']
            firstEndPointList = currentFrameInfo['endPoint_list']
            firstCategoryList = currentFrameInfo['category_list']
            trackerCount = len(firstLastPointList)
            trackers = list()
            print('initialization ...')
            # for initial
            for i in range(trackerCount):
                trackers.append(KCFTracker(True,True,True))
                x, y, w, h = return_x_y_w_h(firstLastPointList[i], firstEndPointList[i])
                print('x:%s ,y：%s ,w:%s ,h:%s' %(x, y, w, h))
                trackers[i].init([x, y, w, h],self.currentFrame)
                print('track '+str(i)+ ' init finished ...')
            # for tracking
            print('start tracking ...')
            for i in range(self.video_tracking_frame):
                self.video_current_frame = self.video_current_frame + 1
                self.update_current_frame()
                outLastPointList = []
                outEndPointList = []
                outCategoryList = []
                for currentTracker in range(trackerCount):
                    boundingbox = trackers[currentTracker].update(self.currentFrame)
                    pt1 = QPoint(boundingbox[0], boundingbox[1])
                    pt2 = QPoint(boundingbox[0] + boundingbox[2], boundingbox[1] + boundingbox[3])
                    cate = firstCategoryList[currentTracker]
                    outLastPointList.append(pt1)
                    outEndPointList.append(pt2)
                    outCategoryList.append(cate)
                dictLabelTemp = {'lastPoint_list': outLastPointList,
                                 'endPoint_list': outEndPointList,
                                 'category_list': outCategoryList}
                dictTemp = {self.video_current_frame: dictLabelTemp}
                self.labelled_frame_dict.update(dictTemp)
                self.update_current_frame_to_play()
                print('frame %s solved' % self.video_current_frame)

    def event_button_save(self):
        temp_cap = cv2.VideoCapture(self.filepath)
        if (self.check_state_change_value):
            saveImagePath = os.path.join(self.save_dir_path, 'JPEGImages')
            saveAnnosPath = os.path.join(self.save_dir_path, 'Annotations')
            if not os.path.isdir(saveImagePath):
                os.mkdir(saveImagePath)
            if not os.path.isdir(saveAnnosPath):
                os.mkdir(saveAnnosPath)
            for num in range(self.save_start_frame, self.save_end_frame + 1, self.save_gap):
                if(num in self.labelled_frame_dict.keys()):
                    frameId = num
                    frameInfo = self.labelled_frame_dict[num]
                    temp_cap.set(cv2.CAP_PROP_POS_FRAMES, frameId - 1)
                    ret, frame = temp_cap.read()
                    cv2.imwrite(saveImagePath + '/' + str(frameId) + '.jpg', frame)
                    writer = PascalVocWriter(saveAnnosPath, str(frameId)+'.jpg', [self.video_width, self.video_height, 3], localImgPath=None)
                    temptLastPointList = frameInfo['lastPoint_list']
                    tempEndPointList = frameInfo['endPoint_list']
                    tempCategoryList = frameInfo['category_list']
                    tempCount = len(temptLastPointList)
                    for i in range(tempCount):
                        x, y, w, h = return_x_y_w_h(temptLastPointList[i], tempEndPointList[i])
                        writer.addBndBox(x, y, w, h,tempCategoryList[i], 0)
                    writer.save(targetFile=(saveAnnosPath + '/' + str(frameId) + '.xml'))
                    print('frame ', num, ' saved')
        else:
            # saveImagePath = os.path.join(self.save_dir_path, 'Images')
            saveImagePath = self.save_dir_path + '/Images'
            if not os.path.isdir(saveImagePath):
                os.mkdir(saveImagePath)
            f = open(os.path.join(self.save_dir_path, 'label_train.txt'), 'w')
            for num in range(self.save_start_frame, self.save_end_frame + 1, self.save_gap):
                if (num in self.labelled_frame_dict.keys()):
                    frameId = num
                    frameInfo = self.labelled_frame_dict[num]
                    temp_cap.set(cv2.CAP_PROP_POS_FRAMES, frameId - 1)
                    ret, frame = temp_cap.read()
                    temptLastPointList = frameInfo['lastPoint_list']
                    tempEndPointList = frameInfo['endPoint_list']
                    tempCategoryList = frameInfo['category_list']
                    tempCount = len(temptLastPointList)
                    for i in range(tempCount):
                        x, y, w, h = return_x_y_w_h(temptLastPointList[i], tempEndPointList[i])
                        frameCrop = frame[y:y+h+1, x:x+w+1]
                        cv2.imwrite(saveImagePath + '/' + tempCategoryList[i] + '_' + str(frameId) + '_' + str(i) + '.jpg', frameCrop)
                        f.write(saveImagePath + '/' + tempCategoryList[i] + '_' + str(frameId) + '_' + str(i) + '.jpg' +' '+tempCategoryList[i]+'\n')
                    print('frame ', num, ' saved')

    def check_state_change(self):
        self.check_state_change_value = self.diffcButton.isChecked()
        print('state: ', self.check_state_change_value)

def main(argv=[]):
    app = QApplication(argv)
    # app.setApplicationName(__appname__)
    win = MainWindow()
    win.show()
    return app.exec_()

if __name__ == '__main__':
    sys.exit(main(sys.argv))