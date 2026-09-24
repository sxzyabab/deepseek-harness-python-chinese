"""把 Loader 条目/补丁结构与发现的插件输入模式合成一份 JSON Schema 文档。"""
from .投影器 import 创建配置投影器,装载器表达式数据架构
from .类型 import 配置json数据架构网址,配置数据架构补丁引用

__all__=['构建配置数据架构文档']

def 引用(名):
    """$defs 引用。"""
    return {'$ref':'#/$defs/'+名}

def 元数据():
    """条目元字段模式。"""
    return {
        'id':{'type':'string','description':'Entry id. Loader generates an id when an entry omits it; patches use the configured id.'},
        'name':{'type':'string','description':'Plugin module specifier. Inserted relative plugin paths are anchored beside their patch file.'},
        'config':{},
        'group':{'type':['boolean','null'],'description':'Allows patch indexing and insertion into an entry-list config; does not select the plugin implementation.'},
        'disabled':{'anyOf':[{'type':['boolean','null']},引用('loaderExpression')],'description':'Boolean or !!js expression. The Loader coerces other truthy values as disabled; this schema rejects them.'},
        'inject':{'anyOf':[{'type':'array','items':{'type':'string'}},{'type':'object'},{'type':'null'}]},
        'intercept':{'type':['object','null']},
        'isolate':{'type':['object','null'],'additionalProperties':{'anyOf':[{'const':True},{'type':'string'}]}},
    }

def 补丁结构():
    """根树补丁对象。"""
    return {
        'type':'object',
        'allOf':[引用('entryMetadata')],
        'properties':{'insert':引用('entryList')},
        'description':'An insert appends entries, optionally inside the group identified by id. Other patches replace supplied fields; config is replaced wholesale, not deep-merged. A truthy name asserts the existing plugin name rather than renaming it. Unknown targets and non-insert patches without a nonempty id are warned and skipped.',
    }

