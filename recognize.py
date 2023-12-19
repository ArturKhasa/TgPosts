import asyncio

import torch
from transformers import AutoTokenizer, AutoModel

class Recognizer():
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained('cointegrated/rubert-tiny2')
        self.model = AutoModel.from_pretrained('cointegrated/rubert-tiny2')

    async def embed_bert_cls(self, texts):
        """
        :param text: list[str, ...]
        :return: torch.tensor[n, 312]
        """
        embs = []
        for text in texts:
            await asyncio.sleep(0)
            t = self.tokenizer(text, padding=True, truncation=True, return_tensors='pt')
            with torch.no_grad():
                model_output = self.model(**{k: v.to(self.model.device) for k, v in t.items()})
            embeddings = model_output.last_hidden_state[:, 0, :]
            embeddings = torch.nn.functional.normalize(embeddings)
            embs.extend(embeddings)


        return embs