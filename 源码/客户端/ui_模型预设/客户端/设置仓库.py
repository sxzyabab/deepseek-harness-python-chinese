from .目录 import 预设错误#本包失败
from .呈现 import 展示权限预设#显示名

__all__=['权限预设设置控制器','权限默认于','权限设置命名空间']#仅中文公开名

权限设置命名空间='permission'#宿主线上的权限设置命名空间

class 快照存储:#简易 SnapshotStore
    """值 + 订阅。"""
    def __init__(自身,初值):
        """记下初值。"""
        自身.状态=初值#当前
        自身.监听者=set()#订阅者

    def getSnapshot(自身):
        """当前值。"""
        return 自身.状态#值

    def subscribe(自身,回调):
        """登记。"""
        自身.监听者.add(回调)#加入
        def 退订():
            """取消。"""
            自身.监听者.discard(回调)#删除
        return 退订#退订器

    def set(自身,下一份):
        """写入并通知。"""
        自身.状态=下一份#覆盖
        for 回调 in list(自身.监听者):#通知
            回调()#触发

def 权限默认于(视图,模式):
    """读取宿主 defaultPreset 模式编码的动态预设枚举。"""
    袋=视图['value'] if 'value' in 视图 else None#命名空间值
    值=袋['defaultPreset'] if 袋 is not None and 'defaultPreset' in 袋 else None#当前默认
    if isinstance(值,str) is False:#不是字符串
        raise 预设错误('permission settings has no defaultPreset value')#拒绝
    节点=模式.路径节点(模式.再水合(视图['schema']),['defaultPreset'])#复水后取字段
    if 节点 is None:#模式无该字段
        raise 预设错误('permission settings schema has no defaultPreset field')#拒绝
    if 节点['type']=='union':#联合则展开成员
        生选择=节点['list'] if 'list' in 节点 and 节点['list'] is not None else []#成员
    else:#非联合则单节点
        生选择=[节点]#单
    选项=[]#可选预设
    for 候选 in 生选择:#各常量
        if 候选['type']!='const':#非常量
            continue#丢掉
        常量=候选['value'] if 'value' in 候选 else None#常量值
        if isinstance(常量,str) is False:#非字符串
            continue#丢掉
        元=候选['meta'] if 'meta' in 候选 else None#可选元数据
        描述=元['description'] if 元 is not None and 'description' in 元 else None#可选描述
        if isinstance(描述,str) is True and len(描述)>0:#有非空描述
            标签=展示权限预设(常量,描述)#描述作显示名
        else:#否则用键本身
            标签=展示权限预设(常量,常量)#键
        选项.append({'id':常量,'label':标签})#一条选项
    含当前=False#当前值是否在选项里
    for 项 in 选项:#扫
        if 项['id']==值:#命中
            含当前=True#在
            break#停
    if len(选项)==0 or 含当前 is False:#空或当前值不在
        raise 预设错误('permission settings schema does not advertise its current preset')#拒绝
    return {'currentValue':值,'options':选项}#当前值与选项

