import os,re#绝对路径与名模式
import yaml

__all__=['解析快照清单','写当前会话夹具']#仅中文公开名

合法配置档=frozenset(['headless','sdk','acp','web'])#合法 profile
合法录制=frozenset(['live','authored'])#合法录制
合法平台=frozenset(['posix','pwsh'])#合法平台
合法权限=frozenset(['read-only','workspace-write','danger-full-access'])#合法权限
合法会话格式覆盖=frozenset([#合法覆盖名
    'multi-hop','packed-row','retry-failure','shipped-profile','adjacent-migration','retired-tools',
])#覆盖结束
名称模式=re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*\Z',re.ASCII)#kebab-case 名
环境名模式=re.compile(r'^[A-Z][A-Z0-9_]*\Z',re.ASCII)#环境名

def 写当前会话夹具(清单,模式):#是否写当前世代
    """一次运行是否为本场景写入当前写入器的 Session fixture。"""
    return 模式!='replay' and 'session' not in 清单 and 'sessionFormat' not in 清单#非回放且自有且无钉住历史
def 要求映射(值,标签):#要求映射
    """值必须为映射。"""
    if not isinstance(值,dict):#非映射
        raise Exception(f'{标签} must be a mapping')#必须映射
    return 值#断言映射

def 精确键集(值,允许,标签):#精确键集
    """拒绝未知字段。"""
    未知=sorted(键 for 键 in 值 if 键 not in 允许)#未知键
    if 未知:#有未知
        raise Exception(f"{标签} has unknown field(s): {', '.join(未知)}")#未知字段

def 要求名(值,标签):#要求 kebab 名
    """要求 lower-kebab-case 名。"""
    if not isinstance(值,str) or not 名称模式.match(值):#名非法
        raise Exception(f'{标签} must be a lower-kebab-case name')#名非法
    return 值#返回名

def 要求场景源(值,标签):#要求场景源路径
    """要求 kebab 路径段。"""
    if not isinstance(值,str) or not all(名称模式.match(段) for 段 in 值.split('/')):#路径非法
        raise Exception(f'{标签} must be a lower-kebab-case name or corpus-relative path')#路径非法
    return 值#返回路径

def 要求正整数索引(值,标签):#要求正整数索引
    """要求唯一正整数数组。"""
    if not isinstance(值,list) or any(not isinstance(项,int) or isinstance(项,bool) or 项<1 for 项 in 值) or len(set(值))!=len(值):#非法
        raise Exception(f'{标签} must be an array of unique positive integers')#索引非法
    return list(值)#拷贝返回

