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

  大多数来说，我觉得这些都是一些重复的东西。甚至包括以前的 Dict Prompt Template 和 Few Shots Prompt Template，本质上这些东西在很多功能上都具有很大程度的交叉和重叠，我觉得这个设计上来说是冗余的