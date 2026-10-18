'DeepSeek GET /models：一次带鉴权的请求，并逐条解码'
import json,threading#正文与放弃等待
import urllib.request#列出请求
from urllib.error import HTTPError,URLError#状态与重定向
from urllib.request import Request#请求对象
from ...工具.超时 import 超时原因,已中止错误#截止原因
from ...基础设施.通用工具.数值判定 import 是否正安全整数#容量
from ..llm import 应用身份,归属头,大模型错误,已中止#身份、归属与错误

__all__=('列举超时码','解析模型列举','请求模型列举')#仅中文公开名

已列模态=('text','image')#本构建会发送的模态
列举超时码='MODEL_LISTING_TIMEOUT'#列举截止的超时原因码

class 拒绝重定向(urllib.request.HTTPRedirectHandler):#重定向即失败
    '重定向即失败，凭据留在请求的源站'
    def redirect_request(自身,请求,文件对象,状态码,消息,响应头,新网址):#不跟随
        '任何重定向都拒绝'
        raise URLError('redirect refused')#不把目标地址写进消息

拒绝重定向打开器=urllib.request.build_opener(拒绝重定向())#替换默认跟随

def 信号超时(信号,码):#从信号取出匹配的超时原因
    '信号原因是指定码的超时原因时返回它'
    if 信号 is None:#无信号
        return None#未匹配
    原因=getattr(信号,'_异常',None)#中止原因
    if isinstance(原因,超时原因) and 原因.code==码:#码精确匹配
        return 原因#该截止
    return None#普通取消

def 字段表(值):#非数组对象
    '只接受 dict'
    if type(值) is dict:#映射
        return 值#字段
    return None#其余不是字段表

def 已知模态(值):#本构建认得的模态
    '按列出顺序去重；值不是数组时为空'
    if type(值) is not list:#不是数组
        return None#无法读取
    顺序={}#首次出现的下标
    下标=0#列出位置
    for 项 in 值:#逐项
        if 项 not in 顺序:#只留第一次
            顺序[项]=下标#记下
        下标+=1#推进
    命中=[]#认得的模态
    for 模态 in 已列模态:#固定词表
        if 模态 in 顺序:#列出里有
            命中.append(模态)#收下
    def 位置(模态):#排序键
        '按列出中的首次下标'
        return 顺序[模态]#下标
    命中.sort(key=位置)#列出顺序
    return 命中#去重后的顺序

def 容量(值):#声明的正安全整数
    '缺席由调用方区分；null 与非正安全整数均为非法'
    if 是否正安全整数(值):#正安全整数
        return 值#原值
    return False#非法

def 客户端要求(条目):#本产品记号下的要求
    'client_requirements 缺席或没有本产品时为 none'
    if 'client_requirements' not in 条目:#未声明
        return {'kind':'none'}#无要求
    要求表=字段表(条目['client_requirements'])#必须是对象
    if 要求表 is None:#不是对象
        return {'kind':'invalid'}#读不了
    产品=应用身份['product']#本构建产品记号
    if 产品 not in 要求表:#没有本产品
        return {'kind':'none'}#无要求
    自家=字段表(要求表[产品])#本产品的对象
    if 自家 is None:#不是对象
        return {'kind':'invalid'}#读不了
    if 'min_version' not in 自家:#没有最低版本
        return {'kind':'none'}#无要求
    版本=自家['min_version']#声明的版本
    if type(版本) is str and len(版本)>0:#非空字符串
        return {'kind':'min-version','version':版本}#最低版本
    return {'kind':'invalid'}#空串或其它类型

def 能力(条目):#Messages 能否驱动
    '没有 anthropic_messages、文本输出或受支持输入时不可用'
    接口能力=字段表(条目['api_capabilities']) if 'api_capabilities' in 条目 else None#api_capabilities
    消息=字段表(接口能力['anthropic_messages']) if 接口能力 is not None and 'anthropic_messages' in 接口能力 else None#消息能力
    if 消息 is None:#没有消息能力
        return {'usable':False,'reason':'declares no api_capabilities.anthropic_messages'}#不可用
    if 'output_modalities' not in 条目:#缺席默认文本
        输出=['text']#默认
    else:#声明了才解码
        输出=已知模态(条目['output_modalities'])#列出的输出
    if 输出 is None or 'text' not in 输出:#没有文本输出
        return {'usable':False,'reason':'declares no text output'}#不可用
    if 'input_modalities' not in 条目:#缺席默认文本
        输入=['text']#默认
    else:#声明了才解码
        输入=已知模态(条目['input_modalities'])#列出的输入
    if 输入 is None or len(输入)==0:#没有受支持的输入
        return {'usable':False,'reason':'declares no input modality DeepSeek Harness supports'}#不可用
    窗口=容量(条目['context_window']) if 'context_window' in 条目 else None#上下文
    最大输出=容量(条目['max_output_tokens']) if 'max_output_tokens' in 条目 else None#输出上限
    if 窗口 is False or 最大输出 is False:#非法容量
        return {'usable':False,'reason':'declares an invalid context_window or max_output_tokens'}#不可用
    事实={'inputModalities':输入}#至少有输入模态
    if 窗口 is not None:#声明了窗口
        事实['contextWindow']=窗口#记下
    if 最大输出 is not None:#声明了输出上限
        事实['maxOutputTokens']=最大输出#记下
    if 'system_prompt_update' in 消息:#声明了系统提示更新
        更新=消息['system_prompt_update']#原值
        事实['systemPromptUpdate']='in-history' if 更新=='in-history' else 'leading-only'#其它都读成 leading-only
    return {'usable':True,'facts':事实}#可用

