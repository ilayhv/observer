import numpy as np
import cv2
import imutils
import time
import math
import configparser
import os

def rotationFrame(frame):
    angle=90
    frame = imutils.rotate_bound(frame, angle)
    return(frame)


class recognize():

    def __init__(self):
        labelsPath = "coco.names"
        self.labels=open(labelsPath).read().strip().split("\n")
        print(self.labels)
        weightsPath = "yolov3.weights"
        configPath = "yolov3.cfg"
        print("[INFO] loading YOLO from disk...")
        self.net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)
        self.ln = self.net.getLayerNames()
        self.ln = [self.ln[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]
        self.plate_cascade = cv2.CascadeClassifier()
        self.plate_cascade.load("haarcascade_russian_plate_number.xml")


    def recognize(self, frame):
        #frame=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        (H, W) = frame.shape[:2]

        blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416),
	     swapRB=False,crop=True)
        self.net.setInput(blob)

        start = time.time()
        layerOutputs = self.net.forward(self.ln)
        end = time.time()
        print("[INFO] YOLO took {:.6f} seconds".format(end - start))

        boxes = []
        confidences = []
        classIDs = []
        frameCar = []
        threshold=0.1
        for output in layerOutputs:
            for detection in output:
                scores = detection[5:]
                classID = np.argmax(scores)
                confidence = scores[classID]
                if confidence > threshold:
                    box = detection[0:4] * np.array([W, H, W, H])
                    (centerX, centerY, width, height) = box.astype("int")

                    x = int(centerX - (width / 2))
                    y = int(centerY - (height / 2))
                    boxes.append([x, y, int(width), int(height)])
                    confidences.append(float(confidence))
                    classIDs.append(classID)
        idxs = cv2.dnn.NMSBoxes(boxes, confidences, threshold, 0.5)
        print(idxs)
        if len(idxs) > 0:
            for i in idxs.flatten():

                (x, y) = (boxes[i][0], boxes[i][1])
                (w, h) = (boxes[i][2], boxes[i][3])
                color = (255,255,0)
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                text = "{}: {:.4f}".format(self.labels[classIDs[i]], confidences[i])
                print(self.labels[classIDs[i]])
                if self.labels[classIDs[i]]=="car" or "truck":
                    frameCar=frame[y:y+h,x:x+w]
                cv2.putText(frame, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        return(frame,frameCar)

    
    def plate_recognize(self,frame):
        numberPlate=[]
        try:
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame_gray = cv2.equalizeHist(frame_gray)
            plate = self.plate_cascade.detectMultiScale(frame_gray)
            for (x,y,w,h) in plate:
                frame=cv2.rectangle(frame, (x, y), (x+w, y+h),
                    (255, 0, 255), 2)
                carROI = frame_gray[y:y+h,x:x+w]
                carROI=cv2.cvtColor(carROI,cv2.COLOR_GRAY2BGR)
                numberPlate.append(carROI)
        except Exception as ex:
            print(ex)
        return(frame,numberPlate)


    def set_horizont(self,frame):
        status=False
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        (h, w) = frame_gray.shape

        edge=cv2.Canny(frame_gray,100,200,apertureSize = 3)
        lines = cv2.HoughLinesP(edge, 1, np.pi/180, int(w/3), maxLineGap=50)
        t=0
        i=0
        if lines is not None:
            for line in lines:
                i+=1
                x1, y1, x2, y2 = line[0]
                t=t+(math.fabs(y2-y1)/math.fabs(x1-x2))
        if i !=0:
            status=True
            r=t/i
            angle=-(math.atan(r)*180)/math.pi
            n=1.4
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, n)
            frame = cv2.warpAffine(frame, M, (int(w*n), int(h*n)),borderValue=0)
        return(frame, status)


class config():

    def __init__(self):
        pathSetting = "settings.ini"
        config = configparser.ConfigParser()
        config.read(pathSetting)
        self.camCount = config.get("Settings", "camCount")
        self.ip_washpro=config.get("washpro", "ip")
        self.port_washpro=config.get("washpro", "port")
        self.len_h=config.get("display", "len_h")
        self.len_w=config.get("display", "len_w")
        self.width_frame=config.get("display", "width")
        self.height_frame=config.get("display", "height")
        i=1
        self.ipList=[]
        for i in range(1,12,1):
            row="cam"+str(i)+"IP"
            self.ipList.append(config.get("Settings",row))

        
        
    def read_setting(self):
        return (
            self.camCount,
            self.ip_washpro,
            self.port_washpro,
            self.ipList
        )


    def get_display_params(self):
        return(
            self.len_h,
            self.len_w,
            self.width_frame,
            self.height_frame
        )

    def get_ip_camera(self, nBox):
        return(self.ipList[nBox])


class display_compositing():

    def get_display_params(self, len_h, len_w, width, height, cam_count):
        #создаем фреймбуффер
        self.frame_buffer=[]
        self.height=int(height)
        self.width=int(width)
        # делаем количество фреймов четными
        cam_count=int(cam_count)
        if cam_count%2 !=0:
            cam_count+=1       
        # определяем сколько будет в строке фреймов
        self.len_h=int(cam_count/2)
        #делаем болванку фрейма
        frame=np.zeros((int(height),int(width),3),dtype=np.uint8)       
        #начальная ини буффера
        for i in range(0,int(cam_count),1):
            self.frame_buffer.append(frame)


    def concatenate_buffer(self):
        #out_x=np.array()
        #out_x=np.array()
        # небольшая окантовочка для фрейма чтобы могла нормально сложить
        out_x=np.zeros((self.height,1,3),dtype=np.uint8)
        out_y=np.zeros((self.height,1,3),dtype=np.uint8)

        # складываем первую линию
        for x in range(0,self.len_h,1):
            #print("||||||||||||||||||||")
            #print(self.frame_buffer[x])
            out_x=np.concatenate((out_x,self.frame_buffer[x]), axis=1)
        #print(out_x)
        # складываем вторую линию
        for x in range(0,self.len_h,1):
            out_y=np.concatenate((out_y,self.frame_buffer[int(x+(self.len_h))]), axis=1)
        #print(out_y)
        # окончательное сложение 2х линий
        out=np.concatenate((out_x,out_y),axis=0)
        return (out)

    def updateFrame(self, frame, i):
        frame1=cv2.resize(frame,(self.width,self.height))
        self.frame_buffer[i]=frame1


if __name__=="__main__":
    config=config()
    
    display=display_compositing()
    data=config.get_display_params()
    cam_count=config.read_setting()[0]
    print(cam_count)
    display.get_display_params(data[0],data[1],data[2],data[3],cam_count)
    frame=display.concatenate_buffer()
    cv2.imshow("frame", frame)
    cv2.waitKey(0)
    