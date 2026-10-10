'从公开窄入口组装的 pi-ai 模型辅助'
import pi_ai#外部依赖胶水（pi-ai SDK）
from .目录 import 思考档位列表#思考档升级序

__all__=('创建模型集','创建提供方','取受支持思考档','对话更新',)#仅中文公开名

def 创建模型集(选项=None):
    '创建空的 pi-ai 集合，不导入其聚合入口'
    if 选项 is None:#无选项
        模型集=pi_ai.builtinModels()#内建集合
    else:#有选项
        模型集=pi_ai.builtinModels(选项)#带认证集成
    模型集.clearProviders()#清空提供方
    return 模型集#可变集合

def 创建提供方(输入):
    '创建配置自定义路由所用的静态、单协议提供方'
    def 取模型():
        '本路由模型表'
        return 输入['models']#模型表
    def 流(模型,上下文,选项):
        '委托协议流'
        return 输入['api'].stream(模型,上下文,选项)#流
    def 简化流(模型,上下文,选项):
        '委托协议简化流'
        return 输入['api'].stream_simple(模型,上下文,选项)#简化流
    结果={'id':输入['id'],'name':输入['name'],'auth':输入['auth'],#身份与认证
          'getModels':取模型,'stream':流,'streamSimple':简化流}#委托面
    if 'baseUrl' in 输入:#有基址
        结果['baseUrl']=输入['baseUrl']#带上
    return 结果#提供方

def 取受支持思考档(模型):
    '从 pi-ai 公开模型元数据解析可选推理档'
    if not getattr(模型,'reasoning',False):#不支持推理
        return ['off']#仅 off
    结果=[]#受支持档
    映射=getattr(模型,'thinkingLevelMap',None) or {}#线路映射
    for 档 in 思考档位列表:#按升级序
        if 档 in 映射 and 映射[档] is None:#显式禁用
            continue#跳过
        if 档=='xhigh' or 档=='max':#高档
            if 档 not in 映射:#无显式映射
                continue#跳过
        结果.append(档)#记下
    return 结果#受支持档

def _兼容值(兼容,名):
    '从 dict 或对象上取一条 compat 开关'
    if isinstance(兼容,dict):#配置合并后的 dict
        return 兼容.get(名)#缺席为 None
    return getattr(兼容,名,None)#SDK 对象

def 对话更新(模型):
    '按模型协议能力给出系统提示与工具历史的更新方式'
    兼容=getattr(模型,'compat',None)#协议兼容
    if 兼容 is None or not _兼容值(兼容,'supportsMidConvoSystemMessages'):#不能中途改系统提示
        return {}#不声明更新方式
    更新={'systemPromptUpdate':'in-history'}#系统提示进历史
    协议=getattr(模型,'api',None)#线路
    if 协议=='anthropic-messages' and _兼容值(兼容,'supportsMidConvoToolChanges'):#可增可删
        更新['toolUpdate']='in-history'#历史内更新
    elif 协议=='openai-completions' and _兼容值(兼容,'supportsMidConvoToolAdditions'):#只能追加
        更新['toolUpdate']='addition-only'#只追加
    elif 协议 in ('openai-responses','azure-openai-responses','openai-codex-responses') and (
            _兼容值(兼容,'supportsAdditionalTools') or _兼容值(兼容,'supportsToolSearch')):#响应线路的追加工具
        更新['toolUpdate']='addition-only'#只追加
    return 更新#更新方式
