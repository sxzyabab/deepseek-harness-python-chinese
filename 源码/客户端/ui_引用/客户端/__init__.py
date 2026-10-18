'登记 @ 文件和会话引用，以及行内文件、文件夹芯片'
import json#候选载荷
from ....基础设施.通用工具 import 获取内部数据,当前毫秒,紧凑json编码#宿主事实、现在、紧凑 JSON
from ....上下文.文件引用.词法 import 格式化文件提及#文件提及
from ....工具.工作区路径 import 缩写家目录路径,文件地址为#家目录缩写、文件地址
from ...ui_基础界面组件.相对时间 import 相对时间#会话年龄分档
from . import (
    文案,
    文件引用,
    用户文本规则,
)
from .文案 import 中文,英文,命名空间#中英文案表
from .用户文本规则 import 文件引用规则,文件夹引用规则#原文规则

__all__=[#同目录模块，不把类再导出一层
    '文案','文件引用','用户文本规则',
    '依赖','命名空间','应用','目录载荷','面包屑',
]

依赖=[#所需服务
    'inputTriggers','locale','sessions','remote','remote.fileReferences',#触发、文案、会话、远程
    'remote.sessionReferenceResolver','sidebarRight','slots','uiConversation',#会话引用、侧栏、槽位、对话
]#依赖结束

def 目录载荷(标签,提及):
    '把一个目录目的地写成 onPick 已经认识的下钻载荷'
    值={'kind':'file','fileKind':'directory','label':标签,'mention':提及}#目录载荷
    return 紧凑json编码(值)#紧凑 JSON

def 面包屑(查询,引号路径,已下钻):
    '只有下钻才有页眉。某一段写不成提及，就整条都不要'
    if not 已下钻:#不是下钻
        return None#无页眉
    斜杠=查询.rfind('/')#最后一条斜杠
    if 斜杠<0:#还没有目录
        return None#无页眉
    段列表=[段 for 段 in 查询[:斜杠].split('/') if 段!='']#祖先段
    屑=[{#工作区根
        'label':'工作区',#根标签
        'value':目录载荷('工作区','@"' if 引号路径 else '@'),#根的下钻载荷
    }]#根结束
    for 索引,段 in enumerate(段列表):#从根往下
        路径='/'.join(段列表[:索引+1])#到这一段为止
        提及=格式化文件提及({'path':路径,'kind':'directory'},引号路径)#目录提及
        if 提及 is None:#写不成
            return None#整条放弃
        项={'label':段,'value':目录载荷(段,提及)}#这一段
        if 索引==len(段列表)-1:#正在列出的目录
            项['current']=True#标成当前
        屑.append(项)#接上
    return 屑#整条面包屑

