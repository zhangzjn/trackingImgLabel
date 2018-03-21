
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

BB = QDialogButtonBox


class LabelDialog(QDialog):

    def __init__(self, text="choose a label", parent=None, listItem=None):
        super(LabelDialog, self).__init__(parent)
        self.setWindowTitle(text)
        self.setWindowModality(Qt.ApplicationModal)
        self.current_text = str()
        if listItem is not None and len(listItem) > 0:
            self.listWidget = QListWidget(self)
            self.listWidget.resize(300, 300)
            self.listWidget.setCurrentRow(1)
            for item in listItem:
                self.listWidget.addItem(item)
            self.listWidget.itemClicked.connect(self.itemClick)
            self.show()



    def itemClick(self, chooseItem):
        self.current_text = chooseItem.text().strip()
        self.close()

