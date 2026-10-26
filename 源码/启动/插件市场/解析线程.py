'在新线程里解析索引，调用线程可以因中止提前返回'
import threading#工作线程
from ...内核.智能体循环.中止与并发 import 已中止,若已中止则抛出#寿命
from .工作线程 import 执行解析#解析入口

__all__=['在线程解析索引']#仅中文公开名

def 在线程解析索引(正文,网址,信号):
    '在守护线程里跑解析。中止后不再等待；线程本身会自己结束'
    若已中止则抛出(信号)#进来时已中止
    盒子={}#结果或错误
    完成=threading.Event()#结算

    def 跑():
        '线程体'
        try:#解析
            盒子['结果']=执行解析({'body':正文,'url':网址})#请求
        except Exception as 错误:#失败
            盒子['错误']=错误#记下
        finally:#无论成败
            完成.set()#放开等待

    threading.Thread(target=跑,daemon=True).start()#不阻塞进程退出
    while not 完成.wait(0.05):#短等
        if 已中止(信号):#调用方或寿命已中止
            若已中止则抛出(信号)#不再等结果
    if '错误' in 盒子:#解析失败
        raise 盒子['错误']#原样
    return 盒子['结果']#解析结果
