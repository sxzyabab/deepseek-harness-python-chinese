"""经一次配置解析登记解析出的包元数据。"""
import os,json#路径与清单
from ....依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis 服务基类
from .解析器 import 裸包名,安装配置解析,登记工作线程解析#解析器

__all__=['插件包表','读包']#仅中文公开名

def 读包(目录,回退名):
    """读目录上的 package.json 收成包记录。"""
    清单路径=os.path.join(目录,'package.json')#清单
    if not os.path.exists(清单路径):#无清单
        return None#缺席
    清单=json.loads(open(清单路径,encoding='utf-8').read())#解析
    名=清单['name'] if 'name' in 清单 else None#声明名
    版本=清单['version'] if 'version' in 清单 else None#声明版本
    return {#包记录
        'name':名 if isinstance(名,str) else 回退名,#名
        'version':版本 if isinstance(版本,str) else None,#版本
        'dir':目录,#目录
        'manifestPath':清单路径,#清单路径
        'manifest':清单,#清单
    }#结束

def 从父解析包目录(名,父网址):
    """无运行时解析器时按父 URL 的 node_modules 查找。"""
    if 父网址.startswith('file:'):#文件 URL
        父=父网址[5:]#去掉 scheme
        if 父.startswith('///'):#三斜杠
            父=父[3:]#本地路径
        elif 父.startswith('//'):#双斜杠
            父=父[2:]#本地
        父=父.replace('/',os.sep)#分隔符
    else:#已是路径
        父=父网址#原样
    当前=os.path.dirname(父)#从父目录起
    while True:#向上
        候选=os.path.join(当前,'node_modules',名)#候选
        if os.path.exists(os.path.join(候选,'package.json')):#有清单
            return 候选#命中
        上一=os.path.dirname(当前)#上一级
        if 上一==当前:#到根
            return None#未找到
        当前=上一#继续

class 插件包表(服务):
    """一次配置进程内元数据消费方共用的包查找。"""

    def __init__(自身,上下文,配置=None):
        """以 pluginPackages 登记；有世代则安装运行时解析。"""
        super().__init__(上下文,'pluginPackages')#登记
        if 配置 is None:#缺省
            配置={}#空
        自身._行为=配置['behavior'] if 'behavior' in 配置 and 配置['behavior'] is not None else 'enforce'#默认强制
        自身._包表={}#缓存
        自身._解析器=None#运行时解析器
        自身._拆除工作线程=None#工作线程登记拆除
        if 'generation' not in 配置 or 配置['generation'] is None:#只暴露原生查找
            return#不装解析器
        解析器=安装配置解析(配置['generation'],自身._行为)#安装
        自身._拆除工作线程=登记工作线程解析(配置['generation'],自身._行为)#工作线程
        自身._解析器=解析器#记下
        def 拆除解析():
            """拆除工作线程登记与解析器。"""
            if 自身._拆除工作线程 is not None:#有登记
                自身._拆除工作线程()#拆除
            解析器.拆除()#恢复原生
        上下文.副作用(拆除解析,'profile package resolution')#生命周期

    def 替换(自身,世代):
        """为本进程及随后创建的工作线程发布加性世代。"""
        if 自身._解析器 is None:#未安装运行时解析
            raise Exception('plugin-packages: runtime resolution is not installed')#拒绝
        自身._解析器.替换(世代)#替换
        自身._包表={}#清空缓存
        if 自身._拆除工作线程 is not None:#有旧登记
            自身._拆除工作线程()#拆除
        自身._拆除工作线程=登记工作线程解析(世代,自身._行为)#新登记

    def 包属于(自身,说明符,父网址):
        """按说明符定位拥有该模块的包，不要求导出。"""
        名=裸包名(说明符)#裸包名
        if 名 is None:#非包请求
            return None#缺席
        if 自身._解析器 is None:#原生查找
            目录=从父解析包目录(名,父网址)#查找
        else:#运行时解析
            目录=自身._解析器.包目录(名,父网址)#查找
        if 目录 is None:#未找到
            return None#缺席
        键=json.dumps({'dir':目录,'name':名},ensure_ascii=False,separators=(',',':'),allow_nan=False)#缓存键
        if 键 not in 自身._包表:#未缓存
            自身._包表[键]=读包(目录,名)#读入
        return 自身._包表[键]#包记录
