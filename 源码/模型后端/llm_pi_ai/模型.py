"""从公开窄入口组装的 pi-ai 模型辅助。"""
import pi_ai#外部依赖胶水（pi-ai SDK）
from .目录 import 思考档位列表#思考档升级序

__all__=('创建模型集','创建提供方','取受支持思考档',)#仅中文公开名

def 创建模型集(选项=None):
    """创建空的 pi-ai 集合，不导入其聚合入口。"""
    if 选项 is None:#无选项
        模型集=pi_ai.builtinModels()#内建集合
    else:#有选项
        模型集=pi_ai.builtinModels(选项)#带认证集成
    模型集.clearProviders()#清空提供方
    return 模型集#可变集合

def 创建提供方(输入):
    """创建配置自定义路由所用的静态、单协议提供方。"""
    def 取模型():
        """本路由模型表。"""
        return 输入['models']#模型表
    def 流(模型,上下文,选项):
        """委托协议流。"""
        return 输入['api'].stream(模型,上下文,选项)#流
    def 简化流(模型,上下文,选项):
        """委托协议简化流。"""
        return 输入['api'].streamSimple(模型,上下文,选项)#简化流
    结果={'id':输入['id'],'name':输入['name'],'auth':输入['auth'],#身份与认证
          'getModels':取模型,'stream':流,'streamSimple':简化流}#委托面
    if 'baseUrl' in 输入:#有基址
        结果['baseUrl']=输入['baseUrl']#带上
    return 结果#提供方

def 取受支持思考档(模型):
    """从 pi-ai 公开模型元数据解析可选推理档。"""
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
