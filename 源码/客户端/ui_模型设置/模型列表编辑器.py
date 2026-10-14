import re#正则
from nicegui import ui as 界面
from .DeepSeek模型编辑器 import 解析容量,格式化容量#容量拼写
from .存储 import 错误文案#拒绝文案
from .编辑器页脚 import 画输入类型#输入类型勾选

__all__=['容量提示','采纳候选','模型列表编辑器']

容量提示={'contextWindow':'256K','maxTokens':'32K'}#空字段占位（适配器回退量级）
行号前缀=re.compile(r'^[0-9]+',re.ASCII)#缓冲键行号

def 文本自(模型,键):#行文本字段
    '非字符串则空串'
    值=模型[键] if 键 in 模型 else None#值
    return 值 if isinstance(值,str) else ''#文本

def 数字自(模型,键):#行数字字段
    '非数字则 None'
    值=模型[键] if 键 in 模型 else None#值
    return 值 if isinstance(值,(int,float)) and not isinstance(值,bool) else None#数字

def 容量拼写(值):#存量容量→字段文本
    '未设为空串'
    return '' if 值 is None else 格式化容量(值)#拼写

def 采纳候选(候选):#发现结果→草稿行
    '保留端点披露的容量'
    行={'id':候选['id']}#必有 id
    if 'name' in 候选 and 候选['name'] is not None:#有名
        行['name']=候选['name']
    if 'contextWindow' in 候选 and 候选['contextWindow'] is not None:#有上下文
        行['contextWindow']=候选['contextWindow']
    if 'maxTokens' in 候选 and 候选['maxTokens'] is not None:#有上限
        行['maxTokens']=候选['maxTokens']
    return 行#草稿

