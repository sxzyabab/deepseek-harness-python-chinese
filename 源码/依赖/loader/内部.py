"""按父网址解析说明符并用 importlib 导入。loadCache 与依赖图留给后续。"""

import hashlib,importlib,importlib.util,os,sys#标准库
from pathlib import Path#file URL 与本地路径互转
from urllib.parse import urljoin#按父网址拼接相对说明符

class 模块阶段:
    "Node 内部模块请求的阶段"
    源码=1#只要源码，不求值
    求值=2#求值到模块命名空间

_单例=None#加载器单例

class 导入加载器:
    "用 importlib 按父网址解析说明符并导入模块"
    version='py'#版本标记，供后续 HMR 分支
    def import_(自身,说明符,父网址,导入属性):
        "按 Node internal.import 语义同步导入并返回模块对象"
        if 说明符.startswith('.'):#相对说明符
            路径=_网址到路径(urljoin(_规范父网址(父网址),说明符))#拼成网址再转路径
            return _从路径加载(路径)#按文件路径加载
        if '://' in 说明符:#已是 file: 等网址
            return _从路径加载(_网址到路径(说明符))#直接转路径加载
        if os.path.isabs(说明符):#绝对本地路径
            return _从路径加载(说明符)#按路径加载
        目录=_父目录路径(父网址)#裸名从父目录解析
        for 路径 in (
            os.path.join(目录,说明符),#同名文件或目录
            os.path.join(目录,说明符+'.py'),#单文件模块
            os.path.join(目录,说明符,'__init__.py'),#包入口
        ):
            if os.path.isfile(路径):
                return _从路径加载(路径)#命中文件
        return _从搜索路径导入(说明符,目录)#退回 importlib 按目录搜

class 模块加载器:
    "定位 importlib 模块加载器"
    @staticmethod
    def 从内部():
        "取出 importlib 加载器单例"
        global _单例
        if _单例 is None:
            _单例=导入加载器()#惰性创建
        return _单例#不再恒为空

def _规范父网址(父网址):
    "把父网址规范成可供 urljoin 使用的 file URL"
    if not 父网址:
        return Path.cwd().as_uri()+'/'#无父网址时用当前目录
    文本=str(父网址)#统一成字符串
    if '://' in 文本:
        return 文本 if 文本.endswith('/') else 文本+'/'#网址缺尾斜杠则补上
    return Path(文本).absolute().as_uri()+'/'#本地路径转 file URL

def _父目录路径(父网址):
    "取出父网址对应的目录路径"
    路径=_网址到路径(_规范父网址(父网址))#先规范再转路径
    if os.path.isfile(路径):
        return os.path.dirname(路径)#父网址指向文件时取其目录
    return 路径.rstrip(os.sep) or 路径#父网址指向目录

def _网址到路径(网址):
    "file URL 或本地路径字符串转规范本地路径"
    文本=str(网址)#统一成字符串
    if 文本.startswith('file:'):
        return str(Path.from_uri(文本))#file URL 转路径
    return os.path.normpath(文本)#已是路径

def _模块名(路径):
    "为同一路径生成稳定的 sys.modules 键"
    规范=os.path.normpath(os.path.abspath(路径))#绝对规范路径
    摘要=hashlib.sha256(规范.encode()).hexdigest()#路径摘要
    return '_cordis_'+摘要#避免与正常包名冲突

def _从路径加载(路径):
    "用 importlib 从文件或包目录加载模块"
    路径=os.path.normpath(路径)#规范路径
    if os.path.isdir(路径):#说明符指向目录
        入口=os.path.join(路径,'__init__.py')#包入口
        if not os.path.isfile(入口):
            raise ImportError(f'不是包目录：{路径}')#目录里没有 __init__.py
        路径=入口#改加载包入口
    elif not os.path.isfile(路径):#还缺 .py 扩展名
        补扩展=路径+'.py'#尝试补扩展名
        if os.path.isfile(补扩展):
            路径=补扩展#改用带扩展名的路径
        else:
            raise ImportError(f'找不到模块文件：{路径}')#路径不存在
    名称=_模块名(路径)#稳定模块名
    已有=sys.modules.get(名称)#是否已加载
    if 已有 is not None:
        return 已有#同一文件只加载一次
    规格=importlib.util.spec_from_file_location(名称,路径)#构造加载规格
    if 规格 is None or 规格.loader is None:
        raise ImportError(f'无法构造加载规格：{路径}')#规格无效
    模块=importlib.util.module_from_spec(规格)#空模块对象
    sys.modules[名称]=模块#先登记再执行
    规格.loader.exec_module(模块)#执行模块体
    return 模块#模块对象

def _从搜索路径导入(名称,目录):
    "把目录临时插入 sys.path 后用 importlib 导入裸模块名"
    目录=os.path.normpath(目录)#规范目录
    已插入=False#是否由本函数插入
    if 目录 not in sys.path:
        sys.path.insert(0,目录)#临时加到搜索路径
        已插入=True
    try:
        return importlib.import_module(名称)#按模块名导入
    finally:
        if 已插入:
            sys.path.pop(0)#恢复搜索路径
