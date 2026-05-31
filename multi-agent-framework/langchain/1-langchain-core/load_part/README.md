# langchain_core load part

这里定义了 langchain 的核心行为之一，即 Serializable 它实现了langchain对象的在模型输入输出的序列化和反序列化，尤其重要的一点

并且给出了大量的解释，为何要这么设计，序列化和反序列化时的所要注意的问题



## Reviver
和 Serializable 是一对，负责 lc 对象的恢复，涉及到 langchain 运行周期的各个方面

## Serializable

### mapping
这里规定了所有的可序列化/反序列化相关规定的  langchain 命名空间
兼容了一堆老包,  比如说那个 serializable mapping，它会把以前的 langchain.schema.messages.ai_messages 映射到 langchain.core.messages.ai_messages。而且这也是现在的包里边的结构，它已经不是以前那样了
然后剩下的基本上都是这样的 repeat 操作了


### validators

我看了一下，大概就是针对亚马逊单独适配的一个东西，我估计之前发生过什么问题
这个详细的定义了lc的序列化和反序列化的核心内容,在 LangChain 里面，基本上所有的 Runnable 对象都会有这些属性。也就是说，在 Runnable 的定义中，LangChain 不只是分了三层，而是分了四五层这样的继承,我只觉得很繁琐吧


### Serializable Details
这里我会详细说一下 LangChain 的序列化和反序列化的一个行为


比如 Serializable，其实可以看到它那个基础的属性有

Is langchain serializable （is_lc_serializable）
这一属性就跟我们之前看到的 langchain 里面规定的序列化和反序列化的规定对应上了。

langchain 官方提到，对于其基础的 langchain-core 包，它可以完全信任地将你提供的 JSON 串还原成 langchain 所专属的一个类，从而方便地使用。

但对于一些外来的、不属于其核心包的内容，它就不会进行反反序列化。官方给出的理由是可能会发生网络连接异常等问题，但其实最主要的核心考量还是为了防投毒。


Get LangChain namespaces (get_lc_namespace)
这个方法是序列化和反序列化的一个钩子。

当你序列化的时候，会用它来生成包所在的路径并作为它的 ID；而在反序列化的时候，也会通过这个 Class Path 去将它还原为某类的一个实例。



@property
def lc_secrets(self) -> dict[str, str]:
LC_SECRET 其实你可以看到，它就是 LangChain 的 BaseModel 里面代指 API Key 的东西。

当你看到 OpenAI 的这一部分，不管是写成 openai_api_key 还是别的什么，反正指的就是这些东西，加载的就是这些玩意儿。在初始化的时候，你会往里填，这个其实没什么好说的


@property
def lc_attributes(self) -> dict:
然后 lc_attributes 其实是一些其他的参数，就是一些序列化的时候需要用的参数。也没什么好说的，不是什么重要的东西

  @classmethod
    def lc_id(cls) -> list[str]:这玩意儿其实跟 generate_namespace 差不多，它其实是生成类的一个标识


to_json 
然后这里边可以说的就是一个 to_json 的方法，它那个 signature 写的是：
1. Serialize the object to JSON
2. Raise value if class has deprecated attributes
3. Or return a JSON-realizable object
4. Or serialize non-serializable object



然后他那个叫 _is_field_useful ，就是 to_json 序列化的时候它序列化的时候会有一个判断，即 field is useful。他原文写的是：checking the field is useful as a constructor argument。

也就是说，它是作为序列化的时候，判断这个东西是否有用。因为有的字段其实是没用的



 to_json 他去序列化的时候，有一个比较值得注意的东西：他会从整个继承树去进行 secret key 的挂载和查找
 因为 LC 的 namespace 以及 LC 的 Serializable，这两个参数已经 deprecated 了




它基本上是这样一个逻辑：从 MRO 拿到继承树上的所有内容，然后从底往上开始排，获取到定义的 secret key，再继续整合到 LangChain 的 lc_Kwargs 里面。







我一开始想的时候，就在思考他序列化和反序列化的时候，为什么没有直接把 secret key 放到类属性里面一起进行序列化。

后来看了 Revive 的实现，发现他那边又专门定义了一个字段，叫做 secrets_from_env。他的解释是：
"Only include specific secrets that serializable objects require. If a secret is not found in the map, it will be loaded from environment."

因为你在处理的时候，一般就是 secret_from_env。对于 false 的话，只传 secret_mac 嘛，然后这样的话你就可以避免恶意地去加载