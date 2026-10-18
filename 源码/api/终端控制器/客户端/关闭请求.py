'未完成的关闭请求在刷新后还在。和已经去掉的侧栏标签无关'
from ....客户端.模块.客户端.通告 import 取握手窗口
import json#请求正文
import re#身份形态

__all__=['终端关闭请求']#仅这一类

前缀='dsh.terminal.close.v1.'#每个请求自己的键
身份形态=re.compile(r'^[\w-]{1,128}\Z',re.ASCII)#终端身份


class 终端关闭请求:
    '每个请求单独一个存储键，别的窗口不能盖掉它的清理'
    def __init__(自身):
        '从本地存储收回还没被宿主确认的关闭'
        自身._请求={}#身份到请求
        try:#没有存储就只留内存
            存储=取握手窗口().localStorage#页面存储
            if 存储 is None:#没有
                return#只留内存
            长度=存储['length']#条数
            序号=0#下标
            while 序号<长度:#逐条
                键=存储.key(序号)#键
                序号+=1#前进
                if 键 is not None and str(键).startswith(前缀):#是关闭请求
                    自身._载入(str(键))#收一条
        except Exception as 错误:#恢复失败只记日志
            取握手窗口().console.error('Terminal cleanup recovery failed:',错误)#诊断

    def 未完成(自身):
        '还在等宿主确认的请求'
        return list(自身._请求.values())#拷贝

    def 保存(自身,请求):
        '先记下清理，再允许摘掉标签'
        自身._请求[请求['id']]=请求#内存
        try:#存储失败仍留在内存
            取握手窗口().localStorage.setItem(前缀+请求['id'],json.dumps(请求,ensure_ascii=False))#跨刷新
        except Exception as 错误:#写失败
            取握手窗口().console.error('Terminal cleanup persistence failed:',错误)#诊断

    def 移除(自身,标识):
        '宿主确认后从内存和存储忘掉'
        自身._请求.pop(标识,None)#内存
        try:#存储失败不把请求加回来
            取握手窗口().localStorage.removeItem(前缀+标识)#存储
        except Exception as 错误:#删失败
            取握手窗口().console.error('Terminal cleanup persistence failed:',错误)#诊断

    def _载入(自身,键):
        '非法记录丢掉并记日志'
        try:#解析一条
            原始=取握手窗口().localStorage.getItem(键)#正文
            if 原始 is None:#已经没了
                return#跳过
            解析=json.loads(原始)#对象
            if not isinstance(解析,dict):#不是对象
                raise RuntimeError('Invalid terminal cleanup request')#丢掉
            会话=解析.get('sessionId')#会话
            标识=解析.get('id')#终端
            标题=解析.get('title')#标题
            会话合法=isinstance(会话,str) and len(会话)>0#非空会话
            身份合法=isinstance(标识,str) and 身份形态.match(标识) is not None#身份形态
            标题合法=isinstance(标题,str)#标题只要是字符串
            if not 会话合法 or not 身份合法 or not 标题合法 or 键!=前缀+标识:#对不上键
                raise RuntimeError('Invalid terminal cleanup request')#丢掉
            自身._请求[标识]=解析#收下
        except Exception as 错误:#这一条坏了
            取握手窗口().console.error('Terminal cleanup recovery failed:',错误)#诊断
