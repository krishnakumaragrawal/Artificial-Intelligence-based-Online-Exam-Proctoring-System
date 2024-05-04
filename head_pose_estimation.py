import numpy as np
import dlib
import math
import cv2
# from facial_detections import detectFace

def get_2d_points(img, rotation_vector, translation_vector, camera_matrix, val):
    
    #Returns the 3D points present as 2D for making annotation box.
    point_3d = []
    dist_coeffs = np.zeros((4,1))

    rear_size = val[0]
    rear_depth = val[1]
    point_3d.append((-rear_size, -rear_size, rear_depth))
    point_3d.append((-rear_size, rear_size, rear_depth))
    point_3d.append((rear_size, rear_size, rear_depth))
    point_3d.append((rear_size, -rear_size, rear_depth))
    point_3d.append((-rear_size, -rear_size, rear_depth))

    front_size = val[2]
    front_depth = val[3]
    point_3d.append((-front_size, -front_size, front_depth))
    point_3d.append((-front_size, front_size, front_depth))
    point_3d.append((front_size, front_size, front_depth))
    point_3d.append((front_size, -front_size, front_depth))
    point_3d.append((-front_size, -front_size, front_depth))

    point_3d = np.array(point_3d, dtype=np.float).reshape(-1, 3)

    #Map to 2D image points
    (point_2d, _) = cv2.projectPoints(point_3d, rotation_vector, translation_vector, camera_matrix, dist_coeffs)
    point_2d = np.int32(point_2d.reshape(-1,2))
    return point_2d


def draw_annotation_box(img, rotation_vector, translation_vector, camera_matrix, rear_size=300, rear_depth=0, front_size=500, front_depth=400, color=(255,255,0), line_width=2):

    #Draw a 3D annotation box on the face for head pose estimation.
    rear_size = 1
    rear_depth = 0
    front_size = img.shape[1]
    front_depth = front_size*2

    val = [rear_size, rear_depth, front_size, front_depth]
    point_2d = get_2d_points(img, rotation_vector, translation_vector, camera_matrix, val)

    #Draw all the lines
    cv2.polylines(img, [point_2d], True, color, line_width, cv2.LINE_AA)
    cv2.line(img, tuple(point_2d[1]), tuple(point_2d[6]), color, line_width, cv2.LINE_AA)
    cv2.line(img, tuple(point_2d[2]), tuple(point_2d[7]), color, line_width, cv2.LINE_AA)
    cv2.line(img, tuple(point_2d[3]), tuple(point_2d[8]), color, line_width, cv2.LINE_AA)

    
def head_pose_points(img, rotation_vector, translation_vector, camera_matrix):

    #Get the points to estimate head pose sideways
    rear_size = 1
    rear_depth = 0
    front_size = img.shape[1]
    front_depth = front_size*2

    val = [rear_size, rear_depth, front_size, front_depth]
    point_2d = get_2d_points(img, rotation_vector, translation_vector, camera_matrix, val)

    y = (point_2d[5] + point_2d[8]) // 2
    x = point_2d[2]

    return  (x,y)

#3D Model points
model_points = np.array([
    (0.0, 0.0, 0.0),            #Nose tip
    (0.0, -330.0, -65.0),       #Chin
    (-255.0, 170.0, -135.0),    #Left eye left corner
    (225.0, 170.0, -135.0),     #Right eye right corner
    (-150.0, -150.0, -125.0),   #Left mouth corner
    (150.0, -150.0, -125.0)     #Right mouth corner
])

# cap = cv2.VideoCapture(0)
# ret, img = cap.read()

size = (480, 640, 3)
font = cv2.FONT_HERSHEY_PLAIN

#Camera internals
focal_length = size[1]
center = (size[1]/2, size[0]/2)

camera_matrix = np.array(
    [[focal_length, 0, center[0]],
    [0, focal_length, center[1]],
    [0, 0, 1]], dtype = "double"
)

shapePredictorModel  = 'shape_predictor_model/shape_predictor_68_face_landmarks.dat'
shapePredictor = dlib.shape_predictor(shapePredictorModel)

# while True:
#     ret, img = cap.read()
#     if ret == True:
#         faceCount, faces = detectFace(img)
    
def head_pose_detection(faces, img):

    for face in faces:
        marks = shapePredictor(img, face)

        image_points = np.array([
            [marks.part(30).x, marks.part(30).y],    #Nose tip
            [marks.part(8).x, marks.part(8).y],      #Chin
            [marks.part(36).x, marks.part(36).y],    #Left eye left corner
            [marks.part(45).x, marks.part(45).y],    #Right eye right corner
            [marks.part(48).x, marks.part(48).y],    #Left Mouth corner
            [marks.part(54).x, marks.part(54).y]     #Right mouth corner
        ], dtype="double")

        dist_coeffs = np.zeros((4,1))
        (success, rotation_vector, translation_vector) = cv2.solvePnP(model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_UPNP)

        #Draw the annotation box
        # draw_annotation_box(img, rotation_vector, translation_vector, camera_matrix)


        (nose_end_point2D, jacobian) = cv2.projectPoints(np.array([(0.0, 0.0, 1000.0)]), rotation_vector, translation_vector, camera_matrix, dist_coeffs)

        for p in image_points:
            cv2.circle(img, (int(p[0]), int(p[1])), 3, (0,0,255), -1)


        # Represent the coordinates of the nose tip 
        p1 = ( int(image_points[0][0]), int(image_points[0][1]))

        # Represents the coordinates of projected nose tip after estimating the head pose
        p2 = ( int(nose_end_point2D[0][0][0]), int(nose_end_point2D[0][0][1]))

        x1, x2 = head_pose_points(img, rotation_vector, translation_vector, camera_matrix)

        # Drawing Lines for the better visualization.
        # cv2.line(img, p1, p2, (0, 255, 255), 2)
        # cv2.line(img, tuple(x1), tuple(x2), (255, 255, 0), 2)

        try:
            m = (p2[1] - p1[1])/(p2[0] - p1[0])
            ang1 = int(math.degrees(math.atan(m)))
        except:
            ang1 = 90
            
        try:
            m = (x2[1] - x1[1])/(x2[0] - x1[0])
            ang2 = int(math.degrees(math.atan(-1/m)))
        except:
            ang2 = 90

        # print(ang1)
        # print(ang2)

        if ang1 >= 45:
            print('Head up')
            cv2.putText(img, 'Head up', (50, 50), font, 2, (255, 255, 128), 2)
            return "Head Up"
        elif ang1 <= -45:
            print('Head down')
            cv2.putText(img, 'Head down', (50, 50), font, 2, (255, 255, 128), 2)
            return "Head Down"
        if ang2 >= 45:
            print('Head right')
            cv2.putText(img, 'Head right', (50, 30), font, 2, (255, 255, 128), 2)
            return "Head Right"
        elif ang2 <= -45:
            print('Head left')
            cv2.putText(img, 'Head left', (50, 30), font, 2, (255, 255, 128), 2)
            return "Head Left"

        cv2.putText(img, str(ang1), tuple(p1), font, 2, (128, 255, 255), 3)
        cv2.putText(img, str(ang2), tuple(x1), font, 2, (255, 255, 128), 3)
        return -1   