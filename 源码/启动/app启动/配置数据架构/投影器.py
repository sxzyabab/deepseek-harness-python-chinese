"""投影原生 Config 输入约束，不执行其校验器或变换回调。"""
import json,math
from .原生 import 是否原生配置数据架构
from .匹配模式 import 创建模式检查

__all__=['装载器表达式数据架构','创建配置投影器']

装载器表达式数据架构={
    'type':'object','properties':{'__jsExpr':{'type':'string'}},'required':['__jsExpr'],
    'description':'Inert representation of a YAML !!js scalar from the Cordis entry-list parser. Its result is evaluated and validated only at runtime. Extra marker-object fields are ignored by interpolation.',
}

继承名=tuple(object.__dict__.keys())

def json值(值,空化未定义=False):
    """复制 JSON 兼容注解，不把非 JSON 默认值悄悄转换。"""
    def 访问(项,活动):
        """拒绝环与非 JSON。"""
        if 空化未定义 and 项 is None and 项 is not False:
            pass
        if 空化未定义 and 项 is None:
            return
        if 项 is None or isinstance(项,(str,bool)):
            return
        if isinstance(项,(int,float)) and not isinstance(项,bool) and math.isfinite(项):
            return
        if not isinstance(项,(dict,list)):
            raise Exception('schema annotation is not JSON-compatible')
        身份=id(项)
        if 身份 in 活动:
            raise Exception('schema annotation contains a cycle')
        活动.add(身份)
        if isinstance(项,dict):
            for 子 in 项.values():
                访问(子,活动)
        else:
            for 子 in 项:
                访问(子,活动)
        活动.remove(身份)
    访问(值,set())
    文本=json.dumps(值,ensure_ascii=False,allow_nan=False,default=_json默认)
    return json.loads(文本)

def _json默认(项):
    """禁止非 JSON。"""
    raise Exception('schema annotation contains a non-JSON object')

def 常量(值,对象比较):
    """原生常量相等把省略与空成员同等对待。"""
    if isinstance(值,list):
        结果={'type':'array','minItems':len(值),'maxItems':len(值),'items':False}
        if len(值)>0:
            结果['prefixItems']=[常量(项,对象比较) for 项 in 值]
        return 结果
    if 值 is not None and isinstance(值,dict):
        对象比较()
        属性={键:常量(子,对象比较) for 键,子 in 值.items()}
        必需=[键 for 键 in 属性 if 键 not in 继承名 and 值.get(键) is not None]
        模式='|'.join(re_escape(键) for 键 in 继承名)
        结果={
            'type':'object','properties':属性,'additionalProperties':{'type':'null'},
            'patternProperties':{'^(?:'+模式+')$':{}},
        }
        if len(必需)>0:
            结果['required']=必需
        return 结果
    return {'const':值}

def re_escape(文本):
    """正则转义。"""
    import re
    return re.escape(文本)

def 可空(核心,接受):
    """加减 null 接受。"""
    if isinstance(核心,bool):
        if 接受:
            return 核心 or {'type':'null'}
        return 核心 and {'not':{'type':'null'}}
    类型=核心.get('type')
    类型列=[类型] if isinstance(类型,str) else 类型
    if 类型列 is None:
        return {'anyOf':[核心,{'type':'null'}]} if 接受 else dict(核心,not={'type':'null'})
    if 接受:
        合并=[]
        for 项 in 类型列+['null']:
            if 项 not in 合并:
                合并.append(项)
        类型列=合并
    else:
        类型列=[项 for 项 in 类型列 if 项!='null']
    if len(类型列)==0:
        return False
    拷贝=dict(核心)
    拷贝['type']=类型列[0] if len(类型列)==1 else 类型列
    return 拷贝

