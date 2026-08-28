"""pi-ai 提供方档案的模型列表与端点探询。

对齐上游 `ui-settings-models/src/client/ModelListEditor.tsx`。公开面仅中文名。
空列表表示沿用内置目录；任一条目即整体替换。探询问的是表单当前值（含未存密钥）。
"""
import re#正则
from ...依赖 import cordis#外部依赖胶水
是否thenable=cordis.工具.是否thenable#可等待判定
from .DeepSeek模型编辑器 import 解析容量,格式化容量#容量拼写
from .仓库 import 错误文案#拒绝文案

__all__=[#仅中文公开名
    '容量提示','采纳候选','模型列表编辑器','ModelListEditor','ModelDraft','ProbeTarget',
]#公开面结束

容量提示={'contextWindow':'256K','maxTokens':'32K'}#空字段占位（适配器回退量级）

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 解开(值):#承诺则等待
    """承诺则等待，否则原样。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

def 文本自(模型,键):#行文本字段
    """非字符串则空串。"""
    值=模型.get(键) if isinstance(模型,dict) else None#值
    return 值 if isinstance(值,str) else ''#文本

def 数字自(模型,键):#行数字字段
    """非数字则 None。"""
    值=模型.get(键) if isinstance(模型,dict) else None#值
    return 值 if isinstance(值,(int,float)) and not isinstance(值,bool) else None#数字

def 容量拼写(值):#存量容量→字段文本
    """未设为空串。"""
    return '' if 值 is None else 格式化容量(值)#拼写

def 采纳候选(候选):#发现结果→草稿行
    """保留端点披露的容量。"""
    行={'id':取字段(候选,'id')}#必有 id
    名称=取字段(候选,'name')#可选名
    if 名称 is not None:#有名
        行['name']=名称#记下
    上下文=取字段(候选,'contextWindow')#上下文
    if 上下文 is not None:#有
        行['contextWindow']=上下文#记下
    上限=取字段(候选,'maxTokens')#上限
    if 上限 is not None:#有
        行['maxTokens']=上限#记下
    return 行#草稿

ModelDraft=dict#上游别名
ProbeTarget=dict#上游别名

class 模型列表编辑器:#模型列表 + 探询
    """行编辑、展开容量、探询采纳对话框。"""
    def __init__(自身,属性):#构造
        """记下 props 与本地态。"""
        自身.属性=属性#合成 props
        自身.忙=False#探询在飞
        自身.失败=None#失败文案
        自身.候选=None#发现列表或 None
        自身.已选=set()#勾选 id
        自身.已展开=set()#展开行号
        自身.编辑中={}#缓冲键→文本

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 缓冲键(自身,下标,字段):#容量缓冲键
        """`index:field`。"""
        return f'{下标}:{字段}'#键

    def 改容量(自身,下标,字段,文本):#键入容量
        """缓冲并解析写入行。"""
        自身.编辑中[自身.缓冲键(下标,字段)]=文本#缓冲
        自身.补丁(下标,{字段:解析容量(文本)})#写行

    def 容量文本(自身,模型,下标,字段):#容量显示
        """优先缓冲。"""
        键=自身.缓冲键(下标,字段)#键
        if 键 in 自身.编辑中:#有键入
            return 自身.编辑中[键]#键入
        return 容量拼写(数字自(模型,字段))#存量

    def 移除重键(自身,当前,下标):#删行后重键缓冲
        """丢被删行，其后行号减一。"""
        下一={}#新图
        for 键,值 in 当前.items():#每缓冲
            位=int(键[:键.index(':')])#行号
            if 位==下标:#被删
                continue#跳过
            新键=re.sub(r'^\d+',str(位-1),键,count=1) if 位>下标 else 键#重键
            下一[新键]=值#记下
        return 下一#新图

    def 切换展开(自身,下标):#切换披露
        """开则关，关则开。"""
        if 下标 in 自身.已展开:#已开
            自身.已展开.discard(下标)#关
        else:#未开
            自身.已展开.add(下标)#开

    def 补丁(自身,下标,下一):#改一行
        """清空字段则从档案丢掉。"""
        模型们=list(取字段(自身.属性,'models') or [])#当前
        清除=set(键 for 键,值 in 下一.items() if 值 is None or 值=='')#待清
        结果=[]#新表
        for 位,模型 in enumerate(模型们):#逐行
            if 位!=下标:#非目标
                结果.append(dict(模型))#拷贝
                continue#下一项
            合并={**dict(模型),**下一}#合并
            结果.append({键:值 for 键,值 in 合并.items() if 键 not in 清除})#丢掉清空
        变更=取字段(自身.属性,'onChange')#回调
        if 变更 is not None:#有
            变更(结果)#通知

    def 探询(自身):#问端点当前表单
        """发现模型；失败文案挂本面。"""
        自身.忙=True#在飞
        自身.失败=None#清错
        探测=取字段(自身.属性,'probe') or {}#探测目标
        接口=取字段(自身.属性,'api')#llm 面
        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案
        try:#探询
            请求={'settingsNs':取字段(探测,'settingsNs')}#基础
            if 取字段(探测,'provider') is not None:#有路由
                请求['provider']=取字段(探测,'provider')#带上
            基址=取字段(探测,'baseURL')#端点
            if isinstance(基址,str) and len(基址)>0:#有端点
                请求['baseURL']=基址#带上
            if 取字段(探测,'api') is not None:#有协议
                请求['api']=取字段(探测,'api')#带上
            if 取字段(探测,'apiKey') is not None:#有密钥
                请求['apiKey']=取字段(探测,'apiKey')#带上
            响应=解开(接口.llm.discoverModels(请求))#发现
            结果=取字段(响应,'result')#结果
            if 取字段(结果,'ok') is not True:#失败
                自身.失败=取字段(取字段(结果,'error'),'message')#文案
                return#结束
            找到=取字段(取字段(结果,'value'),'models') or []#候选
            if len(找到)==0:#空
                自身.失败=翻译('fetchEmpty')#空文案
                return#结束
            已知=set(文本自(模,'id') for 模 in (取字段(自身.属性,'models') or []))#已配 id
            自身.候选=找到#挂候选
            自身.已选=set(取字段(模,'id') for 模 in 找到 if 取字段(模,'id') not in 已知)#默认勾新
        except Exception as 错误:#传输拒绝
            自身.失败=错误文案(错误)#文案
        finally:#收尾
            自身.忙=False#闲

    def 关挑选(自身):#关对话框
        """清候选与勾选。"""
        自身.候选=None#清
        自身.已选=set()#清

    def 采纳已选(自身):#把勾选并入列表
        """已配行保留用户容量。"""
        if 自身.候选 is None:#无
            return#结束
        按标识={}#id→行
        for 模型 in (取字段(自身.属性,'models') or []):#已有
            按标识[文本自(模型,'id')]=dict(模型)#记下
        for 候选 in 自身.候选:#候选
            标识=取字段(候选,'id')#id
            if 标识 not in 自身.已选:#未勾
                continue#跳过
            按标识[标识]=按标识.get(标识) or 采纳候选(候选)#保留已配或采纳
        变更=取字段(自身.属性,'onChange')#回调
        if 变更 is not None:#有
            变更(list(按标识.values()))#写入
        自身.关挑选()#关

    def 切换勾选(自身,标识):#勾选切换
        """有则去，无则加。"""
        if 标识 in 自身.已选:#已勾
            自身.已选.discard(标识)#去
        else:#未勾
            自身.已选.add(标识)#加

    def 移除(自身,下标):#删行并重键
        """展开与缓冲随行号移动。"""
        模型们=[dict(模) for 位,模 in enumerate(取字段(自身.属性,'models') or []) if 位!=下标]#过滤
        新展开=set()#新展开
        for 位 in 自身.已展开:#每展开
            if 位<下标:#前
                新展开.add(位)#保留
            elif 位>下标:#后
                新展开.add(位-1)#移位
        自身.已展开=新展开#覆盖
        自身.编辑中=自身.移除重键(自身.编辑中,下标)#重键
        变更=取字段(自身.属性,'onChange')#回调
        if 变更 is not None:#有
            变更(模型们)#通知

    def 渲染(自身):#结构化视图
        """目录头、行、探询对话框。"""
        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案
        禁用=bool(取字段(自身.属性,'disabled'))#禁用
        模型们=list(取字段(自身.属性,'models') or [])#行
        探测=取字段(自身.属性,'probe') or {}#探测
        覆盖=取字段(自身.属性,'overridden')#是否用户层拥有
        基址=取字段(探测,'baseURL')#端点
        可问=取字段(探测,'provider') is not None or (isinstance(基址,str) and len(基址)>0)#可探询
        阻塞=取字段(自身.属性,'probeBlocked')#阻塞文案键
        行表=[]#行视图
        for 下标,模型 in enumerate(模型们):#逐行
            行={#行
                'index':下标,#下标
                'id':文本自(模型,'id'),#id
                'name':文本自(模型,'name'),#name
                'expanded':下标 in 自身.已展开,#展开
                'onToggle':(lambda 某=下标:自身.切换展开(某)),#披露
                'onRemove':(lambda 某=下标:自身.移除(某)),#删除
                'onId':(lambda 文,某=下标:自身.补丁(某,{'id':文})),#改 id
                'onName':(lambda 文,某=下标:自身.补丁(某,{'name':None if 文=='' else 文})),#改 name
            }#行基础
            if 下标 in 自身.已展开:#容量披露
                行['advanced']=[#容量字段
                    {'field':'contextWindow','label':翻译('modelContextWindow'),'text':自身.容量文本(模型,下标,'contextWindow'),'placeholder':容量提示['contextWindow'],'onChange':(lambda 文,某=下标:自身.改容量(某,'contextWindow',文))},#上下文
                    {'field':'maxTokens','label':翻译('modelMaxTokens'),'text':自身.容量文本(模型,下标,'maxTokens'),'placeholder':容量提示['maxTokens'],'onChange':(lambda 文,某=下标:自身.改容量(某,'maxTokens',文))},#上限
                ]#高级结束
            行表.append(行)#记入
        def 添加():#加空行
            """追加空 id。"""
            变更=取字段(自身.属性,'onChange')#回调
            if 变更 is not None:#有
                变更([dict(模) for 模 in 模型们]+[{'id':''}])#追加
        复位=取字段(自身.属性,'onReset')#复位
        对话框=None#挑选框
        if 自身.候选 is not None:#有候选
            对话框={#对话框
                'title':翻译('fetchTitle'),#标题
                'description':翻译('fetchDescription'),#说明
                'closeLabel':翻译('close'),#关闭
                'cancelLabel':翻译('cancel'),#取消
                'adoptLabel':翻译('fetchAdopt'),#采纳
                'onClose':自身.关挑选,#关
                'onAdopt':自身.采纳已选,#采纳
                'candidates':[{#候选行
                    'id':取字段(候,'id'),#id
                    'checked':取字段(候,'id') in 自身.已选,#勾选
                    'onToggle':(lambda 某=取字段(候,'id'):自身.切换勾选(某)),#切换
                } for 候 in 自身.候选],#候选表
            }#对话框结束
        return {#视图
            'type':'model-list-editor',#类型
            'title':翻译('models'),#标题
            'meta':None if 覆盖 is None else 翻译('modelsCustomized' if 覆盖 else 'modelsInherited'),#元信息
            'overridden':覆盖,#覆盖
            'resetLabel':翻译('resetModels') if 覆盖 is True and 复位 is not None else None,#复位
            'onReset':复位 if 覆盖 is True else None,#复位句柄
            'fetchLabel':翻译('fetching' if 自身.忙 else 'fetchModels'),#探询
            'fetchDisabled':禁用 or 自身.忙 or not 可问 or 阻塞 is not None,#门闩
            'fetchTitle':翻译(阻塞) if 阻塞 is not None else (None if 可问 else 翻译('fetchNeedsBaseUrl')),#提示
            'onFetch':自身.探询,#探询
            'empty':翻译('modelsEmpty') if len(模型们)==0 else None,#空态
            'rows':行表,#行
            'addLabel':翻译('addModel'),#添加
            'onAdd':添加,#添加
            'error':自身.失败,#失败
            'dialog':对话框,#挑选
            'disabled':禁用,#禁用
            'cssModule':'模型分区.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

ModelListEditor=模型列表编辑器#上游名
