"""会话 Header 按钮与 /export 共享的浏览器下载状态。"""
from ..路由列表 import 会话日志导出路由#导出路由
from ..归档 import 会话日志zip文件名#ZIP 文件名

初始状态={'bySession':{}}#空状态

def 错误消息(错误):#错误消息
    """把未知失败收成字符串。"""
    return str(错误)#消息

class 会话日志下载控制器:#下载控制器
    """每个会话至多一个在途浏览器下载，并发布对话框状态。"""
    def __init__(自身,请求器=None,保存=None):
        """记下 HTTP 载体与保存操作。"""
        自身.store={'getSnapshot':lambda:自身._快照,'update':自身._更新}#快照仓
        自身._快照=dict(初始状态)#状态
        自身._活跃={}#会话→中止旗
        自身._已拆除=False#拆除
        自身._请求器=请求器#HTTP
        自身._保存=保存#保存

    def download(自身,会话标识):#下载
        """下载一棵会话树；同一会话的并发手势共享一次操作。"""
        if 会话标识 in 自身._活跃:#已在途
            return#共享
        if 自身._已拆除:#已拆除
            return#忽略
        中止={'aborted':False}#中止旗
        自身._活跃[会话标识]=中止#登记
        try:#运行
            自身._运行(会话标识,中止)#运行
        finally:#清理
            自身._活跃.pop(会话标识,None)#摘掉

    def dismiss(自身,会话标识):#关闭对话框
        """关闭对话框，不取消在途下载。"""
        当前=自身._快照['bySession'].get(str(会话标识))#条目
        if 当前 is None or not 当前.get('open'):#未开
            return#无事
        自身._发布(会话标识,{**当前,'open':False})#关闭

    def dispose(自身):#拆除
        """中止活跃请求。"""
        自身._已拆除=True#标记
        for 操作 in list(自身._活跃.values()):#逐个
            操作['aborted']=True#中止

    def _运行(自身,会话标识,中止):#一次下载
        """HEAD 探测后交给保存。"""
        自身._发布(会话标识,{'open':True,'status':'downloading','error':None})#进行中
        try:#探测
            if 中止['aborted']:#已中止
                return#停
            路由=f'{会话日志导出路由}?sessionId={会话标识}&includeDescendants=true'#查询
            if 自身._请求器 is not None:#有载体
                响应=自身._请求器(路由,{'method':'HEAD'})#HEAD
                成功=响应.get('ok') if isinstance(响应,dict) else getattr(响应,'ok',True)#是否成功
                状态=响应.get('status') if isinstance(响应,dict) else getattr(响应,'status',200)#状态
                if 成功 is not True:#失败
                    raise RuntimeError(f'Export failed: HTTP {状态}')#失败
            if 自身._保存 is not None:#保存
                自身._保存(路由,会话日志zip文件名(会话标识))#保存
            打开=自身._快照['bySession'].get(str(会话标识),{}).get('open',True)#仍开
            自身._发布(会话标识,{'open':打开,'status':'success','error':None})#成功
        except BaseException as 错误:
            if 中止['aborted']:#已中止
                return#停
            打开=自身._快照['bySession'].get(str(会话标识),{}).get('open',True)#仍开
            自身._发布(会话标识,{'open':打开,'status':'error','error':错误消息(错误)})#失败

    def _发布(自身,会话标识,条目):#发布
        """写入按会话键控的对话框状态。"""
        自身._快照={'bySession':{**自身._快照['bySession'],str(会话标识):条目}}#替换

    def _更新(自身,变更):#仓更新
        """快照仓更新入口。"""
        变更(自身._快照)#就地

__all__=['会话日志下载控制器','会话日志zip文件名']#公开面
