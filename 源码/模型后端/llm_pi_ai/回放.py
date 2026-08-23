"""持久的 pi-ai 回放元数据与助手历史重建。

对齐上游 `llm-pi-ai/src/replay.ts`。公开面仅中文名；无英文别名。
"""
import json#JSON 解析
from .. import llm#语言模型服务

__all__=('转派回放状态','读回放状态','转派助手','空派用量','解析参数')#仅中文公开名

结束原因集合=('stop','length','toolUse','error','aborted')#合法结束原因
块类型集合=('text','reasoning','tool-call')#合法回放块类型
签名字段=('textSignature','thinkingSignature','thoughtSignature')#签名字段
必填字符串=('api','provider','model')#必填字符串字段

def 解析参数(原始):
    """解析工具调用参数 JSON；畸形则容忍为 {}。"""
    try:#尝试解析
        已解析=json.loads(原始)#按未知查看
        if isinstance(已解析,dict):#合法对象
            return 已解析#合法对象
    except Exception:#畸形
        pass#只吞畸形JSON；数组、原语与抛出都落到下方空对象
    return {}#畸形则空对象

def 空派用量():
    """构造历史派爱消息所需的零用量。"""
    return {
        'input':0,#输入
        'output':0,#输出
        'cacheRead':0,#缓存读
        'cacheWrite':0,#缓存写
        'totalTokens':0,#合计
        'cost':{'input':0,'output':0,'cacheRead':0,'cacheWrite':0,'total':0},#费用全零
    }#空用量

def 转派回放状态(消息):
    """把一次成功的派爱响应投影成最小持久回放状态。"""
    内容=消息['content'] if isinstance(消息,dict) else 消息.content#内容块
    块们=[]#块级元数据
    for 块 in 内容:#逐块
        类型=块['type'] if isinstance(块,dict) else 块.type#块类型
        if 类型=='text':#文本
            投影={'type':'text'}#文本
            签名=块.get('textSignature') if isinstance(块,dict) else getattr(块,'textSignature',None)#文本签名
            if 签名 is not None:#有签名
                投影['textSignature']=签名#有签名才带上
            块们.append(投影)#写入
        elif 类型=='thinking':#思考
            投影={'type':'reasoning'}#harness推理
            签名=块.get('thinkingSignature') if isinstance(块,dict) else getattr(块,'thinkingSignature',None)#思考签名
            if 签名 is not None:#有签名
                投影['thinkingSignature']=签名#有签名才带上
            脱敏=块.get('redacted') if isinstance(块,dict) else getattr(块,'redacted',None)#脱敏
            if 脱敏 is not None:#有脱敏
                投影['redacted']=脱敏#有脱敏才带上
            块们.append(投影)#写入
        elif 类型=='toolCall':#工具调用
            投影={'type':'tool-call'}#harness工具调用
            签名=块.get('thoughtSignature') if isinstance(块,dict) else getattr(块,'thoughtSignature',None)#思考签名
            if 签名 is not None:#有思考签名
                投影['thoughtSignature']=签名#有思考签名才带上
            块们.append(投影)#写入
    状态={
        'kind':'pi-ai',#判别标签
        'version':1,#状态版本
        'api':消息['api'] if isinstance(消息,dict) else 消息.api,#线路协议
        'provider':消息['provider'] if isinstance(消息,dict) else 消息.provider,#提供方
        'model':消息['model'] if isinstance(消息,dict) else 消息.model,#模型
        'stopReason':消息['stopReason'] if isinstance(消息,dict) else 消息.stopReason,#结束原因
        'blocks':块们,#块级元数据
    }#最小投影
    响应模型=消息.get('responseModel') if isinstance(消息,dict) else getattr(消息,'responseModel',None)#响应模型
    if 响应模型 is not None:#有响应模型
        状态['responseModel']=响应模型#有响应模型才带上
    响应标识=消息.get('responseId') if isinstance(消息,dict) else getattr(消息,'responseId',None)#响应id
    if 响应标识 is not None:#有响应id
        状态['responseId']=响应标识#有响应id才带上
    return 状态#回放状态

