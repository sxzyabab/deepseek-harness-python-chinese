"""向官方 DeepSeek 请求贡献 dsh_plugin_packages 字段。"""
import json,os#读 manifest 与路径
from json import JSONDecodeError#清单解析失败
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 布尔字段#配置字段
纤程状态=cordis.纤程状态#纤程状态

名称='plugin-package-inventory-deepseek'#框架 插件名
依赖=['agents','deepseekLlmApiExtensions','loader']#依赖
配置模式={'enabled':布尔字段(默认值=True)}#默认开启

__all__=['清单错误','名称','依赖','配置模式','应用','默认']#仅中文公开名

class 清单错误(Exception):
    """插件包清单解析与校验失败。"""

def 裸包名(说明符):#解析 bare package 名
    """相对路径、绝对路径与带协议说明符返回 None。"""
    if 说明符.startswith('.') or ':' in 说明符 or os.path.isabs(说明符):#非 bare
        return None#跳过
    段=说明符.split('/')#分段
    if len(段)==0:#空
        return None#跳过
    if 段[0].startswith('@') and len(段)>=2:#scoped
        return 段[0]+'/'+段[1]#@scope/name
    return 段[0]#普通包名

def 从manifest读身份(路径,允许匿名=False):#读 package.json 身份
    """无效 manifest 抛错；匿名 loose module 可返回 None。清单为 dict。"""
    文本=open(路径,'r',encoding='utf-8').read()#读文件
    try:#解析
        清单=json.loads(文本)#解析
    except JSONDecodeError as 错误:#清单不是 JSON
        raise 清单错误('plugin-package-inventory-deepseek: package.json is not valid JSON') from 错误#拒绝
    if not isinstance(清单,dict):#必须是对象
        raise 清单错误('plugin-package-inventory-deepseek: package.json must be an object')#拒绝
    if 允许匿名 and 'name' not in 清单:#匿名
        return None#无身份
    名称值=清单['name'] if 'name' in 清单 else None#包名
    版本=清单['version'] if 'version' in 清单 else None#版本
    if not isinstance(名称值,str) or 名称值=='' or not isinstance(版本,str) or 版本=='':#无效
        raise 清单错误('plugin-package-inventory-deepseek: package.json must declare non-empty name and version')#拒绝
    return {'name':名称值,'version':版本}#身份

def 最近manifest(模块路径):#向上找 package.json
    """找不到返回 None。"""
    当前=os.path.dirname(os.path.abspath(模块路径))#起始目录
    根=os.path.splitdrive(当前)[0]+os.sep+os.path.splitdrive(当前)[1].split(os.sep)[0]#盘根
    while True:#向上
        候选=os.path.join(当前,'package.json')#候选 manifest
        if os.path.isfile(候选):#存在
            return 候选#命中
        父=os.path.dirname(当前)#父目录
        if 父==当前:#到顶
            return None#未找到
        当前=父#上移

def 身份排序键(项):
    """按 name 再 version 排序。"""
    return (项['name'],项['version'])#排序键

class 包身份解析器:#带进程内缓存的解析器
    """按 Loader 入口解析 owning package。"""
    def __init__(自身,宿主基础url):
        """构造解析器。"""
        自身.宿主基础url=宿主基础url#宿主 base
        自身.缓存={}#manifest 缓存

    def 解析(自身,活动条目):
        """返回身份或 None（loose module）。活动条目为 dict，Loader 条目为对象。"""
        条目=活动条目['entry']#Loader 条目
        选项=条目.options#条目选项，配置为 dict
        说明符=str(选项['name'])#模块说明符
        树基础=条目.parent.tree.ctx#树 ctx
        树基础url=树基础.baseUrl if 树基础 is not None else None#树 base
        if 树基础url is None:#树未给基址
            树基础url=自身.宿主基础url#回落宿主
        锚列表=[]#搜索锚点
        if 'bareBaseUrl' in 活动条目 and 活动条目['bareBaseUrl'] is not None:#有 bare base
            锚列表.append(活动条目['bareBaseUrl'])#bare
        锚列表.append(树基础url)#树
        锚列表.append(自身.宿主基础url)#宿主
        去重=[]#去重后的锚
        已见=set()#已见锚
        for 锚 in 锚列表:#逐个
            if 锚 is None or 锚 in 已见:#空或重复
                continue#跳过
            已见.add(锚)#记下
            去重.append(锚)#按出现顺序保留
        锚列表=去重#用去重后的
        键='\u0000'.join(锚列表)+'\u0000'+说明符#缓存键
        if 键 in 自身.缓存:#命中缓存
            return 自身.缓存[键]#返回
        包名=裸包名(说明符)#bare 名
        manifest=None#manifest 路径
        if 包名 is not None:#bare package
            for 锚 in 锚列表:#逐个锚点
                搜索根=os.path.dirname(锚.replace('file://','').replace('file:','')) if isinstance(锚,str) else None#粗解析
                if 搜索根 is not None and os.path.isdir(搜索根):#可搜索
                    候选=os.path.join(搜索根,'node_modules',包名,'package.json')#node_modules 路径
                    if os.path.isfile(候选):#存在
                        manifest=候选#命中
                        break#停止
        elif not 说明符.startswith('cordis:'):#文件模块
            模块路径=说明符 if os.path.isabs(说明符) else os.path.normpath(os.path.join(锚列表[0] if len(锚列表)>0 else '.',说明符))#解析路径
            manifest=最近manifest(模块路径)#向上找
        身份=None if manifest is None else 从manifest读身份(manifest,包名 is None)#读身份
        自身.缓存[键]=身份#写缓存
        return 身份#返回

