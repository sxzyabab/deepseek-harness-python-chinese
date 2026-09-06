"""统一的 Web `@` 引用源。

对齐上游 `ui-reference/src/client/index.ts`。公开面仅中文名。
文件与会话发现经可取消的 Remote 命名空间并行，排序与标签确定。
"""
import json#行载荷编解码
import time#相对时间基准
from ....上下文.文件引用.词法 import 格式化文件提及#文件 mention 格式化
from .文案 import 命名空间,中文,英文#词典与键

__all__=[#仅中文公开名
    '注入','应用','面包屑','目录载荷','文件候选行','会话候选行','解析候选',
    '相对时间','缩写家目录路径','命名空间','中文','英文','已中止','若已中止则抛出',
]#公开面结束

注入=[#Cordis inject
    'inputTriggers','locale','sessions','remote','remote.fileReferences',#基础服务
    'remote.sessionReferenceResolver',#会话引用解析
]#inject 结束

class 引用错误(Exception):
    """本包引用源失败。"""
    def __init__(自身,消息):
        """记下英文消息。"""
        super().__init__(消息)#消息原样英文

def 已中止(信号):
    """threading.Event 是否已置位。"""
    return 信号.is_set()#已置位

def 若已中止则抛出(信号):
    """已置位则抛引用中止。"""
    if 已中止(信号):
        raise 引用错误('The operation was aborted.')#中止

