'账号目录：版本门、本构建的模型知识，以及部署覆盖'
import re#语义化版本
from ...工具.值 import 断言永不#封闭联合
from ..llm_deepseek.配置 import 解析适配器选项#覆盖与目录校验

__all__=('解析账号目录',)#仅中文公开名

预发布段=r'(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)'#一段预发布，不允许前导零
版本表达式=re.compile(#完整 major.minor.patch，可选 v 与构建元数据
    r'^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)'
    r'(?:-('+预发布段+r'(?:\.'+预发布段+r')*))?'
    r'(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$'
)#第 4 组是预发布，第 5 组是构建元数据

def 解析版本(文本):#拆成可比较的四段
    '非法或带前导零的版本返回空'
    if type(文本) is not str:#必须是字符串
        return None#非法
    匹配=版本表达式.fullmatch(文本)#整串
    if 匹配 is None:#不匹配
        return None#非法
    预发=匹配.group(4)#预发布，可缺席
    return (int(匹配.group(1)),int(匹配.group(2)),int(匹配.group(3)),None if 预发 is None else 预发.split('.'))#主次补丁与预发布

def 版本合法(文本):#semver.valid
    '合法时返回非空；比较不使用这个字符串'
    if 解析版本(文本) is None:#非法
        return None#空
    if len(文本)>0 and 文本[0] in ('v','V'):#去掉一个前缀
        return 文本[1:]#规范写法
    return 文本#原样

def 比较标识(左,右):#预发布的一段
    '数字按数值，数字小于非数字，其余按字典序'
    左数=左.isdigit()#纯数字
    右数=右.isdigit()#纯数字
    if 左数 and 右数:#都是数字
        左值=int(左)#数值
        右值=int(右)#数值
        if 左值>右值:#左大
            return 1#大于
        if 左值<右值:#左小
            return -1#小于
        return 0#相等
    if 左数:#数字小于非数字
        return -1#小于
    if 右数:#非数字大于数字
        return 1#大于
    if 左>右:#字典序
        return 1#大于
    if 左<右:#字典序
        return -1#小于
    return 0#相等

def 版本不低于(当前,要求):#semver.gte
    '任一方非法则抛 TypeError。无预发布大于同号的预发布'
    左=解析版本(当前)#客户端
    右=解析版本(要求)#要求
    if 左 is None or 右 is None:#非法版本
        raise TypeError('Invalid Version')#与 semver.gte 一样拒绝
    下标=0#主次补丁
    while 下标<3:#三段
        if 左[下标]!=右[下标]:#不等
            return 左[下标]>右[下标]#数值
        下标+=1#下一段
    左预=左[3]#预发布
    右预=右[3]#预发布
    if 左预 is None and 右预 is None:#都是正式版
        return True#相等
    if 左预 is None:#正式版大于预发布
        return True#不低于
    if 右预 is None:#预发布小于正式版
        return False#低于
    长度=len(左预) if len(左预)<len(右预) else len(右预)#公共长度
    下标=0#预发布段
    while 下标<长度:#逐段
        差=比较标识(左预[下标],右预[下标])#这一段
        if 差!=0:#不等
            return 差>0#左大才不低于
        下标+=1#下一段
    return len(左预)>=len(右预)#公共前缀相同时更长的更大

def 分层(模型,层):#叠一层字段
    '文本结果丢掉它继承来的、且这一层没有声明的图片限额'
    合并=dict(模型)#拷贝
    合并.update(层)#层覆盖
    模态=合并['inputModalities'] if 'inputModalities' in 合并 else None#输入模态
    if 模态 is None or 'image' not in 模态:#不再接受图片
        if 'imagePixelBudget' not in 层:#这一层没声明
            合并.pop('imagePixelBudget',None)#丢掉继承值
        if 'imageMaxBytes' not in 层:#这一层没声明
            合并.pop('imageMaxBytes',None)#丢掉继承值
    return 合并#叠好的模型

def 列举叠加(基底,条目,事实,路由最大令牌):#用一条可用列出覆盖同 id 的本构建条目
    'leading-only 去掉基底的系统提示更新；in-history 才写回'
    if 事实.get('systemPromptUpdate')=='leading-only':#列出要求只放开头
        基底=dict(基底)#不要改调用方的原件
        基底.pop('systemPromptUpdate',None)#去掉继承的更新模式
    层={}#这一层声明的字段
    if 'name' in 条目:#列出有展示名
        层['name']=条目['name']#覆盖
    if 'contextWindow' in 事实:#列出有窗口
        层['contextWindow']=事实['contextWindow']#覆盖
    if 'maxOutputTokens' in 事实:#列出有输出能力
        层['maxTokens']=min(路由最大令牌,事实['maxOutputTokens'])#路由上限再封一次
    if 事实.get('systemPromptUpdate')=='in-history':#只有这个值写回
        层['systemPromptUpdate']='in-history'#写回
    层['inputModalities']=list(事实['inputModalities'])#列出的输入，拷贝
    return 分层(基底,层)#leading-only 时基底已去掉继承的更新模式