def 解析模型列举(正文):#逐条解码 /models
    """逐条解码一个 /models 正文。
    正文是已解析的 JSON。
    返回有可用 id 的条目，顺序与列出一致。
    没有 data 数组或没有可用条目时抛大模型错误 INVALID_RESPONSE
    """
    根=字段表(正文)#根对象
    数据=根['data'] if 根 is not None and 'data' in 根 else None#data
    if type(数据) is not list:#没有数组
        raise 大模型错误('DeepSeek model listing has no "data" array','INVALID_RESPONSE')#拒绝
    条目=[]#收下的模型
    已见=set()#已用 id
    for 行 in 数据:#列出顺序
        记录=字段表(行)#一行
        标识=记录['id'] if 记录 is not None and 'id' in 记录 else None#模型 id
        if 记录 is None or type(标识) is not str or len(标识)==0 or 标识 in 已见:#无可用 id 或重复
            continue#跳过
        已见.add(标识)#记下
        一条={'id':标识,'requirement':客户端要求(记录),'capabilities':能力(记录)}#身份与能力都保留
        if type(记录.get('name')) is str and len(记录['name'])>0:#非空展示名
            一条['name']=记录['name']#记下
        条目.append(一条)#收下
    if len(条目)==0:#没有模型
        raise 大模型错误('DeepSeek model listing contains no model entry','INVALID_RESPONSE')#拒绝
    return {'entries':条目,'skipped':len(数据)-len(条目)}#跳过数含无 id 与重复 id

def 读列举正文(请求对象,信号):#读完正文或随信号放弃
    '工作线程读完正文；信号先中止则不再等。返回状态与文本'
    盒={}#工作结果
    完成=threading.Event()#工作结束
    def 工作():#阻塞读
        '打开并读完正文，HTTP 错误状态也先读正文'
        响应=None#成功响应
        try:#打开
            响应=拒绝重定向打开器.open(请求对象)#不跟随重定向
            盒['状态']=响应.status#状态
            盒['文本']=响应.read().decode('utf-8','replace')#正文
        except HTTPError as 错误:#非 2xx 仍是一份响应
            try:#先读正文，读失败才算传输失败
                盒['状态']=错误.code#状态
                盒['文本']=错误.read().decode('utf-8','replace')#正文
            except Exception as 读错误:#读正文失败
                盒['错误']=读错误#交给分类
            finally:#关掉错误响应
                try:#关
                    错误.close()#关
                except Exception as 关闭错误:#关闭失败不能替代列举结果
                    _=关闭错误#不覆盖已记下的正文或读错误
        except Exception as 错误:#网络或重定向
            盒['错误']=错误#交给分类
        finally:#关掉成功响应
            if 响应 is not None:#有响应
                try:#关
                    响应.close()#关
                except Exception as 关闭错误:#关闭失败不能替代正文
                    _=关闭错误#正文已经记下
            完成.set()#结束
    threading.Thread(target=工作,daemon=True).start()#不阻塞信号
    while not 完成.wait(0.05):#短轮询
        if 已中止(信号):#截止或取消先到
            原因=getattr(信号,'_异常',None)#原因
            if isinstance(原因,BaseException):#已是异常
                raise 原因#原样
            raise 已中止错误()#无原因
    if '错误' in 盒:#传输失败
        raise 盒['错误']#交给外层分类
    return 盒['状态'],盒['文本']#状态与正文

def 请求模型列举(网址,头,信号):#请求并解码一次列出
    """请求并解码一次模型列出。重定向失败，凭据留在请求的源站。
    网址是列出端点。
    头是该端点的鉴权头。
    信号是整次交换的取消与截止。
    返回解码后的列出。
    截止先到为 TIMEOUT，其它中止为 ABORTED，网络失败为 TRANSPORT，非 2xx 为 HTTP_<status>，非 JSON 为 INVALID_RESPONSE
    """
    请求头=dict(归属头())#产品归属
    请求头['accept']='application/json'#只要 JSON
    请求头.update(头)#调用方头可覆盖
    请求对象=Request(网址,headers=请求头,method='GET')#GET
    try:#整次交换
        状态,文本=读列举正文(请求对象,信号)#读完
    except Exception as 错误:#传输、截止或取消
        到期=信号超时(信号,列举超时码)#本截止是否获胜
        if 到期 is not None:#截止先到
            raise 大模型错误('DeepSeek model listing request to '+网址+' timed out after '+str(到期.timeoutMs)+' ms','TIMEOUT',{'cause':错误})#超时
        if 已中止(信号):#其它中止
            raise 大模型错误('DeepSeek model listing request to '+网址+' was aborted','ABORTED',{'cause':错误})#取消
        raise 大模型错误('could not reach '+网址,'TRANSPORT',{'cause':错误})#网络
    if 状态<200 or 状态>=300:#非成功
        raise 大模型错误(网址+' answered HTTP '+str(状态),'HTTP_'+str(状态),{'status':状态})#状态
    try:#解析 JSON
        正文=json.loads(文本)#未知 JSON
    except json.JSONDecodeError as 错误:#不是 JSON
        raise 大模型错误(网址+' did not answer with JSON','INVALID_RESPONSE',{'cause':错误})#拒绝
    return 解析模型列举(正文)#逐条解码
