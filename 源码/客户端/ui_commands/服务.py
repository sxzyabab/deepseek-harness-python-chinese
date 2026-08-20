"""CommandUiRuntime（ctx.commandUi）：贡献登记与每会话弹出控制器。



对齐上游 `ui-commands/src/client/service.ts`。公开面仅中文名。

目录缓存见 目录.py；模糊候选见本模块边界加分/模糊评分/模糊候选。

"""

from cordis import 服务#Cordis 服务基类

from .弹出 import 弹出选择控制器#弹出控制器

from .目录 import 命令目录#按会话目录缓存



__all__=['命令界面运行时','边界加分','模糊评分','模糊候选','已提交命令名']#仅中文公开名



无对齐=float('-inf')#未对齐哨兵



def 已提交命令名(行):#从已执行行取命令名

    """去掉前导斜杠，取到第一个空白前。"""

    去空白=行.strip()#去首尾

    切=-1#空白下标

    for 下标,字 in enumerate(去空白):#找空白

        if 字.isspace():#空白

            切=下标#记下

            break#停

    令牌=去空白 if 切==-1 else 去空白[:切]#到空白前

    return 令牌[1:] if 令牌.startswith('/') else 令牌#去掉 '/'



def 边界加分(名,下标):#开头或分隔边界加分

    """开头或 '-' '_' 后加 8 分。"""

    if 下标==0:#开头

        return 8#边界

    前=名[下标-1]#前一字符

    if 前=='-' or 前=='_':#分隔后

        return 8#边界

    return 0#否则 0



def 模糊评分(名,查询):#有序子序列最强对齐分

    """对不上则 None；空查询零分。"""

    if 查询=='':#空

        return 0#零分

    if len(查询)>len(名):#查询更长

        return None#不可能

    上一=[无对齐]*len(名)#上一查询字符的各名位置分

    for 下标 in range(len(名)):#对齐 query[0]

        if 名[下标]==查询[0]:#首字符命中

            上一[下标]=1+边界加分(名,下标)-下标#边界加分减去前导跳过

    for 查询下标 in range(1,len(查询)):#后续查询字符

        当前=[无对齐]*len(名)#本查询字符分

        最佳间隔=无对齐#跳过至少一个名字符后的最佳前驱

        for 下标 in range(len(名)):#扫命令名

            间隔下标=下标-2#至少隔一个

            if 间隔下标>=0:#有间隔前驱

                前=上一[间隔下标]#该前驱分

                if 前!=无对齐:#有对齐

                    最佳间隔=max(最佳间隔,前+间隔下标)#累计跳过代价

            if 名[下标]!=查询[查询下标]:#对不上

                continue#只推进间隔

            加分=1+边界加分(名,下标)#命中基础+边界

            相邻=上一[下标-1] if 下标>0 else 无对齐#紧邻前一

            if 相邻!=无对齐:#相邻命中

                当前[下标]=相邻+加分+4#相邻权重

            if 最佳间隔!=无对齐:#间隔路径

                间隔分=最佳间隔+加分+1-下标#跳过代价

                if 当前[下标]==无对齐 or 间隔分>当前[下标]:#更优

                    当前[下标]=间隔分#写

        上一=当前#本轮成前驱

    最佳=无对齐#最强

    for 分 in 上一:#各终点

        if 分>最佳:#更大

            最佳=分#记

    return None if 最佳==无对齐 else 最佳#无对齐则 None



def 模糊候选(候选们,原查询):#过滤并按前缀/分数/原位排名

    """大小写不敏感；空查询原样返回。"""

    查询=原查询.lower()#小写

    if 查询=='':#空

        return list(候选们)#原样

    排名=[]#有对齐分的

    for 下标,候选 in enumerate(候选们):#保留源下标

        名=str(候选.get('name') if isinstance(候选,dict) else getattr(候选,'name','')).lower()#名

        分=模糊评分(名,查询)#有序子序列分

        if 分 is not None:#对上

            排名.append({#排名行

                'candidate':候选,#原候选

                'index':下标,#源下标

                'prefix':名.startswith(查询),#前缀

                'score':分,#分

            })#结束

    排名.sort(key=lambda 行:(-int(行['prefix']),-行['score'],行['index']))#前缀优先、分高、原位靠前

    return [行['candidate'] for 行 in 排名]#剥排名字段