def 门控(条目,已知,客户端版本,问题):#网络之前拒绝
    '没有最低版本时，只有本构建认识的模型才提供；读不了的要求记入问题'
    要求=条目['requirement']#列举解码的要求
    种类=要求['kind']#封闭种类
    if 种类=='none':#无要求
        if 已知:#本构建支持
            return None#提供
        return {'kind':'unsupported'}#藏起来
    if 种类=='min-version':#声明了最低客户端版本
        if 版本合法(要求['version']) is not None:#版本可读
            if 版本不低于(客户端版本,要求['version']):#本构建够新
                return None#提供，即使内置目录没有
            return {'kind':'upgrade-required','requiredVersion':要求['version']}#需要升级
    elif 种类!='invalid':#列举只产生这三种
        return 断言永不(要求,'model listing client requirement')#不可达
    问题.append('model "'+条目['id']+'" declares an unreadable client requirement')#读不了
    return {'kind':'unsupported'}#拒绝

def 解析账号目录(输入):#解析一份账号目录
    """解析账号目录。声明了最低客户端版本就由它决定列出的模型是否可用；没有时只提供本构建支持的模型，其余列出的模型保持隐藏。
    输入含 listing、supported、overrides、routeMaxTokens、clientVersion。
    返回提供的模型、请求解析条目、拒绝与诊断
    """
    支持表={}#id 到本构建模型
    for 模型 in 输入['supported']:#本构建支持的模型
        支持表[模型['id']]=模型#后者覆盖前者
    问题=[]#列出声明读不了或不可用
    覆盖错误=[]#modelOverrides 诊断
    def 带覆盖(模型):#叠一条覆盖
        '覆盖让适配器选项校验失败时保持原模型'
        覆盖=输入['overrides'][模型['id']] if 模型['id'] in 输入['overrides'] else None#该 id
        if 覆盖 is None:#无覆盖
            return 模型#原样
        候选=分层(模型,覆盖)#叠上
        try:#跨字段规则
            解析适配器选项({'models':[候选]})#用图片能力占位之外的真实候选
        except Exception as 错误:#这条覆盖不适用
            覆盖错误.append('modelOverrides.'+模型['id']+' does not apply ('+str(错误)+')')#诊断
            return 模型#保持原模型
        return 候选#用覆盖后的
    if 输入['listing'] is None:#还没有成功的列出
        解析=解析适配器选项({'models':[带覆盖(模型) for 模型 in 输入['supported']]})['models']#内置目录
        return {'offered':解析,'resolution':解析,'refusals':{},'problems':问题,'overrideErrors':覆盖错误}#提供与解析是同一份
    提供=[]#列出顺序里可选的
    拒绝={}#按 id
    for 条目 in 输入['listing']:#列出顺序
        拒绝项=门控(条目,条目['id'] in 支持表,输入['clientVersion'],问题)#版本门
        if 拒绝项 is not None:#网络前拒绝
            拒绝[条目['id']]=拒绝项#记下
            continue#不提供
        if not 条目['capabilities']['usable']:#声明不可用
            问题.append('model "'+条目['id']+'" '+条目['capabilities']['reason'])#原因来自列举
            拒绝[条目['id']]={'kind':'unsupported'}#隐藏
            continue#不提供
        基底=支持表[条目['id']] if 条目['id'] in 支持表 else {'id':条目['id']}#没有内置知识时只留 id
        提供.append(带覆盖(列举叠加(基底,条目,条目['capabilities']['facts'],输入['routeMaxTokens'])))#叠列出再叠覆盖
    提供标识=set()#已提供
    for 模型 in 提供:#收集 id
        提供标识.add(模型['id'])#记下
    列出标识=set()#列出里出现过
    for 条目 in 输入['listing']:#全部列出 id，含被拒绝的
        列出标识.add(条目['id'])#记下
    for 标识 in 输入['overrides']:#覆盖的键
        if 标识 not in 列出标识 and 标识 not in 支持表:#两边都不认识
            覆盖错误.append('modelOverrides names "'+标识+'", which neither the account listing nor the built-in catalog describes')#诊断
    其余=[]#列出没提供、但本构建支持的
    for 模型 in 输入['supported']:#内置顺序
        if 模型['id'] not in 提供标识:#列出没有把它提供出来
            其余.append(带覆盖(模型))#仍参与请求解析
    合并=list(提供)#先是提供的
    合并.extend(其余)#再是其余
    解析=解析适配器选项({'models':合并})['models']#校验后的解析序
    return {'offered':解析[:len(提供)],'resolution':解析,'refusals':拒绝,'problems':问题,'overrideErrors':覆盖错误}#提供的是解析结果的前缀
