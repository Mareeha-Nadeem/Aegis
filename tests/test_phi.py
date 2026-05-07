from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

tokenizer = AutoTokenizer.from_pretrained("microsoft/phi-2")
model = AutoModelForCausalLM.from_pretrained(
    "microsoft/phi-2",
    torch_dtype=torch.float16,  # half precision soo uses less RAM
    device_map="cpu",
    low_cpu_mem_usage=True
)
print("Phi loaded successfully!")