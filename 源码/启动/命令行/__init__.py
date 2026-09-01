"""dsh 启动器交给它所启动应用的命令行。

启动器只解析自己的旗标，把其后的一切通过 `命令行参数` 服务原样交给树，因此应用拥有自己的旗标族、`--help` 文本和解析错误。

对齐上游 `@deepseek-ai/dsh-cmdline`。公开面仅中文名。服务键与诊断英文字面量保持上游。
"""
import argparse#参数解析
import sys#标准流

__all__=['提供命令行','标准输入结束退出','解析命令行','命令','命令错误','内部流']#仅中文公开名

class 命令错误(Exception):#commander 控制流错误
    """帮助、版本、解析错误或程序主动拒绝时抛出；携带退出码。"""
    def __init__(自身,消息,退出码=1,码='commander.error'):#构造
        """记下消息、退出码与错误码。"""
        super().__init__(消息)#消息
        自身.exitCode=退出码#退出码
        自身.code=码#错误码前缀 commander.*

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键,缺省)#映射
    return getattr(对象,键,缺省)#属性

def 短横转驼峰(名):#trusted-host → trustedHost
    """把短横名收成驼峰。"""
    段=名.split('-')#分段
    if len(段)==0:#空
        return 名#原样
    结果=段[0]#首段
    for 片 in 段[1:]:#后续
        if 片:#非空
            结果=结果+片[:1].upper()+片[1:]#首字母大写
    return 结果#驼峰

