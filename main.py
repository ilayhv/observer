import api
import queue
import time
import json
import threading
import logging
import random
import cv2

config=api.config()


message_queue=queue.Queue()
message_queue.maxsize=10
#################################################################
# сюда необходимо поместить код отвечающий за работу одного бокса
# распознавание машины, плашки номера и т.д.
def start_capture_box(message_queue, n_box:int):
    number=n_box
    ip=config.get_ip_camera(number)
    camera=cv2.VideoCapture(str(ip))

    exit_bit=False # бит остановки треда
    while exit_bit !=True:
        try:
            ret,frame=camera.read()
            #cv2.imshow("Camera"+str(n_box), frame)
            cv2.waitKey(25)
            
            if frame is None:
                camera=cv2.VideoCapture(str(ip))
                continue
            else:
                try:
                    message_queue.put((frame,number))
                except Exception as ex:
                    print(ex)
        except Exception as ex:
            print(ex)
            camera=cv2.VideoCapture(str(ip))
            continue
        



##################################################################
# это тред отвечающий за работу с washpro
# Он сам все делает его трогать не надо
def start_view_frame(message_queue):
    exit_bit=False # бит остановки треда
    display=api.display_compositing()
    data=config.get_display_params()
    cam_count=config.read_setting()[0]
    display.get_display_params(data[0],data[1],data[2],data[3],cam_count)

    while exit_bit !=True:

        if message_queue.empty() !=True:# проверяем сообщения в очереди  
            frame,n_box=message_queue.get() # если оно есть то берем его и отправляем в washPro
            #print("---------------")
            #print(frame)
            #print(frame.dtype)
            display.updateFrame(frame,n_box)
            out=display.concatenate_buffer()
            #print(out.shape)
            #cv2.imshow("Camera"+str(n_box), frame)

            cv2.imshow("out", out)
            cv2.waitKey(1)
        else:
            #time.sleep(0.1)
            #print("нет сообщений в очереди") 
            pass




if __name__ == "__main__":
    console_out = logging.StreamHandler()
    logging.basicConfig(level=logging.INFO)
    #################################################
    (all_box_count,_,_,_)=config.read_setting()
    all_box_count=int(all_box_count)
    #all_box_count=2 #указываем общее количество боксов
    n_box=0 # счетчик боксов для запуска тредов
    start_collect=[] #хранилище хендлеров на треды
    
    ################## ЗАПУСК ТРЕДОВ #################
    # запускаем последовательно нужное количество тредов
    while n_box !=all_box_count: 
        #запускаем тред передаем ему номер бокса и добавляем в хранилище
        start_collect.append(threading.Thread(target=start_capture_box,daemon=False, args=(message_queue,n_box)))
        print(start_collect)
        # стартуем тред
        start_collect[n_box].start()
        # переходим к следующему боксы
        n_box+=1
    
    # тред для обработки очереди и отправки данных в washpro
    start_view=threading.Thread(target=start_view_frame,daemon=False, args=(message_queue,))
    start_view.start()
    ##################################################