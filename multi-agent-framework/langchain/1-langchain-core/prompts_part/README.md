"""    现在来看一下 Prompt 的介绍：

1. Prompt 是模型的输入 (Prompt is input of the model)
2. Prompt 是由多个组件和 Prompt Value 构成的开放结构 (Prompt is open construct for multiple components and prompt values)
3. Prompt 的类及其函数是为了让构建和处理 Prompt 变得更加简单 (Prompt classes and functions make construction and working with prompts easy)

大意上就是说，Prompt 这个类以及它的一些函数，就是为了让处理 Prompt 的过程更加简单。


现在来看一下 Prompt 大类的设计部分。目前来说，它还是集中了刚才以下的一些东西，但本质上我觉得很多内容是没有用的。

我来说一下为什么没有用啊。

因为在大体上看来，比如 Few-shot Prompt，本质上你是在 Prompt 里面提供一些 example。但为什么我要对此单独设计一个类呢？我觉得是没有必要的。

 大体上目前来说，集成了 AI 的：
  1. Message
  2. Chat Message Prompt
  3. Chat Prompt Template
  4. Human Message Prompt
  5. Message Placeholder
  6. System Message Prompt

主要是集中在一些这样的场景，比如说是 Chat、Dict、Few-shot 这种场景下，集成了很多个 Prompt 类型。


拿 AI Message 来说的话，你可以看到它集成了：
1. Tool Call
2. Invalid Tool Call
3. Usage Metadata

这些东西是能够去获取到 AI 执行的一些状态最主要的就是 message placeholder，至于 prompt template 甚至都不重要（这句话可以删掉了），还是  message placeholder 比较重要。

我感觉更多地应该是去学到，它这个 prompt 在整个 agent loop 的环节下，到底会产生一个什么样的作用。