class 命令:#应用拥有的命令行程序
    """对齐 commander 的最小子集：名称、描述、位置参数、选项、action、error、parse。"""
    def __init__(自身):#新程序
        """建立空程序。"""
        自身._名='program'#程序名
        自身._描述=''#描述
        自身._帮助选项=('-h','--help')#帮助旗标
        自身._帮助说明='show this help'#帮助说明
        自身._位置=[]#位置参数声明
        自身._选项=[]#选项声明
        自身._帮助尾=''#帮助尾注
        自身._动作=None#成功解析后的同步 action
        自身.args=[]#位置参数值
        自身._已解析选项={}#选项值
        自身._写标准=None#标准输出写
        自身._写错误=None#标准错误写
        自身._退出覆盖=False#是否把退出变成抛错

    def name(自身,名=None):#读或设程序名
        """读或设程序名；设时链式返回自身。"""
        if 名 is None:#读取
            return 自身._名#当前名
        自身._名=名#写入
        return 自身#链式

    def description(自身,文本):#设描述
        """设描述并链式返回。"""
        自身._描述=文本#描述
        return 自身#链式

    def helpOption(自身,旗标,说明):#帮助旗标
        """设帮助旗标与说明。"""
        部分=旗标.replace(' ','').split(',')#拆短长旗标
        自身._帮助选项=tuple(部分) if len(部分)>=2 else ('-h','--help')#两旗标
        自身._帮助说明=说明#说明
        return 自身#链式

    def argument(自身,规格,说明=''):#位置参数
        """声明位置参数（如 `[task...]`）。"""
        自身._位置.append({'规格':规格,'说明':说明})#登记
        return 自身#链式

    def option(自身,旗标,说明=''):#选项
        """声明选项；可重复权威用 `<authority...>`。"""
        自身._选项.append({'旗标':旗标,'说明':说明})#登记
        return 自身#链式

    def addHelpText(自身,位置,文本):#帮助尾注
        """在帮助后追加文本。"""
        if 位置=='after':#仅支持 after
            自身._帮助尾=文本#尾注
        return 自身#链式

    def action(自身,回调):#登记成功动作
        """登记解析成功后的同步 action。"""
        自身._动作=回调#动作
        return 自身#链式

    def exitOverride(自身):#退出覆盖
        """把退出变成抛 `命令错误`。"""
        自身._退出覆盖=True#覆盖
        return 自身#链式

    def configureOutput(自身,选项):#改写输出
        """改写标准输出与标准错误写函数。"""
        自身._写标准=取字段(选项,'writeOut')#标准输出
        自身._写错误=取字段(选项,'writeErr')#标准错误
        return 自身#链式

    def opts(自身):#已解析选项
        """返回已解析选项映射。"""
        return dict(自身._已解析选项)#副本

    def error(自身,消息):#用法错误
        """写出错误并按覆盖策略退出或抛错。"""
        写出=自身._写错误 or (lambda 块:sys.stderr.write(块))#错误流
        写出(消息 if 消息.endswith('\n') else 消息+'\n')#写出
        if 自身._退出覆盖:#覆盖则抛
            raise 命令错误(消息,1,'commander.error')#抛控制流
        raise SystemExit(1)#直接退出

    def _构建解析器(自身):#构造 argparse
        """按声明构造 ArgumentParser。"""
        解析器=argparse.ArgumentParser(prog=自身._名,description=自身._描述,add_help=False)#自管帮助
        短=自身._帮助选项[0]#短旗标
        长=自身._帮助选项[1] if len(自身._帮助选项)>1 else '--help'#长旗标
        解析器.add_argument(短,长,action='store_true',dest='_求助',help=自身._帮助说明)#帮助
        for 项 in 自身._选项:#选项
            旗标=项['旗标']#旗标串
            部分=旗标.split()#如 --host <host>
            长旗=部分[0]#主旗标
            属性=旗标.lstrip('-').replace('-','_').split()[0] if ' ' not in 长旗 else 长旗.lstrip('-').replace('-','_')#属性名
            属性=长旗.lstrip('-').replace('-','_')#属性名
            可重复='...' in 旗标#可重复
            吃值='<' in 旗标#带值
            if 可重复:#可重复权威
                解析器.add_argument(长旗,action='append',default=None,dest=属性,help=项['说明'])#列表
            elif 吃值:#单值
                解析器.add_argument(长旗,default=None,dest=属性,help=项['说明'])#单值
            else:#开关
                解析器.add_argument(长旗,action='store_true',dest=属性,help=项['说明'])#开关
        for 项 in 自身._位置:#位置
            规格=项['规格']#规格
            名=规格.strip('[]<>').replace('...','').strip() or 'args'#参数名
            if '...' in 规格:#剩余词
                解析器.add_argument(名,nargs='*',default=[],help=项['说明'])#剩余
            elif 规格.startswith('['):#可选
                解析器.add_argument(名,nargs='?',default=None,help=项['说明'])#可选
            else:#必填
                解析器.add_argument(名,help=项['说明'])#必填
        return 解析器#解析器

    def parse(自身,参数,选项=None):#解析参数列表
        """解析用户参数；成功则跑 action；帮助则写出并退出。"""
        来源=取字段(选项,'from') if 选项 else None#来源
        列表=list(参数)#快照
        解析器=自身._构建解析器()#解析器
        try:#解析
            命名空间,未知=解析器.parse_known_args(列表)#解析
        except SystemExit as 退出:#argparse 帮助/错误
            码=退出.code if isinstance(退出.code,int) else 1#退出码
            if 自身._退出覆盖:#覆盖
                raise 命令错误(str(退出),码,'commander.help' if 码==0 else 'commander.error')#抛
            raise#原样
        if getattr(命名空间,'_求助',False):#帮助
            文本=解析器.format_help()+自身._帮助尾#帮助文本
            写出=自身._写标准 or (lambda 块:sys.stdout.write(块))#标准输出
            写出(文本 if 文本.endswith('\n') else 文本+'\n')#写出
            if 自身._退出覆盖:#覆盖
                raise 命令错误('help',0,'commander.help')#帮助退出
            raise SystemExit(0)#正常退出
        if 未知 and 来源=='user':#未知旗标
            自身.error(自身._名+': unknown option '+repr(未知[0]))#拒绝
        自身._已解析选项={}#清空
        for 项 in 自身._选项:#填选项
            旗标=项['旗标'].split()[0]#主旗标
            属性=旗标.lstrip('-').replace('-','_')#属性
            值=getattr(命名空间,属性,None)#取值
            驼峰=短横转驼峰(旗标.lstrip('-'))#驼峰键
            if 值 is not None:#有值才记
                自身._已解析选项[驼峰]=值#写入
        自身.args=[]#位置值
        for 项 in 自身._位置:#位置
            规格=项['规格']#规格
            名=规格.strip('[]<>').replace('...','').strip() or 'args'#名
            值=getattr(命名空间,名,None)#取值
            if isinstance(值,list):#剩余词
                自身.args=list(值)#列表
            elif 值 is not None:#单值
                自身.args=[值]#单元素
        if 自身._动作 is not None:#有动作
            自身._动作()#跑同步 action

内部流={#可替换输出流
    'stdin':sys.stdin,#标准输入
    'stdout':sys.stdout,#标准输出
    'stderr':sys.stderr,#标准错误
}#内部流结束

