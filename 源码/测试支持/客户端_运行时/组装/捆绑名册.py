import json,os,re,yaml#JSON、路径、正则与 YAML
from ....依赖.include import 应用插件补丁,插件列表读取器#补丁应用与条目列表方言
from ....客户端.模块 import 解析客户端声明#dsh.client 声明解析
from ....客户端.模块.清单 import 精确包说明符#精确包说明符
from .名册 import 客户端名册,客户端名册行,客户端测试运行时错误#名册与异常

__all__=['网页配置档捆绑','组合捆绑名册','网页应用名册']#仅中文公开名

网页配置档捆绑=('@deepseek-ai/dsh-base','@deepseek-ai/dsh-web-app')#网页配置档捆绑
百分C=re.compile(r'%C')#include 插件的 %C 占位

def 组合捆绑名册(捆绑表,锚点=None):#组合捆绑名册
    """按应用顺序组合捆绑表的浏览器名册。"""
    if 锚点 is None:#缺省本文件
        锚点=os.path.abspath(__file__)#本文件
    层表=[读一层(名,锚点) for 名 in 捆绑表]#读每层
    def 补丁失败(消息,*参数):#补丁失败即抛
        """把 include 警告收成组装错误。"""
        raise 客户端测试运行时错误('client-test-runtime: bundle patch '+描述补丁(消息,参数))#英文诊断
    条目列表=应用插件补丁([],[补丁 for 层 in 层表 for 补丁 in 层['patches']],补丁失败)#应用补丁
    锚点表=[层['manifestPath'] for 层 in 层表]#各层清单路径
    行表=[]#名册行
    已见=set()#已见包名
    for 摊平 in 摊平组(条目列表):#摊平组后逐行
        条目=摊平['entry']#条目
        禁用=摊平['disabled']#禁用值
        包名=精确包说明符(条目['name']) if 'name' in 条目 else None#精确包名
        if 包名 is None or 禁用 is True or 包名 in 已见:#跳过非包根、禁用或重复
            continue#下一行
        已见.add(包名)#记下
        清单路径=定位清单(锚点表,包名)#定位 package.json
        if 清单路径 is None:#解析不到
            raise 客户端测试运行时错误('client-test-runtime: cannot resolve plugin package '+包名+' from '+', '.join(捆绑表))#英文诊断
        清单=读清单(清单路径)#读清单
        清单名=清单['name'] if 'name' in 清单 else None#清单包名
        if 清单名!=包名:#包名不符
            raise 客户端测试运行时错误('client-test-runtime: package.json names '+json.dumps(清单名,ensure_ascii=False,separators=(',',':'),allow_nan=False)+', expected '+包名)#英文诊断
        dsh=清单['dsh'] if 'dsh' in 清单 else None#dsh 字段
        声明值=dsh['client'] if isinstance(dsh,dict) and 'client' in dsh else None#client 声明
        声明=解析客户端声明(包名,声明值)#解析 dsh.client
        if 声明 is None or 声明['platform']!='web':#非 web 客户端
            continue#下一行
        if 禁用 is not None and not isinstance(禁用,bool):#!!js 表达式
            raise 客户端测试运行时错误('client-test-runtime: browser row '+包名+' has a `disabled` value this reader cannot evaluate (a !!js expression)')#英文诊断
        依赖=声明['inject'] if 'inject' in 声明 else []
        立即='immediately' in 声明 and 声明['immediately'] is True
        行表.append(客户端名册行(包名,依赖,立即))
    return 客户端名册.从行表(行表)#建造名册

def 读一层(捆绑,锚点):#读一层捆绑
    """定位捆绑 package.json 并解析其补丁列表。"""
    清单路径=定位清单([锚点],捆绑)#定位捆绑 package.json
    if 清单路径 is None:#解析不到
        raise 客户端测试运行时错误('client-test-runtime: cannot resolve bundle '+捆绑)#英文诊断
    清单=读清单(清单路径)#读清单
    dsh=清单['dsh'] if 'dsh' in 清单 else None#dsh 字段
    捆绑字段=dsh['bundle'] if isinstance(dsh,dict) and 'bundle' in dsh else None#bundle 字段
    补丁=捆绑字段['patch'] if isinstance(捆绑字段,dict) and 'patch' in 捆绑字段 else None#补丁路径字段
    if not isinstance(补丁,str):#无补丁
        raise 客户端测试运行时错误('client-test-runtime: bundle '+捆绑+' declares no dsh.bundle.patch')#英文诊断
    文件=os.path.join(os.path.dirname(清单路径),补丁)#补丁文件
    with open(文件,'r',encoding='utf-8') as 句柄:#读补丁
        解析结果=yaml.load(句柄.read(),Loader=插件列表读取器)#按条目列表方言解析
    if not isinstance(解析结果,list):#必须是列表
        raise 客户端测试运行时错误('client-test-runtime: bundle patch must be a top-level list of patches')#英文诊断
    return {'manifestPath':清单路径,'patches':解析结果}#返回层

def 摊平组(条目列表,继承=None):#摊平组
    """按 Loader 顺序摊平组后的行；组本身从不是插件，组的 disabled 禁用其下每一行。"""
    行表=[]#摊平行
    for 条目 in 条目列表:#逐条
        自身禁用=条目['disabled'] if isinstance(条目,dict) and 'disabled' in 条目 else None#自身禁用
        禁用=继承 if (继承 is not None and 继承 is not False) else 自身禁用#继承或自身
        是组=isinstance(条目,dict) and 条目.get('group') is True and isinstance(条目.get('config'),list)#组
        if 是组:#组
            行表.extend(摊平组(条目['config'],禁用))#下钻
            continue#组本身不是插件
        行表.append({'entry':条目,'disabled':禁用})#收下插件行
    return 行表#返回

def 读清单(路径):#读 package.json
    """解析包清单。"""
    with open(路径,'r',encoding='utf-8') as 文件:#读
        return json.load(文件)#解析

def 定位清单(锚点列表,名称):#定位清单
    """在任一锚点向上的 node_modules 上定位 名称/package.json。"""
    for 锚点 in 锚点列表:#每个锚点
        当前=os.path.dirname(os.path.abspath(锚点)) if os.path.isfile(锚点) else os.path.abspath(锚点)#起点
        while True:#向上走
            候选=os.path.join(当前,'node_modules',名称,'package.json')#候选
            if os.path.isfile(候选):#命中
                return 候选#路径
            父=os.path.dirname(当前)#父目录
            if 父==当前:#到根
                break#下一锚点
            当前=父#继续
    return None#未命中

def 描述补丁(消息,参数):#描述补丁
    """按启动器打印方式填充 %C。"""
    下标=[0]#参数游标
    def 填一处(_匹配):#填一处
        """取下一个参数作 JSON。"""
        值=参数[下标[0]] if 下标[0]<len(参数) else None#参数
        下标[0]+=1#前进
        return json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)#JSON
    return 百分C.sub(填一处,消息)#全替换 %C

网页应用名册=组合捆绑名册(网页配置档捆绑)#网页应用名册，导入时组合
