'内容身份到终端身份的记录彼此独立，并发写入不会互相覆盖'
from ....客户端.模块.客户端.通告 import 取握手窗口
import json#存储值
import re#身份形态
from ....基础设施.通用工具 import 紧凑json编码#键里的数组

__all__=['终端绑定']#仅这一类

前缀='dsh.terminal.binding.v1.'#存储前缀
身份形态=re.compile(r'^[\w-]{1,128}\Z',re.ASCII)#终端身份


class 终端绑定:
    '按会话和全局唯一的内容身份保存恢复目标'
    def __init__(自身):
        '只准备内存。存储在每次读写时再碰'
        自身._内存={}#键到终端身份

    def 获取(自身,会话标识,内容标识):
        '读取已保存的目标。存储不可用时保留这个窗口已经知道的值'
        键=自身._键(会话标识,内容标识)#存储键
        已知=自身._内存.get(键)#这个窗口写过的
        if 已知 is not None:#内存优先
            return 已知#已有
        try:#存储不可用则当没有
            存储=取握手窗口().localStorage#页面存储
            if 存储 is None:#没有
                return None#没有保存
            原始=存储.getItem(键)#正文
            if 原始 is None:#没有这条
                return None#没有保存
            值=json.loads(原始)#身份字符串
            if not isinstance(值,str) or 身份形态.match(值) is None:#不是合法身份
                return None#丢掉
            自身._内存[键]=值#记住
            return 值#身份
        except Exception as 存储不可用:#读失败
            return None#当没有

    def 设置(自身,会话标识,内容标识,标识):
        '在宿主分配开始前保存身份'
        键=自身._键(会话标识,内容标识)#存储键
        自身._内存[键]=标识#这个窗口先记住
        try:#存储失败不撤回内存
            存储=取握手窗口().localStorage#页面存储
            if 存储 is None:#没有
                return#只留内存
            存储.setItem(键,紧凑json编码(标识))#JSON 字符串
        except Exception as 错误:#写失败
            取握手窗口().console.error('Terminal binding persistence failed:',错误)#诊断

    def 删除(自身,会话标识,内容标识):
        '关闭意图已经保存之后，去掉这个内容的目标'
        键=自身._键(会话标识,内容标识)#存储键
        自身._内存.pop(键,None)#内存
        try:#存储失败不把内存加回来
            存储=取握手窗口().localStorage#页面存储
            if 存储 is None:#没有
                return#只清内存
            存储.removeItem(键)#存储
        except Exception as 错误:#删失败
            取握手窗口().console.error('Terminal binding cleanup failed:',错误)#诊断

    def 清空(自身):
        '客户端服务拆除时放开缓存。不删存储里的绑定'
        自身._内存.clear()#只清内存

    def _键(自身,会话标识,内容标识):
        '会话和内容身份组成的存储键'
        return 前缀+紧凑json编码([会话标识,内容标识])#稳定 JSON 数组