def 提供命令行(上下文,宿主):#向宿主提供命令行事实
    """在任何树入口挂载之前，于宿主上下文上提供命令行、退出与可选就绪信号。"""
    快照=tuple(取字段(宿主,'args') or [])#冻结参数快照
    def 取参数():#读快照
        """返回不可变参数列表。"""
        return 快照#快照
    上下文.provide('cmdlineArgs',{'get':取参数})#提供内部参数服务
    上下文.provide('appExit',取字段(宿主,'exit'))#提供退出请求
    就绪=取字段(宿主,'ready')#可选就绪信号
    if 就绪 is not None:#嵌入宿主提供就绪
        上下文.provide('appReady',就绪)#提供成功启动信号

def 标准输入结束退出(上下文,标签):#stdin EOF 绑定有界退出
    """在 appReady 提交后，stdin EOF 请求有界成功退出。"""
    退出=上下文.get('appExit')#退出请求
    就绪=上下文.get('appReady')#就绪信号
    if 退出 is None or 就绪 is None:#启动器未提供
        raise Exception('stdio app: the launcher must provide ctx.appExit and ctx.appReady before the tree mounts')#拒绝
    标准输入=内部流['stdin']#标准输入流
    活跃=True#监听仍有效
    已结束=False#EOF 已处理
    取消就绪=lambda:None#就绪监听拆除器
    def 结束():#EOF 处理
        nonlocal 已结束,取消就绪#闭包状态
        if (not 活跃) or 已结束:#已拆或已处理
            return#跳过
        已结束=True#标记
        取消就绪=就绪.onReady(lambda:退出(0))#成功启动后再退出
    def 拆除():#effect 拆除
        nonlocal 活跃,取消就绪#闭包状态
        活跃=False#停用
        取消就绪()#取消就绪监听
        if hasattr(标准输入,'off'):#可移除监听
            标准输入.off('end',结束)#移除 EOF 监听
    上下文.effect(拆除,标签)#登记拆除
    if hasattr(标准输入,'once'):#可订阅 EOF
        标准输入.once('end',结束)#订阅一次 EOF
    if getattr(标准输入,'readableEnded',False):#已 EOF
        结束()#排队处理

def 有动作(程序):#是否声明 action
    """程序是否登记了成功解析后的 action。"""
    return callable(取字段(程序,'_动作'))#有动作

def 配置退出与输出(程序):#接到启动器适配器
    """把退出与输出接到内部流。"""
    def 写标准(文本):#标准输出
        """写标准输出。"""
        流=内部流['stdout']#输出流
        写=getattr(流,'write',None)#写方法
        if 写 is not None:#有写
            写(文本)#写出
    def 写错误(文本):#标准错误
        """写标准错误。"""
        流=内部流['stderr']#错误流
        写=getattr(流,'write',None)#写方法
        if 写 is not None:#有写
            写(文本)#写出
    程序.exitOverride().configureOutput({'writeOut':写标准,'writeErr':写错误})#链式配置

def 是否命令错误(错误):#是否控制流错误
    """按结构检测 commander 风格控制流错误。"""
    if not isinstance(错误,Exception):#非异常
        return False#不是
    码=getattr(错误,'code',None)#错误码
    退出码=getattr(错误,'exitCode',None)#退出码
    return isinstance(码,str) and 码.startswith('commander.') and isinstance(退出码,(int,float))#结构命中

def 解析命令行(上下文,程序):#解析内部参数并跑 action
    """用应用的命令程序解析启动器不可变的参数快照。"""
    参数=上下文.get('cmdlineArgs')#内部参数服务
    退出=上下文.get('appExit')#退出请求
    if 参数 is None or 退出 is None:#启动器未提供
        raise Exception(程序.name()+': the launcher must provide ctx.cmdlineArgs and ctx.appExit before the tree mounts')#拒绝
    if not 有动作(程序):#无 action
        raise Exception(程序.name()+': no command in the program declares an action; parseCmdline runs the invoked command\'s action on a successful parse, and app code there publishes its service')#拒绝
    配置退出与输出(程序)#接到适配器
    try:#解析
        程序.parse(参数.get(),{'from':'user'})#按 user 来源解析
    except Exception as 错误:#控制流或其它
        if not 是否命令错误(错误):#非控制流
            raise#原样
        退出(错误.exitCode)#按退出码请求退出