class 模型列表编辑器:
    '行编辑、展开容量、探询采纳对话框。父组件调用渲染，构造不画'
    def __init__(自身,属性):#构造
        '记下 props 与本地态'
        自身.属性=属性
        自身.忙=False#探询在飞
        自身.失败=None#失败文案
        自身.候选=None#发现列表或 None
        自身.已选=set()#勾选 id
        自身.已展开=set()#展开行号
        自身.编辑中={}#缓冲键→文本

    def 更新(自身,属性):#props 变更
        '刷新'
        自身.属性=属性#最新

    def 缓冲键(自身,下标,字段):#容量缓冲键
        '`index:field`'
        return f'{下标}:{字段}'#键

    def 改容量(自身,下标,字段,文本):#键入容量
        '缓冲并解析写入行'
        自身.编辑中[自身.缓冲键(下标,字段)]=文本#缓冲
        自身.补丁(下标,{字段:解析容量(文本)})#写行

    def 容量文本(自身,模型,下标,字段):#容量显示
        '优先缓冲'
        键=自身.缓冲键(下标,字段)#键
        if 键 in 自身.编辑中:#有键入
            return 自身.编辑中[键]#键入
        return 容量拼写(数字自(模型,字段))#存量

    def 移除重键(自身,当前,下标):#删行后重键缓冲
        '丢被删行，其后行号减一'
        下一={}#新图
        for 键,值 in 当前.items():#每缓冲
            位=int(键[:键.index(':')])#行号
            if 位==下标:#被删
                continue#跳过
            新键=行号前缀.sub(str(位-1),键,count=1) if 位>下标 else 键#重键
            下一[新键]=值
        return 下一#新图

    def 切换展开(自身,下标):#切换披露
        '开则关，关则开'
        if 下标 in 自身.已展开:#已开
            自身.已展开.discard(下标)#关
        else:#未开
            自身.已展开.add(下标)

    def 补丁(自身,下标,下一):#改一行
        '清空字段则从档案丢掉'
        模型列表=list(自身.属性['models']) if 'models' in 自身.属性 and 自身.属性['models'] is not None else []#当前
        清除=set(键 for 键,值 in 下一.items() if 值 is None or 值=='')#待清
        结果=[]#新表
        for 位,模型 in enumerate(模型列表):#逐行
            if 位!=下标:#非目标
                结果.append(dict(模型))#拷贝
                continue#下一项
            合并={**dict(模型),**下一}#合并
            结果.append({键:值 for 键,值 in 合并.items() if 键 not in 清除})#丢掉清空
        变更=自身.属性['onChange'] if 'onChange' in 自身.属性 else None#回调
        if 变更 is not None:
            变更(结果)#通知

    def 探询(自身):#问端点当前表单
        '发现模型；失败文案挂本面'
        自身.忙=True#在飞
        自身.失败=None#清错
        探测=自身.属性['probe'] if 'probe' in 自身.属性 and 自身.属性['probe'] is not None else {}#探测目标
        接口=自身.属性['api']#llm 面
        翻译=自身.属性['t']#文案
        try:#探询
            请求={'settingsNs':探测['settingsNs'] if 'settingsNs' in 探测 else None}#基础
            if 'provider' in 探测 and 探测['provider'] is not None:#有路由
                请求['provider']=探测['provider']#带上
            基址=探测['baseURL'] if 'baseURL' in 探测 else None#端点
            if isinstance(基址,str) and len(基址)>0:#有端点
                请求['baseURL']=基址#带上
            if 'api' in 探测 and 探测['api'] is not None:#有协议
                请求['api']=探测['api']#带上
            if 'apiKey' in 探测 and 探测['apiKey'] is not None:#有密钥
                请求['apiKey']=探测['apiKey']#带上
            响应=接口.llm.discoverModels(请求).等待()#发现
            结果=响应['result'] if 'result' in 响应 else None#结果
            if 结果 is None or 结果['ok'] is not True:#失败
                错=结果['error'] if 结果 is not None and 'error' in 结果 else None#错误
                自身.失败=错误文案(错['message'] if 错 is not None and 'message' in 错 else None)
                return
            值=结果['value'] if 'value' in 结果 else None#值
            找到=值['models'] if 值 is not None and 'models' in 值 and 值['models'] is not None else []#候选
            if len(找到)==0:#空
                自身.失败=翻译('fetchEmpty')#空文案
                return
            已有=自身.属性['models'] if 'models' in 自身.属性 and 自身.属性['models'] is not None else []#已配
            已知=set(文本自(模,'id') for 模 in 已有)#已配 id
            自身.候选=找到#挂候选
            自身.已选=set(模['id'] for 模 in 找到 if 模['id'] not in 已知)#默认勾新
        except Exception as 错误:#传输拒绝；RPC 异常契约未定
            自身.失败=错误文案(错误)#文案
        finally:#收尾
            自身.忙=False#闲

    def 关挑选(自身):#关对话框
        '清候选与勾选'
        自身.候选=None
        自身.已选=set()

    def 采纳已选(自身):#把勾选并入列表
        '已配行保留用户容量'
        if 自身.候选 is None:#无
            return
        按标识={}#id→行
        已有=自身.属性['models'] if 'models' in 自身.属性 and 自身.属性['models'] is not None else []#已有
        for 模型 in 已有:#已有
            按标识[文本自(模型,'id')]=dict(模型)
        for 候选 in 自身.候选:#候选
            标识=候选['id']#id
            if 标识 not in 自身.已选:#未勾
                continue#跳过
            按标识[标识]=按标识[标识] if 标识 in 按标识 else 采纳候选(候选)#保留已配或采纳
        变更=自身.属性['onChange'] if 'onChange' in 自身.属性 else None#回调
        if 变更 is not None:
            变更(list(按标识.values()))#写入
        自身.关挑选()#关

    def 切换勾选(自身,标识):#勾选切换
        '有则去，无则加'
        if 标识 in 自身.已选:#已勾
            自身.已选.discard(标识)#去
        else:#未勾
            自身.已选.add(标识)#加

    def 移除(自身,下标):#删行并重键
        '展开与缓冲随行号移动'
        已有=自身.属性['models'] if 'models' in 自身.属性 and 自身.属性['models'] is not None else []#当前
        模型列表=[dict(模) for 位,模 in enumerate(已有) if 位!=下标]#过滤
        新展开=set()#新展开
        for 位 in 自身.已展开:#每展开
            if 位<下标:#前
                新展开.add(位)#保留
            elif 位>下标:#后
                新展开.add(位-1)#移位
        自身.已展开=新展开#覆盖
        自身.编辑中=自身.移除重键(自身.编辑中,下标)#重键
        变更=自身.属性['onChange'] if 'onChange' in 自身.属性 else None#回调
        if 变更 is not None:
            变更(模型列表)#通知

    def 渲染(自身):#结构化视图
        '目录头、行、探询对话框'
        翻译=自身.属性['t']#文案
        禁用=bool(自身.属性['disabled']) if 'disabled' in 自身.属性 else False#禁用
        模型列表=list(自身.属性['models']) if 'models' in 自身.属性 and 自身.属性['models'] is not None else []#行
        探测=自身.属性['probe'] if 'probe' in 自身.属性 and 自身.属性['probe'] is not None else {}#探测
        覆盖=自身.属性['overridden'] if 'overridden' in 自身.属性 else None#是否用户层拥有
        基址=探测['baseURL'] if 'baseURL' in 探测 else None#端点
        可问=('provider' in 探测 and 探测['provider'] is not None) or (isinstance(基址,str) and len(基址)>0)#可探询
        阻塞=自身.属性['probeBlocked'] if 'probeBlocked' in 自身.属性 else None#阻塞文案键
        行表=[]#行视图
        for 下标,模型 in enumerate(模型列表):#逐行
            def 切换本行(某=下标):#披露
                '切换该行展开'
                自身.切换展开(某)#切换
            def 移除本行(某=下标):#删除
                '删除该行'
                自身.移除(某)#删除
            def 改标识(文,某=下标):#改 id
                '写入 id'
                自身.补丁(某,{'id':文})#补丁
            def 改名称(文,某=下标):#改 name
                '空串则清 name'
                自身.补丁(某,{'name':None if 文=='' else 文})#补丁
            行={#行
                'index':下标,#下标
                'id':文本自(模型,'id'),#id
                'name':文本自(模型,'name'),#name
                'expanded':下标 in 自身.已展开,#展开
                'onToggle':切换本行,#披露
                'onRemove':移除本行,#删除
                'onId':改标识,#改 id
                'onName':改名称,#改 name
            }#行基础
            if 下标 in 自身.已展开:#容量披露
                def 改上下文(文,某=下标):#上下文
                    '写入 contextWindow'
                    自身.改容量(某,'contextWindow',文)#改
                def 改上限(文,某=下标):#上限
                    '写入 maxTokens'
                    自身.改容量(某,'maxTokens',文)#改
                行['advanced']=[#容量字段
                    {'field':'contextWindow','label':翻译('modelContextWindow'),'text':自身.容量文本(模型,下标,'contextWindow'),'placeholder':容量提示['contextWindow'],'onChange':改上下文},#上下文
                    {'field':'maxTokens','label':翻译('modelMaxTokens'),'text':自身.容量文本(模型,下标,'maxTokens'),'placeholder':容量提示['maxTokens'],'onChange':改上限},#上限
                ]#高级结束
            行表.append(行)#记入
        def 添加():#加空行
            '追加空 id'
            变更=自身.属性['onChange'] if 'onChange' in 自身.属性 else None#回调
            if 变更 is not None:
                变更([dict(模) for 模 in 模型列表]+[{'id':''}])#追加
        复位=自身.属性['onReset'] if 'onReset' in 自身.属性 else None#复位
        对话框=None#挑选框
        if 自身.候选 is not None:#有候选
            候选行=[]#候选行
            for 候 in 自身.候选:#逐候选
                def 切换勾(某=候['id']):#勾选
                    '切换该候选勾选'
                    自身.切换勾选(某)#切换
                候选行.append({#候选行
                    'id':候['id'],#id
                    'checked':候['id'] in 自身.已选,#勾选
                    'onToggle':切换勾,#切换
                })#候选结束
            对话框={#对话框
                'title':翻译('fetchTitle'),#标题
                'description':翻译('fetchDescription'),#说明
                'closeLabel':翻译('close'),#关闭
                'cancelLabel':翻译('cancel'),#取消
                'adoptLabel':翻译('fetchAdopt'),#采纳
                'onClose':自身.关挑选,#关
                'onAdopt':自身.采纳已选,#采纳
                'candidates':候选行,#候选表
            }#对话框结束
        with 界面.column().classes('model-list-editor modelCatalog'):
            界面.label(翻译('models'))
            if 覆盖 is not None:
                界面.label(翻译('modelsCustomized' if 覆盖 else 'modelsInherited'))
            if 覆盖 is True and 复位 is not None:
                复位钮=界面.button(翻译('resetModels'), on_click=复位)
                if 禁用:
                    复位钮.disable()
            探询文=翻译('fetching' if 自身.忙 else 'fetchModels')
            探询钮=界面.button(探询文, on_click=自身.探询)
            if 禁用 or 自身.忙 or not 可问 or 阻塞 is not None:
                探询钮.disable()
            if 阻塞 is not None:
                界面.label(翻译(阻塞))
            elif not 可问:
                界面.label(翻译('fetchNeedsBaseUrl'))
            if isinstance(自身.失败,str) and 自身.失败!='':
                界面.label(自身.失败)
            if len(模型列表)==0:
                界面.label(翻译('modelsEmpty'))
            for 行 in 行表:
                with 界面.row():
                    界面.button(on_click=行['onToggle']).props('icon=expand_more flat round')
                    def 改号(事件,回调=行['onId']):
                        '写入标识'
                        回调(事件.value)
                    def 改名(事件,回调=行['onName']):
                        '写入名称'
                        回调(事件.value)
                    号框=界面.input(value=行['id'], on_change=改号)
                    名框=界面.input(value=行['name'], on_change=改名)
                    删=界面.button(on_click=行['onRemove']).props('icon=delete flat round')
                    if 禁用:
                        号框.disable()
                        名框.disable()
                        删.disable()
                if 行['expanded'] and 'advanced' in 行:
                    for 容量 in 行['advanced']:
                        def 改容(事件,回调=容量['onChange']):
                            '写入容量'
                            回调(事件.value)
                        容框=界面.input(容量['label'], value=容量['text'], placeholder=容量['placeholder'], on_change=改容)
                        if 禁用:
                            容框.disable()
                    def 改输入(补丁,某=行['index']):
                        '写入输入类型'
                        自身.补丁(某,补丁)
                    回退=自身.属性['defaultInput'] if 'defaultInput' in 自身.属性 else None
                    画输入类型(界面,模型列表[行['index']],'input',禁用,回退,翻译,改输入)
            加=界面.button(翻译('addModel'), on_click=添加)
            if 禁用:
                加.disable()
            if 对话框 is not None:
                with 界面.dialog() as 挑选框:
                    with 界面.card():
                        界面.label(对话框['title'])
                        界面.label(对话框['description'])
                        for 候 in 对话框['candidates']:
                            def 改勾(事件,回调=候['onToggle']):
                                '切换候选'
                                回调()
                            界面.checkbox(候['id'], value=候['checked'], on_change=改勾)
                        界面.button(对话框['closeLabel'], on_click=对话框['onClose'])
                        界面.button(对话框['cancelLabel'], on_click=对话框['onClose'])
                        界面.button(对话框['adoptLabel'], on_click=对话框['onAdopt'])
                挑选框.open()

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 调用'
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
