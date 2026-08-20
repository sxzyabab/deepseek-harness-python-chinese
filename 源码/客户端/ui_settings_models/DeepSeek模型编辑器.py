"""直连 DeepSeek 适配器的模型目录编辑与容量解析。

对齐上游 `ui-settings-models/src/client/DeepSeekModelsEditor.tsx`。公开面仅中文名。
"""
import math#数学
import re#正则

__all__=[#仅中文公开名
    '解析容量','格式化容量','模型草稿表','校验DeepSeek模型',
    'DeepSeek模型编辑器','parseCapacity','formatCapacity','modelDrafts',
    'validateDeepSeekModels','DeepSeekModelsEditor',
]#公开面结束

容量模式=re.compile(r'^(\d+(?:\.\d+)?)([km])?$',re.I)#带可选 K/M 后缀
容量尺度={'k':1000,'m':1000000}#十进制尺度

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 解析容量(文本):#解析 K/M 容量拼写
    """空为继承；不可读为 NaN。"""
    去空白=文本.strip()#去空白
    if len(去空白)==0:#空
        return None#继承
    匹配=容量模式.match(去空白)#匹配
    if 匹配 is None:#不可读
        return float('nan')#NaN
    后缀=(匹配.group(2) or '').lower()#后缀
    尺度=容量尺度[后缀] if 后缀 in 容量尺度 else 1#尺度
    缩放=float(匹配.group(1))*尺度#缩放
    取整=round(缩放)#取整意图
    return 取整 if abs(缩放-取整)<1e-6 else 缩放#整意图则取整

def 格式化容量(值):#最短可回写拼写
    """非正整数原样；能整除 M/K 则用后缀。"""
    if not isinstance(值,(int,float)) or isinstance(值,bool):#非数
        return str(值)#原样
    if not float(值).is_integer() or 值<=0:#非整或非正
        return str(值)#原样
    整=int(值)#整数
    if 整%容量尺度['m']==0:#整百万
        return f"{整//容量尺度['m']}M"#M
    if 整%容量尺度['k']==0:#整千
        return f"{整//容量尺度['k']}K"#K
    return str(整)#原样

def 模型草稿表(值):#目录值→开放记录表
    """非数组则空；非对象项变空对象。"""
    if not isinstance(值,list):#非数组
        return []#空
    结果=[]#草稿
    for 项 in 值:#每项
        if isinstance(项,dict) and not isinstance(项,list):#对象
            结果.append(dict(项))#拷贝
        else:#畸形
            结果.append({})#空对象
    return 结果#草稿表

def 校验DeepSeek模型(值):#适配器约束校验
    """首个非法行；继承态(undefined)通过。"""
    if 值 is None:#继承
        return None#通过
    模型们=模型草稿表(值)#草稿
    已见=set()#已见 id
    for 下标,模型 in enumerate(模型们):#逐行
        标识=模型.get('id')#id
        去空白=标识.strip() if isinstance(标识,str) else None#去空白
        if 去空白 is None or len(去空白)==0:#缺 id
            return {'index':下标,'key':'modelIdRequired'}#必填
        if 去空白 in 已见:#重复
            return {'index':下标,'key':'modelIdDuplicate'}#重复
        已见.add(去空白)#记下
        名称=模型.get('name')#name
        if 名称 is not None and (not isinstance(名称,str) or len(名称)==0):#非法名
            return {'index':下标,'key':'modelNameInvalid'}#非法
        上下文=模型.get('contextWindow')#上下文
        if 上下文 is not None and (not isinstance(上下文,(int,float)) or isinstance(上下文,bool) or not float(上下文).is_integer() or 上下文<=0):#非法
            return {'index':下标,'key':'modelContextInvalid'}#非法
        上限=模型.get('maxTokens')#上限
        if 上限 is not None and (not isinstance(上限,(int,float)) or isinstance(上限,bool) or not float(上限).is_integer() or 上限<=0):#非法
            return {'index':下标,'key':'modelMaxTokensInvalid'}#非法
    return None#通过

parseCapacity=解析容量#上游名
formatCapacity=格式化容量#上游名
modelDrafts=模型草稿表#上游名
validateDeepSeekModels=校验DeepSeek模型#上游名

def 行号自键(键):#缓冲键前缀行号
    """`index:field` 取行号。"""
    return int(键[:键.index(':')])#行号