def 非法回放(消息):
    """非法回放状态。"""
    raise llm.大模型错误(f'invalid pi-ai replay state: {消息}','INVALID_REPLAY_STATE')#带诊断抛出

def 读回放状态(值):
    """在适配器私有状态到达 pi-ai 之前校验它。"""
    if not isinstance(值,dict):#根必须是普通对象，数组与原语一律拒绝
        return 非法回放('expected an object')#必须是对象
    if 值.get('kind')!='pi-ai':#判别标签钉死为本后端，其它判别标签不是本状态
        return 非法回放('unknown state kind')#判别标签必须是pi-ai
    if 值.get('version')!=1:#只认当前状态版本，未知版本不得静默放行
        return 非法回放(f'unsupported version {值.get("version")}')#只认版本1
    for 键 in 必填字符串:#线路协议、提供方、模型三个字段逐个核对
        字段=值.get(键)#字段值
        if not isinstance(字段,str) or len(字段)==0:#缺席、非字符串、空串都算缺失
            return 非法回放(f'{键} must be a non-empty string')#必须非空
    if str(值.get('stopReason')) not in 结束原因集合:#结束原因必须落在派爱封闭集合
        return 非法回放('unknown stopReason')#非法结束原因
    if 值.get('responseModel') is not None and not isinstance(值.get('responseModel'),str):#可选响应模型有则必须是字符串
        return 非法回放('responseModel must be a string')#可选响应模型必须是字符串
    if 值.get('responseId') is not None and not isinstance(值.get('responseId'),str):#可选响应id有则必须是字符串
        return 非法回放('responseId must be a string')#可选响应id必须是字符串
    if not isinstance(值.get('blocks'),list):#块列必须是数组，对象或缺席都非法
        return 非法回放('blocks must be an array')#块必须是数组
    下标=0#块下标
    for 块值 in 值['blocks']:#按出现顺序校验每一块元数据
        if not isinstance(块值,dict):#单块必须是对象，不能是字符串或数组
            return 非法回放(f'block {下标} must be an object')#块必须是对象
        if str(块值.get('type')) not in 块类型集合:#块类型必须是文本、推理或工具调用
            return 非法回放(f'block {下标} has an unknown type')#类型必须已知
        for 签名 in 签名字段:#三种可选签名字段有则逐个校验
            if 块值.get(签名) is not None and not isinstance(块值.get(签名),str):#有签名则必须是字符串
                return 非法回放(f'block {下标} {签名} must be a string')#有则必须是字符串
        if 块值.get('redacted') is not None and not isinstance(块值.get('redacted'),bool):#有脱敏则必须是布尔，禁止用 0/1
            return 非法回放(f'block {下标} redacted must be boolean')#脱敏必须是布尔
        下标+=1#前进
    return 值#通过校验

