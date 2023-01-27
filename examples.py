examples = {
  "invert random box":
"""class Worker(QtCore.QObject):
	updateImage = QtCore.pyqtSignal(np.ndarray)
	finished = QtCore.pyqtSignal()
	def __init__(self,  img):
		super().__init__(None)
		self.img = img

	def run(self):
		for i in range(10):
			import time
			time.sleep(1)
			print(i)
			a = np.random.randint(0,self.img.shape[0])
			b = np.random.randint(a,self.img.shape[0])

			c = np.random.randint(0,self.img.shape[1])
			d = np.random.randint(c,self.img.shape[1])

			self.img[a:b,c:d] = -self.img[a:b,c:d]
			print(f\"inverted range {a}:{c},{c}:{d}\")
			self.updateImage.emit(self.img)
		self.finished.emit()

workerObj = Worker(self.npimage)"""
}