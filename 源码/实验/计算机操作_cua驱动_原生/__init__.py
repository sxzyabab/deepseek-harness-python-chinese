import json,re,threading#目录、工具名与在途
from ...依赖.schemastery import 复合类型字段#空配置
from ...计算机操作.计算机操作.标识构造 import 计算机操作提供方名#提供方名
from ...工具.超时 import 中止控制器,若已中止则抛出,合成信号,已中止#中止
from ...内核.作用域 import 操作任务#在途结算
from cua_driver import CuaDriver

__all__=['名称','依赖','配置','应用']

名称='experimental-computer-use-cua-driver-native'
依赖=['computerUse','tools','systemPrompt']
配置=复合类型字段({})#无字段
工具名模式=re.compile(r'^[A-Za-z0-9_-]{1,64}\Z',re.ASCII)#函数名
指引=(#系统提示
    'Cua Driver native computer-use tools operate the host desktop. Discover the exact app and window, then get a fresh window snapshot before acting. Use element_token from that snapshot, or coordinates from its screenshot. A new snapshot of that window invalidates its earlier element tokens. Select either target or the legacy pid/window_id fields; do not combine them.\n'
    '\n'
    'Prefer background delivery. A refusal does not authorize a foreground retry. Verify the requested outcome from fresh state after an action; a delivered click alone does not prove the outcome. After cancellation, inspect current state before retrying because completed input is not rolled back. Other sessions and applications may change the same desktop.\n'
    '\n'
    'On macOS, cursor-overlay operations may return facility_unavailable even when screenshots and input work.'
)#指引结束

def 解析目录(原始):#校验目录
    """解析 SDK 列出的工具目录。"""
    if not isinstance(原始,dict) or not isinstance(原始.get('tools'),list):#非法
        raise Exception('Cua 驱动工具目录无效')
    工具表=[]#表
    for 工具 in 原始['tools']:#逐项
        if not isinstance(工具,dict) or not isinstance(工具.get('name'),str) or len(工具['name'])<1:#非法
            raise Exception('Cua 驱动工具目录无效')
        if not isinstance(工具.get('inputSchema'),dict):#非法
            raise Exception('Cua 驱动工具目录无效')
        项={'name':工具['name'],'inputSchema':工具['inputSchema']}#项
        if 工具.get('description') is not None:#描述
            项['description']=工具['description']#描述
        if 'outputSchema' in 工具:#输出
            项['outputSchema']=工具['outputSchema']#输出
        工具表.append(项)#记下
    return {'tools':工具表}#目录

def 应用(上下文,配置值=None):#占用并挂原生
    """启动失败回滚全部登记。"""
    寿命=中止控制器()#寿命
    在途=set()#在途任务
    驱动箱={'驱动':None}#原生句柄
    def 插件事件(纤程):#启动期拆除
        """纤程拆除则中止寿命。"""
        if 纤程 is getattr(上下文,'fiber',None) and getattr(纤程,'uid',True) is None:#本纤程
            寿命.中止()#中止
    上下文.on('internal/plugin',插件事件)#监听
    就绪=操作任务()#子就绪
    def 运行时寿命():#登记与拆除
        """先放登记再关原生。"""
        撤销=上下文.computerUse.登记(计算机操作提供方名('cua-driver-native'))#占用
        def 应用子(内):#挂运行时
            """子插件拥有目录与工具。"""
            挂运行时(内,寿命,在途,驱动箱,就绪)#挂
        子=上下文.启动插件({'name':'computer-use-cua-driver-native-runtime','inject':['tools','systemPrompt'],'apply':应用子})#子
        def 卸():#拆除
            """中止、等在途、关 SDK、放登记。"""
            寿命.中止()#中止
            try:#等就绪失败
                就绪.等待()#等
            except Exception:#启动失败
                pass#拆除仍拥有句柄
            for 任务 in list(在途):#在途
                try:#等
                    任务.等待()#等
                except Exception:#忽略
                    pass#结算
            驱动=驱动箱['驱动']#句柄
            if 驱动 is not None:#有
                驱动.shutdown()#关
                if hasattr(驱动,'uniffiDestroy'):#销毁
                    驱动.uniffiDestroy()#销毁
            if hasattr(子,'dispose'):#纤程
                子.dispose()#拆
            撤销()#放
        return 卸#拆除器
    拆除=上下文.副作用(运行时寿命,'computer-use-cua-driver-native.runtime')#寿命
    try:#等就绪
        就绪.等待()#等
    except Exception as 错误:#失败
        if callable(拆除):#拆除
            拆除()#回滚
        elif hasattr(拆除,'dispose'):#纤程
            拆除.dispose()#回滚
        raise 错误#原样

def 挂运行时(内,寿命,在途,驱动箱,就绪):#发现并登记
    """导入 SDK、建运行时、发现工具。"""
    try:#启动
        若已中止则抛出(寿命.信号)#中止
        活动=CuaDriver.create(None)#创建
        驱动箱['驱动']=活动#记下
        选项={'signal':寿命.信号}#中止
        目录=解析目录(json.loads(活动.listToolsJson(选项)))#目录
        若已中止则抛出(寿命.信号)#中止
        名集=set()#公开名
        for 工具 in 目录['tools']:#逐工具
            公开名='cua_driver_native__'+工具['name']#公开名
            if not 工具名模式.fullmatch(公开名):#超格式
                raise Exception('Cua 驱动工具 "'+工具['name']+'" 超出支持的函数名格式')
            if 公开名 in 名集:#重名
                raise Exception('Cua 驱动目录中工具 "'+工具['name']+'" 出现了多次')
            名集.add(公开名)#记下
            def 调用(参数,执行=None,原始名=工具['name'],活动驱动=活动):#调用
                """经原生 SDK 调工具。"""
                合成=合成信号(执行['signal'] if isinstance(执行,dict) else None,寿命.信号)#合成
                若已中止则抛出(合成)#中止
                结果=活动驱动.callTool(原始名,json.dumps(参数,ensure_ascii=False),{'signal':合成})#调用
                若已中止则抛出(合成)#中止
                原文=结果['rawJson'] if isinstance(结果,dict) and 'rawJson' in 结果 else getattr(结果,'rawJson',None)#原文
                return json.loads(原文)#结果
            定义={'name':公开名,'description':工具.get('description') or '','parameters':工具['inputSchema'],'execute':调用}#定义
            if 'outputSchema' in 工具:#输出
                定义['output']=工具['outputSchema']#输出
            内.tools.登记(定义)#登记
        def 执行钩(执行,下一):#在途跟踪
            """本提供方工具合成寿命信号。"""
            if 执行['name'] not in 名集:#他方
                return 下一()#过
            上游=执行.get('signal')
            执行['signal']=合成信号(上游,寿命.信号)#合成
            任务=操作任务()#在途
            在途.add(任务)#记下
            try:#跑
                值=下一()#跑
                任务.兑现(值)#兑现
                return 值#结果
            except Exception as 错误:#失败
                任务.拒绝(错误)#拒绝
                raise 错误#原样
            finally:#清
                在途.discard(任务)#摘
                执行['signal']=上游#还原
        内.on('tools/execute',执行钩)#钩
        内.systemPrompt.section({'name':'computer-use:cua-driver-native','order':内.systemPrompt.getSectionOrder('TOOL_COMPUTER_USE'),'text':指引})#指引
        就绪.兑现(None)#就绪
    except Exception as 错误:#失败
        就绪.拒绝(错误)#拒绝
        raise 错误#原样

name=名称
inject=依赖
apply=应用
Config=配置
