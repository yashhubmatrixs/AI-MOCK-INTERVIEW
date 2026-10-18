# Deep Learning and Generative AI

## Neural network basics
An artificial neuron computes a weighted sum of its inputs plus a bias and passes it through an activation function. A network stacks layers of neurons (input, hidden, output). Training adjusts the weights to minimise a loss function.

## Activation functions
ReLU outputs max(0, x); it is the usual default for hidden layers because it is cheap and reduces vanishing gradients, but neurons can "die" if they only receive negative inputs. Sigmoid squashes values to 0 to 1 (used for binary outputs) and suffers from vanishing gradients. Tanh outputs -1 to 1. Softmax turns a vector of scores into probabilities that sum to 1 for multi-class output.

## Backpropagation
Backpropagation computes the gradient of the loss with respect to every weight by applying the chain rule from the output layer back to the input layer; an optimiser such as SGD or Adam then uses those gradients to update the weights.

## Vanishing and exploding gradients
In deep networks gradients can shrink towards zero (vanishing) or grow very large (exploding) as they are propagated backwards, which stalls or destabilises training. Remedies: ReLU-type activations, careful weight initialisation, batch normalization, residual (skip) connections, gradient clipping, and LSTM or GRU cells for sequences.

## Dropout and batch normalization
Dropout randomly switches off a fraction of neurons during training so the network cannot rely on any single neuron, which reduces overfitting. Batch normalization normalises each layer's inputs over the mini-batch, which stabilises and speeds up training.

## Optimizers
SGD updates weights using the gradient of a mini-batch; momentum smooths the updates. Adam combines momentum with per-parameter adaptive learning rates and is a common default choice.

## Epoch, batch and iteration
An epoch is one full pass over the training data. The batch size is the number of samples used per weight update. One iteration is one update, so iterations per epoch = number of samples / batch size.

## Convolutional neural networks (CNN)
A CNN uses convolution layers whose small filters slide over an image to detect local patterns (edges, textures, shapes), pooling layers that shrink the feature maps, and fully connected layers for the final prediction. Weight sharing makes them efficient for image data.

## RNN and LSTM
A recurrent neural network processes sequences by passing a hidden state from one step to the next. Plain RNNs struggle with long-range dependencies because of vanishing gradients; LSTM cells add input, forget and output gates (and GRU a simpler gating) to keep information over long spans.

## Transformers and attention
A transformer uses self-attention so that every token in a sequence can weigh its relevance to every other token, and processes all tokens in parallel (with positional encodings to keep word order). It was introduced in the 2017 paper "Attention Is All You Need" and underlies modern large language models (LLMs).

## Transfer learning and fine-tuning
Transfer learning reuses a model pre-trained on a large dataset and adapts it to a new task. Fine-tuning continues training the pre-trained weights on task-specific data, which needs far less data and compute than training from scratch.

## LLM hallucination
Hallucination is when a language model produces fluent but false or unsupported content. It happens because an LLM predicts likely next tokens from patterns in its training data rather than looking facts up or checking them. Ways to reduce it: ground answers in retrieved documents (RAG), lower the temperature, instruct the model to say when it does not know, require citations, and verify outputs.

## Retrieval-Augmented Generation (RAG)
RAG retrieves relevant passages from an external knowledge base at question time and puts them in the prompt so the model answers from that evidence instead of from memory alone. Pipeline: split documents into chunks, index them (keyword search such as BM25 and/or embeddings in a vector store), retrieve the top matches for the query, then generate an answer that cites them. RAG gives access to private or up-to-date information without retraining and reduces, but does not eliminate, hallucination.

## Embeddings and vector search
An embedding is a dense numeric vector that represents the meaning of a piece of text, so semantically similar texts have nearby vectors. Similarity is usually measured with cosine similarity. Vector databases and libraries such as FAISS and Chroma store embeddings and find nearest neighbours quickly.

## Chunking in RAG
Documents are split into chunks before indexing. Small chunks give precise matches but can lose context; large chunks keep context but dilute relevance and use more of the model's context window. Typical chunks are a few hundred tokens, split along natural boundaries such as headings and paragraphs.

## RAG vs fine-tuning
Use RAG when the model needs facts that are private, large or change often, because you update the knowledge base instead of retraining, and answers can cite sources. Use fine-tuning to change the model's style, format or behaviour on a task. The two can be combined.

## Prompt engineering basics
Zero-shot prompting gives only an instruction; few-shot prompting adds worked examples; chain-of-thought prompting asks the model to reason step by step. Clear roles, constraints and an explicit output format improve results. Temperature controls randomness: low values give more deterministic output, high values more varied output.

## Tokens and context window
LLMs read and write tokens, which are pieces of words. The context window is the maximum number of tokens (prompt plus reply) the model can handle at once; anything beyond it is cut off or must be summarised or retrieved selectively.
