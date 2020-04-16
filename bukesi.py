# -*- coding: utf-8 -*-
2
3  # ------------------------------------
4  # Name:         bukesi
5  # Description:  
6  # Author:       kingming
7  # Date:         2020/4/10
8  # ------------------------------------

import time
import json
import struct
from socket import *
from threading import Thread
from configRead import Read
# 读取配置文件
R = Read('config.ini')
server_ip = R.getInfo('info', 'server_ip')


# 过滤消息
set_filter = {
    "message_type": "set_filter",
    "filter": ["laser", "all_file_info", "report_sensor_data_info", "set_sensor_data_info", "report_basic_status"
        , "report_obd_status", 'sensor_power_status', 'report_stat', 'report_pos_vel_status', 'auto_guided_task_status'
        , 'device_status', 'local_path', 'register_status', 'all_robot_info', 'sonar']
}
def getDate():
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

def writeLog(content):
    f1 = open('logs/boocax_'+time.strftime('%Y-%m-%d', time.localtime())+'.log', 'a+')
    f1.write(getDate()+':'+str(content)+'\n')

def receive2dic(tcp_sock):
    """ 以字节方式（bytes）接收数据，
    返回 “字典”（python 的 key-value 数据类型） """
    # 接收 4 字节的固定头部
    head_bytes = tcp_sock.recv(4)
    while 4 - head_bytes.__len__():
        head_bytes += tcp_sock.recv(4 - head_bytes.__len__())
    head_int = struct.unpack('=L', head_bytes)[0]
    # # 接收消息体
    buffer = []
    message_len = 0
    while head_int - message_len:
        data_byte = tcp_sock.recv(head_int - message_len)
        buffer.append(data_byte)
        message_len += data_byte.__len__()
        # 拼接字符串与编码转换
    str_json = (b''.join(buffer)).decode()
    return json.loads(str_json)

def pack2bytes(dic_ready):
    """ 将 JSON 消息打包成（含固定头部的）字节（bytes）数据 """
    json_str = json.dumps(dic_ready)  # Python 数据格式（dict） -> JSON 字符串
    json_bytes = json_str.encode()  # 字符串 转换编码为 bytes 格式
    # Head
    json_bytes_len = len(json_bytes)  # 计算消息的字节（bytes）长度
    message_packed = struct.pack('=L', json_bytes_len) + json_bytes
    return message_packed
    # return json_bytes

class RecvTread(Thread):
    def __init__(self, tcp_socket):
        Thread.__init__(self)
        self.s = tcp_socket

    def run(self):
        while True:
            msg = receive2dic(self.s)
            # time.sleep(1)
            # print(msg['message_type'])
            print msg


if __name__ == '__main__':
    # Socket TCP
    s = socket(AF_INET, SOCK_STREAM)
    s.connect((server_ip, 6789))

    # status
    json_packed = pack2bytes(R.getInfo('status', 'reg_client_message'))  # 注册客户端
    s.send(json_packed)
    # json_packed = pack2bytes(set_filter)  # 过滤消息
    # s.send(json_packed)
    # json_packed = pack2bytes(R.getInfo('status', 'get_all_robot_info_message'))  # 获取全部机器人信息
    # s.send(json_packed)
    # json_packed = pack2bytes(R.getInfo('status', 'report_loc_status'))  # 定位状态
    # s.send(json_packed)
    json_packed = pack2bytes(R.getInfo('status', 'move_status_v2'))  # 移动状态
    s.send(json_packed)
    json_packed = pack2bytes(R.getInfo('status', 'charge_status'))  # 充电状态
    s.send(json_packed)

    # control
    # json_packed = pack2bytes(R.getInfo('status', 'move_message'))  # 移动控制一段距离
    # s.send(json_packed)
    # json_packed = pack2bytes(R.getInfo('status', 'poi_action'))  # 导航点指定点
    # s.send(json_packed)
    # json_packed = pack2bytes(R.getInfo('control', 'goCharge'))  # 导航到对桩点并充电
    # s.send(json_packed)
    # json_packed = pack2bytes(R.getInfo('control', 'cancel_charge')) # 取消充电
    # s.send(json_packed)


    # 启动接收线程
    # RecvTread(s).start()

    i = 1
    fail = 0
    while i <= 10:
        print '*****************开始第%d轮导航****************************'%i
        writeLog('*****************开始第%d轮导航****************************'%i)
        # 导航到p4
        print '导航到p1...'
        writeLog('导航到p1...')
        json_packed = pack2bytes(R.getInfo('control', 'poi_action'))  # 导航点指定点
        s.send(json_packed)
        while True:
            msg = receive2dic(s)
            writeLog(msg)
            if msg.get('move_status') == 300:
                print '到达目的地'
                writeLog('到达目的地')
                break
            else:
                print '导航中...'
                continue

        # 导航到p5
        print '导航到p2...'
        writeLog('导航到p2...')
        json_packed = pack2bytes(R.getInfo('control', 'poi_action1'))  # 导航点指定点
        s.send(json_packed)
        while True:
            msg = receive2dic(s)
            writeLog(msg)
            if msg.get('move_status') == 300:
                print '到达目的地'
                writeLog('到达目的地')
                break
            else:
                print '导航中...'
                continue

        # 充电
        print '导航到充电点并充电'
        writeLog('导航到充电点并充电')
        json_packed = pack2bytes(R.getInfo('control', 'goCharge'))  # 导航到对桩点并充电
        s.send(json_packed)
        while True:
            msg = receive2dic(s)
            if msg.get('charge_status') == 1:
                print '正在使用充电桩充电(自动对接)'
                writeLog('正在使用充电桩充电(自动对接)')
                break
            elif msg.get('charge_status') == 0:
                print '充电失败'
                writeLog('充电失败')
                fail += 1
                break
            else:
                print '导航到充电桩...'
                continue
        time.sleep(3)
        json_packed = pack2bytes(R.getInfo('control', 'cancel_charge'))
        s.send(json_packed)
        json_packed = pack2bytes(R.getInfo('control', 'poi_action'))
        i += 1
    print '*********************已完成{}轮导航,充电失败{}次*****************************'.format(i, fail)
    writeLog('*********************已完成{}轮导航,充电失败{}次*****************************'.format(i, fail))
    # Close
    s.close()