def 构建配置数据架构文档(配置档,已收集,目标表,初始诊断):
    """为组合条目列表与可单独寻址的根树补丁列表建模式。"""
    投影=创建配置投影器()
    诊断=list(初始诊断)
    定义={
        'loaderExpression':装载器表达式数据架构,
        'entryMetadata':{'type':'object','properties':元数据()},
        'entryList':{'type':'array','items':引用('entry')},
        'patchList':{'type':'array','items':引用('patch')},
        'unknownConfig':{'$comment':'No projected Config schema is available; this is unknown configuration, not a prohibition on fields.'},
        'includeConfig':{
            'type':'object','required':['path'],
            'properties':{
                'path':{'type':'string','description':'YAML/JSON filename resolved relative to the owning Loader tree. This field is literal, not a !!js expression.'},
                'initial':引用('entryList'),
                'patches':{'type':'array','items':引用('includePatch')},
                'enableLogs':{'type':'boolean'},
            },
            'description':'Native Include configuration stays literal. initial is used only when the file is absent. Included files have their own module-resolution base and patch target index.',
        },
        'includePatch':补丁结构(),
    }
    条目=[]
    按条目输出={}
    投影表={}
    树=set(['#/$defs/entryList','#/$defs/includeConfig'])
    必需配置=set(树)
    名表={
        'cordis:group':set(['#/$defs/entryList']),
        'cordis:include':set(['#/$defs/includeConfig']),
    }
    for 项 in 已收集:
        输出={键:项[键] for 键 in 项 if 键!='native'}
        if 项.get('tree'):
            输出['configRef']='#/$defs/entryList' if 项['tree']=='group' else '#/$defs/includeConfig'
        elif 项.get('native') is not None:
            原生=项['native']
            投影结果=投影表.get(id(原生))
            if 投影结果 is None:
                名='config'+str(len(投影表))
                try:
                    结果=投影(原生,名)
                    定义[名]=结果['schema']
                    定义.update(结果['definitions'])
                    投影结果={'reference':'#/$defs/'+名,'required':结果['acceptsMissing'] is False,'limitations':结果['limitations']}
                    投影表[id(原生)]=投影结果
                except Exception as 错误:
                    输出['status']='error'
                    诊断.append({'level':'error','path':项['path'],'message':str(错误)})
            if 投影结果 is not None:
                输出['configRef']=投影结果['reference']
                输出['status']='partial' if len(投影结果['limitations'])>0 else 'schema'
                if 投影结果['required']:
                    必需配置.add(投影结果['reference'])
                for 消息 in 投影结果['limitations']:
                    诊断.append({'level':'warning','path':项['path'],'message':消息})
        if 'configRef' not in 输出:
            输出['configRef']='#/$defs/unknownConfig'
        条目.append(输出)
        按条目输出[id(项)]=输出
        if 项.get('name') is not None:
            选择=名表.get(项['name'])
            if 选择 is None:
                选择=set()
                名表[项['name']]=选择
            选择.add(输出['configRef'])
    休眠={'properties':{'disabled':{'anyOf':[{'const':True},引用('loaderExpression')]},'group':{'not':{'const':True}}},'required':['disabled']}
    条目规则=[]
    for 名,选择 in 名表.items():
        校验={'properties':{'config':{'anyOf':[{'$ref':引用值} for 引用值 in 选择]}}}
        则=校验
        if all(引用值 in 必需配置 for 引用值 in 选择):
            则={'if':休眠,'else':dict(校验,required=['config'])}
            if not all(引用值 in 树 for 引用值 in 选择):
                则['then']=校验
        条目规则.append({'if':{'properties':{'name':{'const':名}},'required':['name']},'then':则})
        if len(选择)>1:
            诊断.append({'level':'warning','message':'Plugin '+json_dumps(名)+' has multiple collected schemas; entry validation accepts their union because module resolution depends on the owning tree.'})
    定义['entry']={
        'type':'object','required':['name'],'allOf':[引用('entryMetadata')]+条目规则,
        'description':'Loader entry. Unknown metadata and plugin names are accepted; plugin-specific validation is available only for the names collected in this profile. Distinct resolutions of one name use a union of their schemas.',
    }
    补丁规则=[]
    for 标识,目标 in 目标表.items():
        if 目标.get('name') is None:
            continue
        配置引用=(按条目输出.get(id(目标)) or {}).get('configRef') or '#/$defs/unknownConfig'
        补丁规则.append({
            'if':{
                'required':['id'],'properties':{'id':{'const':标识}},
                'allOf':[
                    {'not':{'required':['insert']}},
                    {'anyOf':[{'not':{'required':['name']}},{'properties':{'name':{'enum':['',目标['name']]}}}]},
                ],
            },
            'then':{'properties':{'config':{'$ref':配置引用}}},
        })
    定义['patch']=dict(补丁结构(),allOf=[引用('entryMetadata')]+补丁规则)
    位置={条目项['path']:下标 for 下标,条目项 in enumerate(条目)}
    诊断.sort(key=lambda 项:位置.get(项.get('path') or '',-1))
    完整=not any(项['level']=='error' for 项 in 诊断) and not any(项['status'] in ('partial','unsupported','error') for 项 in 条目) and not any(len(选择)>1 for 选择 in 名表.values())
    return {
        '$schema':配置json数据架构网址,
        'title':'Cordis configuration for profile '+str(配置档),
        'description':'Describes the parsed entry-list YAML printed by --dump-config. Use $defs.patchList for a profile/home/CLI overlay. Parse !!js with the Cordis entry-list YAML dialect. Expression results, service dependencies, plugin startup checks, and sequence-dependent patch targets still require runtime validation.',
        '$comment':'Bundle, profile, home, and CLI layers apply in that order. A patch config replaces the whole config. JSON Schema defaults are annotations; Schemastery validates a fallback on null/omission unless required rejects it first. Schemastery unions select the first successful branch. Root patch id constraints describe the current index, not ids introduced or changed by earlier patches. Include-local patches have a separate index. Relative plugin insertions require their source patch directory; this document does not infer future overlay locations.',
        'type':'array','items':引用('entry'),'$defs':定义,
        'x-cordis':{
            'profile':配置档,
            'complete':完整,
            'entries':条目,
            'diagnostics':诊断,
            'patchSchema':配置数据架构补丁引用,
        },
    }

def json_dumps(值):
    """诊断用 JSON。"""
    import json
    return json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)
