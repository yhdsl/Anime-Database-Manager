配置模块 --- 全局通用配置管理
===============================

.. automodule:: core.base.conf

命名为 `conf` 的模块可以在项目的许多其他地方见到，但是位于底层层的这个\
可是其中最为重要的，**没有之一**！

哈哈，不要被上方加粗的内容吓到了，虽然说是作为一个配置模块，实际上呢，这个模块\
更像是一个仓库，里面储存着可以向全局\ [1]_\ 开放的好东西，里面有着经常用到函数，\
其他模块用到的异常以及该模块的老本行 --- 全局配置\ [#]_\ 的定义以及具体内容。

.. [1] 本章的全局均定义为所有与项目有关的代码部分

.. [#] 这里的配置实际上是故意模糊了枚举类和配置类，在下文中会详细说明原因

接下来让我们看看这个多拉A梦的口袋里都有些什么吧。

常用函数
--------

常用函数是指可能会多次跨模块被调用的功能性函数，为了便于维护和调用，\
选择统一在该模块内定义。

本模块目前定义了如下常用函数，它们往往可以独立使用：

.. autofunction:: core.base.conf.get_version_dict

.. seealso::
    也可以看看下文的 :class:`core.base.conf.Version` 了解关于返回的字典\
    的键的更为详细的介绍。

.. autofunction:: core.base.conf.extend

异常定义
----------

与常用函数类似，异常部分也是为了便于维护等因素而在该模块内被定义的，\
但是它们往往也可以在其对应的模块中被导入。

.. autoexception:: core.base.conf.PluginsTypeError

.. autoexception:: core.base.conf.NeedHookError


全局配置
-----------

全局配置是一个类似于字典的容器，用于储存一系列有着类似属性的配置\ [#]_\ ，\
例如可用的数据库链接对象等。

.. [#] 实际上是以类属性的形式储存的，下文会进行详细的介绍

ADM项目内有两种配置形式：一种是不可变配置，在运行过程中不能动态修改，这种配置\
使用 `枚举` 形式进行储存；另一种是可变配置，在运行过程中可以随时进行更改。

由于在使用中经常混合使用它们，分别进行描述过于繁琐，因此配置一词一般指代枚举类和\
配置类。

第二种类型的配置使用本模块定义的配置类进行创建和操作。这有点类似于字典，事实上，\
你完全可以按照字典的使用方法来操作它；而创建一个配置则有点类似于枚举类，它们大体\
上相同，但有些微妙的差异，请务必仔细阅读下文。

.. seealso::
    枚举是 `Python` 标准库的一部分，看看 :mod:`enum` 的文档获取更多信息，本文\
    不会单独介绍枚举的使用。

.. tip::
    本模块定义的配置类与枚举类在某些操作上并不相同，请仔细阅读下方的注意事项。

单例模式
^^^^^^^^^^

为了保证每个模块访问的均是同一个配置，而不是彼此之间相互独立，我们使用了单例模式\
限制这种行为，并且确保这种行为线程安全。

.. autoclass:: core.base.conf.Singleton

直接子类化该类便可以使用单例模式

>>> class SingletonUser(conf.Singleton):
...     pass

现在无论在何时实例化 `SingletonUser` 均会返回一个相同的实例

>>> singleton_1 = SingletonUser()
>>> singleton_2 = SingletonUser()
>>> print(id(singleton_1))
... 2800302886144
>>> print(id(singleton_2))
... 2800302886144

.. warning::
    在多次实例化同一个单例类时，该类的初始化代码\ [#]_\ 会在\ **每一次**\ 实例化时被调用，\
    这可能会造成令人困惑的运行结果，例如运行后数据发生了改变，导致多次初始化后实例的值出现了\
    难以理解的异常。

    目前暂时折中的处理办法是使用类属性记录初始化代码是否被调用::

            class SingletonUser(conf.Singleton):
                def __init__(self):
                if not self._init_bool:
                    pass
                super().__init__()
                return

    其中 类属性 `_init_bool` 在 `Singleton` 类的 `__init__` 中被跟踪，是一个用于表明初始化\
    代码运行与否的布尔值。

    该实现可能会在未来的版本中被修改。

.. [#] 这里指类的魔术方法：__init__

.. tip::
    单例类可以独立使用，其不依赖本模块的其他任何内容，因此可以在其他地方安全的实现单例模式。

配置类
^^^^^^^^^^^

以下是与配置类有关的定义和说明，也可以直接看看下一节了解可用的配置。

创建一个配置
""""""""""""

配置类的使用与枚举类似，你可以像创建枚举一样创建一个配置

>>> class ConfUser(conf.Conf):
...     RED = 1
...     GREEN = 2

配置的访问
""""""""""""

获取配置的值可以使用属性调用

>>> ConfUser().RED
1

或者像使用字典一样访问

>>> ConfUser()['RED']
1

类似于列表索引的形式也是允许的，会按照配置被添加的顺序进行访问，但配置的顺序\
有时并不重要，采用这种形式有可能会返回错误的结果，因此并不推荐使用

>>> ConfUser()[0]
1

也可以使用迭代来访问

.. # noinspection PyTypeChecker

>>> for data in ConfUser():
...     print(data)
1
2

注意返回的是配置的\ **值**。

添加和修改
""""""""""""

添加一个配置使用的方法与上文一样简单

>>> ConfUser()['BLUE'] = 3
>>> ConfUser()['BLUE']
3

>>> ConfUser().WHITE = 4
>>> ConfUser()['WHITE']
4

修改它也很容易

>>> ConfUser()['BLUE'] = 5
>>> ConfUser()['BLUE']
5

>>> ConfUser().WHITE = 6
>>> ConfUser()['WHITE']
6

配置的只读属性
""""""""""""""""

但如果接下来你试图仿照上文修改 `RED` 配置时，便会意外的发现一个让人感到意外的
`AttributeError` 异常

>>> ConfUser()['RED'] = 0
Traceback (most recent call last):
...
AttributeError

这是由于 `RED` 配置是在 `ConfUser` 内部被定义的，而 `BLUE` 配置则是我们后来添加的。\
配置类将在初始化时将已有的配置视为只读，这一般用于储存较为重要的，不应当在运行中被修改的内容，\
而这部分内容往往是在运行其便可以被写入的。

但如果必须要进行修改，也可以在运行中改变配置的只读属性

>>> ConfUser().state('RED', readonly=False)

接下来便可以随意修改 `RED` 配置了

>>> ConfUser()['RED'] = 0
>>> ConfUser()['RED']
0

也可以再次设为只读

>>> ConfUser().state('RED', readonly=True)

删除属性
""""""""""

删除操作也遵循一致的方法

>>> del ConfUser()['BLUE']
>>> ConfUser()['BLUE']  # 期待获得一个异常表明删除成功
Traceback (most recent call last):
...
KeyError

>>> del ConfUser().WHITE
>>> ConfUser().WHITE  # 期待获得一个异常表明删除成功
Traceback (most recent call last):
...
AttributeError

注意使用不同方法的访问不存在的配置获得的异常并不一致

此外删除只读属性并不需要其他额外的操作

>>> del ConfUser()['RED']
>>> ConfUser()['RED']  # 期待获得一个异常表明删除成功
Traceback (most recent call last):
...
KeyError

类型检测
""""""""""""

假如我们来添加一个不一样的配置

>>> ConfUser()['Skyrim'] = 'Dragonborn'
Traceback (most recent call last):
...
TypeError

哦不，我们未能阻挡奥杜因的袭击！

原因在于我们在定义配置类时添加的两条只读配置，仔细观察可以发现，它们都是
`int` 类型的，因此配置类默认开启了类型检测：仅允许 `int` 类型的配置被存入。

可用使用如下的方法获取当前的类型检测参数

>>> ConfUser().get_types()
<class 'int'>

当然修改它也很容易

>>> ConfUser().set_types(str)
>>> ConfUser().get_types()
<class 'str'>

再试一试

>>> ConfUser()['Skyrim'] = 'Dragonborn'
>>> ConfUser()['Skyrim']
'Dragonborn'

Good，我们再一次拯救了天际。

假如需要关闭类型检测，可以将其设置为 `None`，或者初始化时设置不同类型的只读\
配置，以及定义一个空的配置类。

有趣的输出重载
"""""""""""""""

让我们定义一个有意思的配置类

>>> class ConfSP(conf.Conf):
...     NUM = (1, 2, 3)
...     def get(self, key):
...         return sum(super().get(key))

然后让我们访问一下 `NUM` 属性

>>> ConfSP().NUM
6

天哪，与定义的并不一致！

原因在于我们在定义配置类时提供了自定义的 `get` 方法，该方法默认原样返回 `key` 的值，\
但是我们再次基础上进行了累加，因此返回的便是 `NUM` 经过求和后的结果。

重载 `get` 方法允许每一次读取配置时重新计算一遍配置的值，当你的配置需要根据某些内容动态改变\
时，这将是一个便捷的方法。

.. note::
    重载后配置类的输入和输出将不同步，输入的是一个元组，输出的确是一个整数，在某些时候可能会\
    令人容易混肴，因此请务必小心使用，并多加注明。

配置类的定义
""""""""""""

配置类使用\ **类属性**\ 来储存每一条配置，并在内部使用字典来追踪配置的内容，该类是线程安全的。

.. autoclass:: core.base.conf.Conf
    :members:

一个为空的配置类的布尔值为 False

>>> class ConfNull(conf.Conf):
...     pass

>>> bool(ConfNull())
False

并且

>>> ConfNull()['NotNull'] = 1
>>> bool(ConfNull())
True

此外配置类的 `dump` 和 `load` 方法定义了如何序列化和反序列化配置，这通常由本模块定义的序列化函数\
负责操作，因此无需做额外的操作。

数据类的定义
""""""""""""

实际上配置类仅负责实现了容器操作，迭代操作等用于交互的功能；至于数据的只读属性，类型检测等均\
委托至了数据类，配置类仅记录了配置的原始数据\ [#]_\ 以及其对应的数据类。

数据类本质上是一个描述器\ [#]_\ ，其 `__get__` 方法被委托至对应配置类的 `get` 方法中。

.. [#] 该部分内容储存在配置类 get_data 返回的字典中
.. [#] 这也是为什么配置实际上储存在类属性而不是实例属性中，直接打印实例的 __dict__ 属性是无法查到其拥有的配置的

.. autoclass:: core.base.conf.Data
    :members:
    :special-members: __init__

.. warning::
    数据类是一个功能实现，随时有可能发生改变，不推荐在其他地方使用它。

.. seealso::
    `描述器 <https://docs.python.org/zh-cn/3/reference/datamodel.html#implementing-descriptors>`__\
    是 Python 提供的一个强大的功能，可以看看\ `这里 <https://docs.python.org/zh-cn/3/howto/descriptor.html>`__\
    了解如何使用它。

和枚举类的不同之处
""""""""""""""""""""

本模块使用了两种不同的配置，因此尽可能的希望两种配置均有着完全相同的接口。\
虽然配置类尽量模仿了枚举的行为，但是仍有些许不同，列举如下：

枚举直接调用类

>>> class Enum(enum.Enum):
...     RED = 1
>>> Enum.RED.value
1

而配置类需要使用其的实例

>>> class ConfDiff(conf.Conf):
...     RED = 1
>>> ConfDiff().RED
1

幸运的是，你可以使用一个变量来模仿枚举类的行为

>>> Conf = ConfDiff()
>>> Conf.RED
1

.. important::
    该行为可能会进行修改，但是不要期待可以在短时间内得到改进

此外由上式可以看出，枚举的属性获得的是枚举成员，而配置类直接返回配置的值，即

>>> Enum.RED.value  # 注意这里的 value
1
>>> Conf.RED
1

.. note::
    这是配置类与枚举类在使用时最为容易混肴的地方，请务必多加注意

并且尝试进行迭代也会得到不同的内容，枚举会返回枚举成员的名称

>>> for value in Enum:
...     print(value)
Enum.RED

而配置类会返回配置的值

>>> for value in Conf:
...     print(value)
1

.. note::
    这是故意这么设计的，因为在使用中配置的值更为重要，而配置的名称往往并不需要额外\
    被注意。

.. note::
    此外，枚举中对枚举值的重复的严格性在配置类中也被忽略了，因为配置的值对此并无特别的\
    要求，故也一并移除了自动设定的值、比较运算的支持。

常用配置
----------

在使用中，往往我们并不需要自己创建一个配置类，因此本模块内定义了许多配置以供全局调用。

不可变的配置 (全局常量)
^^^^^^^^^^^^^^^^^^^^^^^^

不可变的配置使用枚举定义，这是在全局范围内可用的\ **只读配置**。

.. autoclass:: core.base.conf.Project
    :members:

-----

.. autoclass:: core.base.conf.Version
    :members:

-----

.. autoclass:: core.base.conf.BuiltinPlugins
    :members:

-----

.. autoclass:: core.base.conf.Path
    :members:
    :undoc-members:

可变的配置 (全局变量)
^^^^^^^^^^^^^^^^^^^^^^^

可变的配置使用配置类定义，这是在全局范围内可用的\ **可写配置**。

.. autoclass:: core.base.conf.Dump
    :members:

.. autoclass:: core.base.conf._Dump
    :members:

-----

.. autoclass:: core.base.conf.RunInfo
    :members:

.. autoclass:: core.base.conf._RunInfo
    :members:

.. note::
    `ADDRESS` 配置默认指向软件的根目录，ADM在设计上考虑到了便携性，所有文件夹均\
    参考该配置读写，因此修改后便可以重定向文件夹的位置。

-----

.. autoclass:: core.base.conf.Folder
    :members:

.. autoclass:: core.base.conf._Folder
    :members:

.. note::
    该配置类定义的配置涵盖了本项目所有使用到的文件夹的位置，一个更为具体的说明如下，以供\
    开发者以及插件作者参考。

    + **核心部分资源文件夹**:
        储存核心部分以及全局需要的资源文件，例如图标等，其他部分所需的内容不储存于此

        **不要删除该文件夹**

    + **日志文件夹**:
        储存项目的日志文件，删除后无影响，但会丢失所有的日志文件

    + **插件文件夹**:
        项目所有的插件均储存于此，删除后丢失所有的插件

    + **用户配置文件夹**:
        储存项目的配置，缓存等自定义的内容，**删除后丢失所有的自定义内容**

    + **备份文件夹**:
        位于用户配置文件夹内，储存所有的备份内容

    + **缓存文件夹**:
        位于用户配置文件夹内，用于储存缓存，可以在多次运行之间被保留和读取，\
        用于跨运行保留数据，但是又不需要长期保存

    + **配置文件夹**:
        位于用户配置文件夹内，储存用户的配置文件，删除后会生成新的默认配置，\
        用于自定义软件功能

        插件提供了一个更为强大的功能，但是修改配置文件更为简单和便捷

    + **数据库文件夹**:
        位于用户配置文件夹内，用于储存数据库文件，通常是运行过程中需要长期储存的,\
        但不希望被用户修改的内容

    + **临时文件夹**:
        位于用户配置文件夹内，储存这本次运行中临时需要的文件，不应当期待其中的内容一定\
        会一直存在

        **注意在每次运行和退出前，该文件夹均会被清空**

    + **模板文件夹**:
        储存模板文件，目前是Web的占位符

.. todo::
    为上下文添加 seealso

-----

.. autoclass:: core.base.conf.DBToINIAddress
    :members:

.. autoclass:: core.base.conf._DBToINIAddress
    :members:

.. note::
    以上的两个配置类 :class:`core.base.conf.Folder` 和 :class:`core.base.conf.DBToINIAddress`
    内的配置均为文件地址，因此返回的类型为 **str**，但是储存的类型却为 **tuple**！

    这么设计的缘由是ADM设计时考虑到了便携性，将根目录储存在 `RunInfo.ADDRESS` 内，\
    因此其他文件地址仅需储存相对地址即可，并且重置输出允许在运行时通过修改 `ADDRESS`
    实现以上配置类内的文件地址的重定向。

    但假若有时只需要对其中一个配置进行重定向修改，同时保证其他配置不变，可以通过传入绝对地址\
    来实现，可以看看 :func:`os.path.join` 了解原因，同时请务必再次确认写入的是一个 **tuple**！

-----

.. autoclass:: core.base.conf.INIConnect
    :members:

.. autoclass:: core.base.conf._INIConnect
    :members:

-----

.. autoclass:: core.base.conf.DBConnect
    :members:

.. autoclass:: core.base.conf._DBConnect
    :members:

-----

.. autoclass:: core.base.conf.LogName
    :members:

.. autoclass:: core.base.conf._LogName
    :members:

缓存配置
----------

写好的配置，我们往往希望可以在下次运行时可以直接使用，无需再额外重新\
调整一遍，这部分便提供了一个可用的序列化 (缓存) 操作。

执行序列化或反序列化的最简单的方法是调用如下的两个函数

.. autofunction:: core.base.conf.dump

.. autofunction:: core.base.conf.load

以上两个函数默认会缓存本模块中的所有使用配置类定义的全局配置，如果需要\
添加额外的内容，向 :class:`core.base.conf.Dump` 配置类中写入该配置实例\
即可。
