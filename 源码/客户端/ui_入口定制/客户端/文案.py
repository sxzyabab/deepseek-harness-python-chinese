__all__=['英文','中文','日文','西班牙文','法文','德文','俄文','葡萄牙文','中文句']

英文={
    'install':'Browse other plugins',
    'create':'Create your plugin',
    'createPrompt.sidebar':'Create a DSH plugin with a left sidebar entry.',
    'createPrompt.conversation':'Create a DSH conversation view plugin.',
    'createPrompt.rightbar':'Create a DSH plugin with a right sidebar entry.',
}

中文={
    'install':'浏览更多插件',
    'create':'创建你的插件',
    'createPrompt.sidebar':'创建一个带左侧栏入口的 DSH 插件。',
    'createPrompt.conversation':'创建一个 DSH 会话视图插件。',
    'createPrompt.rightbar':'创建一个带右侧栏入口的 DSH 插件。',
}

日文={
    'install':'他のプラグインを探す',
    'create':'プラグインを作成',
    'createPrompt.sidebar':'左サイドバーにエントリを持つ DSH プラグインを作成します。',
    'createPrompt.conversation':'DSH 会話ビュープラグインを作成します。',
    'createPrompt.rightbar':'右サイドバーにエントリを持つ DSH プラグインを作成します。',
}

西班牙文={
    'install':'Explorar otros complementos',
    'create':'Crea tu complemento',
    'createPrompt.sidebar':'Cree un complemento DSH con una entrada en la barra lateral izquierda.',
    'createPrompt.conversation':'Cree un complemento de vista de conversación DSH.',
    'createPrompt.rightbar':'Cree un complemento DSH con una entrada en la barra lateral derecha.',
}

法文={
    'install':"Parcourir d'autres plugins",
    'create':'Créez votre plugin',
    'createPrompt.sidebar':'Créez un plugin DSH avec une entrée dans la barre latérale gauche.',
    'createPrompt.conversation':"Créez un plugin d'affichage de conversation DSH.",
    'createPrompt.rightbar':'Créez un plugin DSH avec une entrée dans la barre latérale droite.',
}

德文={
    'install':'Durchsuchen Sie andere Plugins',
    'create':'Erstellen Sie Ihr Plugin',
    'createPrompt.sidebar':'Erstellen Sie ein DSH-Plugin mit einem Eintrag in der linken Seitenleiste.',
    'createPrompt.conversation':'Erstellen Sie ein DSH-Plugin für die Konversationsansicht.',
    'createPrompt.rightbar':'Erstellen Sie ein DSH-Plugin mit einem Eintrag in der rechten Seitenleiste.',
}

俄文={
    'install':'Просмотрите другие плагины',
    'create':'Создайте свой плагин',
    'createPrompt.sidebar':'Создайте плагин DSH с записью на левой боковой панели.',
    'createPrompt.conversation':'Создайте плагин просмотра диалога DSH.',
    'createPrompt.rightbar':'Создайте плагин DSH с записью на правой боковой панели.',
}

葡萄牙文={
    'install':'Procure outros plug-ins',
    'create':'Crie seu plug-in',
    'createPrompt.sidebar':'Crie um plug-in DSH com uma entrada na barra lateral esquerda.',
    'createPrompt.conversation':'Crie um plug-in de visualização de conversa DSH.',
    'createPrompt.rightbar':'Crie um plug-in DSH com uma entrada na barra lateral direita.',
}

def 中文句(键,参数=None):
    '按中文表原文填占位。界面不读英文表'
    模板=中文[键]
    if 参数 is None:
        return 模板
    结果=模板
    for 名,值 in 参数.items():
        结果=结果.replace('{'+名+'}','' if 值 is None else str(值))
    return 结果
