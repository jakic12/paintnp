from PyQt5 import QtWidgets, uic, QtGui, QtCore
import sys
import highlight
import numpy as np
from PIL import Image
import threading

from examples import examples

def p_r(x):
    print(x)
    return x

class ConsoleStdoutWrapper():
    def __init__(self, parent):
        self.parent = parent

    def write(self, txt):
        self.parent.appendPlainText(str(txt))
    
    def clear(self):
        self.parent.setPlainText("")


class Ui(QtWidgets.QMainWindow):
    lastSavedCode = ""
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('paint.ui', self)
        
        self.menuBarOpen = self.findChild(QtWidgets.QAction, 'actionOpen')
        self.menuBarOpen.triggered.connect(self.openImagePressed)

        self.codeEditor = self.findChild(QtWidgets.QPlainTextEdit, 'codeEdit')
        #self.codeEditor = QtWidgets.QPlainTextEdit()
        # connect code editor changed to a handle
        self.codeEditor.textChanged.connect(self.codeEditorChanged)

        self.highlighter = highlight.PythonHighlighter(self.codeEditor.document())
        self.highlighter.setDocument(self.codeEditor.document())

        self.codeEditor.setPlainText(examples["invert random box"])
        self.lastSavedCode = self.codeEditor.toPlainText()

        self.mainImageLabel = self.findChild(QtWidgets.QLabel, 'mainImage')
        self.mainPaint = self.findChild(QtWidgets.QVBoxLayout, 'mainPaint')

        self.executeBtn = self.findChild(QtWidgets.QPushButton, 'executeBtn')
        self.executeBtn.clicked.connect(self.executeCode)

        self.codeOutput = self.findChild(QtWidgets.QPlainTextEdit, 'codeOutput')

        # shift+enter to execute with code editor QShortcut
        #self.executeShortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Shift+Return"), self.codeEditor)
        #self.executeShortcut.activated.connect(self.executeCode)

        # cmd+s to save with code editor QShortcut
        self.saveShortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+S"), self.codeEditor)
        self.saveShortcut.activated.connect(self.saveCode)

        # cmd+enter to execute with code editor QShortcut
        self.executeShortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Return"), self.codeEditor)
        self.executeShortcut.activated.connect(self.executeCode)

        self.unsavedChangesLabel = self.findChild(QtWidgets.QLabel, 'unsavedChanges')
        self.unsavedLabel = self.findChild(QtWidgets.QLabel, 'unsavedLabel')

        # set icons for unsaved changes label
        self.unsavedLabel.setPixmap(QtGui.QPixmap("icons/save.png"))
        self.unsavedChangesLabel.setPixmap(QtGui.QPixmap("icons/warning.png"))
        self.changeDisplayUnsavedChanges(False)

        self.npimage = None

        #update on resize
        self.mainImageLabel.resizeEvent = self.updateDisplayImage
        self.mainImageLabel.setAcceptDrops(True)
        self.mainImageLabel.dropEvent = self.imageDropped
        self.mainImageLabel.dragEnterEvent = self.dragEnterEvent

        #self.myThread = MyQThread()
        self.codeStdout = ConsoleStdoutWrapper(self.codeOutput)

        self.show()

    def codeEditorChanged(self):
        if 'lastSavedCode' in dir(self) and 'unsavedChangesLabel' in dir(self):
            if self.codeEditor.toPlainText() != self.lastSavedCode:
                print("changed: T")
                self.changeDisplayUnsavedChanges(True)
            else:
                print("changed: F")
                self.changeDisplayUnsavedChanges(False)
    
    def saveCode(self):
        print("save code request")
        self.lastSavedCode = self.codeEditor.toPlainText()
        self.changeDisplayUnsavedChanges(False)
    
    def changeDisplayUnsavedChanges(self, show):
        # hide/ungide label
        self.unsavedChangesLabel.setHidden(not show)

    def numpyToQImage(self, arr):
        height, width, channel = arr.shape
        return QtGui.QImage(arr, width, height, channel * width, QtGui.QImage.Format_RGB888)

    def executeCode(self):
        code = self.codeEditor.toPlainText()
        old_stdout = sys.stdout
        self.codeStdout.clear()
        sys.stdout = self.codeStdout

        if self.npimage is None:
            print("No image loaded")
            return

        new_locals = locals()
        try:
            exec(code, globals(), new_locals)
        except Exception as e:
            print(e)

        if 'workerObj' in new_locals:
            print('workerObj found')
            self.workerObj = new_locals['workerObj']
            #self.workerObj = workerObj

            def bind(instance, func, as_name=None):
                """
                Bind the function *func* to *instance*, with either provided name *as_name*
                or the existing name of *func*. The provided *func* should accept the 
                instance as the first argument, i.e. "self".
                """
                if as_name is None:
                    as_name = func.__name__
                bound_method = func.__get__(instance, instance.__class__)
                setattr(instance, as_name, bound_method)
                return bound_method

            self1 = self

            def stdoutWrappedRun(self):
                old_stdout = sys.stdout
                sys.stdout = self1.codeStdout
                self1.workerObj.run()
                sys.stdout = old_stdout


            #self.workerObj.stdoutWrappedRun = stdoutWrappedRun

            bind(self.workerObj, stdoutWrappedRun)
            
            self.workerThread = QtCore.QThread()
            self.workerObj.moveToThread(self.workerThread)
            self.workerThread.started.connect(self.workerObj.stdoutWrappedRun)
            self.workerThread.finished.connect(self.workerThread.deleteLater)
            self.workerObj.finished.connect(self.workerThread.quit)
            self.workerObj.finished.connect(self.workerObj.deleteLater)
            print(self.workerObj.run)
            #self.workerThread.started.connect(lambda: print("thread started"))

            if 'updateImage' in dir(self.workerObj):
                self.workerObj.updateImage.connect(self.updateImage)
                print('updateImage connected')
            self.workerThread.start()
        else:
            print('workerObj not found')


        # convert numpy array back to image
        if self.npimage is not None:
            self.updateDisplayImage()

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
            self.loadImageFromFile(file_path)

            event.accept()
        else:
            event.ignore()

    def openImagePressed(self):
        print("open")
        file_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', '/home')[0]

        self.loadImageFromFile(file_path)
    
    def loadImageFromFile(self,path):
        self.imageFileName = path
        self.updateImage(np.array(Image.open(path).convert('RGB')).astype(np.uint8))

    def updateImage(self, image):
        self.npimage = image
        self.updateDisplayImage()
    
    def updateDisplayImage(self, event_=None):
        #print('resizing mainPaint to ', self.mainImageLabel.width())
        if self.npimage is not None:
            im_np = np.transpose(self.npimage, (0,1,2)).copy()
            img = self.numpyToQImage(self.npimage)
            self.scaledImage = img.scaled(int(self.mainImageLabel.width()), int(self.mainImageLabel.height()), QtCore.Qt.KeepAspectRatio)
            self.mainImageLabel.setPixmap(QtGui.QPixmap.fromImage(self.scaledImage))



app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec_()