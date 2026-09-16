from threading import Thread as 线程#创建扇出
from .加载器状态 import 状态标签#光纤状态标签

__all__=['网页错误','加载器插件','启动客户端','断言条目已激活']#仅中文公开名

class 网页错误(Exception):
    """web 包异常基类。"""

加载器插件=None#cordis Loader 插件类；启动前由宿主写入

def 全部并发(调用表):
    """扇出：每路一线程，join 后按原序抬错。"""
    if len(调用表)==0:#空
        return#无事
    错误表=[None]*len(调用表)#按原序错误
    def 跑一路(下标,调用):
        """执行一路并记下错误。"""
        try:#跑
            调用()#无参调用
        except BaseException as 错误:#失败
            错误表[下标]=错误#记下
    线程表=[]#工作线程
    for 下标,调用 in enumerate(调用表):#每路一线程
        工作=线程(target=跑一路,args=(下标,调用),daemon=True)#工作线程
        工作.start()#启动
        线程表.append(工作)#登记
    for 工作 in 线程表:#扇出 join
        工作.join()#等到结束
    for 错误 in 错误表:#按原序检查
        if 错误 is not None:#有失败
            raise 错误#原样抛

def 启动客户端(选项):
    """组装客户端。选项为 dict：ctx、modules、manifest、onEntryState?。"""
    if 加载器插件 is None:#未绑定
        raise 网页错误('网页启动：未绑定 cordis Loader 插件类')#失败
    上下文=选项['ctx']#根上下文
    清单=选项['manifest']#启动清单
    汇报=选项['onEntryState'] if 'onEntryState' in 选项 else None#条目状态回调
    上下文.plugin(加载器插件)#挂加载器
    加载器=上下文.loader#取加载器服务
    加载器.internal=选项['modules']#注入模块系统
    def 光纤状态(光纤):
        """投影条目状态到启动页。"""
        条目=光纤.entry#关联条目
        if 条目 is None:#无条目
            return#跳过
        if 条目.fiber is None:#无光纤
            return#跳过
        if 汇报 is None:#无人渲染
            return#跳过
        汇报(条目.options.name,状态标签[条目.fiber.state])#投影
    上下文.on('internal/status',光纤状态)#光纤状态变化
    行表=[行['id'] for 行 in 清单['plugins']]#全部插件 id
    def 造创建(名):
        """创建一条目标。"""
        def 创建一条():
            """标加载中并创建。"""
            if 汇报 is not None:#有汇报
                汇报(名,'loading')#标加载中
            标识=加载器.create({'name':名})#创建条目
            if 加载器.resolve(标识).fiber is None and 汇报 is not None:#导入失败
                汇报(名,'failed')#失败
        return 创建一条#调用
    全部并发([造创建(名) for 名 in 行表])#并发创建
    加载器.等待()#等全部静默，cordis 须显式调用
    断言条目已激活(上下文)#审计激活

def 断言条目已激活(上下文):
    """拒绝导入/apply 失败或仍在等缺失服务的条目。"""
    失败表=[]#失败汇总
    for 条目 in 上下文.loader.entries():#逐条目
        名=条目.options.name#条目名
        if 条目.fiber is None:#导入失败
            失败表.append(名+': 导入失败（导入错误见控制台）')#记失败
            continue#下一条
        态=状态标签[条目.fiber.state]#投影状态
        if 态=='active':#已激活
            continue#下一条
        if 态=='pending':#等服务
            缺失=[]#缺失服务
            for 服务名 in 条目.fiber.inject:#逐服务
                if 上下文.get(服务名) is None:#缺席
                    缺失.append(服务名)#记下
            缺失文=', '.join(缺失) if len(缺失)>0 else '未知'#名单
            失败表.append(名+': pending（等待服务: '+缺失文+'）')#记 pending
        else:#其它非激活态
            失败表.append(名+': '+态)#记状态
    if len(失败表)>0:#有失败
        raise 网页错误('网页启动：'+str(len(失败表))+' 个条目未激活\n'+'\n'.join(失败表))#汇总抛错