def 解析快照清单(源,路径='snapshot.yml'):#解析清单
    """解析一份 snapshot.yml，不接纳未知字段。"""
    try:
        解析=yaml.safe_load(源)
    except yaml.YAMLError as 错误:
        raise Exception(f'session-snapshot: {os.path.basename(路径)}: YAML 非法: {错误}')
    try:#校验
        根=要求映射(解析,'manifest')#根映射
        精确键集(根,[#允许键
            'version','scenario','profile','composition','recording','header','replay',
            'platform','permission','environment','workspace','input','session','sessionFormat',
        ],'manifest')#精确键
        if 根.get('version')!=1:#版本
            raise Exception('manifest.version 必须等于 1')#版本
        场景=None if 'scenario' not in 根 else 要求名(根['scenario'],'manifest.scenario')#场景
        if not isinstance(根.get('profile'),str) or 根['profile'] not in 合法配置档:#profile
            raise Exception('manifest.profile 必须是 headless、sdk、acp 或 web')#profile
        组合=None if 'composition' not in 根 else 要求名(根['composition'],'manifest.composition')#组合
        录制=None#录制
        if 根.get('recording') is not None:#有录制
            if not isinstance(根['recording'],str) or 根['recording'] not in 合法录制:#非法
                raise Exception('manifest.recording 必须是 live 或 authored')#非法
            录制=根['recording']#写入
        头=None#头
        if 根.get('header') is not None:#有头
            值=要求映射(根['header'],'manifest.header')#头映射
            精确键集(值,['class','pin','systemPromptSource','toolSchemasSource','childSystemPrompts','childToolSchemas','changes','promptChanges'],'manifest.header')#键
            if 值.get('pin') is not None and 值['pin'] is not True:#pin
                raise Exception('manifest.header.pin 若出现必须等于 true')#pin
            for 字段 in ('changes','promptChanges'):#非负整数字段
                if 值.get(字段) is not None and (not isinstance(值[字段],int) or isinstance(值[字段],bool) or 值[字段]<0):#非法
                    raise Exception(f'manifest.header.{字段} must be a non-negative integer')#字段非法
            头={'class':要求名(值['class'],'manifest.header.class')}#头
            if 值.get('pin') is True:#钉住
                头['pin']=True#写入
            if 值.get('systemPromptSource') is not None:#系统提示词源
                头['systemPromptSource']=要求场景源(值['systemPromptSource'],'manifest.header.systemPromptSource')#写入
            if 值.get('toolSchemasSource') is not None:#工具 schema 源
                头['toolSchemasSource']=要求场景源(值['toolSchemasSource'],'manifest.header.toolSchemasSource')#写入
            if 值.get('childSystemPrompts') is not None:#子提示词
                头['childSystemPrompts']=要求正整数索引(值['childSystemPrompts'],'manifest.header.childSystemPrompts')#写入
            if 值.get('childToolSchemas') is not None:#子 schema
                头['childToolSchemas']=要求正整数索引(值['childToolSchemas'],'manifest.header.childToolSchemas')#写入
            if 值.get('changes') is not None:#变更
                头['changes']=int(值['changes'])#写入
            if 值.get('promptChanges') is not None:#提示词变更
                头['promptChanges']=int(值['promptChanges'])#写入
        回放=None#回放
        if 根.get('replay') is not None:#有回放
            值=要求映射(根['replay'],'manifest.replay')#回放映射
            精确键集(值,['override'],'manifest.replay')#键
            if 值.get('override') is not True:#override
                raise Exception('manifest.replay.override 必须等于 true')#override
            回放={'override':True}#写入
        平台=None#平台
        if 根.get('platform') is not None:#有平台
            if not isinstance(根['platform'],str) or 根['platform'] not in 合法平台:#非法
                raise Exception('manifest.platform 必须是 posix 或 pwsh')#非法
            平台=根['platform']#写入
        权限=None#权限
        if 根.get('permission') is not None:#有权限
            if not isinstance(根['permission'],str) or 根['permission'] not in 合法权限:#非法
                raise Exception('manifest.permission 必须是 read-only、workspace-write 或 danger-full-access')#非法
            权限=根['permission']#写入
        环境=None#环境
        if 根.get('environment') is not None:#有环境
            值=要求映射(根['environment'],'manifest.environment')#环境映射
            if any(not 环境名模式.match(键) or not isinstance(项,str) for 键,项 in 值.items()):#非法
                raise Exception('manifest.environment 必须把大写环境名映射到字符串')#非法
            环境=dict(值)#写入
        工作区=None#工作区
        if 根.get('workspace') is not None:#有工作区
            值=要求映射(根['workspace'],'manifest.workspace')#工作区映射
            精确键集(值,['setup','final','parent'],'manifest.workspace')#键
            if 值.get('final') is not None and 值['final'] is not True:#final
                raise Exception('manifest.workspace.final 若出现必须等于 true')#final
            if 值.get('parent') is not None and 值['parent']!='outside-temp':#parent
                raise Exception('manifest.workspace.parent 必须是 outside-temp')#parent
            工作区={}#组装
            if 值.get('setup') is not None:#setup
                工作区['setup']=要求名(值['setup'],'manifest.workspace.setup')#写入
            if 值.get('final') is True:#final
                工作区['final']=True#写入
            if 值.get('parent')=='outside-temp':#parent
                工作区['parent']='outside-temp'#写入
            if len(工作区)==0:#空
                raise Exception('manifest.workspace 不能为空')#空
        输入=None#输入
        if 根.get('input') is not None:#有输入
            值=要求映射(根['input'],'manifest.input')#输入映射
            精确键集(值,['task','attachments'],'manifest.input')#键
            if 值.get('task') is not None and (not isinstance(值['task'],str) or 值['task'].strip()==''):#task
                raise Exception('manifest.input.task 若出现必须是非空字符串')#task
            附件列表=None#附件
            if 值.get('attachments') is not None:#有附件
                if not isinstance(值['attachments'],list) or len(值['attachments'])==0:#非法
                    raise Exception('manifest.input.attachments 必须是非空数组')#非法
                附件列表=[]#列表
                for 索引,项 in enumerate(值['attachments']):#逐项
                    附件=要求映射(项,f'manifest.input.attachments[{索引}]')#映射
                    精确键集(附件,['id','mediaType','data'],f'manifest.input.attachments[{索引}]')#键
                    if not isinstance(附件.get('id'),str) or not 附件['id'].startswith('sha256:'):#id
                        raise Exception(f'manifest.input.attachments[{索引}].id must start with sha256:')#id
                    if not isinstance(附件.get('mediaType'),str) or '/' not in 附件['mediaType']:#mediaType
                        raise Exception(f'manifest.input.attachments[{索引}].mediaType must be a MIME type')#mediaType
                    if not isinstance(附件.get('data'),str) or 附件['data']=='':#data
                        raise Exception(f'manifest.input.attachments[{索引}].data must be non-empty base64')#data
                    附件列表.append({'id':附件['id'],'mediaType':附件['mediaType'],'data':附件['data']})#追加
                if len({项['id'] for 项 in 附件列表})!=len(附件列表):#重复
                    raise Exception('manifest.input.attachments 的 id 必须唯一')#重复
            if 'task' not in 值 and 附件列表 is None:#空输入
                raise Exception('manifest.input 必须声明 task 或 attachments')#空
            输入={}#组装
            if 值.get('task') is not None:#task
                输入['task']=值['task']#写入
            if 附件列表 is not None:#附件
                输入['attachments']=附件列表#写入
        会话=None#会话
        if 根.get('session') is not None:#有会话
            值=要求映射(根['session'],'manifest.session')#会话映射
            精确键集(值,['source'],'manifest.session')#键
            if not isinstance(值.get('source'),str) or 值['source'].strip()=='':#source
                raise Exception('manifest.session.source 必须是非空字符串')#source
            if os.path.isabs(值['source']) or '\\' in 值['source'] or '\0' in 值['source']:#相对 POSIX
                raise Exception('manifest.session.source 必须是相对 POSIX 路径')#相对
            会话={'source':值['source']}#写入
        会话格式=None#会话格式
        if 根.get('sessionFormat') is not None:#有会话格式
            值=要求映射(根['sessionFormat'],'manifest.sessionFormat')#格式映射
            精确键集(值,['version','coverage'],'manifest.sessionFormat')#键
            if not isinstance(值.get('version'),int) or isinstance(值['version'],bool) or 值['version']<0:#version
                raise Exception('manifest.sessionFormat.version 必须是非负安全整数')#version
            覆盖=值.get('coverage')#覆盖
            if (not isinstance(覆盖,list) or len(覆盖)==0
                or any(not isinstance(项,str) or 项 not in 合法会话格式覆盖 for 项 in 覆盖)
                or len(set(覆盖))!=len(覆盖)):#coverage 非法
                raise Exception(
                    'manifest.sessionFormat.coverage must be a non-empty array of unique supported coverage names',
                )#coverage
            if 会话 is not None:#借用方不可钉历史
                raise Exception('仅当场景拥有自己的 Session 夹具时才允许 manifest.sessionFormat')#冲突
            会话格式={'version':int(值['version']),'coverage':list(覆盖)}#组装
        结果={'version':1,'profile':根['profile']}#组装清单
        if 场景 is not None:#场景
            结果['scenario']=场景#写入
        if 组合 is not None:#组合
            结果['composition']=组合#写入
        if 录制 is not None:#录制
            结果['recording']=录制#写入
        if 头 is not None:#头
            结果['header']=头#写入
        if 回放 is not None:#回放
            结果['replay']=回放#写入
        if 平台 is not None:#平台
            结果['platform']=平台#写入
        if 权限 is not None:#权限
            结果['permission']=权限#写入
        if 环境 is not None:#环境
            结果['environment']=环境#写入
        if 工作区 is not None:#工作区
            结果['workspace']=工作区#写入
        if 输入 is not None:#输入
            结果['input']=输入#写入
        if 会话 is not None:#会话
            结果['session']=会话#写入
        if 会话格式 is not None:#会话格式
            结果['sessionFormat']=会话格式#写入
        return 结果
    except Exception as 错误:
        消息=错误.args[0] if 错误.args else str(错误)
        raise Exception(f'session-snapshot: {os.path.basename(路径)}: {消息}') from 错误