def 列出活动条目(树,根裸基础url=None):#枚举活动非 group 条目
    """只保留 ACTIVE 且未 disabled 的条目。树为对象。"""
    输出=[]#活动非 group 条目
    for 条目 in 树.entries():#遍历
        选项=条目.options#选项，配置为 dict
        分组=选项['group'] if 选项 is not None and 'group' in 选项 else None#group 行
        if 分组 is not None and 分组 is not False:#group 行（空 dict 在 JS 为真，这里按非 None 非 False 跳过）
            continue#跳过
        if 条目.disabled is True:#禁用
            continue#跳过
        纤程=条目.fiber#纤程
        if 纤程 is None or 纤程.state!=纤程状态.已激活:#非 ACTIVE
            continue#跳过
        项={'entry':条目}#基础项
        if 根裸基础url is not None and 条目.parent.tree is 树:#根树，按对象引用相等
            项['bareBaseUrl']=根裸基础url#带上 bare base
        输出.append(项)#纳入结果
    return 输出#仅活动条目

def 收集活动插件包(上下文,解析器,宿主基础url,会话id=None):#收集一次请求的包集
    """去重后按 name/version 排序。"""
    条目列表=列出活动条目(上下文.loader)#宿主 Loader
    if 会话id is not None and 上下文.获取服务('agentPresets') is not None:#可选 preset 树
        智能体=上下文.agents.get(会话id)#按会话找智能体
        if 智能体 is not None:#命中
            try:#动态取 standing mount
                from ...预设.智能体预设.挂载 import 常驻挂载于#preset 内部 API
                挂载=常驻挂载于(智能体.ctx)#preset 挂载记录，为 dict
                if 挂载 is not None and 'tree' in 挂载:#有树
                    条目列表=条目列表+列出活动条目(挂载['tree'],宿主基础url)#合并
            except ImportError:#preset 未组合
                pass#忽略
    唯一={}#去重表
    for 活动 in 条目列表:#逐条解析
        身份=解析器.解析(活动)#解析身份
        if 身份 is None:#loose module
            continue#跳过
        唯一[身份['name']+'\u0000'+身份['version']]=身份#去重
    return sorted(唯一.values(),key=身份排序键)#按 name 再 version 排序

def 应用(上下文,配置=None):#注册 dsh_plugin_packages 字段
    """默认开启；关闭时直接返回。配置为 dict。"""
    if 配置 is None:#未传配置
        配置={}#空配置
    if 'enabled' in 配置 and 配置['enabled'] is False:#显式关闭
        return#无贡献
    宿主基础url=上下文.baseUrl#宿主 base
    if 宿主基础url is None:#未给
        宿主基础url=''#空串
    解析器=包身份解析器(宿主基础url)#解析器
    class 提供方:#扩展提供方
        """每次请求读取 Loader 真值。"""
        def prepare(自身,请求):
            """组装 version=1 的包清单。请求为 dict。"""
            会话号=请求['sessionId'] if 'sessionId' in 请求 else None#可选会话
            值={'version':1,'packages':收集活动插件包(上下文,解析器,宿主基础url,会话号)}#扩展体
            return {'value':值}#返回
    上下文.deepseekLlmApiExtensions.注册('dsh_plugin_packages',提供方())#登记字段

apply=应用#框架槽
name=名称#框架槽
inject=依赖#框架槽
Config=配置模式#框架槽
默认=应用
default=应用#框架槽
