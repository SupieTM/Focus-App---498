from typing import Optional
import numpy as np
import cv2
import dlib

dlib_predictor_path = "shape_predictor_68_face_landmarks.dat"


class eyeTracker:
    eyeList = []
    endTracker = False
    camera: Optional[cv2.VideoCapture] = None

    def __init__(self):
        self.initalizeCamera()
        pass

    def getState(self):
        return self.endTracker

    def initalizeCamera(self):
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            self.endTracker = True
            print("Failed to open camera")
            return 0

    def cameraLoop(self):

        notDetected = 0

        # Check if the camera is initalized
        if self.camera is None:
            print("Camera not yet initalized")
            return 0

        # initalize the detectors
        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor(dlib_predictor_path)

        # I frame can be read
        while not self.endTracker:

            # capture each frame
            ret, frame = self.camera.read()

            # If frame cannot be read skip
            if not ret:
                print("could not read this frame, contnuing to the next one")
                continue

            # Change the color to gray to help with proccessing
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # detect faces
            dets = detector(gray, 1)

            if (len(dets) == 0):
                print(f"{notDetected}, Face not found")
                notDetected += 1

            for k, d, in enumerate(dets):
                shape = predictor(gray, d)
                #
                # Grab the left and right eye through the shape predictor
                left_eye = [(shape.part(i).x, shape.part(i).y)
                            for i in range(36, 42)]
                right_eye = [(shape.part(i).x, shape.part(i).y)
                             for i in range(42, 48)]

                # Draw the eyes in the output picture
                for (x, y) in left_eye:
                    cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

                for (x, y) in right_eye:
                    cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

                pitch, yaw, roll = self.getFaceangle(shape, gray)

                self.drawViewLine(pitch, yaw, 100, shape.part(30), frame)

                print(f"Pitch: {pitch}, Yaw: {yaw}, Roll: {roll}")

                cv2.imshow("frame", frame)

            if cv2.waitKey(1) == ord('q'):
                break

        self.closeCamera()

    def closeCamera(self):
        self.camera.release()
        cv2.destroyAllWindows()

    def getFaceangle(self, facialPoints, img):

        size = img.shape

        imagePoints2D = np.array([
            (facialPoints.part(30).x, facialPoints.part(30).y),  # Nose
            (facialPoints.part(8).x, facialPoints.part(8).y),  # Chin
            # Left eye left corner
            (facialPoints.part(36).x, facialPoints.part(36).y),
            # Right eye right corner
            (facialPoints.part(45).x, facialPoints.part(45).y),
            (facialPoints.part(48).x, facialPoints.part(48).y),  # Left mouth Corner
            # Right mouth right corner
            (facialPoints.part(54).x, facialPoints.part(54).y)
        ], dtype="double")

        # Frontal face figurepoints: These are approximations for common features on the human face in a 3d plane
        figure_points_3D = np.array(
            [
                (0.0, 0.0, 0.0),  # Nose tip
                (0.0, -330.0, -65.0),  # Chin
                (-225.0, 170.0, -135.0),  # Left eye left corner
                (225.0, 170.0, -135.0),  # Right eye right corne
                (-150.0, -150.0, -125.0),  # Left Mouth corner
                (150.0, -150.0, -125.0),  # Right mouth corner
            ], dtype="double")

        distortionCoeff = np.zeros((4, 1))
        focalLength = size[1]
        center = (size[1] / 2, size[0] / 2)
        matrixCamera = np.array(
            [[focalLength, 0, center[0]], [0, focalLength, center[1]], [0, 0, 1]], dtype="double",)

        ret, rot, trans = cv2.solvePnP(
            figure_points_3D, imagePoints2D, matrixCamera, distortionCoeff)

        # Make rot a little more readable

        rotationMatrix, _ = cv2.Rodrigues(rot)

        # Converto to euler angels, and flatten to more readable angles
        proj_matrix = np.hstack((rotationMatrix, trans))
        _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(
            proj_matrix)
        pitch, yaw, roll = euler_angles.flatten()

        return (pitch, yaw, roll)

    def drawViewLine(self, pitch, yaw, length, nose, frame):
        # convert into radians
        pitchR = np.radians(pitch)
        yawR = np.radians(yaw)

        directionVector = np.array(
            [np.cos(pitchR) * np.sin(yawR), -np.sin(pitchR), np.cos(pitchR) * np.cos(yawR)])

        # scale to image space
        dx = int(directionVector[0] * length)
        dy = int(directionVector[1] * length)

        endpoint = (nose.x + dx, nose.y + dy)

        cv2.line(frame, (nose.x, nose.y), endpoint, (255, 0, 0), 2)


def main():
    cam = eyeTracker()
    cam.cameraLoop()

    return 0


main()