def 表达式化(模式,值位置=True,启用=True):
    """只在配置值位置加表达式备选。"""
    结果=dict(模式)
    if 模式.get('properties') is not None:
        结果['properties']={键:表达式化(子,True,启用) for 键,子 in 模式['properties'].items()}
    for 键 in ('items','additionalProperties'):
        if 键 in 模式:
            结果[键]=False if 模式[键] is False else 表达式化(模式[键],True,启用)
    if 模式.get('propertyNames') is not None:
        结果['propertyNames']=表达式化(模式['propertyNames'],False,False)
    if 模式.get('prefixItems') is not None:
        结果['prefixItems']=[表达式化(子,True,启用) for 子 in 模式['prefixItems']]
    if 模式.get('anyOf') is not None:
        结果['anyOf']=[表达式化(子,False,启用) for 子 in 模式['anyOf']]
    if 'not' in 模式:
        结果['not']=表达式化(模式['not'],False,False)
    if not 值位置 or not 启用:
        return 结果
    注解={}
    for 键 in ('title','description','default','$comment','x-cordis'):
        if 键 in 结果:
            注解[键]=结果[键]
            del 结果[键]
    return dict(注解,anyOf=[结果,{'$ref':'#/$defs/loaderExpression'}])

def 校验易变放置(节点,路径,阻塞=False,已见=None):
    """不求值、不调用未解析惰性构建器。"""
    if 已见 is None:
        已见={}
    身份=id(节点)
    状态=已见.get(身份)
    if 状态 is None:
        状态=set()
        已见[身份]=状态
    if 阻塞 in 状态:
        return
    状态.add(阻塞)
    元=节点.meta if hasattr(节点,'meta') else 节点.get('meta') or {}
    if 元.get('volatile') and 阻塞:
        raise Exception(路径+': volatile fields require a fixed object path without an enclosing volatile field')
    嵌套=阻塞 or bool(元.get('volatile'))
    字典=节点.dict if hasattr(节点,'dict') else 节点.get('dict')
    if 字典:
        for 键,子 in 字典.items():
            校验易变放置(子,路径+'/'+键,嵌套,已见)
    键模式=节点.sKey if hasattr(节点,'sKey') else 节点.get('sKey')
    if 键模式 is not None:
        校验易变放置(键模式,路径+'/keys',True,已见)
    内部=节点.inner if hasattr(节点,'inner') else 节点.get('inner')
    类型=节点.type if hasattr(节点,'type') else 节点.get('type')
    if 内部 is not None and (类型!='lazy' or 是否原生配置数据架构(内部)):
        校验易变放置(内部,路径+'/inner',True,已见)
    列表=节点.list if hasattr(节点,'list') else 节点.get('list')
    if 列表:
        for 下标,子 in enumerate(列表):
            校验易变放置(子,路径+'/'+str(下标),True,已见)

def 取(节点,名,缺省=None):
    """对象或 dict 取值。"""
    if isinstance(节点,dict):
        return 节点.get(名,缺省)
    return getattr(节点,名,缺省)

def 浅校验(模式,值):
    """对生成模式做默认值字面校验。"""
    if 模式 is True:
        return True
    if 模式 is False:
        return False
    if not isinstance(模式,dict):
        return True
    if 'const' in 模式:
        return 值==模式['const']
    if 'anyOf' in 模式:
        return any(浅校验(分支,值) for 分支 in 模式['anyOf'])
    if 'not' in 模式 and 浅校验(模式['not'],值):
        return False
    类型=模式.get('type')
    类型列=[类型] if isinstance(类型,str) else (类型 or [])
    if len(类型列)>0:
        命中=False
        if 'null' in 类型列 and 值 is None:
            命中=True
        if 'boolean' in 类型列 and isinstance(值,bool):
            命中=True
        if 'string' in 类型列 and isinstance(值,str):
            命中=True
        if 'number' in 类型列 and isinstance(值,(int,float)) and not isinstance(值,bool):
            命中=True
        if 'integer' in 类型列 and isinstance(值,int) and not isinstance(值,bool):
            命中=True
        if 'array' in 类型列 and isinstance(值,list):
            命中=True
        if 'object' in 类型列 and isinstance(值,dict):
            命中=True
        if not 命中:
            return False
    if isinstance(值,str):
        if 'minLength' in 模式 and len(值)<模式['minLength']:
            return False
        if 'maxLength' in 模式 and len(值)>模式['maxLength']:
            return False
    if isinstance(值,(int,float)) and not isinstance(值,bool):
        if 'minimum' in 模式 and 值<模式['minimum']:
            return False
        if 'maximum' in 模式 and 值>模式['maximum']:
            return False
        if 'multipleOf' in 模式 and 模式['multipleOf']!=0 and (值%模式['multipleOf'])!=0:
            return False
    if isinstance(值,list):
        if 'minItems' in 模式 and len(值)<模式['minItems']:
            return False
        if 'maxItems' in 模式 and len(值)>模式['maxItems']:
            return False
        项=模式.get('items')
        if 项 is False and len(值)>len(模式.get('prefixItems') or []):
            return False
        if isinstance(项,dict) or 项 is True:
            for 子 in 值:
                if not 浅校验(项,子):
                    return False
        前=模式.get('prefixItems') or []
        for 下标,子模式 in enumerate(前):
            if 下标>=len(值):
                break
            if not 浅校验(子模式,值[下标]):
                return False
    if isinstance(值,dict):
        必需=模式.get('required') or []
        for 键 in 必需:
            if 键 not in 值:
                return False
        属性=模式.get('properties') or {}
        for 键,子 in 值.items():
            if 键 in 属性:
                if not 浅校验(属性[键],子):
                    return False
            else:
                额外=模式.get('additionalProperties')
                if 额外 is False:
                    return False
                if isinstance(额外,dict) or 额外 is True:
                    if not 浅校验(额外,子):
                        return False
    return True

