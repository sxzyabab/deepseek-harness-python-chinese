"""断言本地化文案的规格用的浏览器语言钉住。

对齐上游 `client-runtime/src/locale-env.ts`。公开面仅中文名。
无 vitest 时钩子为可选 no-op 注册表。
"""
__all__=['用钉住浏览器语言','套件前钩子','套件后钩子']#仅中文公开名

套件前钩子=[]#beforeEach 回调表
套件后钩子=[]#afterEach 回调表
浏览器语言钉=['en-US']#当前钉住 languages
浏览器主语言='en-US'#当前 language

def 用钉住浏览器语言(主语言,*其余):#钉住浏览器语言
    """为调用文件内每个测试钉住 navigator.languages/language。"""
    def 钉前():#每个测试前
        """写入钉住值。"""
        global 浏览器语言钉,浏览器主语言#可变
        浏览器语言钉=[主语言,*其余]#钉住 languages
        浏览器主语言=主语言#钉住 language
    def 钉后():#每个测试后
        """恢复默认。"""
        global 浏览器语言钉,浏览器主语言#可变
        浏览器语言钉=['en-US']#恢复
        浏览器主语言='en-US'#恢复
    套件前钩子.append(钉前)#登记前钩
    套件后钩子.append(钉后)#登记后钩

usePinnedBrowserLanguages=用钉住浏览器语言#上游名
