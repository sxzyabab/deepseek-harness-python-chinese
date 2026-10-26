__all__=['中文','英文','日文','西班牙文','法文','德文','俄文','葡萄牙文','中文句']

中文={'failed':'拖放失败，请重试'}

英文={'failed':'Drag failed. Try again.'}

日文={'failed':'ドラッグ＆ドロップに失敗しました。もう一度お試しください。'}

西班牙文={'failed':'Error al arrastrar. Intentar otra vez.'}

法文={'failed':'Le glissement a échoué. Essayer à nouveau.'}

德文={'failed':'Ziehen ist fehlgeschlagen. Versuchen Sie es erneut.'}

俄文={'failed':'Перетащить не удалось. Попробуйте еще раз.'}

葡萄牙文={'failed':'Falha ao arrastar. Tente novamente.'}

def 中文句(键,参数=None):
    '按中文表原文填占位。界面不读英文表'
    模板=中文[键]
    if 参数 is None:
        return 模板
    结果=模板
    for 名,值 in 参数.items():
        结果=结果.replace('{'+名+'}','' if 值 is None else str(值))
    return 结果