def 应用(上下文,配置=None):
    '登记中英文案、文件和文件夹规则，以及组合的 @ 引用源'
    def 登记词典():
        '登记中英文案表。界面上的字不走英文表'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记

    上下文.副作用(登记词典,'ui-reference: dictionaries')#词典随插件拆掉
    会话面=上下文.获取服务('sessions')#会话
    上下文.uiConversation.userText.register(文件引用规则)#文件规则
    上下文.uiConversation.userText.register(文件夹引用规则)#文件夹规则

    def 登记文本节点():
        '文件芯片和文件夹芯片登记到同一条用户文本节点'
        def 注入文件(会话标识):
            '按来源会话准备打开文件'
            def 打开文件(路径):
                '用该会话的工作目录编成文件地址再打开'
                列表=会话面.list.getSnapshot()['byId']#会话列表
                摘要=列表[会话标识] if 会话标识 in 列表 else None#这一会话
                工作目录=None if 摘要 is None else 摘要.get('cwd')#工作目录
                上下文.sidebarRight.打开资源(文件地址为(会话标识,工作目录,路径))#打开

            return {'openFile':打开文件}#注入面

        yield 上下文.slots.register({#文件芯片
            'name':'conversation.user.text.node',#槽位
            'key':'file',#文件
            'priority':100,#优先级
            'locale':命名空间,#文案命名空间
            'inject':注入文件,#按会话打开
        },文件引用.文件引用)#文件类
        yield 上下文.slots.register({#文件夹芯片
            'name':'conversation.user.text.node',#槽位
            'key':'folder',#文件夹
            'priority':100,#优先级
        },文件引用.文件夹引用)#文件夹类

    上下文.slots.inject('conversation.user.text.node',登记文本节点)#等槽位声明后再登记

    def 列出候选(会话,请求):
        '持留到历史打开后发现文件和会话。文件在前，子智能体其次，其余会话在后'
        查询=请求['query']#查询
        引号=请求['quoted'] is True if 'quoted' in 请求 else False#真引号才抑制会话
        已下钻=请求['drilled'] if 'drilled' in 请求 else False#下钻
        信号=请求['signal']#取消
        会话标识=会话['sessionId'] if isinstance(会话,dict) else 会话.sessionId#会话

        def 已中止():
            'AbortSignal 认 aborted，输入触发传来的 Event 认 is_set'
            if hasattr(信号,'aborted'):#AbortSignal
                return 信号.aborted is True#已取消
            return 信号.is_set()#Event 已置位

        if 会话面.binding(会话标识) is None:#没有持留
            raise Exception('reference candidates require a retained session "'+str(会话标识)+'"')#拒绝

        def 在持有内拉取(引用):
            '历史打开之后再发现。任一边失败只让那一边变空'
            if hasattr(信号,'throwIfAborted'):#带原因的取消原样抛出
                信号.throwIfAborted()#抛原因
            if 已中止():#已取消
                raise Exception('The operation was aborted.')#不再发现
            状态=引用.binding['session'].getSnapshot()#会话快照
            if 状态['openState']!='open':#历史没打开
                if 状态['openError'] is not None:#有打开错误
                    raise 状态['openError']#原样抛出
                raise Exception('session "'+str(会话标识)+'" is not open')#没打开
            文件结果=上下文.获取服务('remote.fileReferences').list(会话标识,查询,信号)#文件
            文件项=文件结果['value'] if 文件结果['ok'] else []#失败当空
            if 引号:#引号路径不查会话
                会话项=[]#空
            else:#查会话
                会话结果=上下文.获取服务('remote.sessionReferenceResolver').candidates(会话标识,查询,信号)#会话
                会话项=会话结果['value'] if 会话结果['ok'] else []#失败当空
            return 文件项,会话项#两边都到齐

        文件项,会话项=会话面.using(#持留到回调结束
            会话标识,#会话
            {'source':'referenceCandidates','signal':信号},#来源与取消
            在持有内拉取,#发现
        )#持留结束
        if 已中止():#到齐之后已被取代
            return []#丢掉
        标位置=面包屑(查询,引号,已下钻) is None#没有页眉才在行上写父路径
        现在=当前毫秒()#现在
        宿主=获取内部数据(上下文.remote,'host',None)#remote.$host，没有则不缩写
        if isinstance(宿主,dict):#宿主事实是字典
            家=宿主['home'] if 'home' in 宿主 else None#家目录
        elif 宿主 is None:#没有宿主事实
            家=None#不缩写
        else:#宿主事实是对象
            家=getattr(宿主,'home',None)#家目录
        列表=会话面.list.getSnapshot()['byId']#会话列表
        行列表=[]#合并后的行
        for 候选 in 文件项:#文件和文件夹在前
            提及=格式化文件提及(候选,引号)#提及
            if 提及 is None:#写不成
                continue#丢掉这一条
            路径=候选['path']#路径
            斜杠=路径.rfind('/')#末斜杠
            名=路径[斜杠+1:]#基名
            父='' if 斜杠<0 else 路径[:斜杠]#父目录
            目录=候选['kind']=='directory'#目录
            值={#行载荷
                'kind':'file',#文件类
                'fileKind':候选['kind'],#文件或目录
                'label':名,#基名
                'mention':提及,#提及
            }#载荷结束
            行={#一行
                'name':名+('/' if 目录 else ''),#目录带尾斜杠
                'icon':'folder' if 目录 else 'file',#图标
                'section':'文件与文件夹',#分组
                'value':紧凑json编码(值),#载荷
            }#行结束
            if 标位置 and 父!='':#行上只写父路径
                行['description']=父#位置
            if 目录:#目录可以下钻
                行['drill']=True#下钻
            行列表.append(行)#收下
        包装=[]#先分出子智能体
        for 候选 in 会话项:#会话
            标识=候选['sessionId']#标识
            摘要=列表[标识] if 标识 in 列表 else None#列表摘要
            if 摘要 is not None and 摘要.get('updatedAt') is not None:#列表上的活动时间
                更新=摘要['updatedAt']#更新时间
            else:#列表没有就用候选自己的创建时间
                更新=候选['createdAt']#创建时间
            子项=摘要 is not None and 摘要.get('origin')=='subagent' and 摘要.get('parentId')==会话标识#本会话的子智能体
            if 候选.get('displayTitle') is not None:#展示标题优先
                标签=候选['displayTitle']#展示标题
            else:#否则用标签
                标签=候选['label']#标签
            分组='子智能体' if 子项 else '对话'#分组
            分档=相对时间(更新,现在)#年龄分档
            单位=分档['unit']#单位
            数=分档['n']#数量
            if 单位=='now':#刚刚
                年龄='刚刚'#刚刚
            elif 单位=='minutes':#分钟
                年龄=str(数)+'分钟'#分钟
            elif 单位=='hours':#小时
                年龄=str(数)+'小时'#小时
            elif 单位=='days':#天
                年龄=str(数)+'天'#天
            elif 单位=='months':#月
                年龄=str(数)+'个月'#月
            else:#年
                年龄=str(数)+'年'#年
            if 候选.get('sameWorkspace'):#已经在这个工作区
                位置=None#不重复写工作区
            elif 候选.get('cwd') is None:#没有工作目录
                位置='（无工作目录）'#占位
            else:#别的工作区
                位置=缩写家目录路径(候选['cwd'],家)#缩写家目录
            载荷={'kind':'session','label':标签,'mention':候选['mention']}#会话载荷
            会话行={#一行
                'name':标签,#名称
                'description':年龄 if 位置 is None else 位置+' · '+年龄,#位置和年龄
                'icon':'session',#图标
                'section':分组,#分组
                'value':紧凑json编码(载荷),#载荷
            }#行结束
            包装.append({'child':子项,'row':会话行})#记下是否子项
        for 项 in 包装:#子智能体排在前面
            if 项['child']:#是子项
                行列表.append(项['row'])#收下
        for 项 in 包装:#其余会话排在后面
            if not 项['child']:#不是子项
                行列表.append(项['row'])#收下
        return 行列表#候选

    def 页眉(_会话,请求):
        '下钻才返回面包屑'
        引号=请求['quoted'] is True if 'quoted' in 请求 else False#引号
        已下钻=请求['drilled'] if 'drilled' in 请求 else False#下钻
        return 面包屑(请求['query'],引号,已下钻)#面包屑

    def 选中(事件):
        '目录下钻继续补全，文件和会话落成插入'
        候选=事件['candidate']#候选
        动作=事件['action'] if 'action' in 事件 else None#动作
        if 'value' not in 候选 or 候选['value'] is None:#没有本源载荷
            return None#不认
        值=json.loads(候选['value'])#解析载荷
        if 值['kind']=='file':#文件或目录
            if 值['fileKind']=='directory' and 动作=='drill':#下钻目录
                return {'text':值['mention'],'continue':True}#菜单继续开着
            目录=值['fileKind']=='directory'#目录
            return {#落成插入
                'insert':{#插入体
                    'source':'reference',#源
                    'ref':值['mention'],#提及
                    'label':(值['label']+'/') if 目录 else 值['label'],#目录标签带尾斜杠
                    'appearance':'folder' if 目录 else 'file',#外观
                    'clipboardText':值['mention'],#剪贴板
                },#插入体结束
            }#插入结束
        if 值['kind']=='session':#会话
            return {#落成插入
                'insert':{#插入体
                    'source':'reference',#源
                    'ref':值['mention'],#提及
                    'label':值['label'],#标签
                    'appearance':'session',#外观
                    'clipboardText':值['mention'],#剪贴板
                },#插入体结束
            }#插入结束
        return None#不认

    def 打开引用(会话,引用):
        '只打开文件外观。剥掉提及后按会话工作目录编址'
        if 引用.get('appearance')!='file':#文件夹和会话不在这里打开
            return False#不接
        原文=引用['ref']#提及
        if 原文.startswith('@"'):#引号提及
            路径=原文[2:-1]#去掉 @" 和结尾引号
        else:#普通提及
            路径=原文[1:]#去掉 @
        会话标识=会话['sessionId'] if isinstance(会话,dict) else 会话.sessionId#会话
        列表=会话面.list.getSnapshot()['byId']#会话列表
        摘要=列表[会话标识] if 会话标识 in 列表 else None#这一会话
        工作目录=None if 摘要 is None else 摘要.get('cwd')#工作目录
        上下文.sidebarRight.打开资源(文件地址为(会话标识,工作目录,路径))#打开
        return True#已接

    def 剪贴板文本(引用文本):
        '剪贴板就是提及'
        return 引用文本#原样

    def 序列化引用(引用文本,_信号=None):
        '序列化不另造身份。同步返回提及'
        return 引用文本#原样

    源={#组合引用源
        'trigger':'@',#触发字符
        'name':'reference',#源名
        'showGroupTitle':False,#不显示源级分组标题
        'candidates':列出候选,#发现
        'header':页眉,#页眉
        'onPick':选中,#选中
        'openReference':打开引用,#打开文件
        'codec':{#编解码
            'clipboardText':剪贴板文本,#剪贴板
            'serialize':序列化引用,#序列化
        },#编解码结束
    }#源结束
    触发=上下文.获取服务('inputTriggers')#触发服务

    def 登记源():
        '登记 @ 引用源'
        return 触发.registerSource(源)#登记

    上下文.副作用(登记源,'ui-reference: @ source')#源随插件拆掉

inject=依赖#框架槽
apply=应用#框架槽