def 相对时间(更新于,现在):
    """会话行的紧凑相对时间结构化桶。"""
    分=60_000#一分钟毫秒
    时=3_600_000#一小时
    日=86_400_000#一天
    差=max(0,现在-更新于)#非负差
    if 差<分:
        return {'unit':'now','n':0}#刚刚
    if 差<时:
        return {'unit':'minutes','n':差//分}#分钟
    if 差<日:
        return {'unit':'hours','n':差//时}#小时
    if 差<30*日:
        return {'unit':'days','n':差//日}#天
    if 差<365*日:
        return {'unit':'months','n':差//(30*日)}#月
    return {'unit':'years','n':差//(365*日)}#年

def 缩写家目录路径(路径,家目录):
    """家目录前缀换成 ~。"""
    if 路径 is None or 路径=='' or 家目录 is None or 家目录=='':
        return 路径#原样
    if 路径==家目录 or 路径.startswith(家目录.rstrip('/')+'/'):
        return '~'+路径[len(家目录):]#缩写
    return 路径#原样

def 目录载荷(标签,提及):
    """把一个目录目的地投影为 onPick 已理解的 drill 载荷。"""
    值={'kind':'file','fileKind':'directory','label':标签,'mention':提及}#目录载荷
    return json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)#行 value 序列化

def 面包屑(查询,引号路径,已下钻,翻译):
    """只有 drill 才产生；无法格式化则放弃页眉。"""
    if 已下钻 is not True:
        return None#无页眉
    斜杠=查询.rfind('/')#末斜杠
    if 斜杠<0:
        return None#无
    段列表=[段 for 段 in 查询[:斜杠].split('/') if 段!='']#祖先段
    屑=[{#根 crumb
        'label':翻译('crumb.root'),#根标签
        'value':目录载荷(翻译('crumb.root'),'@"' if 引号路径 else '@'),#根下钻载荷
    }]#根结束
    for 索引,段 in enumerate(段列表):
        路径='/'.join(段列表[:索引+1])#到本段路径
        提及=格式化文件提及({'path':路径,'kind':'directory'},引号路径)#目录 mention
        if 提及 is None:
            return None#放弃页眉
        项={'label':段,'value':目录载荷(段,提及)}#crumb
        if 索引==len(段列表)-1:
            项['current']=True#标当前
        屑.append(项)#追加
    return 屑#完整面包屑

def 文件候选行(候选,保留引号,标位置,翻译):
    """无法格式化则丢弃。候选为线协议 dict。"""
    提及=格式化文件提及(候选,保留引号)#格式化 mention
    if 提及 is None:
        return []#丢弃
    路径=候选['path'] if 'path' in 候选 else ''#路径
    种类=候选['kind'] if 'kind' in 候选 else None#种类
    斜杠=路径.rfind('/')#末斜杠
    名=路径[斜杠+1:]#基名
    父='' if 斜杠<0 else 路径[:斜杠]#父目录
    目录=种类=='directory'#是否目录
    值={'kind':'file','fileKind':种类,'label':名,'mention':提及}#行载荷
    行={#候选行
        'name':名+('/' if 目录 else ''),#行名
        'icon':'folder' if 目录 else 'file',#图标
        'section':翻译('section.files'),#分组
        'value':json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False),#序列化载荷
    }#行结束
    if 标位置 and 父!='':
        行['description']=父#位置只写父路径
    if 目录:
        行['drill']=True#下钻
    return [行]#行结束

def 会话候选行(候选,更新于,现在,家目录,翻译):
    """位置只在非当前工作区时才告知。候选为线协议 dict。"""
    分档=相对时间(更新于,现在)#相对时间分档
    单位=分档['unit']#单位
    年龄=翻译('time.now') if 单位=='now' else 翻译(f'time.{单位}',{'n':分档['n']})#年龄文案
    同区=候选['sameWorkspace'] if 'sameWorkspace' in 候选 else False#亲和
    if 同区:
        位置=None#不标
    else:
        cwd=候选['cwd'] if 'cwd' in 候选 else None#cwd
        位置=翻译('candidate.noCwd') if cwd is None else 缩写家目录路径(cwd,家目录)#缩写 cwd
    标签=候选['label'] if 'label' in 候选 else ''#展示名
    提及=候选['mention'] if 'mention' in 候选 else ''#序列化
    值={'kind':'session','label':标签,'mention':提及}#行载荷
    return {#候选行
        'name':标签,#行名
        'description':年龄 if 位置 is None else f'{位置} · {年龄}',#位置 · 年龄
        'icon':'session',#图标
        'section':翻译('section.sessions'),#分组
        'value':json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False),#序列化载荷
    }#行结束

def 解析候选(值):
    """无值则 None。"""
    if 值 is None:
        return None#无
    return json.loads(值)#解析 JSON

def 剪贴板文本(引用):
    """剪贴板即 mention。"""
    return 引用#原样

def 序列化引用(引用):
    """序列化不重建身份。"""
    return 引用#原样

def 应用(上下文):
    """登记组合的 @file / @session 源。"""
    def 登记词典():
        """登记引用词典。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记词典
    上下文.副作用(登记词典,'ui-reference: dictionaries')#登记词典
    翻译=上下文.locale.bind(命名空间)#绑定翻译
    会话面=上下文.获取服务('sessions')#会话列表面

    def 列出候选(会话,请求):
        """文件与会话并行；引号路径只搜文件。请求为线协议 dict。"""
        查询=请求['query'] if 'query' in 请求 else ''#查询
        引号=请求['quoted'] is True if 'quoted' in 请求 else False#引号
        已下钻=请求['drilled'] if 'drilled' in 请求 else False#下钻
        信号=请求['signal'] if 'signal' in 请求 else None#取消
        文件结果=上下文.remote.fileReferences.list(会话.sessionId,查询,信号)#文件发现
        文件项=文件结果['value'] if 文件结果['ok'] else []#失败静默为空
        if 引号:
            会话项=[]#空
        else:
            会话结果=上下文.remote.sessionReferenceResolver.candidates(会话.sessionId,查询,信号)#会话发现
            会话项=会话结果['value'] if 会话结果['ok'] else []#失败静默为空
        if 信号 is not None and 已中止(信号):
            return []#空
        标位置=面包屑(查询,引号,已下钻,翻译) is None#是否行上标位置
        现在=int(time.time()*1000)#相对时间基准
        家=上下文.remote.$host.home#宿主 home
        列表=会话面.list.getSnapshot().byId#会话列表
        行列表=[]#合并候选行
        for 候选 in 文件项:
            行列表.extend(文件候选行(候选,引号,标位置,翻译))#展开
        表=列表 if 列表 is not None else {}#缺席当空
        for 候选 in 会话项:
            标识=候选['sessionId'] if 'sessionId' in 候选 else None#id
            摘要=表[标识] if 标识 in 表 else None#列表摘要
            if 摘要 is not None and 'updatedAt' in 摘要:
                更新=摘要['updatedAt']#更新时间
            elif 'createdAt' in 候选:
                更新=候选['createdAt']#创建时间
            else:
                更新=现在#回退现在
            行列表.append(会话候选行(候选,更新,现在,家,翻译))#会话行
        return 行列表#候选结束

    def 页眉(_会话,请求):
        """下钻面包屑。"""
        查询=请求['query'] if 'query' in 请求 else ''#查询
        引号=请求['quoted'] is True if 'quoted' in 请求 else False#引号
        已下钻=请求['drilled'] if 'drilled' in 请求 else False#下钻
        return 面包屑(查询,引号,已下钻,翻译)#面包屑

    def 选中(事件):
        """落定插入或目录下钻。事件为线协议 dict。"""
        候选=事件['candidate'] if 'candidate' in 事件 else None#候选
        动作=事件['action'] if 'action' in 事件 else None#动作
        if 候选 is None:
            return None#无
        原文=候选['value'] if 'value' in 候选 else None#载荷
        值=解析候选(原文)#解码
        if 值 is None:
            return None#无
        if 值['kind']=='file':
            if 值['fileKind']=='directory' and 动作=='drill':
                return {'text':值['mention'],'continue':True}#继续补全
            目录=值['fileKind']=='directory'#是否目录
            return {#落定插入
                'insert':{#插入体
                    'source':'reference',#源名
                    'ref':值['mention'],#隐藏序列化
                    'label':(值['label']+'/') if 目录 else 值['label'],#目录带尾斜杠
                    'appearance':'folder' if 目录 else 'file',#外观
                    'clipboardText':值['mention'],#剪贴板
                },#插入结束
            }#插入结束
        if 值['kind']=='session':
            return {#落定插入
                'insert':{#插入体
                    'source':'reference',#源名
                    'ref':值['mention'],#隐藏序列化
                    'label':值['label'],#展示标签
                    'appearance':'session',#外观
                    'clipboardText':值['mention'],#剪贴板
                },#插入结束
            }#插入结束
        return None#无法识别

    源={#组合引用源
        'trigger':'@',#触发字符
        'name':'reference',#源名
        'showGroupTitle':False,#不显示源级分组标题
        'candidates':列出候选,#并行发现
        'header':页眉,#页眉面包屑
        'onPick':选中,#选中行
        'codec':{#编解码
            'clipboardText':剪贴板文本,#剪贴板即 mention
            'serialize':序列化引用,#序列化不重建身份
        },#编解码结束
    }#source 结束
    触发=上下文.获取服务('inputTriggers')#触发服务
    def 登记源():
        """登记 @ 引用源。"""
        return 触发.registerSource(源)#登记源
    上下文.副作用(登记源,'ui-reference: @ source')#登记源

inject=注入#框架槽
apply=应用#框架槽
