"""为官方 DeepSeek 请求贡献 `dsh_plugin_packages` 字段。

对齐上游 `@deepseek-ai/dsh-plugin-package-inventory-deepseek`。公开面仅中文名。
"""
import json,os#读 manifest 与路径
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 布尔字段#配置字段
光纤状态=cordis.纤程状态#纤程状态

名称='plugin-package-inventory-deepseek'#Cordis 插件名
注入=['agents','deepseekLlmApiExtensions','loader']#依赖
name=名称#Cordis 插件名
inject=注入#Cordis 依赖
配置模式={'enabled':布尔字段(默认值=True)}#默认开启
Config=配置模式#Cordis 配置

__all__=['名称','注入','配置模式','应用','默认']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步值

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

def 比较线文本(左,右):#确定性字典序
    """不依赖 locale 的文本序。"""
    return (左>右)-(左<右)#三态比较

def 从manifest读身份(路径,允许匿名=False):#读 package.json 身份
    """无效 manifest 抛错；匿名 loose module 可返回 None。"""
    文本=open(路径,'r',encoding='utf-8').read()#读文件
    清单=json.loads(文本)#解析
    if 允许匿名 and 取字段(清单,'name') is None:#匿名
        return None#无身份
    名称=取字段(清单,'name')#包名
    版本=取字段(清单,'version')#版本
    if not isinstance(名称,str) or 名称=='' or not isinstance(版本,str) or 版本=='':#无效
        raise Exception('plugin-package-inventory-deepseek: '+路径+' must declare non-empty name and version')#拒绝
    return {'name':名称,'version':版本}#身份

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

class 包身份解析器:#带进程内缓存的解析器
    """按 Loader 入口解析 owning package。"""
    def __init__(自身,宿主基础url):#记住宿主 base
        """构造解析器。"""
        自身.宿主基础url=宿主基础url#宿主 base
        自身.缓存={}#manifest 缓存

    def 解析(自身,活动条目):#解析一条活动 Loader 条目
        """返回身份或 None（loose module）。"""
        条目=取字段(活动条目,'entry')#Loader 条目
        选项=取字段(条目,'options')#条目选项
        说明符=str(取字段(选项,'name'))#模块说明符
        树基础=取字段(取字段(取字段(条目,'parent'),'tree'),'ctx')#树 ctx
        树基础url=取字段(树基础,'baseUrl') if 树基础 is not None else None#树 base
        锚们=[取字段(活动条目,'bareBaseUrl'),树基础url,自身.宿主基础url]#搜索锚点
        锚们=[锚 for 锚 in 锚们 if 锚 is not None]#去空
        键='\u0000'.join(锚们)+'\u0000'+说明符#缓存键
        if 键 in 自身.缓存:#命中缓存
            return 自身.缓存[键]#返回
        包名=裸包名(说明符)#bare 名
        manifest=None#manifest 路径
        if 包名 is not None:#bare package
            for 锚 in 锚们:#逐个锚点
                搜索根=os.path.dirname(锚.replace('file://','').replace('file:','')) if isinstance(锚,str) else None#粗解析
                if 搜索根 and os.path.isdir(搜索根):#可搜索
                    候选=os.path.join(搜索根,'node_modules',包名,'package.json')#node_modules 路径
                    if os.path.isfile(候选):#存在
                        manifest=候选#命中
                        break#停止
        elif not 说明符.startswith('cordis:'):#文件模块
            模块路径=说明符 if os.path.isabs(说明符) else os.path.normpath(os.path.join(锚们[0] if 锚们 else '.',说明符))#解析路径
            manifest=最近manifest(模块路径)#向上找
        身份=None if manifest is None else 从manifest读身份(manifest,包名 is None)#读身份
        自身.缓存[键]=身份#写缓存
        return 身份#返回

def 活动条目们(树,根裸基础url=None):#枚举活动非 group 条目
    """只保留 ACTIVE 且未 disabled 的条目。"""
    输出=[]#收集
    for 条目 in 树.entries():#遍历
        选项=取字段(条目,'options')#选项
        if 取字段(选项,'group'):#group 行
            continue#跳过
        if 取字段(条目,'disabled'):#禁用
            continue#跳过
        纤程=取字段(条目,'fiber')#纤程
        if 纤程 is None or 取字段(纤程,'state')!=光纤状态.已激活:#非 ACTIVE
            continue#跳过
        项={'entry':条目}#基础项
        if 根裸基础url is not None and 取字段(取字段(条目,'parent'),'tree') is 树:#根树
            项['bareBaseUrl']=根裸基础url#带上 bare base
        输出.append(项)#收下
    return 输出#返回

def 收集活动插件包(上下文,解析器,宿主基础url,会话id=None):#收集一次请求的包集
    """去重后按 name/version 排序。"""
    条目们=活动条目们(上下文.loader)#宿主 Loader
    if 会话id is not None and 上下文.get('agentPresets') is not None:#可选 preset 树
        智能体=上下文.agents.get(会话id)#按会话找智能体
        if 智能体 is not None:#命中
            try:#动态取 standing mount
                from ...预设.智能体预设.挂载 import 常驻挂载于#preset 内部 API
                预设树=常驻挂载于(智能体.ctx)#preset 树
                if 预设树 is not None:#有 preset
                    条目们=条目们+活动条目们(预设树.tree if hasattr(预设树,'tree') else 预设树,宿主基础url)#合并
            except Exception:#preset 未组合
                pass#忽略
    唯一={}#去重表
    for 活动 in 条目们:#逐条解析
        身份=解析器.解析(活动)#解析身份
        if 身份 is None:#loose module
            continue#跳过
        唯一[身份['name']+'\u0000'+身份['version']]=身份#去重
    return sorted(唯一.values(),key=lambda 项:(项['name'],项['version']))#按 name 再 version 排序

def 应用(上下文,配置=None):#注册 dsh_plugin_packages 字段
    """默认开启；关闭时直接返回。"""
    配置=配置 or {}#默认空
    if 取字段(配置,'enabled') is False:#显式关闭
        return#无贡献
    宿主基础url=取字段(上下文,'baseUrl') or ''#宿主 base
    解析器=包身份解析器(宿主基础url)#解析器
    class 提供方:#扩展提供方
        """每次请求读取 Loader 真值。"""
        def prepare(自身,请求):#准备字段
            """组装 version=1 的包清单。"""
            值={'version':1,'packages':收集活动插件包(上下文,解析器,宿主基础url,取字段(请求,'sessionId'))}#扩展体
            return {'value':值}#返回
    上下文.deepseekLlmApiExtensions.注册('dsh_plugin_packages',提供方())#登记字段

apply=应用#Cordis 插件入口
默认=应用#默认导出
default=应用#Cordis 默认导出
