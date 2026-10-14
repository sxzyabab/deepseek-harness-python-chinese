'会话 Header 按钮与 /export 共享的浏览器下载状态'
from ..路由列表 import 会话日志导出路由#导出路由
from ..归档 import 会话日志zip文件名#ZIP 文件名

def 错误消息(错误):#错误消息
    '把未知失败收成字符串。说明去掉绝对路径'
    if isinstance(错误,BaseException):
        if len(错误.args)>0 and isinstance(错误.args[0],str):
            文本=错误.args[0]
        else:
            文本=str(错误)
    else:
        文本=str(错误)
    留下=[]
    for 词 in 文本.split():
        统一=词.strip('\'"').replace('\\','/')
        if 统一.startswith('/') or 统一.startswith('~/'):
            continue
        if len(统一)>2 and 统一[0].isalpha() and 统一[1]==':' and 统一[2]=='/':
            continue
        留下.append(词)
    说明=' '.join(留下).strip()
    if 说明=='':
        return 'Export failed'
    return 说明

class 下载状态仓:#钩子源
    'getSnapshot / subscribe / update。必须是带方法的对象，不能是同名键的字典'
    def __init__(自身):
        '每个控制器一份空的按会话表'
        自身._状态={'bySession':{}}#状态
        自身._监听=set()#订阅

    def getSnapshot(自身):#读
        '当前按会话状态'
        return 自身._状态#状态

    def subscribe(自身,监听):#订阅
        '状态变化时调用；返回退订'
        自身._监听.add(监听)#登记
        def 退订():#退订
            '去掉这一个监听'
            自身._监听.discard(监听)#删
        return 退订#拆除

    def update(自身,变更):#写入
        '变换当前状态并通知'
        变更(自身._状态)#就地
        for 监听 in list(自身._监听):#扇出
            监听()#回调

class 会话日志下载控制器:#下载控制器
    '每个会话至多一个在途浏览器下载，并发布对话框状态'
    def __init__(自身,请求器=None,保存=None):
        '记下 HTTP 载体与保存操作'
        自身.store=下载状态仓()#钩子源对象
        自身._活跃={}#会话→中止旗
        自身._已拆除=False#拆除
        自身._请求器=请求器#HTTP
        自身._保存=保存#保存

    def download(自身,会话标识):#下载
        '下载一棵会话树；同一会话的并发手势共享一次操作'
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
        '关闭对话框，不取消在途下载'
        当前=自身.store.getSnapshot()['bySession'].get(str(会话标识))#条目
        if 当前 is None or 当前.get('open') is not True:#未开
            return#无事
        自身._发布(会话标识,{**当前,'open':False})#关闭

    def dispose(自身):#拆除
        '中止活跃请求'
        自身._已拆除=True#标记
        for 操作 in list(自身._活跃.values()):#逐个
            操作['aborted']=True#中止

    def _运行(自身,会话标识,中止):#一次下载
        'HEAD 探测后交给保存'
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
                    细节=''#响应正文
                    if isinstance(响应,dict):#映射
                        体=响应['body'] if 'body' in 响应 else 响应.get('text')#正文
                    else:#对象
                        体=getattr(响应,'text',None)#正文
                    if isinstance(体,bytes):#字节
                        体=体.decode('utf-8','replace')#文本
                    if isinstance(体,str) and 体!='':#有字
                        细节=' '+体#附上
                    raise RuntimeError(错误消息(f'Export failed: HTTP {状态}{细节}'))#失败
            if 自身._保存 is not None:#保存
                自身._保存(路由,会话日志zip文件名(会话标识))#保存
            表=自身.store.getSnapshot()['bySession']#按会话
            已有=表[str(会话标识)] if str(会话标识) in 表 else {}#当前
            打开=已有['open'] if 'open' in 已有 else True#仍开
            自身._发布(会话标识,{'open':打开,'status':'success','error':None})#成功
        except BaseException as 错误:
            if 中止['aborted']:#已中止
                return#停
            表=自身.store.getSnapshot()['bySession']#按会话
            已有=表[str(会话标识)] if str(会话标识) in 表 else {}#当前
            打开=已有['open'] if 'open' in 已有 else True#仍开
            自身._发布(会话标识,{'open':打开,'status':'error','error':错误消息(错误)})#失败

    def _发布(自身,会话标识,条目):#发布
        '写入按会话键控的对话框状态'
        def 变更(状态):#替换该会话
            '换掉这一条，保留其余会话'
            状态['bySession']={**状态['bySession'],str(会话标识):条目}#新表
        自身.store.update(变更)#通知

__all__=['会话日志下载控制器','下载状态仓','会话日志zip文件名']#公开面
