'跑模组的 register，并按加载顺序选出钩子'
import os,re#默认根目录与插件名
from .值 import 消息,浅冻结副本,兑现#register 抛出、选项冻结与期约
from .匹配器 import 引擎事件,事件命中,是事件图案,描述匹配器#事件名与打印

__all__=['钩子注册表','创建on','登记模组']

插件名规则=re.compile(r'^[A-Za-z0-9_-]{1,64}$')#字母、数字、_ 和 -

class 钩子注册表:
    '按加载顺序放模组，钩子再按注册顺序排在模组后面'
    def __init__(自身):
        '空表'
        自身.钩子=[]#注册
        自身.模组=[]#已加载

    def 列出(自身):
        '加载顺序上的模组'
        return list(自身.模组)#副本

    def 添加(自身,模组,钩子):
        '放入一个模组。同名必须先卸掉'
        for 已有 in 自身.模组:#查重
            if 已有['name']==模组['name']:#同名
                raise RuntimeError('钩子模块 '+模组['name']+' 没加载：已有同名插件先加载')#拒绝
        自身.模组.append(模组)#按顺序
        自身.钩子.extend(钩子)#接在后面

    def 移除(自身,名字):
        '卸掉一个模组和它的钩子'
        下标=-1#找到的位置
        序号=0#扫描
        while 序号<len(自身.模组):#逐个
            if 自身.模组[序号]['name']==名字:#同名
                下标=序号#记下
                break#停
            序号+=1#下一个
        if 下标<0:#没有
            return#不用卸
        模组=自身.模组.pop(下标)#摘下
        倒序=len(自身.钩子)-1#从后往前删
        while 倒序>=0:#还有
            if 自身.钩子[倒序]['mod'] is 模组:#同一份模组
                自身.钩子.pop(倒序)#删掉
            倒序-=1#前一个

    def 选择(自身,事件,引发者=None):
        '图案选中这个事件的钩子，外层在前。模组自己的 $ 只让更早加载的模组看见'
        选中=[]#结果
        for 钩子 in 自身.钩子:#注册顺序
            if 引发者 is not None and 钩子['mod']['order']>=引发者['order']:#不早于引发者
                continue#看不见
            if 事件命中(钩子['event'],事件):#图案选中
                选中.append(钩子)#候选
        选中.sort(key=lambda 钩子:钩子['mod']['order'])#外层在前
        return 选中#匹配器留到运行时

    def 未服务(自身,模组,已服务):
        '这个模组按精确名挂上、但宿主从不引发的引擎事件'
        名字=[]#注册顺序，每个一次
        for 钩子 in 自身.钩子:#逐条
            事件=钩子['event']#事件名
            if 钩子['mod'] is not 模组 or 事件 not in 引擎事件 or 事件 in 已服务 or 事件 in 名字:#不算
                continue#下一条
            名字.append(事件)#记下
        return 名字#未服务的事件

    def 描述(自身,模组):
        'claude plugin validate 那种 hooks 行'
        段=[]#一段一段
        for 钩子 in 自身.钩子:#逐条
            if 钩子['mod'] is 模组:#这个模组
                段.append(钩子['event']+描述匹配器(钩子['matcher']))#事件加匹配器
        return ', '.join(段)#逗号隔开

def 是匹配器(值):
    '匹配器必须是对象，不能是列表'
    return isinstance(值,dict)#普通对象

def 创建on(模组):
    '做出 register 收到的 on，并收集它登记的钩子'
    钩子=[]#登记顺序
    无匹配=set()#同一事件不带匹配器只能登记一次
    def on(事件,匹配器或钩子,也许钩子=None):
        'on(事件, 钩子) 或 on(事件, 匹配器, 钩子)。返回带 catch 的登记'
        if not isinstance(事件,str):#事件名必须是字符串
            raise TypeError(模组['name']+'：传给 on() 的事件名不是字符串')#类型
        if not 是事件图案(事件):#未知名字
            raise RuntimeError(模组['name']+'："'+事件+'" 不是事件')#加载时失败
        钩子函数=匹配器或钩子 if 也许钩子 is None else 也许钩子#函数在最后
        匹配器=None if 也许钩子 is None else 匹配器或钩子#有第三参才是匹配器
        if not callable(钩子函数):#必须是函数
            raise TypeError(模组['name']+'：on("'+事件+'") 需要钩子函数')#类型
        if 匹配器 is not None and not 是匹配器(匹配器):#匹配器类型
            raise TypeError(模组['name']+'：on("'+事件+'") 的匹配器必须是对象')#类型
        if 匹配器 is None:#不带匹配器
            if 事件 in 无匹配:#第二次
                raise RuntimeError(模组['name']+'：on("'+事件+'") 不带匹配器注册了两次')#拒绝
            无匹配.add(事件)#记下
        已登记={'mod':模组,'event':事件,'matcher':匹配器,'hook':钩子函数,'catchHandler':None,'reported':set()}#一条登记
        钩子.append(已登记)#按 on 的顺序
        def catch(处理函数):
            '挂上这条钩子的失败处理'
            if not callable(处理函数):#必须是函数
                raise TypeError(模组['name']+'：on("'+事件+'").catch 需要处理函数')#类型
            已登记['catchHandler']=处理函数#替换
        登记=type('登记',(),{})()#带 catch 方法的对象
        登记.catch=catch#模组调用 .catch
        return 登记#登记结果
    return {'on':on,'hooks':钩子}#on 与它写下的列表

def 登记模组(定义,顺序):
    '跑 register。抛错时用钩子模块没加载的文案包起来'
    名字=定义['name']#插件名
    if 插件名规则.fullmatch(名字) is None:#不合法
        raise RuntimeError('模组 "'+名字+'" 没加载：插件名只能用字母、数字、_ 和 -')#拒绝
    根=定义['root'] if 'root' in 定义 and 定义['root'] is not None else os.getcwd()#没给就用进程当前目录
    选项=定义['options'] if 'options' in 定义 and 定义['options'] is not None else {}#缺席当空
    模组={
        'name':名字,#插件名
        'version':定义['version'] if 'version' in 定义 else None,#可选版本
        'root':根,#$.plugin.root
        'options':浅冻结副本(dict(选项)),#register 看见的选项
        'order':顺序,#链上的位置
    }#已加载模组
    做出=创建on(模组)#on 与列表
    try:#register 抛错则整份模组失败
        兑现(定义['register'](做出['on'],模组['options']))#同步 register；若它返回期约则等到结束
    except Exception as 错误:#加载失败
        raise RuntimeError(名字+'：钩子模块没加载：register 抛出了 '+消息(错误)) from 错误#包上原因
    return {'mod':模组,'hooks':做出['hooks']}#模组与登记
