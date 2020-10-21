# набор инструментов для создания соединения и передачи данных в модуль washpro

import socket
import json
import time
import struct
import logging
import os
import queue
import random
import threading
import configparser



class connect_api():

    def __init__(self):
        """
        чтение адреса и порта куда надо подключиться
        ну и добавление всего остального что потребуется
        """
        pathSetting = "settings.ini"
        config = configparser.ConfigParser()
        config.read(pathSetting)
        try:
            self.IP=str(config.get("washpro", "ip"))
        except:
            self.IP="127.0.0.1"
        try:
            self.PORT=int(config.get("washpro", "port"))
        except:
            self.PORT=12345

    def connect(self):
        """
        Выполняет соединение с Washpro, при успешном соединении
        возврашает self.status_connect=True соединение установлено и можно пользоваться дальше
        False- необходимо вызвать еще раз функцию либо проверить натройки и т.д.
        """

        self.status_connect=False
        sockLS = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sockLS.settimeout(5)
        try:
            sockLS.connect((self.IP,self.PORT))
            self._sockLs=sockLS
            msg = {"cmd":"init","msg":""}
            msg=json.dumps(msg)
            message=str(msg)+"\r\n"
            logging.info(message)
            sockLS.send(message.encode('utf-8'))
            try:
                recv=sockLS.recv(4)
                logging.info(recv)
                lenMsg,=struct.unpack("L",recv)
                logging.info(lenMsg)
                recv=sockLS.recv(lenMsg)
                logging.info(recv)
                try:
                    data=json.loads(recv.decode("UTF-8"))
                    print(data)
                    if data["ans"]=="init" and data["msg"] !=0:
                        logging.info(data["msg"])
                        logging.info(time.ctime()+" -- Синхронизация с WashPro выполнена")
                        self.status_connect=True
                    else:
                        logging.info(time.ctime()+" -- Синхронизация с WashPro не выполнена")
                except Exception as ex:
                    logging.info("Ошибка декодера")
                    logging.info(time.ctime()+f" -- {ex}")
                    logging.info(data)
            except Exception as ex:
                logging.info(time.ctime()+" -- Произошла дичь и WashPro не отвечает")
                logging.info(time.ctime()+f" -- {ex}")
        except socket.gaierror:# обработка ошибок сокета
            logging.info(time.ctime()+" -- Невозможно открыть соединение\nПроверьте сетевую карту и настройки брендмауэра!")
        except ConnectionResetError:# при ошибочном ключе дисконект со стороны ЦС
            logging.info(time.ctime()+" -- ЛС завершил работу в процессе подключения!")
        except ConnectionRefusedError:
            logging.info(time.ctime()+" -- WashPro не запущен!")
            sockLS.close()
        except Exception as ex:
            logging.info(time.ctime()+" -- Ошибка соединения с WashPro!")
            logging.info(time.ctime()+f" -- {ex}")
        return(self.status_connect)

    def send_carnumber(self,number:str,nbox:int):
        """
        пердает в washpro информацию о распознанномномере и боксе в котором происходило распознавание
        number=номер автомобиля
        nbox=номер бокса

        возвращает 2 параметра
        self.status_connect - состояние соединения с washpro, при обрыве либо какой тонепонятной дичи сбрасывается в False и надо заново сделать connect
        self.status_transmit - состояние передачи, если данные переданы то True, если ответ не пришел то False
        """

        
        self.status_transmit=False
        sockLS=self._sockLs
        msg = {"cmd":"get_number","msg":"","nbox": 0,"number":""}
        msg["nbox"]=nbox
        msg["number"]=number
        msg=json.dumps(msg)
        #logging.info(msg)
        message=str(msg)+"\r\n"
        #logging.info(message)
        logging.info(time.ctime()+" -- Отправка сообщения в WashPro")
        try:
            sockLS.send(message.encode('utf-8'))
            logging.info(time.ctime()+" -- Cообщения в WashPro отправлено") 
            self.status_transmit=True    
        except socket.timeout:
            logging.info(time.ctime()+" -- WashPro не отвечает")
        try:
            recv=sockLS.recv(4)
            logging.info(recv)
            lenMsg,=struct.unpack("L",recv)
            logging.info(lenMsg)
            recv=sockLS.recv(lenMsg)
            logging.info(recv)
            try:
                data=json.loads(recv.decode("UTF-8"))
                print(data)
                if data["ans"]=="get_number" and data["msg"] !=0:
                    logging.info(data["msg"])
                    logging.info(time.ctime()+" -- Сообщение в WashPro доставлено")
                    self.status_connect=True
                    self.status_transmit=True
                else:
                    logging.info(time.ctime()+" -- Сообщение в WashPro не доставлено")
                    self.status_transmit=False
            except Exception as ex:
                logging.info("Ошибка декодера")
                logging.info(time.ctime()+f" -- {ex}")
                logging.info(data)
                self.status_transmit=False
        except Exception as ex:
            logging.info(time.ctime()+" -- Произошла дичь и WashPro не отвечает")
            logging.info(time.ctime()+f" -- {ex}")
            self.status_connect=False
        return (self.status_connect, self.status_transmit)       

    def close(self):
        """
        Корректно завершает сессию с washpro
        """
        try:
            logging.info(time.ctime()+" --  Закрытие соединения с Washpro")
            self._sockLs.close()
        except:
            logging.info(time.ctime()+" --  Ошибка закрытия соединения с Washpro! Соединение не было установлено!")



    