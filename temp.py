import cv2
from facial_detections import detectFace
from eye_tracker import gazeDetection
from blink_detection import isBlinking
from head_pose_estimation import head_pose_detection
from mouth_tracking import mouthTrack
from object_detection import detectObject
from audio_detection import audio_detection

cam = cv2.VideoCapture(0)

while True:
    ret, frame = cam.read()

    # FUNCTION 1
    faceCount, faces = detectFace(frame)
    # print(faceCount)

    # FUNCTION 2
    eyeStatus = gazeDetection(faces, frame)
    # print(eyeStatus)

    # FUNCTION 3
    blinkStatus = isBlinking(faces, frame)
    # print(blinkStatus[2])

    # FUNCTION 4
    head_pose_detection(faces, frame)

    # FUNCTION 5
    print(mouthTrack(faces, frame))

    # FUNCTION 6
    print(detectObject(frame))

    # FUNCTION 7
    # audio_detection()



    cv2.imshow('Frame', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
