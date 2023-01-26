from PyQt5 import QtWidgets, uic, QtGui, QtCore
import sys
import highlight
from io import StringIO
from contextlib import redirect_stdout

def p_r(x):
    print(x)
    return x

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('paint.ui', self)
        
        self.menuBarOpen = self.findChild(QtWidgets.QAction, 'actionOpen')
        self.menuBarOpen.triggered.connect(self.openImagePressed)

        self.codeEditor = self.findChild(QtWidgets.QPlainTextEdit, 'codeEdit')
        #self.codeEditor = QtWidgets.QPlainTextEdit()

        self.highlighter = highlight.PythonHighlighter(self.codeEditor.document())
        self.highlighter.setDocument(self.codeEditor.document())

        self.mainImageLabel = self.findChild(QtWidgets.QLabel, 'mainImage')
        self.mainPaint = self.findChild(QtWidgets.QVBoxLayout, 'mainPaint')

        self.executeBtn = self.findChild(QtWidgets.QPushButton, 'executeBtn')
        self.executeBtn.clicked.connect(self.executeCode)

        self.codeOutput = self.findChild(QtWidgets.QPlainTextEdit, 'codeOutput')

        # shift+enter to execute with code editor QShortcut
        self.executeShortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Shift+Return"), self.codeEditor)
        self.executeShortcut.activated.connect(self.executeCode)



        self.image = None

        #update on resize
        self.mainImageLabel.resizeEvent = self.resizeImageToFit
        self.mainImageLabel.setAcceptDrops(True)
        self.mainImageLabel.dropEvent = self.imageDropped
        self.mainImageLabel.dragEnterEvent = self.dragEnterEvent

        self.show()

    def executeCode(self):
        code = self.codeEditor.toPlainText()

        f = StringIO()
        with redirect_stdout(f):
            try:
                exec(code, globals(), locals())
            except Exception as e:
                print(e)
        s = f.getvalue()
        self.codeOutput.setPlainText(s)
        

    def dragEnterEvent(self, event):
        file_name = event.mimeData().text()
        if file_name.split('.')[-1] in ['png', 'jpg', 'jpeg']:
            event.acceptProposedAction()
        else:
            event.ignore()

    def imageDropped(self, event):
        if event.mimeData().hasImage:
            #event.setDropAction(QtWidgets.CopyAction)
            file_path = event.mimeData().urls()[0].toLocalFile()
            self.imageFileName = file_path
            self.loadImageFromFile()

            event.accept()
        else:
            event.ignore()

    def openImagePressed(self):
        print("open")
        self.imageFileName = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', '/home')[0]

        self.loadImageFromFile()
    
    def loadImageFromFile(self):
        self.image = QtGui.QImage(self.imageFileName)
        self.resizeImageToFit()
    
    def resizeImageToFit(self, event_=None):
        print('resizing mainPaint to ', self.mainImageLabel.width())
        if self.image:
            self.scaledImage = self.image.scaled(int(self.mainImageLabel.width()), int(self.mainImageLabel.height()), QtCore.Qt.KeepAspectRatio)
            self.updateImage()
    
    def resizeCodeEditorToFit(self):
        self.codeEditor.resize(int(self.width() * (1 - self.imageWidthPortion)), self.codeEditor.height())

    def updateImage(self):
        self.mainImageLabel.setPixmap(QtGui.QPixmap.fromImage(self.scaledImage))

        #exec('self.mainImageLabel=None', globals(), locals())
        
        # make label resizeable
        #self.mainImageLabel.setScaledContents(True)

        # set size policy to ignore size
        #self.mainImageLabel.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)



app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec_()