
import dlib
from math import hypot
import cv2

shapePredictorModel  = 'shape_predictor_model/shape_predictor_68_face_landmarks.dat'
shapePredictor = dlib.shape_predictor(shapePredictorModel)


def midPoint(pointA, pointB):

    #Calculate the mid point of A and B
    X = int(pointA.x + pointB.x)/2
    Y = int(pointA.y + pointB.y)/2

    return (X,Y)


def findDist(pointA, pointB):

    #calc Eucledian Norm of point A and B
    dist = hypot((pointA[0]-pointB[0]), (pointA[1]-pointB[1]))
    return dist


def isBlinking(faces, frame):

    font  = cv2.FONT_HERSHEY_PLAIN
    ratio = ()
    thickness = 2

    #these points are written w.r.t. the 68-specific-human-face-landmarks
    left = [36,37,38,39,40,41]
    right = [42,43,44,45,46,47]


    for face in faces:
        facialLandmarks = shapePredictor(frame, face)

        #left eye markings
        lLeftPoint = (facialLandmarks.part(36).x, facialLandmarks.part(36).y)
        lRightPoint = (facialLandmarks.part(39).x, facialLandmarks.part(39).y)

        lTopPoint = midPoint(facialLandmarks.part(37), facialLandmarks.part(38))
        lBottomPoint = midPoint(facialLandmarks.part(40), facialLandmarks.part(41))

        leftHorLen = findDist(lLeftPoint, lRightPoint)
        leftVerLen = findDist(lTopPoint, lBottomPoint)


        #right eye markings
        rLeftPoint = (facialLandmarks.part(42).x, facialLandmarks.part(42).y)
        rRightPoint = (facialLandmarks.part(45).x, facialLandmarks.part(45).y)

        rTopPoint = midPoint(facialLandmarks.part(43), facialLandmarks.part(44))
        rBottomPoint = midPoint(facialLandmarks.part(46), facialLandmarks.part(47))

        rightHorLen = findDist(rLeftPoint, rRightPoint)
        rightVerLen = findDist(rTopPoint, rBottomPoint)

        #calculating the ratios of left and right eye's vertical and horizontal lengths
        lRatio = leftHorLen/leftVerLen
        rRatio = rightHorLen/rightVerLen

        #optimal threshold for a blink comes to be around 5.1
        if (lRatio >= 3.6 or rRatio >= 3.6):
            cv2.putText(frame, "blink", (50,140), font, 2, (64,64,64), thickness)
            ratio += (lRatio, rRatio, "Blink")
        else:
            ratio += (lRatio, rRatio, "No Blink")


    return ratio