class 权限预设设置控制器:
    """从共享镜像推导行，并经镜像写入默认。"""
    def __init__(自身,描述面,上下文,模式):
        """记下镜像面、上下文与模式服务。"""
        自身.描述面=描述面#共享镜像读/折回面
        自身.上下文=上下文#行插件上下文
        自身.模式=模式#设置模式服务
        自身.store=快照存储({#行快照
            'status':'idle',#尚未读取
            'error':None,#无错误
            'writable':False,#尚未询问可写性
            'currentValue':'',#尚无当前值
            'options':[],#尚无选项
            'revision':0,#尚无修订
        })#仓库结束
        自身.跟随=None#镜像订阅拆除
        自身.保存中=False#是否正在保存
        自身.已拆除=False#是否已拆除

    def 加载(自身):
        """开始跟随镜像并反映当前应答。"""
        if 自身.已拆除 is True:#已拆除
            return#空操作
        if 自身.跟随 is None:#首次订阅
            自身.跟随=自身.描述面.subscribe(自身.推导)#订镜像
        态=dict(自身.store.getSnapshot())#拷
        态['status']='loading'#加载中
        态['error']=None#清错误
        自身.store.set(态)#写入
        自身.描述面.确保()#确保镜像已有应答
        自身.推导()#按镜像推导行

    def 选定(自身,预设):
        """把一个预设写成后续会话默认。"""
        态=自身.store.getSnapshot()#当前行快照
        镜像=自身.描述面.getSnapshot()#镜像快照
        镜像视图=镜像['view'] if 'view' in 镜像 else None#描述符
        视图=None#权限命名空间
        if 镜像视图 is not None:#有应答
            for 项 in 镜像视图['namespaces']:#找
                if 项['ns']==权限设置命名空间:#命中
                    视图=项#记下
                    break#停
        if 视图 is None or 态['writable'] is not True or 自身.保存中 is True:#无视图、只读或保存中
            return#忽略
        自身.保存中=True#标保存中
        下一=dict(自身.store.getSnapshot())#拷
        下一['status']='saving'#保存中
        下一['error']=None#清错误
        自身.store.set(下一)#写入
        try:#调用 settings.mutate
            应答=自身.上下文.remote.settings.mutate(权限设置命名空间,[{'op':'set','path':['defaultPreset'],'value':预设}],视图['revision']).等待()#只写 defaultPreset
        finally:#无论成败
            自身.保存中=False#清保存中，折回经本行订阅到达推导
        if 自身.已拆除 is True:#已拆除
            return#丢
        if 应答['ok'] is not True:#业务失败
            自身.失败(应答['error'])#记下失败
            return#结束失败路径
        自身.描述面.接纳视图(应答['value'])#折回镜像

    def dispose(自身):
        """停止跟随镜像；之后的发布不再动快照。"""
        自身.已拆除=True#标记已拆
        if 自身.跟随 is not None:#有订阅
            自身.跟随()#卸订阅
            自身.跟随=None#清引用

    def 推导(自身):
        """按镜像推导行快照。"""
        if 自身.已拆除 is True or 自身.保存中 is True:#已拆或保存中
            return#跳过
        镜像=自身.描述面.getSnapshot()#镜像快照
        if 镜像['status']=='unavailable':#终端非回环态，行像未服务命名空间一样隐藏
            态=dict(自身.store.getSnapshot())#拷
            态['status']='unavailable'#不可用
            态['writable']=False#不可写
            态['currentValue']=''#清空当前值
            态['options']=[]#清空选项
            自身.store.set(态)#写入
            return#结束不可用
        镜像视图=镜像['view'] if 'view' in 镜像 else None#应答
        if 镜像视图 is None:#尚无应答
            if 镜像['error'] is not None:#持有失败且无应答是失败行
                自身.失败(预设错误(镜像['error']))#有错误则失败
            return#读取仍在飞则保持 loading
        视图=None#权限命名空间
        for 项 in 镜像视图['namespaces']:#找
            if 项['ns']==权限设置命名空间:#命中
                视图=项#记下
                break#停
        if 视图 is None:#命名空间不在描述符里
            态=dict(自身.store.getSnapshot())#拷
            态['status']='unavailable'#不可用
            态['writable']=False#不可写
            态['currentValue']=''#清空当前值
            态['options']=[]#清空选项
            自身.store.set(态)#写入
            return#结束缺席
        try:#解析当前默认
            解析=权限默认于(视图,自身.模式)#抽出当前值与选项
            态=dict(自身.store.getSnapshot())#拷
            态['status']='ready'#就绪
            态['error']=None#清错误
            态['writable']=镜像视图['writable']#可写性
            态['currentValue']=解析['currentValue']#当前默认
            态['options']=解析['options']#可选预设
            态['revision']=视图['revision']#记下修订
            自身.store.set(态)#写入
        except 预设错误 as 错误:#解析失败
            自身.失败(错误)#记下失败

    def 失败(自身,错误):
        """把拒绝写入错误快照。"""
        态=dict(自身.store.getSnapshot())#拷
        态['status']='error'#错误
        态['error']=str(错误)#Error 取其 message，其余 String
        自身.store.set(态)#写入