def 外来助手(消息):
    """转换提供方中立块，不把它们当作同模型回放。"""
    来源=消息['source'] if isinstance(消息,dict) else 消息.source#映射与对象两种助手消息都从 source 取来源
    来源种类=来源['kind'] if isinstance(来源,dict) else 来源.kind#kind 决定能否沿用来源提供方与模型身份
    模型来源=来源 if 来源种类=='model' else None#仅 kind=model 可保留身份；command 等其它来源一律当外来
    内容=[]#pi-ai内容
    块列=消息['content'] if isinstance(消息,dict) else 消息.content#harness 正文；外来路径不读 replayState
    for 块 in 块列:#按 harness 内容顺序转成派爱块，不走同模型回放元数据
        类型=块['type'] if isinstance(块,dict) else 块.type#块类型走映射或对象字段，决定落到哪条派爱联合
        if 类型=='text':#文本块直接落到派爱 text，外来路径不带 textSignature
            内容.append({'type':'text','text':块['text'] if isinstance(块,dict) else 块.text})#只抄正文；签名只存在于同模型回放
        elif 类型=='reasoning':#推理块落到派爱 thinking，外来路径不带签名与脱敏
            内容.append({'type':'thinking','thinking':块['text'] if isinstance(块,dict) else 块.text})#只抄思考正文；thinkingSignature/redacted 不抄
        elif 类型=='tool-call':#工具调用落到派爱 toolCall，参数容忍畸形 JSON
            内容.append({
                'type':'toolCall',#pi-ai工具调用
                'id':块['id'] if isinstance(块,dict) else 块.id,#调用id
                'name':块['name'] if isinstance(块,dict) else 块.name,#工具名
                'arguments':解析参数(块['arguments'] if isinstance(块,dict) else 块.arguments),#畸形 JSON 容忍为 {}，与同模型回放同一解析
            })#工具调用
        elif 类型=='image':#派爱历史无法表示助手结构化图片输出
            raise llm.大模型错误('pi-ai chat history cannot represent structured assistant image output','UNSUPPORTED_CONTENT')#助手图片无法表示
    有工具=False#是否含工具调用，用来钉 stopReason；外来路径不读回放元数据里的结束原因
    for 片 in 内容:#扫一遍已转换内容，决定结束原因
        if 片['type']=='toolCall':#见到工具调用则结束原因必须是 toolUse，与同模型回放读元数据不同
            有工具=True#已见到工具调用，后面块不再影响结束原因
            break#已判定，不必扫完
    提供方='dsh-foreign'#缺模型来源时钉外来提供方，避免被当成某条已配置路由
    模型='dsh-foreign'#缺模型来源时钉外来模型
    if 模型来源 is not None:#来源是模型产出则保留其提供方与模型，否则钉外来标记
        提供方=模型来源['provider'] if isinstance(模型来源,dict) else 模型来源.provider#沿用模型来源的提供方；仍不走 replayState
        模型=模型来源['model'] if isinstance(模型来源,dict) else 模型来源.model#沿用模型来源的模型 id；身份保留不等于同模型回放
    return {
        'role':'assistant',#助手
        'content':内容,#已转换内容
        'api':'dsh-foreign',#外来协议标记，声明这条历史不是本路由线路协议
        'provider':提供方,#来源提供方或外来标记
        'model':模型,#来源模型或外来标记
        'usage':空派用量(),#历史零用量
        'stopReason':'toolUse' if 有工具 else 'stop',#有工具调用则 toolUse，纯文本或推理则 stop
        'timestamp':0,#历史时间戳
    }#外来助手消息

