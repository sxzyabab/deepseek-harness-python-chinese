"""复制、读取与删除本地编写的预设。

对齐上游 `agent-presets/src/authoring.ts`。公开面仅中文名。
"""
import os#路径
import shutil#复制与删除
import stat as 状态模组#权限位
from atomic_write import 原子写文件#原子写文件
from home_paths import 展开家目录路径#展开 ~
from .元数据 import 元数据文件,渲染预设元数据#元数据
from .预设 import 预设标识规则#id 文法

__all__=[#仅中文公开名
    '非法预设标识错误','预设已存在错误','预设不可写错误',
    '可写根','读组合','复制组合','删除组合',
]#公开面结束

class 非法预设标识错误(Exception):#非法预设 id
    """不能用作根下目录名的预设 id。"""
    def __init__(自身,预设标识):#构造
        """记下被拒绝的 id。"""
        super().__init__(
            'agent-presets: preset id '+repr(预设标识)+' must match '+str(预设标识规则.pattern)+' — '
            +'the id is a directory name, so anything else could escape the preset root'
        )#诊断
        自身.presetId=预设标识#被拒绝的 id

class 预设已存在错误(Exception):#预设已存在
    """复制目标已被占用——复制从不覆盖。"""
    def __init__(自身,预设标识):#构造
        """记下已被占用的 id。"""
        super().__init__(
            'agent-presets: preset "'+预设标识+'" already exists — '
            +'a copy never overwrites; delete the existing preset first or choose another id'
        )#诊断
        自身.presetId=预设标识#已被占用的 id

class 预设不可写错误(Exception):#预设不可写
    """在部署不允许编写的地方尝试了编写。"""
    def __init__(自身,预设标识,原因):#构造
        """记下试图改动的对象与原因。"""
        super().__init__('agent-presets: preset "'+预设标识+'" cannot be written: '+原因)#诊断
        自身.presetId=预设标识#试图改动的 id

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键,缺省)#映射
    return getattr(对象,键,缺省)#属性

def 可写根(根们):#解析可写根
    """本地编写预设写入的根：第一个 user 根的绝对路径。"""
    根=None#候选
    for 候选 in 根们:#找第一个 user
        if 取字段(候选,'trust')=='user':#用户根
            根=候选#命中
            break#停
    if 根 is None:#没有可写根
        raise 预设不可写错误('','this deployment configures no user-writable preset root')#部署未配置
    return os.path.abspath(展开家目录路径(取字段(根,'path')))#展开并绝对

def 读组合(预设):#读组合文本
    """读一个预设的组合文本。"""
    路径=取字段(预设,'path')#组合文件
    文件=open(路径,'r',encoding='utf-8')#打开
    try:#读
        return 文件.read()#内容
    finally:#关
        文件.close()#关闭

def 已占用(路径):#路径是否已被占用
    """路径上是否已有任何占用。"""
    return os.path.exists(路径)#存在即占用

def 收紧权限(目录):#收紧目录权限
    """把复制出的树重新收紧为仅所有者。"""
    os.chmod(目录,0o700)#目录仅所有者
    for 名 in os.listdir(目录):#每个条目
        目标=os.path.join(目录,名)#绝对路径
        if os.path.isdir(目标) and not os.path.islink(目标):#子目录
            收紧权限(目标)#递归
        else:#普通文件
            模式=os.stat(目标).st_mode#当前模式
            if (模式&状态模组.S_IXUSR)!=0:#有所有者执行
                os.chmod(目标,0o700)#保留执行
            else:#无执行
                os.chmod(目标,0o600)#仅读写

def 复制组合(根们,源,标识,名称=None):#整目录复制出新预设
    """通过复制已有预设的整个目录来创建预设。"""
    if 预设标识规则.fullmatch(标识) is None:#id 须合法
        raise 非法预设标识错误(标识)#拒绝
    目录=os.path.join(可写根(根们),标识)#目标目录
    if 已占用(目录):#目标已被占用
        raise 预设已存在错误(标识)#拒绝覆盖
    源目录=os.path.dirname(取字段(源,'path'))#源目录
    try:#复制、收紧、重写元数据
        shutil.copytree(源目录,目录,symlinks=False)#递归解引用复制
        收紧权限(目录)#收紧为仅所有者
        元={}#新元数据
        if 名称 is not None:#有展示名
            元['name']=名称#带上
        描述=取字段(源,'description')#源描述
        if 描述 is not None:#保留源描述
            元['description']=描述#保留
        渲染=渲染预设元数据(元)#渲染
        元路径=os.path.join(目录,元数据文件)#副本元数据
        if 渲染 is None:#没有可发布的展示文本
            try:#删掉空白元数据
                os.remove(元路径)#删除
            except OSError:#可能本就不存在
                pass#放过
        else:#有内容则原子写入
            原子写文件(元路径,渲染,{'mode':0o600,'dirMode':0o700})#仅所有者
    except BaseException as 错误:#失败则清掉半成品
        shutil.rmtree(目录,ignore_errors=True)#清掉
        raise 错误#原错上抛
    return 目录#新预设目录

def 删除组合(根们,预设):#删除本地编写的预设
    """删除本地编写的预设。附带预设会被拒绝。"""
    if 取字段(预设,'trust')!='user':#附带不可删
        raise 预设不可写错误(取字段(预设,'id'),'it ships with the deployment')#属于部署
    目录=os.path.join(可写根(根们),取字段(预设,'id'))#可写根下应对应的目录
    路径=取字段(预设,'path')#组合路径
    if not os.path.isabs(路径) or not 路径.startswith(目录):#必须落在可写根下
        raise 预设不可写错误(取字段(预设,'id'),'it does not live under the writable preset root')#不在可写根下
    shutil.rmtree(目录,ignore_errors=True)#递归删除
