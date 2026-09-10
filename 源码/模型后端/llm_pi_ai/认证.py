"""pi-ai 认证模型与 harness 凭证平面之间的适配器。

对齐上游 `llm-pi-ai/src/auth.ts`。公开面仅中文名。
`fileExists` 回答宿主进程文件系统（`~/.aws/credentials` 等），不是工作区 `ctx.fs`。
"""
import os#主目录与路径
from types import SimpleNamespace as 简名空间#属性面
from ...凭据.凭据 import (#凭证键辅助
    凭证键,凭证键标识,凭证键作用域,凭证引用,是否凭证键段,是否凭证引用名,
)#凭证
from ...工具.启动环境 import 取启动环境#启动环境
from .. import llm#大模型错误

__all__=['记录作用域','记录键于','从上下文建凭证仓','从上下文建认证上下文','建认证注入']#仅中文公开名

记录作用域='llm-pi-ai'#记录作用域

def 记录键于(提供方标识):
    """一个 pi-ai 提供方 id 的记录地址。"""
    return 凭证键(记录作用域,提供方标识)#键

def json映像(值):
    """JSON 映像：数组项原样递归；普通 dict 丢掉 None 成员。"""
    if isinstance(值,list):#数组
        return [None if 项 is None else json映像(项) for 项 in 值]#映射
    if isinstance(值,dict) and type(值) is dict:#普通对象
        映像={}#结果
        for 键,成员 in 值.items():#逐成员
            if 成员 is not None:#跳过 None
                映像[键]=json映像(成员)#递归
        return 映像#映像
    return 值#标量

def 转派爱凭证(记录):
    """把已存记录翻译成 pi-ai 期望的凭证。"""
    if 记录 is None:#缺席
        return None#无
    if 记录.get('kind')=='api-key':#api-key
        凭证={'type':'api_key'}#结构
        if 'key' in 记录 and 记录['key'] is not None:#有密钥
            凭证['key']=记录['key']#密钥
        if 'env' in 记录 and 记录['env'] is not None:#有环境
            凭证['env']=dict(记录['env'])#环境
        return 凭证#凭证
    return 记录['payload']#grant 原样

def 转记录(凭证):
    """把 pi-ai 凭证翻译成要存的记录。"""
    if isinstance(凭证,dict) and 凭证.get('type')=='api_key':#api-key
        记录={'kind':'api-key'}#结构
        if 'key' in 凭证 and 凭证['key'] is not None:#有密钥
            记录['key']=凭证['key']#密钥
        if 'env' in 凭证 and 凭证['env'] is not None:#有环境
            记录['env']=dict(凭证['env'])#环境
        return 记录#记录
    类型=getattr(凭证,'type',None)#对象属性
    if 类型=='api_key':#对象形态
        记录={'kind':'api-key'}#结构
        密钥=getattr(凭证,'key',None)#密钥
        if 密钥 is not None:#有
            记录['key']=密钥#密钥
        环境=getattr(凭证,'env',None)#环境
        if 环境 is not None:#有
            记录['env']=dict(环境)#环境
        return 记录#记录
    载荷=凭证 if isinstance(凭证,dict) else getattr(凭证,'__dict__',凭证)#载荷
    return {'kind':'grant','payload':json映像(载荷)}#grant

def 可写仓(上下文):
    """凭证服务，或点名缺什么的失败。"""
    凭证=上下文.获取服务('credentials')#可选
    if 凭证 is None:#无
        raise llm.大模型错误(
            'llm-pi-ai: this composition mounts no credentials service, so there is nowhere to store the'
            +' credential a sign-in produces; mount one (dsh-credentials-local) to sign in',
            'NO_CREDENTIAL_STORE',
        )#无仓
    return 凭证#仓

def 从上下文建凭证仓(上下文):
    """盖在 harness 凭证记录上的 pi-ai CredentialStore（属性面）。"""
    def 读(提供方标识):
        """读提供方凭证。"""
        凭证=上下文.获取服务('credentials')#可选
        if 凭证 is None:#无
            return None#无存储
        if not 是否凭证键段(提供方标识):#非法段
            return None#无
        return 转派爱凭证(凭证.读记录(记录键于(提供方标识)))#转
    def 列举():
        """列出本作用域记录。"""
        凭证=上下文.获取服务('credentials')#可选
        已存=凭证.列举记录() if 凭证 is not None else []#列表
        我的=[]#结果
        for 条目 in 已存:#逐条
            if 凭证键作用域(条目['key'])!=记录作用域:#非本插件
                continue#跳过
            我的.append({
                'providerId':凭证键标识(条目['key']),
                'type':'api_key' if 条目['kind']=='api-key' else 'oauth',
            })#条目
        return 我的#列表
    def 修改(提供方标识,变更):
        """串行读改写。"""
        if not 是否凭证键段(提供方标识):#非法
            raise llm.大模型错误(
                'llm-pi-ai: provider id "'+提供方标识+'" cannot address a stored credential record (a record id is a'
                +' lowercase hyphenated identifier); authenticate this route through apiKeyEnv instead of a stored'
                +' credential',
                'UNSTORABLE_PROVIDER_ID',
            )#不可存
        def 变(当前):
            """把 pi 变更接到记录。"""
            下一=变更(转派爱凭证(当前))#决策
            return None if 下一 is None else 转记录(下一)#转回
        已存=可写仓(上下文).修改记录(记录键于(提供方标识),变)#写
        return 转派爱凭证(已存)#转
    def 删除(提供方标识):
        """删除记录。"""
        if not 是否凭证键段(提供方标识):#非法
            return#空
        可写仓(上下文).删除记录(记录键于(提供方标识))#删
    return 简名空间(read=读,list=列举,modify=修改,delete=删除)#仓

def 从上下文建认证上下文(上下文):
    """盖在 harness 凭证平面与宿主文件系统上的 pi-ai AuthContext。"""
    def 环境(名):
        """先凭证引用，再启动环境。"""
        if 是否凭证引用名(名):#合法引用名
            凭证=上下文.获取服务('credentials')#可选
            if 凭证 is not None:#有
                命中=凭证.解析(凭证引用(名))#解析
                if 命中 is not None:#命中
                    return 命中['value']#值
        项=取启动环境(上下文).取(名)#启动环境
        return 项['value'] if 项 is not None else None#值或无
    def 文件存在(路径):
        """宿主进程文件系统。"""
        if 路径.startswith('~/') or 路径=='~':#家目录
            展开=os.path.join(os.path.expanduser('~'),路径[1:].lstrip('/\\'))#展开
        else:#原路径
            展开=路径#原样
        try:
            return os.path.exists(展开)#存在
        except OSError:
            return False#不可用
    return 简名空间(env=环境,fileExists=文件存在)#认证上下文

def 建认证注入(上下文):
    """交给 createModels 的 {credentials, authContext}。"""
    return 简名空间(
        credentials=从上下文建凭证仓(上下文),
        authContext=从上下文建认证上下文(上下文),
    )#注入
