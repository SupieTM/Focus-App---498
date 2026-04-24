from typing import Optional
import numpy as np
import cv2

# Media Pipe
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Model 
model_path = "face_landmarker.task"


class eyeTracker:
    camera: Optional[cv2.VideoCapture] = None
    BaseOptions = mp.tasks.BaseOptions
    FaceLandmarker = mp.tasks.vision.FaceLandmarker
    FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    options = FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.IMAGE,
    )

    faceTracer = FaceLandmarker.create_from_options(options)

    # Automatically initalizes the camera as well as the detector and predictor for dlib
    def __init__(self):
        self.initalizeCamera()
        pass

    # Gets and sets the endTracker State
    def getState(self):
        return self.endTracker

    def setState(self, stateSet: bool):
        self.endTracker = stateSet

    # Initalizes camera
    def initalizeCamera(self):
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            self.endTracker = True
            print("Failed to open camera")
            return 0

    # Upscaling defines how much the image should be "enchanced" before the predictor starts
    # Base is 1: Higher numbers will be able to predict faces better at the cost of it taking longer to proccess the image
    # Gets a single frame and returns the predicted pitch, yaw, and roll of the personal head.
    # Returns a list of pitch, yaw, roll for each face detected in the image.
    # If the camera cannot be found it returns a empty list

    def getSingleFrame(self, debuggingView: bool):

        # capture a frame
        ret, frame = self.camera.read()

        if not ret:
            print("Camera couldn't be found or can't be read from")
            return []

        # change the color to gray for proccessing help
        RGBIMG = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=RGBIMG)

        detection_result = self.faceTracer.detect(mp_image)

        rl: list = []

        if detection_result.face_landmarks:
            for face in detection_result.face_landmarks:
                print(len(face))

                pitch, yaw, roll = self.getFaceangle(face, frame)

                rl.append((pitch, yaw, roll))

        cv2.imshow("frame", frame)
        cv2.waitKey(1)

        return rl

    def closeCamera(self):
        self.camera.release()
        cv2.destroyAllWindows()
        self.faceTracer.close()

    # Compares the 2D points on certain face parts on the image to a 3d estimate on where those parts would be.
    # With this it estimates the orientation of the users head.
    def getFaceangle(self, face, img):

        h, w, _ = img.shape

        imagePoints2D = np.array([
            # Nose tip
            (int(face[1].x * w), int(face[1].y * h)),

            # Chin
            (int(face[152].x * w), int(face[152].y * h)),

            # Left eye left corner
            (int(face[33].x * w), int(face[33].y * h)),

            # Right eye right corner
            (int(face[263].x * w), int(face[263].y * h)),

            # Left mouth corner
            (int(face[61].x * w), int(face[61].y * h)),

            # Right mouth corner
            (int(face[291].x * w), int(face[291].y * h)),
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
        focalLength = w
        center = (w / 2, h / 2)
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

    def getEyeAngle(self, face, frame):

        h, w, _ = frame.shape

        leftIrisCenter = (face[468].x, face[468].y)
        rightIrisCenter = (face[473].x, face[473].y)


        leftEyePoints = [362,398,384,385,386,387,388,466,263,249,390,373,374,380,381,382]
        rightEyePoints = [33,246,161,160,159,158,157,173,133,155,154,153,145,144,163,7]

        leftEyeMidpoint = [0.0,0.0]
        for point in leftEyePoints:
            leftEyeMidpoint[0] += face[point].x
            leftEyeMidpoint[1] += face[point].y

        leftEyeMidpoint[0] = leftEyeMidpoint[0] / len(leftEyePoints)
        leftEyeMidpoint[1] = leftEyeMidpoint[1] / len(leftEyePoints)

        rightEyeMidpoint = [0.0,0.0]
        for point in leftEyePoints:
            rightEyeMidpoint[0] += face[point].x
            rightEyeMidpoint[1] += face[point].x

        rightEyeMidpoint[0] = rightEyeMidpoint[0] / len(rightEyePoints)
        rightEyeMidpoint[1] = rightEyeMidpoint[1] / len(rightEyePoints)







        return

    # Debugging: Draws certain points onto the screen (Doesn't initalize to print the screen)

    def drawDebuggingVectors(self, pitch, yaw, length, face, frame):

        h, w, _ = frame.shape

        nose = face[1]

        # convert into radians
        pitchR = np.radians(pitch)
        yawR = np.radians(yaw)

        directionVector = np.array(
            [np.cos(pitchR) * np.sin(yawR), -np.sin(pitchR), np.cos(pitchR) * np.cos(yawR)])

        # scale to image space
        dx = int(directionVector[0] * length)
        dy = int(directionVector[1] * length)

        endpoint = (int(nose.x * w) + dx, int(nose.y * h) + dy)

        cv2.line(frame, (int(nose.x * w), int(nose.y * h)),
                 endpoint, (255, 0, 0), 2)

        cv2.circle(frame, (int(face[468].x * w),
                   int(face[468].y * h)), 1, (0, 255, 0), 2)
        cv2.circle(frame, (int(face[473].x * w),
                   int(face[473].y * h)), 1, (0, 255, 0), 2)



# Test function
def main():
    cam = eyeTracker()

    while True:
        rl = cam.getSingleFrame(False)

    return 0


if __name__ == "__main__":
    main()
