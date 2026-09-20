import json,re#解析与身份

__all__=['终端关闭请求']#仅中文公开名

前缀='dsh.terminal.close.v1.'#每身份一键
身份形态=re.compile(r'^[\w-]{1,128}\Z',re.ASCII)#终端 id
本地存储=None#无浏览器存储

def 是否请求(值):#校验关闭意图
    """sessionId/id/title。"""
    if not isinstance(值,dict):#非对象
        return False#否
    会话=值.get('sessionId')#会话
    标识=值.get('id')#终端
    标题=值.get('title')#标题
    if not isinstance(会话,str) or len(会话)==0:#非法会话
        return False#否
    if not isinstance(标识,str) or 身份形态.match(标识) is None:#非法 id
        return False#否
    if not isinstance(标题,str):#非法标题
        return False#否
    return True#是

class 终端关闭请求:#刷新后仍待 Host 确认的清理
    """每个请求独立存储键，其它窗口不能覆盖。"""
    def __init__(自身):#恢复未完成清理
        """存储不可用则只留内存表。"""
        自身._请求={}#id → 请求
        if 本地存储 is None:#无浏览器
            return#跳
        try:#扫键
            for 键 in list(本地存储):#逐键
                if 键.startswith(前缀):#本前缀
                    自身._载入(键)#载
        except BaseException as 错误:#恢复失败
            print('Terminal cleanup recovery failed:',错误)#英文日志

    def 未完成(自身):#仍待确认
        """本实例拥有的未完成请求。"""
        return list(自身._请求.values())#列表

    def 保存(自身,请求):#摘标签前先记下
        """跨刷新保留清理意图。"""
        自身._请求[请求['id']]=请求#内存
        if 本地存储 is None:#无浏览器
            return#跳
        try:#持久
            本地存储[前缀+请求['id']]=json.dumps(请求,ensure_ascii=False,separators=(',',':'),allow_nan=False)#写下
        except BaseException as 错误:#配额或私密
            print('Terminal cleanup persistence failed:',错误)#英文日志

    def 移除(自身,标识):#Host 已确认
        """内存与存储一起忘掉。"""
        自身._请求.pop(标识,None)#内存
        if 本地存储 is None:#无浏览器
            return#跳
        try:#删键
            本地存储.pop(前缀+标识,None)#删
        except BaseException as 错误:
            print('Terminal cleanup persistence failed:',错误)#英文日志

    def _载入(自身,键):#一条存储
        """非法记录丢掉。"""
        try:#解析
            if 键 not in 本地存储:#空
                return#跳
            原文=本地存储[键]#原文
            解析=json.loads(原文)#对象
            if not 是否请求(解析) or 键!=前缀+解析['id']:#校验
                raise ValueError('Invalid terminal cleanup request')#非法
            自身._请求[解析['id']]=解析#收下
        except BaseException as 错误:#恢复失败
            print('Terminal cleanup recovery failed:',错误)#英文日志