def 创建配置投影器():
    """返回把一份受信任原生 Config 图投影进外围文档定义的函数。"""
    可移植模式=创建模式检查()
    构建结果={}
    def 投影(根,前缀):
        """投影一棵图。"""
        校验易变放置(根,'config')
        完成={}
        严格节点={}
        活动=set()
        递归名={}
        定义={}
        限制=[]
        元效果=[]
        def 记限制(路径,消息):
            """记下限制文案。"""
            文本=路径+': '+消息
            限制.append(文本)
            return 文本
        def 访问(节点,路径,严格=False):
            """访问一个原生节点。"""
            键=id(节点)
            if 严格:
                if 键 not in 严格节点:
                    严格节点[键]=节点
                键=('s',id(严格节点[键]))
            else:
                键=('n',id(节点))
            if 键 in 完成:
                return 完成[键]
            if 键 in 活动:
                名=递归名.get(键)
                if 名 is None:
                    名=前缀+'Recursive'+str(len(递归名))
                    递归名[键]=名
                元=取(节点,'meta') or {}
                类型=取(节点,'type')
                return {
                    'schema':{'$ref':'#/$defs/'+名},
                    'acceptsMissing':False if 类型!='lazy' and 元.get('required') else 'unknown',
                    'exact':True,'recursive':True,'effectful':True,'mutating':True,
                }
            活动.add(键)
            类型=取(节点,'type')
            元=dict(取(节点,'meta') or {})
            if 类型=='lazy':
                内部=节点
                元值=dict(取(节点,'meta') or {})
                if 元值.get('volatile'):
                    元值=dict(元值)
                    元值['volatile']=False
                链=set()
                松投影=None
                while 取(内部,'type')=='lazy':
                    缓存内部=是否原生配置数据架构(取(内部,'inner'))
                    if 元值.get('loose'):
                        消息=记限制(路径,'lazy loose fallback can accept inputs rejected by its inner schema')
                        if not 缓存内部:
                            元效果.append(记限制(路径,'unresolved loose lazy metadata propagation may affect shared schemas'))
                        松投影={
                            'schema':{'x-cordis':{'loose':True,'limitations':[消息]}},
                            'acceptsMissing':True,'exact':False,'recursive':False,'effectful':True,'mutating':False,
                        }
                        break
                    身份=id(内部)
                    if 身份 in 链:
                        raise Exception(路径+': lazy cycle has no concrete schema')
                    链.add(身份)
                    下一=取(内部,'inner') if 缓存内部 else 构建结果.get(id(内部))
                    构建器=取(内部,'builder')
                    if 下一 is None and callable(构建器):
                        下一=构建器()
                        构建结果[id(内部)]=下一
                    if not 是否原生配置数据架构(下一):
                        raise Exception(路径+': lazy schema has no native builder result or resolved inner schema')
                    下一元=取(下一,'meta') or {}
                    if not 缓存内部:
                        for 字段 in ('required','default','min','max','step','pattern','loose','volatile'):
                            if 字段 in 元值 and 字段 not in 下一元:
                                真值=bool(元值.get(字段)) if 字段 in ('required','loose','volatile') else 元值.get(字段) is not None
                                if 真值:
                                    元效果.append(记限制(路径,'lazy metadata propagation may affect shared schemas; validation requires native execution'))
                                    break
                    元值=下一元 if 缓存内部 else dict(元值,**下一元)
                    合并=dict(下一.__dict__) if hasattr(下一,'__dict__') else dict(下一)
                    合并['meta']=元值
                    校验易变放置(合并,路径+'/lazy',True)
                    内部=下一
                投影结果=松投影 if 松投影 is not None else 访问(内部 if 取(内部,'meta')==元值 else _带元(内部,元值),路径+'/lazy',严格)
                if (取(节点,'meta') or {}).get('volatile'):
                    模式=dict(投影结果['schema'])
                    扩展=dict(模式.get('x-cordis') or {})
                    扩展['volatile']=True
                    模式['x-cordis']=扩展
                    投影结果=dict(投影结果,schema=模式)
            else:
                自有限制=[]
                输入限制=[]
                不支持=False
                def 输入限制消息(消息):
                    """记下输入限制。"""
                    输入限制.append(消息)
                    自有限制.append(记限制(路径,消息))
                def 注解(值,名):
                    """JSON 兼容注解。"""
                    try:
                        return {'ok':True,'value':json值(值)}
                    except Exception as 错误:
                        自有限制.append(记限制(路径+'/'+名,'annotation omitted: '+str(错误)))
                        return {'ok':False}
                子结果=[]
                def 子(值,后缀,子严格=False):
                    """访问子节点。"""
                    if 值 is None:
                        raise Exception(路径+': '+str(类型)+' schema is missing '+后缀)
                    结果=访问(值,路径+'/'+后缀,子严格)
                    子结果.append(结果)
                    return 结果
                for 字段 in ('min','max','step'):
                    if 元.get(字段) is None or math.isfinite(元[字段]):
                        continue
                    惰性=元[字段]==float('inf') if 字段=='max' else (字段=='min' and 元['min']==float('-inf') and not 元.get('step'))
                    if not 惰性:
                        输入限制消息('non-finite '+字段+' constraint is omitted; native validation is required')
                    元.pop(字段,None)
                核心=True
                字典校验=None
                if 类型=='any':
                    核心=True
                elif 类型=='never':
                    核心=False
                elif 类型=='const':
                    try:
                        def 对象比较():
                            """对象常量比较限制。"""
                            输入限制消息('object constant inherited-member comparison requires native validation')
                        核心=False if 取(节点,'value') is None else 常量(json值(取(节点,'value'),True),对象比较)
                    except Exception as 错误:
                        核心=True
                        输入限制消息('constant constraint requires native validation: '+str(错误))
                elif 类型=='boolean':
                    核心={'type':'boolean'}
                elif 类型=='string':
                    核心={'type':'string'}
                    if 元.get('min') is not None:
                        if 元['min']<=1:
                            核心['minLength']=max(0,int(math.ceil(元['min'])))
                        else:
                            输入限制消息('UTF-16 minimum length requires native validation')
                    if 元.get('max') is not None:
                        if 元['max']<0:
                            核心=False
                        else:
                            上限=int(math.floor(元['max']))
                            核心['maxLength']=上限
                            if 上限>0:
                                输入限制消息('UTF-16 maximum length requires native validation')
                    模式元=元.get('pattern')
                    if 模式元 and 核心 is not False:
                        源=模式元['source'] if isinstance(模式元,dict) else getattr(模式元,'source',None)
                        标志=模式元.get('flags') if isinstance(模式元,dict) else getattr(模式元,'flags',None)
                        if 可移植模式(源 or '',标志 or ''):
                            核心['pattern']=源
                        else:
                            输入限制消息('regular-expression syntax or Unicode semantics require native validation')
                elif 类型=='number':
                    核心={'type':'number'}
                    if 元.get('min') is not None:
                        核心['minimum']=元['min']
                    if 元.get('max') is not None:
                        核心['maximum']=元['max']
                    if 元.get('step'):
                        步=abs(元['step'])
                        原点=元['min'] if 元.get('min') is not None else 0
                        if 步!=int(步) or (原点%步)!=0:
                            输入限制消息('fractional or offset numeric step requires native validation')
                        elif 步==1:
                            核心['type']='integer'
                        else:
                            核心['multipleOf']=步
                elif 类型=='object':
                    字典=取(节点,'dict') or {}
                    必需=[]
                    属性={}
                    for 键,字段值 in 字典.items():
                        值=子(字段值,键)
                        if 值['acceptsMissing'] is False:
                            必需.append(键)
                        属性[键]=值['schema']
                    核心={'type':'object','properties':属性}
                    if len(必需)>0:
                        核心['required']=必需
                elif 类型=='array':
                    项=子(取(节点,'inner'),'items')
                    核心={'type':'array','items':项['schema']}
                    内部=取(节点,'inner')
                    内部元=取(内部,'meta') or {} if 内部 is not None else {}
                    if 元.get('min') is not None and 内部元.get('default') is None:
                        核心['minItems']=max(0,int(math.ceil(元['min'])))
                    if 元.get('max') is not None:
                        if 元['max']<0:
                            核心=False
                        else:
                            核心['maxItems']=int(math.floor(元['max']))
                elif 类型=='dict':
                    值模式=子(取(节点,'inner'),'values')['schema']
                    核心={'type':'object','additionalProperties':值模式}
                    键节点=取(节点,'sKey')
                    if 键节点 is not None:
                        键=子(键节点,'keys')
                        键元=取(键节点,'meta') or {}
                        全串=取(键节点,'type')=='string' and 键元.get('min') is None and 键元.get('max') is None and 键元.get('pattern') is None
                        if not 全串 and (严格 or 键['effectful']):
                            字典校验={'keySchema':键['schema'],'valueSchema':值模式}
                            核心={'type':'object'}
                            输入限制消息('dictionary key normalization can overwrite unvalidated values; native validation is required' if 键['effectful'] else 'strict dictionary filtering and value validation require native validation')
                        else:
                            核心['propertyNames']=键['schema']
                elif 类型=='tuple':
                    列表=取(节点,'list')
                    if 列表 is None:
                        raise Exception(路径+': tuple schema is missing its list')
                    值表=[子(项,str(下标)) for 下标,项 in enumerate(列表)]
                    核心={'type':'array'}
                    if len(值表)>0:
                        核心['prefixItems']=[项['schema'] for 项 in 值表]
                    最小=0
                    for 下标,值 in enumerate(值表):
                        if 值['acceptsMissing'] is False:
                            最小=下标+1
                    if 最小:
                        核心['minItems']=最小
                elif 类型=='union':
                    列表=取(节点,'list')
                    if 列表 is None:
                        raise Exception(路径+': union schema is missing its list')
                    变体=[子(项,str(下标),严格) for 下标,项 in enumerate(列表)]
                    if any(项['mutating'] for 项 in 变体[:-1]):
                        核心=True
                        输入限制消息('earlier union branches may alter later validation inputs; native validation is required')
                    else:
                        核心={'anyOf':[项['schema'] for 项 in 变体]} if len(变体)>0 else False
                elif 类型=='transform':
                    核心=子(取(节点,'inner'),'input',True)['schema']
                    输入限制消息('transform callback validation and normalization are not executed or projected')
                else:
                    核心=True
                    不支持=True
                    输入限制消息('native schema type '+str(类型)+' is not statically projected')
                if 元.get('loose'):
                    核心=True
                    输入限制消息('loose validation can replace invalid values with defaults')
                递归=any(值['recursive'] for 值 in 子结果)
                容器=类型 in ('object','array','dict','tuple')
                变异=不支持 or any(值['mutating'] or (容器 and 值['effectful']) for 值 in 子结果)
                精确=len(输入限制)==0 and all(值['exact'] for 值 in 子结果)
                回退=None if 元.get('default') is None and 'default' not in 元 else 注解(元.get('default'),'default')
                if 元.get('required'):
                    接受缺席=False
                elif 不支持:
                    接受缺席='unknown'
                elif 元.get('default') is None:
                    接受缺席=True
                elif not (回退 and 回退.get('ok')):
                    接受缺席='unknown'
                elif 递归:
                    接受缺席='unknown'
                    输入限制消息('recursive default validation cannot be decided statically')
                elif not 精确:
                    接受缺席='unknown'
                else:
                    接受缺席=浅校验(核心,回退['value'])
                注解表={}
                if 回退 and 回退.get('ok'):
                    注解表['default']=回退['value']
                原生={}
                描述=元.get('description')
                if isinstance(描述,str):
                    注解表['description']=描述
                elif 描述:
                    描述注=注解(描述,'description')
                    if 描述注.get('ok'):
                        原生['descriptions']=描述注['value']
                        英文=描述.get('en') if isinstance(描述,dict) else None
                        if 英文 is None and isinstance(描述,dict):
                            英文=描述.get('') or (next(iter(描述.values())) if len(描述)>0 else None)
                        if isinstance(英文,str):
                            注解表['description']=英文
                if 字典校验 is not None:
                    原生['dictionaryValidation']=字典校验
                def 拷贝(名,值):
                    """拷贝注解。"""
                    if 值 is None:
                        return
                    结果=注解(值,名)
                    if 结果.get('ok'):
                        原生[名]=结果['value']
                for 字段 in ('role','extra','hidden','disabled','collapse','link','comment','badges','loose','volatile'):
                    拷贝(字段,元.get(字段))
                模式元=元.get('pattern')
                if 模式元:
                    标志=模式元.get('flags') if isinstance(模式元,dict) else getattr(模式元,'flags',None)
                    if 标志:
                        拷贝('patternFlags',标志)
                if 类型=='union':
                    原生['branchSelection']='first-success'
                if 接受缺席=='unknown':
                    原生['omissionValidation']='runtime'
                if len(自有限制)>0:
                    原生['type']=类型
                    for 字段 in ('min','max','step','pattern'):
                        拷贝(字段,元.get(字段))
                    原生['limitations']=自有限制
                if len(原生)>0:
                    注解表['x-cordis']=原生
                输入=可空(核心,接受缺席 is not False)
                if isinstance(输入,bool):
                    输入模式={} if 输入 else {'not':{}}
                else:
                    输入模式=输入
                投影结果={
                    'schema':dict(输入模式,**注解表),
                    'acceptsMissing':接受缺席,
                    'exact':精确 and 接受缺席!='unknown',
                    'recursive':递归,
                    'effectful':不支持 or 类型=='transform' or bool(元.get('loose')) or any(子项['effectful'] for 子项 in 子结果),
                    'mutating':变异,
                }
            活动.discard(键)
            名=递归名.get(键)
            if 名 is not None:
                定义[名]=投影结果['schema']
                投影结果=dict(投影结果,schema={'$ref':'#/$defs/'+名})
            完成[键]=投影结果
            return 投影结果
        结果=访问(根,'config')
        模式=表达式化(结果['schema'])
        return {
            'schema':{'anyOf':[模式,{}]} if len(元效果)>0 else 模式,
            'definitions':{键:表达式化(值,False) for 键,值 in 定义.items()},
            'acceptsMissing':'unknown' if len(元效果)>0 else 结果['acceptsMissing'],
            'limitations':list(dict.fromkeys(限制)),
        }
    return 投影

def _带元(节点,元):
    """浅拷贝并换元。"""
    if isinstance(节点,dict):
        拷贝=dict(节点)
        拷贝['meta']=元
        return 拷贝
    class 包装:
        """带替换元的包装。"""
    包装=包装()
    包装.__dict__.update(getattr(节点,'__dict__',{}))
    for 名 in ('type','meta','dict','inner','sKey','list','value','builder'):
        if hasattr(节点,名):
            setattr(包装,名,getattr(节点,名))
    包装.meta=元
    return 包装
