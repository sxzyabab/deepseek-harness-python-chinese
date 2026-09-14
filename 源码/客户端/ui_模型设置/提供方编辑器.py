import copy#深拷草稿
from ..模式表单 import 再水合模式,取路径,有路径,设路径,删路径,校验草稿#路径编辑
from .DeepSeek模型编辑器 import DeepSeek模型编辑器,模型草稿表,校验DeepSeek模型#DeepSeek 目录
from .密钥判定 import 密钥失败#密钥门闩
from .编辑器页脚 import 编辑器页脚#页脚
from .模型列表编辑器 import 模型列表编辑器#pi-ai 列表
from .存储 import 推导密钥引用,错误文案,协议选项#存储辅助

__all__=['公开DeepSeek基址','路径操作','布局自','引用自','提供方编辑器']#仅中文公开名

公开DeepSeek基址='https://api.deepseek.com'#DeepSeek 公开端点占位

def 草稿于(命名空间,路径):#用户层子树作草稿
    """缺席或非对象→空对象。"""
    用户层=命名空间['user'] if 命名空间 is not None and 'user' in 命名空间 else None#用户层
    子树=取路径(用户层,路径)#用户层
    if not isinstance(子树,dict):#非对象
        return {}#空
    return copy.deepcopy(子树)#深拷

def 路径操作(基路径,之前,之后):#最小路径 ops
    """只点名卡片可见字段；两侧皆无则无 op。"""
    旧=之前 if 之前 is not None else {}#之前；缺席当空 dict
    操作=[]#ops
    for 键,值 in 之后.items():#新键
        旧值=旧[键] if 键 in 旧 else None#旧值；缺席当 None
        if 旧值==值:#未变（结构相等用 ==）
            continue#跳过
        操作.append({'op':'set','path':list(基路径)+[键],'value':值})#设
    for 键 in 旧:#旧键
        if 键 not in 之后:#已删
            操作.append({'op':'unset','path':list(基路径)+[键]})#卸
    return 操作#ops

def 布局自(命名空间名):#适配器族布局
    """未知 ns 仅提示。"""
    if 命名空间名=='llm-deepseek':#DeepSeek
        return 'deepseek'#族
    if 命名空间名=='llm-pi-ai':#pi-ai
        return 'pi-ai'#族
    return 'unknown'#未知

def 引用自(命名空间,路径,提供方):#档案解析的凭证引用
    """有 apiKeyEnv 用其值，否则推导。"""
    解析值=命名空间['value'] if 命名空间 is not None and 'value' in 命名空间 else None#已解析
    档=取路径(解析值,路径)#已解析档
    if 档 is None or 'apiKeyEnv' not in 档:#无档或无字段
        return 推导密钥引用(提供方)#推导
    命名=档['apiKeyEnv']#字段
    return 命名 if isinstance(命名,str) and len(命名)>0 else 推导密钥引用(提供方)#引用

