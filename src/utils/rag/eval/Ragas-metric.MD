> 本文由 [简悦 SimpRead](http://ksria.com/simpread/) 转码， 原文地址 [docs.ragas.io](https://docs.ragas.io/en/latest/howtos/customizations/metrics/_write_your_own_metric/#custom-metrics)

> While Ragas has a number of built-in metrics, you may find yourself needing to create a custom metric......

While Ragas has [a number of built-in metrics](https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/), you may find yourself needing to create a custom metric for your use case. This guide will help you do just that.

For the sake of this tutorial, let's assume we want to build a custom metric that measures the hallucinations in a LLM application. While we do have a built-in metric called [Faithfulness](https://docs.ragas.io/en/latest/references/metrics/#ragas.metrics.Faithfulness) which is similar but not exactly the same. `Faithfulness` measures the factual consistency of the generated answer against the given context while `Hallucinations` measures the presence of hallucinations in the generated answer.

before we start, lets load the dataset and define the llm

```
# dataset
from datasets import load_dataset
from ragas import EvaluationDataset

amnesty_qa = load_dataset("explodinggradients/amnesty_qa", "english_v3")
eval_dataset = EvaluationDataset.from_hf_dataset(amnesty_qa["eval"])



```

```
EvaluationDataset(features=['user_input', 'retrieved_contexts', 'response', 'reference'], len=20)



```

Install the langchain-openai package

```
pip install langchain-openai



```

Ensure you have your OpenAI key ready and available in your environment.

```
import os
os.environ["OPENAI_API_KEY"] = "your-openai-key"



```

Wrap the LLMs in `LangchainLLMWrapper` so that it can be used with ragas.

```
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o"))
evaluator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())



```

Install the langchain-aws package

```
pip install langchain-aws



```

Then you have to set your AWS credentials and configurations

```
config = {
    "credentials_profile_name": "your-profile-name",  # E.g "default"
    "region_name": "your-region-name",  # E.g. "us-east-1"
    "llm": "your-llm-model-id",  # E.g "anthropic.claude-3-5-sonnet-20241022-v2:0"
    "embeddings": "your-embedding-model-id",  # E.g "amazon.titan-embed-text-v2:0"
    "temperature": 0.4,
}



```

Define your LLMs and wrap them in `LangchainLLMWrapper` so that it can be used with ragas.

```
from langchain_aws import ChatBedrockConverse
from langchain_aws import BedrockEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

evaluator_llm = LangchainLLMWrapper(ChatBedrockConverse(
    credentials_profile_name=config["credentials_profile_name"],
    region_name=config["region_name"],
    base_url=f"https://bedrock-runtime.{config['region_name']}.amazonaws.com",
    model=config["llm"],
    temperature=config["temperature"],
))
evaluator_embeddings = LangchainEmbeddingsWrapper(BedrockEmbeddings(
    credentials_profile_name=config["credentials_profile_name"],
    region_name=config["region_name"],
    model_id=config["embeddings"],
))



```

If you want more information on how to use other AWS services, please refer to the [langchain-aws](https://python.langchain.com/docs/integrations/providers/aws/) documentation.

Install the langchain-openai package

```
pip install langchain-openai



```

Ensure you have your Azure OpenAI key ready and available in your environment.

```
import os
os.environ["AZURE_OPENAI_API_KEY"] = "your-azure-openai-key"

# other configuration
azure_config = {
    "base_url": "",  # your endpoint
    "model_deployment": "",  # your model deployment name
    "model_name": "",  # your model name
    "embedding_deployment": "",  # your embedding deployment name
    "embedding_name": "",  # your embedding name
}



```

Define your LLMs and wrap them in `LangchainLLMWrapper` so that it can be used with ragas.

```
from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
evaluator_llm = LangchainLLMWrapper(AzureChatOpenAI(
    openai_api_version="2023-05-15",
    azure_endpoint=azure_config["base_url"],
    azure_deployment=azure_config["model_deployment"],
    model=azure_config["model_name"],
    validate_base_url=False,
))

# init the embeddings for answer_relevancy, answer_correctness and answer_similarity
evaluator_embeddings = LangchainEmbeddingsWrapper(AzureOpenAIEmbeddings(
    openai_api_version="2023-05-15",
    azure_endpoint=azure_config["base_url"],
    azure_deployment=azure_config["embedding_deployment"],
    model=azure_config["embedding_name"],
))



```

If you want more information on how to use other Azure services, please refer to the [langchain-azure](https://python.langchain.com/docs/integrations/chat/azure_chat_openai/) documentation.

If you are using a different LLM provider and using Langchain to interact with it, you can wrap your LLM in `LangchainLLMWrapper` so that it can be used with ragas.

```
from ragas.llms import LangchainLLMWrapper
evaluator_llm = LangchainLLMWrapper(your_llm_instance)



```

For a more detailed guide, checkout [the guide on customizing models](https://docs.ragas.io/en/latest/howtos/customizations/howtos/customizations/customize_models.md).

If you using LlamaIndex, you can use the `LlamaIndexLLMWrapper` to wrap your LLM so that it can be used with ragas.

```
from ragas.llms import LlamaIndexLLMWrapper
evaluator_llm = LlamaIndexLLMWrapper(your_llm_instance)



```

For more information on how to use LlamaIndex, please refer to the [LlamaIndex Integration guide](https://docs.ragas.io/en/latest/howtos/customizations/howtos/integrations/_llamaindex.md).

If your still not able use Ragas with your favorite LLM provider, please let us know by by commenting on this [issue](https://github.com/explodinggradients/ragas/issues/1617) and we'll add support for it 🙂.

```
from ragas.llms import llm_factory

evaluator_llm = llm_factory("gpt-4o")



```

Aspect Critic - Simple Criteria Scoring
---------------------------------------

[Aspect Critic](https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/aspect_critic/) that outputs a binary score for `definition` you provide. A simple pass/fail metric can be bring clarity and focus to what you are trying to measure and is a better alocation of effort than building a more complex metric from scratch, especially when starting out.

Check out these resources to learn more about the effectiveness of having a simple pass/fail metric:

*   [Hamel's Blog on Creating LLM-as-a-Judge that drives Business Result](https://hamel.dev/blog/posts/llm-judge/#step-3-direct-the-domain-expert-to-make-passfail-judgments-with-critiques)
*   [Eugene's Blog on AlignEval](https://eugeneyan.com/writing/aligneval/#labeling-mode-look-at-the-data)

Now let's create a simple pass/fail metric to measure the hallucinations in the dataset with Ragas.

```
from ragas.metrics import AspectCritic

# you can init the metric with the evaluator llm
hallucinations_binary = AspectCritic(
    ,
    definition="Did the model hallucinate or add any information that was not present in the retrieved context?",
    llm=evaluator_llm,
)

await hallucinations_binary.single_turn_ascore(eval_dataset[0])



```

Output

Domain Specific Metrics or Rubric based Metrics
-----------------------------------------------

Here we will build a rubric based metric that evaluates the data on a scale of 1 to 5 based on the rubric we provide. You can read more about the rubric based metrics [here](https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/rubrics_based/)

For our example of building a hallucination metric, we will use the following rubric:

```
rubric = {
    "score1_description": "There is no hallucination in the response. All the information in the response is present in the retrieved context.",
    "score2_description": "There are no factual statements that are not present in the retrieved context but the response is not fully accurate and lacks important details.",
    "score3_description": "There are many factual statements that are not present in the retrieved context.",
    "score4_description": "The response contains some factual errors and lacks important details.",
    "score5_description": "The model adds new information and statements that contradict the retrieved context.",
}



```

Now lets init the metric with the rubric and evaluator llm and evaluate the dataset.

```
from ragas.metrics import RubricsScore

hallucinations_rubric = RubricsScore(
    , llm=evaluator_llm, rubrics=rubric
)

await hallucinations_rubric.single_turn_ascore(eval_dataset[0])



```

Output

Custom Metrics
--------------

If your use case is not covered by those two, you can build a custom metric by subclassing the base `Metric` class in Ragas but before that you have to ask yourself the following questions:

1.  Am I trying to build a single turn or multi turn metric? If yes, subclassing the `Metric` class along with either [SingleTurnMetric](https://docs.ragas.io/en/latest/references/metrics/#ragas.metrics.base.SingleTurnMetric) or [MultiTurnMetric](https://docs.ragas.io/en/latest/references/metrics/#ragas.metrics.base.MultiTurnMetric) depending on if you are evaluating single turn or multi turn interactions.
    
2.  Do I need to use LLMs to evaluate my metric? If yes, instead of subclassing the [Metric](https://docs.ragas.io/en/latest/references/metrics/#ragas.metrics.base.Metric) class, subclassing the [MetricWithLLM](https://docs.ragas.io/en/latest/references/metrics/#ragas.metrics.base.MetricWithLLM) class.
    
3.  Do I need to use embeddings to evaluate my metric? If yes, instead of subclassing the [Metric](https://docs.ragas.io/en/latest/references/metrics/#ragas.metrics.base.Metric) class, subclassing the [MetricWithEmbeddings][ragas.metrics.base.MetricWithEmbeddings] class.
    
4.  Do I need to use both LLM and Embeddings to evaluate my metric? If yes, subclass both the [MetricWithLLM](https://docs.ragas.io/en/latest/references/metrics/#ragas.metrics.base.MetricWithLLM) and [MetricWithEmbeddings][ragas.metrics.base.MetricWithEmbeddings] classes.
    

For our example, we need to to use LLMs to evaluate our metric so we will subclass the [MetricWithLLM](https://docs.ragas.io/en/latest/references/metrics/#ragas.metrics.base.MetricWithLLM) class and we are working for only single turn interactions for now so we will subclass the [SingleTurnMetric](https://docs.ragas.io/en/latest/references/metrics/#ragas.metrics.base.SingleTurnMetric) class.

As for the implementation, we will use the [Faithfulness](https://docs.ragas.io/en/latest/references/metrics/#ragas.metrics.Faithfulness) metric to evaluate our metric to measure the hallucinations with the formula

```
# we are going to create a dataclass that subclasses `MetricWithLLM` and `SingleTurnMetric`
from dataclasses import dataclass, field

# import the base classes
from ragas.metrics.base import MetricWithLLM, SingleTurnMetric, MetricType
from ragas.metrics import Faithfulness

# import types
import typing as t
from ragas.callbacks import Callbacks
from ragas.dataset_schema import SingleTurnSample


@dataclass
class HallucinationsMetric(MetricWithLLM, SingleTurnMetric):
    # name of the metric
    name: str = "hallucinations_metric"
    # we need to define the required columns for the metric
    _required_columns: t.Dict[MetricType, t.Set[str]] = field(
        default_factory=lambda: {
            MetricType.SINGLE_TURN: {"user_input", "response", "retrieved_contexts"}
        }
    )

    def __post_init__(self):
        # init the faithfulness metric
        self.faithfulness_metric = Faithfulness(llm=self.llm)

    async def _single_turn_ascore(
        self, sample: SingleTurnSample, callbacks: Callbacks
    ) -> float:
        faithfulness_score = await self.faithfulness_metric.single_turn_ascore(
            sample, callbacks
        )
        return 1 - faithfulness_score



```

```
hallucinations_metric = HallucinationsMetric(llm=evaluator_llm)

await hallucinations_metric.single_turn_ascore(eval_dataset[0])



```

Output

Now let's evaluate the entire dataset with the metrics we have created.

```
from ragas import evaluate

results = evaluate(
    eval_dataset,
    metrics=[hallucinations_metric, hallucinations_rubric, hallucinations_binary],
)



```

{'hallucinations_metric': 0.5932, 'hallucinations_rubric': 3.1500, 'hallucinations_binary': 0.1000}

```
```python
results_df = results.to_pandas()
results_df.head()



```

Output

<table><thead><tr><th></th><th>user_input</th><th>retrieved_contexts</th><th>response</th><th>reference</th><th>hallucinations_metric</th><th>hallucinations_rubric</th><th>hallucinations_binary</th></tr></thead><tbody><tr><th>0</th><td>What are the global implications of the USA Su...</td><td>[- In 2022, the USA Supreme Court handed down ...</td><td>The global implications of the USA Supreme Cou...</td><td>The global implications of the USA Supreme Cou...</td><td>0.423077</td><td>3</td><td>0</td></tr><tr><th>1</th><td>Which companies are the main contributors to G...</td><td>[In recent years, there has been increasing pr...</td><td>According to the Carbon Majors database, the m...</td><td>According to the Carbon Majors database, the m...</td><td>0.862069</td><td>3</td><td>0</td></tr><tr><th>2</th><td>Which private companies in the Americas are th...</td><td>[The issue of greenhouse gas emissions has bec...</td><td>According to the Carbon Majors database, the l...</td><td>The largest private companies in the Americas ...</td><td>1.000000</td><td>3</td><td>0</td></tr><tr><th>3</th><td>What action did Amnesty International urge its...</td><td>[In the case of the Ogoni 9, Amnesty Internati...</td><td>Amnesty International urged its supporters to ...</td><td>Amnesty International urged its supporters to ...</td><td>0.400000</td><td>3</td><td>0</td></tr><tr><th>4</th><td>What are the recommendations made by Amnesty I...</td><td>[In recent years, Amnesty International has fo...</td><td>Amnesty International made several recommendat...</td><td>The recommendations made by Amnesty Internatio...</td><td>0.952381</td><td>3</td><td>0</td></tr></tbody></table>

If you want to learn more about how to build custom metrics, you can read the [Custom Metrics Advanced](https://docs.ragas.io/en/latest/howtos/customizations/metrics/_write_your_own_metric_advanced/) guide.