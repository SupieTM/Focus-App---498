from typing import Optional
import cv2
import dlib

dlib_predictor_path = "shape_predictor_68_face_landmarks.dat"


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

        # Check if the camera is initalized
        if self.camera is None:
            print("Camera not yet initalized")
            return 0

        # initalize the detectors
        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor(dlib_predictor_path)
        win = dlib.image_window()

        # I frame can be read
        while not self.endTracker:

            # capture each frame
            ret, frame = self.camera.read()

            # If frame cannot be read skip
            if not ret:
                print("could not read this frame, contnuing to the next one")
                continue

            #  Set the image to the window
            win.set_image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            # Change the color to gray to help with proccessing
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # detect faces
            dets = detector(gray, 2)

            for k, d, in enumerate(dets):
                shape = predictor(gray, d)

                left_eye = [(shape.part(i).x, shape.part(i).y)
                            for i in range(36, 42)]
                right_eye = [(shape.part(i).x, shape.part(i).y)
                         for i in range(42, 47)]


                for (x, y) in left_eye:
                    cv2.circle(frame, (x,y), 2, (0, 255, 0), -1)

                for (x, y) in right_eye:
                    cv2.circle(frame, (x,y), 2, (0, 255, 0), -1)
                
                cv2.imshow("frame", frame)


            if cv2.waitKey(1) == ord('q'):
                break

        self.closeCamera()

    def closeCamera(self):
        self.camera.release()
        cv2.destroyAllWindows()


def main():
    cam = eyeTracker()
    cam.cameraLoop()

    return 0


main()