class DeepSeek模型编辑器:#DeepSeek 模型目录编辑器
    """id/name 行上，容量藏在行披露里。"""
    def __init__(自身,属性):#构造
        """记下 props 与编辑缓冲。"""
        自身.属性=属性#合成 props
        自身.编辑中={}#键→键入文本
        自身.已展开=set()#展开行

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 改字段(自身,下标,键,值):#改一行字段
        """替换用户层数组。"""
        模型们=list(取字段(自身.属性,'models') or [])#当前
        下一=[]#新表
        for 位,模型 in enumerate(模型们):#逐行
            拷=dict(模型)#拷贝
            if 位==下标:#目标行
                if 值 is None:#清除
                    拷.pop(键,None)#删
                else:#写入
                    拷[键]=值#设
            下一.append(拷)#记入
        变更=取字段(自身.属性,'onChange')#回调
        if 变更 is not None:#有
            变更(下一)#通知

    def 移除(自身,下标):#删一行并重键缓冲
        """行号移动后保留未删缓冲。"""
        新编辑={}#新缓冲
        for 键,文本 in 自身.编辑中.items():#每缓冲
            位=行号自键(键)#行
            if 位==下标:#被删
                continue#跳过
            新键=re.sub(r'^\d+',str(位-1),键,count=1) if 位>下标 else 键#重键
            新编辑[新键]=文本#记下
        自身.编辑中=新编辑#覆盖
        新展开=set()#新展开
        for 位 in 自身.已展开:#每展开
            if 位==下标:#被删
                continue#跳过
            新展开.add(位-1 if 位>下标 else 位)#移位
        自身.已展开=新展开#覆盖
        模型们=[dict(模型) for 位,模型 in enumerate(取字段(自身.属性,'models') or []) if 位!=下标]#过滤
        变更=取字段(自身.属性,'onChange')#回调
        if 变更 is not None:#有
            变更(模型们)#通知

    def 重置(自身):#清除覆盖回继承
        """清缓冲并 onReset。"""
        自身.编辑中={}#清
        自身.已展开=set()#清
        复位=取字段(自身.属性,'onReset')#回调
        if 复位 is not None:#有
            复位()#复位

    def 切换展开(自身,下标):#切换行披露
        """开则关，关则开。"""
        if 下标 in 自身.已展开:#已开
            自身.已展开.discard(下标)#关
        else:#未开
            自身.已展开.add(下标)#开

    def 容量文本(自身,模型,下标,字段):#容量字段显示文本
        """优先键入缓冲，否则格式化存量。"""
        键=f'{下标}:{字段}'#缓冲键
        if 键 in 自身.编辑中:#有键入
            return 自身.编辑中[键]#键入
        值=模型.get(字段)#存量
        return 格式化容量(值) if isinstance(值,(int,float)) and not isinstance(值,bool) else ''#拼写

    def 落定容量(自身,下标,字段):#失焦落定可读缓冲
        """不可读文本留屏。"""
        键=f'{下标}:{字段}'#键
        if 键 not in 自身.编辑中:#无
            return#结束
        解析=解析容量(自身.编辑中[键])#解析
        if 解析 is not None and isinstance(解析,float) and math.isnan(解析):#不可读
            return#留屏
        自身.编辑中.pop(键,None)#清缓冲

    def 渲染(自身):#结构化视图
        """目录头、行、添加。"""
        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案
        禁用=bool(取字段(自身.属性,'disabled'))#禁用
        模型们=list(取字段(自身.属性,'models') or [])#行
        覆盖=bool(取字段(自身.属性,'overridden'))#用户层拥有
        默认上下文=取字段(自身.属性,'defaultContextWindow')#默认上下文
        默认上限=取字段(自身.属性,'defaultMaxTokens')#默认上限
        行表=[]#行视图
        for 下标,模型 in enumerate(模型们):#逐行
            行={#行
                'index':下标,#下标
                'id':模型.get('id') if isinstance(模型.get('id'),str) else '',#id
                'name':模型.get('name') if isinstance(模型.get('name'),str) else '',#name
                'expanded':下标 in 自身.已展开,#展开
                'onToggle':(lambda 某=下标:自身.切换展开(某)),#披露
                'onRemove':(lambda 某=下标:自身.移除(某)),#删除
                'onId':(lambda 文,某=下标:自身.改字段(某,'id',文)),#改 id
                'onIdBlur':(lambda 文,某=下标:自身.改字段(某,'id',文.strip()) if 文.strip()!=文 else None),#落定 id
                'onName':(lambda 文,某=下标:自身.改字段(某,'name',None if 文=='' else 文)),#改 name
            }#行基础
            if 下标 in 自身.已展开:#披露容量
                def 造容量(字段,回退,某=下标,模=模型):#容量控件
                    """单容量字段。"""
                    return {#容量
                        'field':字段,#字段
                        'label':翻译('contextWindow' if 字段=='contextWindow' else 'maxTokens'),#标签
                        'text':自身.容量文本(模,某,字段),#文本
                        'placeholder':格式化容量(回退) if isinstance(回退,(int,float)) else 翻译('contextWindowPlaceholder' if 字段=='contextWindow' else 'maxTokensPlaceholder'),#占位
                        'onChange':(lambda 文,行号=某,列=字段:(
                            自身.编辑中.__setitem__(f'{行号}:{列}',文),
                            自身.改字段(行号,列,解析容量(文)),
                        )),#键入
                        'onBlur':(lambda 行号=某,列=字段:自身.落定容量(行号,列)),#失焦
                    }#容量结束
                行['advanced']=[造容量('contextWindow',默认上下文),造容量('maxTokens',默认上限)]#高级
            行表.append(行)#记入
        def 添加():#加空 id 行
            """追加空模型。"""
            变更=取字段(自身.属性,'onChange')#回调
            if 变更 is not None:#有
                变更([dict(模) for 模 in 模型们]+[{'id':''}])#追加
        return {#视图
            'type':'deepseek-models-editor',#类型
            'title':翻译('models'),#标题
            'meta':翻译('modelsCustomized' if 覆盖 else 'modelsInherited'),#元信息
            'overridden':覆盖,#覆盖
            'resetLabel':翻译('resetModels') if 覆盖 else None,#复位
            'onReset':自身.重置 if 覆盖 else None,#复位句柄
            'empty':翻译('modelsEmpty') if len(模型们)==0 else None,#空态
            'rows':行表,#行
            'addLabel':翻译('addModel'),#添加
            'onAdd':添加,#添加
            'disabled':禁用,#禁用
            'cssModule':'模型分区.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

DeepSeekModelsEditor=DeepSeek模型编辑器#上游名
