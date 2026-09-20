"""带一条继承控制管的子进程载荷的 Windows CRT 启动描述符。"""
import struct#句柄表打包

__all__=('继承控制标准流',)#仅中文公开名

句柄字节=8#64 位句柄
无效句柄=0xffffffffffffffff#INVALID_HANDLE_VALUE
已打开=0x01#FOPEN
是管道=0x08#FPIPE
是设备=0x40#FDEV
字符文件=2#FILE_TYPE_CHAR
管道文件=3#FILE_TYPE_PIPE

def 继承控制标准流(接口表,标准流):#编码 CRT 描述符表
    """在子运行时分配描述符之前编码 CRT 描述符表。空槽保持关闭；返回的缓冲须活到 CreateProcess 返回。"""
    计数=标准流['control']['fileDescriptor']+1#描述符个数
    句柄偏移=4+计数#句柄区起点
    字节=bytearray(句柄偏移+计数*句柄字节)#整表
    struct.pack_into('<I',字节,0,计数)#个数
    下标=0#逐槽填无效句柄
    while 下标<计数:#每个槽
        struct.pack_into('<Q',字节,句柄偏移+下标*句柄字节,无效句柄)#无效
        下标+=1#下一槽
    条目=(
        (0,标准流['stdin']),#stdin
        (1,标准流['stdout']),#stdout
        (2,标准流['stderr']),#stderr
        (标准流['control']['fileDescriptor'],标准流['control']['handle']),#控制管
    )#四路
    取类型=接口表['getFileType']#文件类型
    for 描述符,句柄 in 条目:#逐项
        种类=取类型(句柄)#探测
        if 描述符==标准流['control']['fileDescriptor'] and 种类!=管道文件:#控制必须是管
            raise RuntimeError('subprocess control descriptor is not a Windows pipe')#不是管
        打开标志=已打开#打开
        if 种类==管道文件:#管
            打开标志=打开标志|是管道#FPIPE
        elif 种类==字符文件:#字符设备
            打开标志=打开标志|是设备#FDEV
        字节[4+描述符]=打开标志#标志字节
        struct.pack_into('<Q',字节,句柄偏移+描述符*句柄字节,int(句柄))#句柄值
    return bytes(字节)#STARTUPINFO 保留 CRT 字段