def 回放助手(消息,来源,原始状态):
    """把持久 harness 内容与已校验的派爱回放元数据重新组合。"""
    状态=读回放状态(原始状态)#先校验再重组；非法状态不得拼进派爱历史
    来源提供方=来源['provider'] if isinstance(来源,dict) else 来源.provider#助手来源上的提供方，必须与回放元数据同一路由
    来源模型=来源['model'] if isinstance(来源,dict) else 来源.model#助手来源上的模型，必须与回放元数据同一模型
    if 状态['provider']!=来源提供方:#回放元数据的提供方必须与助手来源同一路由，否则会把别家签名接到本路由历史上
        return 非法回放('provider does not match assistant source')#提供方必须匹配
    if 状态['model']!=来源模型:#回放元数据的模型必须与助手来源同一模型，跨模型不能复用块签名
        return 非法回放('model does not match assistant source')#模型必须匹配
    块列=消息['content'] if isinstance(消息,dict) else 消息.content#harness 正文；回放只补签名，不以状态覆盖正文
    if len(状态['blocks'])!=len(块列):#块数必须一一对应，少一块或多一块都说明不是同一次响应
        return 非法回放('block count does not match assistant content')#块数必须匹配
    内容=[]#重组内容
    下标=0#块下标
    for 块 in 块列:#按 harness 内容下标对齐回放块，把正文与签名重新拼回去
        回放=状态['blocks'][下标]#下标对齐的回放块；错位会在下一行类型核对时拒绝
        块类型=块['type'] if isinstance(块,dict) else 块.type#harness 类型；必须与回放块 type 同一判别
        if 回放 is None or 回放.get('type')!=块类型:#缺块或类型错位都不是同一次响应，禁止错位补签名
            return 非法回放(f'block {下标} does not match assistant content')#类型必须对齐
        if 块类型=='text':#文本块取 harness 正文，签名只从回放元数据补，正文不以状态为准
            重组={'type':'text','text':块['text'] if isinstance(块,dict) else 块.text}#文本
            if 回放.get('type')=='text' and 回放.get('textSignature') is not None:#类型仍是 text 且状态里有签名才写回，缺席不加字段
                重组['textSignature']=回放['textSignature']#有签名才带上
            内容.append(重组)#写入
        elif 块类型=='reasoning':#推理块落到派爱 thinking，签名与脱敏只从回放补
            重组={'type':'thinking','thinking':块['text'] if isinstance(块,dict) else 块.text}#推理
            if 回放.get('type')=='reasoning' and 回放.get('thinkingSignature') is not None:#类型仍是 reasoning 且状态里有思考签名才写回
                重组['thinkingSignature']=回放['thinkingSignature']#有签名才带上
            if 回放.get('type')=='reasoning' and 回放.get('redacted') is not None:#类型仍是 reasoning 且状态里有脱敏旗标才写回
                重组['redacted']=回放['redacted']#有脱敏才带上
            内容.append(重组)#写入
        elif 块类型=='tool-call':#工具调用取 harness 的 id/名/参数，思考签名从回放补
            重组={
                'type':'toolCall',#pi-ai工具调用
                'id':块['id'] if isinstance(块,dict) else 块.id,#调用id
                'name':块['name'] if isinstance(块,dict) else 块.name,#工具名
                'arguments':解析参数(块['arguments'] if isinstance(块,dict) else 块.arguments),#畸形 JSON 容忍为 {}，与外来助手同一解析
            }#工具调用
            if 回放.get('type')=='tool-call' and 回放.get('thoughtSignature') is not None:#类型仍是 tool-call 且状态里有思考签名才写回
                重组['thoughtSignature']=回放['thoughtSignature']#有思考签名才带上
            内容.append(重组)#写入
        else:#封闭联合之外的 harness 类型无法回放到派爱历史
            return 非法回放(f'block {下标} has an unsupported Harness type')#未知harness类型
        下标+=1#前进到下一块，与状态 blocks 下标保持同步
    结果={
        'role':'assistant',#助手
        'content':内容,#重组内容
        'api':状态['api'],#原线路协议
        'provider':状态['provider'],#提供方
        'model':状态['model'],#模型
        'usage':空派用量(),#历史零用量
        'stopReason':状态['stopReason'],#原结束原因，外来路径不读这一字段
        'timestamp':0,#历史时间戳
    }#回放助手消息
    if 状态.get('responseModel') is not None:#状态里有响应模型才写回，缺席不加字段以免伪造
        结果['responseModel']=状态['responseModel']#有响应模型才带上
    if 状态.get('responseId') is not None:#状态里有响应 id 才写回，缺席不加字段
        结果['responseId']=状态['responseId']#有响应id才带上
    return 结果#回放助手

def 转派助手(消息):
    """把一条持久 harness 助手消息转换成派爱历史。"""
    来源=消息['source'] if isinstance(消息,dict) else 消息.source#映射与对象两种助手消息都从 source 分流
    种类=来源['kind'] if isinstance(来源,dict) else 来源.kind#只有 model 才可能带同模型回放状态
    回放=来源.get('replayState') if isinstance(来源,dict) else getattr(来源,'replayState',None)#缺席用 getattr 默认 None，不把空当非法对象
    if 种类!='model' or 回放 is None:#同模型回放要求来源是模型且带 replayState；缺任一条件都走提供方中立转换
        return 外来助手(消息)#外来：只转块类型，不读也不校验回放元数据
    return 回放助手(消息,来源,回放)#同模型：先校验元数据再把正文与签名重新拼回去
