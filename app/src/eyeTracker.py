from typing import Optional
import cv2
import dlib


class eyeTracker:
    eyeList = []
    endTracker = False
    stateCode = 0
    camera: Optional[cv2.VideoCapture] = None

    def __init__(self):
        self.initalizeCamera()
        pass

    def getState(self):
        return (self.endTracker, self.stateCode)

    def changeState(self, changeNum):
        self.stateCode = changeNum

    def initalizeCamera(self):
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            self.stateCode = 1
            self.endTracker = True
            print("Failed to open camera")
            return 0

    def cameraLoop(self):

        if self.camera is None:
            print("Camera not yet initalized")

        # IF frame cannot be read
        while not self.endTracker:
            # capture each frame
            ret, frame = self.camera.read()

            if not ret:
                print("could not read this frame, contnuing to the next one")
                continue

            # Change the collor to gray to help with proccessing
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            cv2.imshow('frame', gray)
            if cv2.waitKey(1) == ord('q'):
                break

        self.closeCamera()



     def closeCamera(self):
        self.camera.release()
        cv2.destroyAllWindows()



def main():
    return 0


main()