class 提供方编辑器:#提供方编辑卡片
    """密钥 + 自定义区 + 页脚提交。"""
    def __init__(自身,属性):#构造
        """播种草稿与在飞态。"""
        自身.属性=属性#合成 props
        命名空间=属性['namespace'] if 'namespace' in 属性 else None#ns 视图
        路径=list(属性['settingsPath']) if 'settingsPath' in 属性 and 属性['settingsPath'] is not None else []#设置路径
        自身.草稿=草稿于(命名空间,路径)#用户层草稿
        自身.密钥草稿=''#只写密钥
        自身.密钥态=None#credentials.describe
        自身.忙=False#在飞
        自身.失败=None#失败文案
        用户层=命名空间['user'] if 命名空间 is not None and 'user' in 命名空间 else None#用户层
        自身.已提交原稿=取路径(用户层,路径)#重试基线
        自身.期望修订=命名空间['revision'] if 命名空间 is not None and 'revision' in 命名空间 else None#冲突修订
        自身.已拉密钥=False#是否已 describe
        自身.目录编辑器=None#内嵌目录
        自身.页脚=None#页脚

    def 更新(自身,属性):#props 变更
        """刷新 props（草稿保留，避免推送冲掉键入）。"""
        自身.属性=属性#最新

    def 改密钥草稿(自身,文):#密钥键入
        """写入只写密钥草稿。"""
        自身.密钥草稿=文#覆盖

    def 点取消(自身):#取消
        """关闭且未变更。"""
        关闭=自身.属性['onClose'] if 'onClose' in 自身.属性 else None#关闭
        if 关闭 is not None:#有
            关闭(False)#未变更

    def 字符串于(自身,源,键):#非空字符串字段
        """空白视作缺席。"""
        值=取路径(源,[键])#取值
        return 值 if isinstance(值,str) and len(值.strip())>0 else None#字符串

    def 设字段(自身,键,下一):#改草稿字段
        """纯空白清空而非存空格。"""
        值=None if 下一 is None or len(下一.strip())==0 else 下一#归一
        if 值 is None:#清
            自身.草稿=删路径(自身.草稿,[键])#删
        else:#写
            自身.草稿=设路径(自身.草稿,[键],值)#设

    def 拉密钥态(自身):#describe 密钥提示
        """失败静默，不挡编辑。"""
        if 自身.已拉密钥:#已拉
            return#跳过
        自身.已拉密钥=True#标记
        命名空间=自身.属性['namespace']#ns
        路径=list(自身.属性['settingsPath']) if 'settingsPath' in 自身.属性 and 自身.属性['settingsPath'] is not None else []#路径
        引用=引用自(命名空间,路径,自身.属性['provider'])#引用
        接口=自身.属性['api']#API
        try:#describe
            响应=接口.credentials.describe({'refs':[引用]}).等待()#描述
            结果=响应['result']#结果
            if 结果['ok'] is not True:#失败
                return#静默
            值=结果['value'] if 'value' in 结果 else None#值
            图=值['credentials'] if 值 is not None and 'credentials' in 值 and 值['credentials'] is not None else {}#图
            自身.密钥态=图[引用] if 引用 in 图 else None#态
        except Exception:#传输拒绝；RPC 异常契约未定
            return#静默

    def 继承模型(自身,根,节点,路径):#目录下方基线
        """优先 composition 钉住，否则 schema 默认。"""
        命名空间=自身.属性['namespace']#ns
        基层=命名空间['base'] if 命名空间 is not None and 'base' in 命名空间 else None#基层
        钉住=取路径(基层,list(路径)+['models'])#base 层
        if 钉住 is not None:#有钉
            return 钉住#钉住
        模型节点=取路径(根,list(路径)+['models'])#schema 节点
        if 模型节点 is None:#无
            return None#无
        return 模型节点['default'] if 'default' in 模型节点 else None#JSON Schema 默认

    def 应用一次(自身):#写线一次
        """返回失败文案或 None。"""
        命名空间=自身.属性['namespace']#ns
        路径=list(自身.属性['settingsPath']) if 'settingsPath' in 自身.属性 and 自身.属性['settingsPath'] is not None else []#路径
        接口=自身.属性['api']#API
        翻译=自身.属性['t']#文案
        布局=布局自(命名空间['ns'] if 'ns' in 命名空间 else None)#布局
        引用=引用自(命名空间,路径,自身.属性['provider'])#引用
        密钥值=自身.密钥草稿.strip()#去空白密钥
        解析值=命名空间['value'] if 'value' in 命名空间 else None#已解析
        回退=取路径(解析值,路径)#有效档
        下一=自身.草稿#草稿
        仅凭证='credentialOnly' in 自身.属性 and 自身.属性['credentialOnly'] is True#仅凭证
        if (布局=='pi-ai' and 自身.字符串于(自身.草稿,'apiKeyEnv') is None
            and 自身.字符串于(回退,'apiKeyEnv') is None and len(密钥值)>0):#需记引用
            下一=设路径(自身.草稿,['apiKeyEnv'],引用)#写入推导引用
        if 仅凭证 is not True:#写设置
            失败=校验DeepSeek模型(取路径(下一,['models']))#模型门闩
            if 失败 is not None:#坏行
                return f"{翻译('model')} {失败['index']+1}: {翻译(失败['key'])}"#行文案
            模式=命名空间['schema'] if 'schema' in 命名空间 else None#schema
            根=再水合模式(模式)#schema
            节点=取路径(根,路径)#节点
            if 节点 is not None and len(路径)==0:#整段校验
                段错=校验草稿(节点,下一)#校验
                if 段错 is not None:#失败
                    return 段错#文案
            物化空档=(布局=='pi-ai' and 回退 is None and 自身.已提交原稿 is None and len(下一)==0)#原生空档
            if 物化空档:#物化 {}
                操作=[{'op':'set','path':list(路径),'value':{}}]#空对象
            else:#路径 ops
                操作=路径操作(路径,自身.已提交原稿,下一)#差分
            if len(操作)>0:#有写
                响应=接口.settings.mutate({'ns':命名空间['ns'],'ops':操作,'expectedRevision':自身.期望修订}).等待()#变更
                结果=响应['result']#结果
                if 结果['ok'] is not True:#失败
                    错=结果['error'] if 'error' in 结果 and 结果['error'] is not None else {}#错
                    码=错['code'] if 'code' in 错 else None#码
                    return 翻译('conflict') if 码=='settings-conflict' else (错['message'] if 'message' in 错 else None)#文案
                值=结果['value'] if 'value' in 结果 else None#新 ns
                新用户=值['user'] if 值 is not None and 'user' in 值 else None#新用户层
                自身.已提交原稿=取路径(新用户,路径)#新基线
                自身.期望修订=值['revision'] if 值 is not None and 'revision' in 值 else None#新修订
                自身.草稿=下一#对齐草稿
        if len(密钥值)>0:#存密钥
            存=接口.credentials.set({'ref':引用,'value':密钥值}).等待()#set
            存结果=存['result']#结果
            if 存结果['ok'] is not True:#失败
                错=存结果['error'] if 'error' in 存结果 else None#错误
                return 错['message'] if 错 is not None and 'message' in 错 else None#文案
        自身.密钥草稿=''#清草稿
        return None#成功

    def 应用(自身):#提交
        """成功则 onClose(True)。"""
        自身.忙=True#在飞
        自身.失败=None#清错
        try:#写线
            失败=自身.应用一次()#一次
            if 失败 is not None:#失败
                自身.失败=失败#挂文案
                return#停
            关闭=自身.属性['onClose'] if 'onClose' in 自身.属性 else None#关闭
            if 关闭 is not None:#有
                关闭(True)#已变更
        except Exception as 错误:#传输拒绝；RPC 异常契约未定
            自身.失败=错误文案(错误)#文案
        finally:#收尾
            自身.忙=False#闲

    def 渲染策展(自身,族):#已知族字段
        """密钥 + 折叠自定义区。"""
        翻译=自身.属性['t']#文案
        命名空间=自身.属性['namespace']#ns
        路径=list(自身.属性['settingsPath']) if 'settingsPath' in 自身.属性 and 自身.属性['settingsPath'] is not None else []#路径
        只读=bool(自身.属性['readOnly']) if 'readOnly' in 自身.属性 else False#只读
        禁用=只读 or 自身.忙#禁用
        解析值=命名空间['value'] if 'value' in 命名空间 else None#已解析
        回退=取路径(解析值,路径)#有效
        拥身份=族=='pi-ai' and 'declared' in 自身.属性 and 自身.属性['declared'] is True#手声明路由
        自定义模型=取路径(自身.草稿,['models'])#用户 models
        模型覆盖=有路径(自身.草稿,['models'])#是否覆盖
        模式=命名空间['schema'] if 'schema' in 命名空间 else None#schema
        根=再水合模式(模式)#schema
        节点=取路径(根,路径)#节点
        模型列表=模型草稿表(自定义模型 if 模型覆盖 else 自身.继承模型(根,节点,路径))#草稿表
        默认上下文=取路径(回退,['defaultContextWindow'])#默认上下文
        默认上限=取路径(回退,['maxTokens'])#默认上限
        密钥锁=自身.密钥态 is not None and 'writable' in 自身.密钥态 and 自身.密钥态['writable'] is False#不可写
        已配密钥=自身.密钥态 is not None and 'configured' in 自身.密钥态 and 自身.密钥态['configured'] is True#已存
        必填='credentialRequired' in 自身.属性 and 自身.属性['credentialRequired'] is True#必填
        if 密钥锁:#锁
            密钥占位=翻译('keyEnvLocked')#锁文案
        elif 已配密钥 and 必填 is not True:#已存
            密钥占位=翻译('keyStored')#已存
        elif 族=='pi-ai':#原生
            密钥占位=翻译('keyPlaceholderNative')#原生占位
        else:#DeepSeek
            密钥占位=翻译('keyPlaceholder')#普通占位
        def 改模型(下一):#目录变更
            """写入 models。"""
            自身.草稿=设路径(自身.草稿,['models'],下一)#设
        def 复位模型():#回继承
            """删 models 覆盖。"""
            自身.草稿=删路径(自身.草稿,['models'])#删
        目录属性={#目录共用
            'models':模型列表,'overridden':模型覆盖,'t':翻译,'disabled':禁用,
            'onChange':改模型,'onReset':复位模型,
        }#目录结束
        if 族=='deepseek':#DeepSeek 目录
            目录属性['defaultContextWindow']=默认上下文 if isinstance(默认上下文,(int,float)) else None#上下文
            目录属性['defaultMaxTokens']=默认上限 if isinstance(默认上限,(int,float)) else None#上限
            自身.目录编辑器=DeepSeek模型编辑器(目录属性)#内嵌
        else:#pi-ai 列表
            密钥值=自身.密钥草稿.strip()#密钥
            探测={#探测
                'settingsNs':命名空间['ns'] if 'ns' in 命名空间 else None,'provider':自身.属性['provider'],
            }#基础
            探测基址=自身.字符串于(自身.草稿,'baseURL') or 自身.字符串于(回退,'baseURL')#端点
            探测协议=自身.字符串于(自身.草稿,'api') or 自身.字符串于(回退,'api')#协议
            if 探测基址 is not None:#有端点
                探测['baseURL']=探测基址#带上
            if 探测协议 is not None:#有协议
                探测['api']=探测协议#带上
            if len(密钥值)>0:#有密钥
                探测['apiKey']=密钥值#带上
            目录属性['probe']=探测#探测
            目录属性['probeBlocked']=密钥失败(自身.密钥草稿)#阻塞
            目录属性['api']=自身.属性['api'] if 'api' in 自身.属性 else None#API
            自身.目录编辑器=模型列表编辑器(目录属性)#内嵌
        协议列表=协议选项(命名空间) if 族=='pi-ai' else []#协议选项
        基座占位=公开DeepSeek基址 if 族=='deepseek' else (自身.字符串于(回退,'baseURL') or 翻译('baseUrlDefault'))#基座占位
        自定义体=[]#自定义字段
        if 拥身份:#显示名
            基层=命名空间['base'] if 'base' in 命名空间 else None#基层
            基名=自身.字符串于(取路径(基层,路径),'displayName') or 自身.属性['provider']#占位
            自定义体.append({'field':'displayName','label':翻译('customDisplayName'),'value':自身.字符串于(自身.草稿,'displayName') or '','placeholder':基名})#名
        自定义体.append({'field':'baseURL','label':翻译('baseUrl'),'value':自身.字符串于(自身.草稿,'baseURL') or '','placeholder':基座占位})#基址
        if 拥身份:#协议
            自定义体.append({'field':'api','label':翻译('customApi'),'value':自身.字符串于(自身.草稿,'api') or 自身.字符串于(回退,'api') or '','choices':协议列表,'unsetLabel':翻译('customApiUnset')})#协议
        仅凭证='credentialOnly' in 自身.属性 and 自身.属性['credentialOnly'] is True#仅凭证
        自动聚焦='autoFocusCredential' in 自身.属性 and 自身.属性['autoFocusCredential'] is True#聚焦
        密钥失败键=自身.所示密钥失败()#门闩
        return {#策展视图
            'keyInput':{#密钥
                'label':翻译('keyInput'),'value':自身.密钥草稿,'placeholder':密钥占位,
                'invalid':密钥失败键 is not None,'required':必填,
                'autoFocus':自动聚焦,'disabled':禁用 or 密钥锁,
                'failure':翻译(密钥失败键) if 密钥失败键 is not None else None,
                'onChange':自身.改密钥草稿,
            },#密钥结束
            'credentialOnly':仅凭证,#仅凭证
            'customizedLabel':翻译('customized'),#折叠标题
            'customFields':自定义体 if 仅凭证 is not True else [],#自定义
            'catalog':自身.目录编辑器() if 仅凭证 is not True and 自身.目录编辑器 is not None else None,#目录
            'onSetField':自身.设字段,#写字段
        }#策展结束

    def 所示密钥失败(自身):#密钥门闩键
        """必填空白优先。"""
        密钥值=自身.密钥草稿.strip()#去空白
        必填='credentialRequired' in 自身.属性 and 自身.属性['credentialRequired'] is True#必填
        if 必填 and len(自身.密钥草稿)>0 and len(密钥值)==0:#必填空白
            return 'keyRequired'#必填
        return 密钥失败(自身.密钥草稿)#普通判定

    def 渲染(自身):#结构化视图
        """整卡投影。"""
        自身.拉密钥态()#首渲拉密钥提示
        翻译=自身.属性['t']#文案
        命名空间=自身.属性['namespace']#ns
        路径=list(自身.属性['settingsPath']) if 'settingsPath' in 自身.属性 and 自身.属性['settingsPath'] is not None else []#路径
        模式=命名空间['schema'] if 'schema' in 命名空间 else None#schema
        根=再水合模式(模式)#schema
        节点=取路径(根,路径)#节点
        if 节点 is None:#不可解析
            return {'type':'provider-editor','error':f"{自身.属性['provider']}: unresolvable settings path",'cssModule':'模型分区.module.css'}#错误卡
        布局=布局自(命名空间['ns'] if 'ns' in 命名空间 else None)#布局
        只读=bool(自身.属性['readOnly']) if 'readOnly' in 自身.属性 else False#只读
        禁用=只读 or 自身.忙#禁用
        模型失败=校验DeepSeek模型(取路径(自身.草稿,['models']))#模型门闩
        密钥值=自身.密钥草稿.strip()#密钥
        仅凭证='credentialOnly' in 自身.属性 and 自身.属性['credentialOnly'] is True#仅凭证
        必填='credentialRequired' in 自身.属性 and 自身.属性['credentialRequired'] is True#必填
        提交禁用=(禁用 or 布局=='unknown'
            or (仅凭证 is not True and 模型失败 is not None)
            or 自身.所示密钥失败() is not None
            or (必填 and len(密钥值)==0))#提交门闩
        提交闲=自身.属性['submitLabel'] if 'submitLabel' in 自身.属性 and 自身.属性['submitLabel'] else 'apply'#提交键
        提交忙=自身.属性['submitBusyLabel'] if 'submitBusyLabel' in 自身.属性 and 自身.属性['submitBusyLabel'] else 'applying'#忙键
        取消键=自身.属性['cancelLabel'] if 'cancelLabel' in 自身.属性 else None#取消键
        自身.页脚=编辑器页脚({#页脚
            't':翻译,'busy':自身.忙,'submitDisabled':提交禁用,
            'submitLabel':提交闲,
            'submitBusyLabel':提交忙,
            'cancelLabel':取消键,
            'onCancel':自身.点取消,
            'onSubmit':自身.应用,
        })#页脚结束
        藏标题='hideTitle' in 自身.属性 and 自身.属性['hideTitle'] is True#藏标题
        显示名=自身.属性['displayName'] if 'displayName' in 自身.属性 else None#显示名
        路由=自身.属性['provider'] if 'provider' in 自身.属性 else None#路由
        if 藏标题:#无标题
            标题=None#无
        else:#标题行
            标题={#标题行
                'displayName':显示名,
                'route':路由 if 路由!=显示名 else None,
            }#标题结束
        未知提示=f"{翻译('advancedHint')} ({命名空间['ns']})" if 布局=='unknown' else None#未知提示
        模型提示=None if 仅凭证 or 模型失败 is None else f"{翻译('model')} {模型失败['index']+1}: {翻译(模型失败['key'])}"#模型提示
        return {#视图
            'type':'provider-editor',#类型
            'credentialOnly':仅凭证,#仅凭证
            'header':标题,#标题
            'advancedHint':未知提示,#未知提示
            'body':None if 布局=='unknown' else 自身.渲染策展(布局),#策展
            'failure':自身.失败,#失败
            'modelHint':模型提示,#模型提示
            'footer':自身.页脚(),#页脚
            'cssModule':'模型分区.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
