__all__=['代际目录','空代际状态']#仅中文公开名

def 空代际状态():#共享目录冷启动
    """无值、空闲。"""
    return {'value':None,'status':'idle','error':None}#冷启动

class 简易快照存储:#对 uSES 安全的浅存储
    """订阅 + 可变快照。"""
    def __init__(自身,初始):#初始快照
        """记下状态与订阅表。"""
        自身.状态=dict(初始)#可变
        自身.订阅列表=[]#监听

    def getSnapshot(自身):#读快照
        """返回浅拷贝。"""
        return dict(自身.状态)#拷贝

    def subscribe(自身,监听器):#订阅
        """返回拆除器。"""
        自身.订阅列表.append(监听器)#登记
        def 拆除订阅():#拆除
            """去掉监听。"""
            if 监听器 in 自身.订阅列表:#仍在
                自身.订阅列表.remove(监听器)#删
        return 拆除订阅#拆除器

    def update(自身,改):#改快照
        """改函数就地改状态后广播。"""
        改(自身.状态)#改
        for 监听器 in list(自身.订阅列表):#广播
            监听器()#回调

    def set(自身,下一快照):#整表替换
        """写快照并广播。"""
        自身.状态=dict(下一快照)#替换
        for 监听器 in list(自身.订阅列表):#广播
            监听器()#回调

class 代际目录:#每个会话选择器共享的 Host 代际模型目录
    """为当前 Host 代际最多加载一份模型目录。"""
    def __init__(自身,上下文):#注入提供方插件上下文
        """记下上下文与初始存储。"""
        自身.上下文=上下文#remote.session 所在上下文
        自身.存储=简易快照存储(空代际状态())#共享目录存储
        自身.世代=0#代际计数
        自身.飞行=None#飞行中加载结果箱

    def load(自身):#返回当代目录
        """共享其一次飞行中加载；内部阻塞。"""
        态=自身.存储.getSnapshot()#当前状态
        if 态['status']=='ready' and 态['value'] is not None:#已就绪
            return 态['value']#目录
        if 自身.飞行 is not None:#共享飞行
            return 自身.飞行#同一结果
        世代=自身.世代#捕获代际
        def 标加载(稿):#loading
            """标 loading。"""
            稿['status']='loading'#加载中
            稿['error']=None#清错
        自身.存储.update(标加载)#loading
        try:#拉目录
            应答=自身.上下文.remote.session.modelCatalog().等待()#Host 目录
            结果=应答['result'] if 'result' in 应答 else 应答#信封
            if not 结果['ok']:#业务失败
                错=结果['error'] if 'error' in 结果 and 结果['error'] is not None else {}#错误
                raise RuntimeError(str(错['code'] if 'code' in 错 else None)+': '+str(错['message'] if 'message' in 错 else None))#抛
            值=结果['value']#目录值
            if 世代==自身.世代:#仍是当代
                自身.存储.set({'value':值,'status':'ready','error':None})#写入就绪
            自身.飞行=值#记下结果供共享
            return 值#返回目录
        except BaseException as 错误:#失败
            if 世代==自身.世代:#仍是当代
                文=str(错误)#错误文案
                def 写错(稿):#错误态
                    """标 error。"""
                    稿['status']='error'#错误
                    稿['error']=文#文案
                自身.存储.update(写错)#写
            raise#继续抛
        finally:#无论成败
            if 世代==自身.世代:#当代才清
                自身.飞行=None#清飞行

    def _失效(自身,清空=False):#使已加载目录失效
        """下次显式菜单读取会重载。"""
        自身.世代+=1#推进代际
        自身.飞行=None#丢飞行
        值=None if 清空 else 自身.存储.getSnapshot()['value']#是否清值
        自身.存储.set({'value':值,'status':'idle','error':None})#回空闲

    def refresh(自身):#Host 侧模型输入变更后使目录失效并重载
        """失效后重载；错误由选择器暴露。"""
        自身._失效()#失效
        try:#重载
            自身.load()#加载
        except BaseException:#吞掉
            pass#选择器暴露

    def resetGeneration(自身):#清除 Host 特定值并加载替换的 Host 代际
        """清值失效后重载。"""
        自身._失效(True)#清值失效
        try:#重载
            自身.load()#加载
        except BaseException:#吞掉
            pass#选择器暴露