def 读字段(对象,键,缺省=None):#读字段

    """映射或对象。"""

    if 对象 is None:#空

        return 缺省#缺

    if isinstance(对象,dict):#映射

        return 对象[键] if 键 in 对象 else 缺省#键

    return getattr(对象,键,缺省)#属性



class 命令界面运行时(服务):#命令 UI 运行时

    """贡献登记表 + 目录缓存 + 每会话弹出 + '/' 模糊候选源。"""

    inject=['inputTriggers','sessions','remote','remote.commands']#依赖



    def __init__(自身,上下文):#挂到 commandUi

        """初始化贡献/装饰/弹出表与目录，登记斜杠源。"""

        super().__init__(上下文,'commandUi')#登记

        自身.贡献表={}#客户端贡献

        自身.装饰表={}#宿主装饰

        自身.弹出表={}#每会话弹出

        自身.聚焦钩={}#会话 → 聚焦回调

        def 拉取(会话标识):#按会话拉命令列表

            """接线 remote.commands.list。"""

            远程=上下文.get('remote.commands') or 上下文.get('remote')#远程面

            if 远程 is None:#无

                return ()#空

            命令=getattr(远程,'commands',远程)#commands 面

            列表=getattr(命令,'list',None)#list

            if 列表 is None:#无

                return ()#空

            应答=列表({'sessionId':会话标识})#拉取

            if hasattr(应答,'等待'):#可等待

                应答=应答.等待()#等待

            if isinstance(应答,dict):#信封

                结果=应答.get('result') or 应答#结果

                if isinstance(结果,dict) and 'value' in 结果:#有 value

                    return tuple(结果.get('value') or ())#列表

                if isinstance(结果,dict) and 结果.get('ok') and 'value' in 结果:#ok 信封

                    return tuple(结果.get('value') or ())#列表

            return tuple(应答 or ())#原样

        自身.目录=命令目录(拉取)#目录缓存

        触发=上下文.get('inputTriggers')#斜杠服务

        if 触发 is not None:#已挂

            def 登记源():#登记 '/' 命令源

                """候选走模糊过滤。"""

                return 触发.registerSource({#源

                    'trigger':'/','name':'command',#斜杠

                    'candidates':自身.候选们,#菜单候选

                    'onPick':自身.分发,#点选

                    'matchSpace':自身.匹配空格,#空格列

                    'matchEnter':自身.匹配回车,#回车列

                    'warm':lambda 会话:自身.目录.预热(读字段(会话,'sessionId')),#预热

                })#结束

            上下文.effect(登记源,'command: slash source')#斜杠源

        远程=上下文.get('remote')#远程

        if 远程 is not None and hasattr(远程,'$on'):#可订阅

            远程.$on('commands/change',lambda *a,**k:自身.目录.全部失效())#软失效

            远程.$on('agent-preset/selected',lambda 会话标识,*a,**k:自身.目录.刷新(会话标识))#单键重拉

        if hasattr(上下文,'on'):#连接重置

            上下文.on('connection/reset',lambda *a,**k:自身.目录.重连重置())#硬重置



    def register(自身,贡献):#注册客户端命令贡献

        """重名抛错；返回拆除器。"""

        名=贡献['name']#名

        if 名 in 自身.贡献表:#重名

            raise Exception('ui-commands: contribution already registered: '+名)#抛

        自身.贡献表[名]=贡献#记

        def 拆():#拆除

            """去掉贡献。"""

            自身.贡献表.pop(名,None)#删

        return 拆#拆除器



    def decorate(自身,装饰):#挂宿主命令装饰

        """重名抛错；返回拆除器。"""

        名=装饰['name']#名

        if 名 in 自身.装饰表:#重名

            raise Exception('ui-commands: decoration already registered: '+名)#抛

        自身.装饰表[名]=装饰#记

        def 拆():#拆除

            """去掉装饰。"""

            自身.装饰表.pop(名,None)#删

        return 拆#拆除器



    def popupFor(自身,作用域):#按会话取弹出控制器

        """惰性创建；作用域拆除时清掉。"""

        会话标识=作用域.sessionId if hasattr(作用域,'sessionId') else 作用域.get('sessionId')#会话 id

        已有=自身.弹出表.get(会话标识)#已有

        if 已有 is not None:#复用

            return 已有#控制器

        def 消费(片段):#消费令牌

            """接线侧实现；默认 True。"""

            return True#良性

        def 聚焦():#聚焦编写器

            """经覆盖层货币。"""

            钩=自身.聚焦钩.get(会话标识)#钩

            if 钩 is not None:#有

                钩()#聚焦

        弹出=弹出选择控制器({'consume':消费,'focusComposer':聚焦})#新建

        自身.弹出表[会话标识]=弹出#记入

        def 拆():#拆除弹出

            """dispose 并删表。"""

            def 清():#清

                """拆除。"""

                弹出.dispose()#拆

                自身.弹出表.pop(会话标识,None)#删

                自身.聚焦钩.pop(会话标识,None)#解绑

            return 清#拆除器

        if hasattr(作用域,'effect'):#有 effect

            作用域.effect(拆,'ui-commands: session popup')#登记

        return 弹出#控制器



    def bindComposerFocus(自身,会话标识,聚焦):#绑定聚焦钩

        """覆盖层槽接线；卸载时解绑。"""

        自身.聚焦钩[会话标识]=聚焦#写

        def 解绑():#卸载

            """仍是本回调才删。"""

            if 自身.聚焦钩.get(会话标识) is 聚焦:#仍是

                自身.聚焦钩.pop(会话标识,None)#删

        return 解绑#拆除器



    def 候选们(自身,会话,请求):#菜单候选：目录+贡献+模糊

        """宿主目录与贡献可用性合并，再位置过滤与模糊名排名。"""

        会话标识=读字段(会话,'sessionId')#会话 id

        信号=读字段(请求,'signal')#中止

        列表=自身.目录.确保就绪(会话标识,信号)#强等待

        行们=[]#合成行

        已见=set()#已占用名

        for 项 in 列表:#宿主目录

            名=读字段(项,'name')#名

            已见.add(名)#占用

            行={'name':名,'description':读字段(项,'description')}#行

            输入=读字段(项,'input')#input

            if 输入 is not None and 读字段(输入,'hint') is not None:#有 hint

                行['hint']=读字段(输入,'hint')#hint

            行们.append(行)#加

        for 贡献 in 自身.贡献表.values():#客户端贡献

            可用=贡献.get('available')#可用性

            if 可用 is not None and not 可用(会话):#不可用

                continue#跳

            名=贡献['name']#名

            if 名 in 已见:#撞名

                raise Exception('ui-commands: contribution /'+名+' collides with a host command')#大声失败

            行们.append({'name':名,'description':贡献.get('description')})#贡献行

        位置=读字段(请求,'position','leading')#位置

        if 位置!='leading':#非 leading 丢掉带 hint

            行们=[c for c in 行们 if c.get('hint') is None]#过滤

        return 模糊候选(行们,读字段(请求,'query') or '')#模糊排名



    def 分发(自身,点选):#菜单点选分发

        """贡献/装饰→弹出；宿主 input→认领；裸调用→即发。"""

        候选=读字段(点选,'candidate') or {}#候选

        名=读字段(候选,'name')#名

        会话=读字段(点选,'session')#会话

        贡献=自身.贡献表.get(名)#贡献

        if 贡献 is not None:#有贡献

            可用=贡献.get('available')#可用性

            if 可用 is None or 可用(会话):#可用

                自身._打开弹出(名,贡献.get('ui'),会话,{'via':'menu','span':读字段(点选,'span')})#弹出

                return 'handled'#已处理

        描述=自身.目录.解析(读字段(会话,'sessionId'),名)#宿主描述

        if 描述 is None:#快照已换

            return None#未命中

        装饰=自身.装饰表.get(名)#装饰

        if 装饰 is not None:#有装饰

            可用=装饰.get('available')#可用性

            if 可用 is None or 可用(会话):#可用

                自身._打开弹出(名,装饰.get('ui'),会话,{'via':'menu','span':读字段(点选,'span')})#弹出

                return 'handled'#已处理

        if 读字段(描述,'input') is not None:#leadingInput

            return {'claim':自身._前导认领(描述,会话)}#认领

        return 'handled'#即发路径由宿主接线；此处标已处理



    def 匹配空格(自身,会话,令牌):#空格热键分发

        """只有宿主 leadingInput 认领。"""

        if not str(令牌).startswith('/'):#非斜杠

            return None#未命中

        名=令牌[1:]#去 '/'

        if 名 in 自身.贡献表:#弹出从不空格认领

            return None#未命中

        描述=自身.目录.解析(读字段(会话,'sessionId'),名)#描述

        if 描述 is None or 读字段(描述,'input') is None:#无

            return None#未命中

        return {'claim':自身._前导认领(描述,会话)}#认领



    def 匹配回车(自身,会话,行,信号=None):#回车分发

        """贡献与裸宿主只作用于裸令牌；leadingInput 对带参宽容。"""

        去空白=行.strip()#去空白

        if not 去空白.startswith('/'):#非斜杠

            return None#未命中

        切=-1#空白

        for 下标,字 in enumerate(去空白):#找

            if 字.isspace():#空白

                切=下标#记

                break#停

        令牌=去空白 if 切==-1 else 去空白[:切]#令牌

        裸=切==-1#无参

        名=令牌[1:]#去 '/'

        if 名=='':#只有斜杠

            return None#未命中

        贡献=自身.贡献表.get(名)#贡献

        if 贡献 is not None:#有

            可用=贡献.get('available')#可用

            if 可用 is None or 可用(会话):#可用

                if not 裸:#带参不归弹出

                    return None#未命中

                自身._打开弹出(名,贡献.get('ui'),会话,{'via':'enter','token':令牌})#弹出

                return 'handled'#已处理

        自身.目录.确保就绪(读字段(会话,'sessionId'),信号)#强等待

        描述=自身.目录.解析(读字段(会话,'sessionId'),名)#描述

        if 描述 is None:#没有

            return None#未命中

        if 裸:#仅裸回车问装饰

            装饰=自身.装饰表.get(名)#装饰

            if 装饰 is not None:#有

                可用=装饰.get('available')#可用

                if 可用 is None or 可用(会话):#可用

                    自身._打开弹出(名,装饰.get('ui'),会话,{'via':'enter','token':令牌})#弹出

                    return 'handled'#已处理

        if 读字段(描述,'input') is not None:#认领

            return {'claim':自身._前导认领(描述,会话)}#认领

        if not 裸:#无 input 不吃带参

            return None#未命中

        return 'handled'#即发



    def _打开弹出(自身,名,规格,会话,片段):#打开该会话弹出

        """作用域没了则静默。"""

        会话标识=读字段(会话,'sessionId')#id

        会话面=自身.ctx.get('sessions') if hasattr(自身,'ctx') else None#sessions

        作用域=None#作用域

        if 会话面 is not None and hasattr(会话面,'scope'):#有

            作用域=会话面.scope(会话标识)#取

        if 作用域 is None:#无

            return#静默

        自身.popupFor(作用域).open(名,规格,会话,片段)#打开



    def _前导认领(自身,描述,会话):#造 leadingInput 认领

        """令牌 `/name `。"""

        名=读字段(描述,'name')#名

        令牌='/'+str(名)+' '#含尾空格

        认领={'token':令牌}#认领

        输入=读字段(描述,'input')#input

        if 输入 is not None and 读字段(输入,'hint') is not None:#hint

            认领['hint']=读字段(输入,'hint')#hint

        return 认领#认领


