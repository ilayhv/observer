import imutils
import cv2
import ConfigRead
import numpy as np
import api

def run():
    print("Импорт библиотек - завершен")
    #чтение настроек
    (ipList,camCount,video,ipLs,portLs)=ConfigRead.readSetting()
    print("Чтение настроек - завершено")
    
    listCam=[]
    frameCount=0
    listRet=[]
    listFrame=[]
    listFrameDetect=[]

    for i in range(0,int(camCount),1):
        listCam.append("cam"+str(i))# составляем массив указателей на отдельные камеры
        listRet.append(0)
        listFrame.append(0)
        listFrameDetect.append(0)
        listCam[i]=cv2.VideoCapture(str(ipList["cam"+str(i+1)+"IP"]))# устанавливаем для каждого указателя устройство захвата
    else:
        pass
    print("Создание кеша - завершено")
    while True:
        for i in range(0,int(camCount),1):
            try:
                listRet[i],listFrame[i]=listCam[i].read()#получение по одному кадру с каждой камеры
                #print(type(listFrame[i]))
                frameCount=frameCount+1
                if listFrame[i] is None:
                    print(1)
                    listCam[i]=cv2.VideoCapture(str(ipList["cam"+str(i+1)+"IP"]))
                    continue
                else:
                    pass
            except Exception as ex:
                print(ex)
                print("камера" +  str(i))
                listCam[i]=cv2.VideoCapture(str(ipList["cam"+str(i+1)+"IP"]))
                continue
        try:
            #out = np.concatenate((listFrame[0], listFrame[1]), axis=1)
            
            if frameCount==48:
                frameCount=0
                for i in range(0,int(camCount),1):
                    #listFrame[i] = imutils.resize(listFrame[i], width=300)
                    listFrameDetect[i]=api.recognize(listFrame[i])
                    listFrameDetect[i] = imutils.resize(listFrameDetect[i], width=600)
            out = np.concatenate((listFrameDetect[0], listFrameDetect[1]), axis=1)

            cv2.imshow("Camera"+str(i), out)    
            
            
            #cv2.imshow("Camera"+str(i), listFrameDetect[i])
        except Exception as ex:
            print("не смог обьединить кадр")
            print(ex)
        #    if frameCount==12 :
        #        frameCount=0    
        #        for i in range(0,int(camCount),1):
        #            cv2.imshow("Camera"+str(i), listFrame[i])
        
        key=cv2.waitKey(25)
        if key == ord("q"):
            break
    cv2.destroyAllWindows()




if __name__ == "__main__":
    run()
