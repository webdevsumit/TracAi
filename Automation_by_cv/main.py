import cv2
# from matplotlib import pyplot as plt
import numpy as np
import time

import requests

requestUrl = 'http://192.168.137.19/'

URL = "http://192.168.137.132"
cap = cv2.VideoCapture(URL + ":81/stream")

pTime = 0
window_name = 'image'

VCalRange = 50
HCalRange = 20
RangeAbsoluteCalValue = 20

isMovingForward = False
isMovingBackward = False

def moveLeft():
    res = requests.get(requestUrl+'left')
    print(res)
    if res.status_code == 200:
        isMovingForward = True
        isMovingBackward = False

def moveRight():
    res = requests.get(requestUrl+'right')
    print(res)
    return res.status_code == 200

def stopFrontWheels():
    res = requests.get(requestUrl+'stopFrontWheels')
    print(res)
    return res.status_code == 200

def moveForward():
    res = requests.get(requestUrl+'forward')
    print(res.status_code == 200)
    if res.status_code == 200:
        isMovingForward = True
        isMovingBackward = False

def moveBackward():
    res = requests.get(requestUrl+'backward')
    print(res)
    if res.status_code == 200:
        isMovingForward = False
        isMovingBackward = True

def stopBackWheels():
    res = requests.get(requestUrl+'stopBackWheels')
    print(res)
    if res.status_code == 200:
        isMovingForward = False
        isMovingBackward = True


def getPointsInLine(points):
    if len(points)<2:
        return []
    newPoints = []
    for key in points.keys():
        lst = points[key]
        if len(lst) == 0:
            continue
        for point in lst:
            newPoints.append([point, key])
    
    sorted(newPoints, key=lambda x: x[0])
    if len(newPoints)<1:
        return []
    start = newPoints[0][0]
    end = newPoints[len(newPoints)-1][0]
    startIndex = 0
    endIndex = len(newPoints)
    lastMidIndexOfArray = startIndex + int((endIndex - startIndex)/2)
    lastMidPoint = (end-start)/2
    while start < end:

        mid = (end-start)/2
        midIndexOfArray = startIndex + int((endIndex - startIndex)/2)
        
        if midIndexOfArray == startIndex or midIndexOfArray == endIndex:
            break

        if mid < newPoints[midIndexOfArray][0]:
            start = mid
            startIndex = midIndexOfArray
        else:
            end = mid
            endIndex = midIndexOfArray

        if len(newPoints[startIndex : endIndex]) > 0:
            lastMidPoint = int(mid)

    newPoints = []
    for key in points.keys():
        lst = points[key]

        if len(lst) < 1:
            continue

        closerValue = lst[0] 
        for point in lst:
            if np.abs(point-lastMidPoint) < np.abs(closerValue-lastMidPoint):
                closerValue = point
        
        newPoints.append(closerValue)

    return newPoints

def getAngleOfPointsLine(points):
    angle = 0
    for i in range(2, len(points)):
        angle += (points[i] - points[i-1])
    return angle


moveForward()

while True:
    ret, frame = cap.read()
    horizontalLineRange = []
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    VCalRangeStartPoint = frame.shape[0] - VCalRange

    verticalAverageColorRange = []
    topBarAvg = 0
    bottomBarAvg = 0


    for it in range(-110, -100):
        topBarAvg += (np.average(frame[it])/2)
        bottomBarAvg += (np.average(frame[it+40])/2)

        frame[it][0:10] = topBarAvg
        frame[it+40][0:10] = bottomBarAvg

        print((topBarAvg - bottomBarAvg))

        if (topBarAvg - bottomBarAvg) < -20:
            while isMovingForward:
                stopBackWheels()

    averageListRange = {}
    for it in range(VCalRangeStartPoint, frame.shape[0]):
        averageColor = np.average(frame[it])
        if not averageListRange.get(it):
            averageListRange[it] = []
        for i in range(0, frame.shape[1]-1):

            if frame[it][i] < averageColor and frame[it][i+1] > averageColor:
                averageListRange[it].append(i)
                # frame[it][i] = 0
            # else:
                # frame[it][i] = 255

    # averageLineRange id 2d and getPointsInLine will return 1d
    averageListRange1D = getPointsInLine(averageListRange)
    angleOfLine = getAngleOfPointsLine(averageListRange1D)

    if len(averageListRange1D)>1:
        if averageListRange1D[0] > 90:
            moveRight()
        elif averageListRange1D[0] > 10:
            moveLeft()
        else:
            if angleOfLine > 0.017:
                moveRight()
            elif angleOfLine < -0.017:
                moveLeft()

    cTime = time.time()
    fps = 1/(cTime-pTime) if (cTime-pTime) != 0 else 1
    pTime = cTime

    cv2.putText(frame, str(int(fps)), (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
    cv2.imshow(window_name, frame)

    # plt.hist(frame.ravel(),256,[0,256])
    # plt.show()

    # Exit if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

