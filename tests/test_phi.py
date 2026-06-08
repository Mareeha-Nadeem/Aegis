<<<<<<< HEAD
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
=======
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from config import PHI_MODEL

has_cuda = torch.cuda.is_available()
device_map = "auto" if has_cuda else "cpu"
torch_dtype = torch.float16 if has_cuda else torch.float32

tokenizer = AutoTokenizer.from_pretrained(PHI_MODEL, use_fast=True)
model = AutoModelForCausalLM.from_pretrained(
    PHI_MODEL,
    torch_dtype=torch_dtype,
    device_map=device_map,
    low_cpu_mem_usage=True,
)

if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
    tokenizer.pad_token_id = tokenizer.eos_token_id

print(f"Model loaded successfully: {PHI_MODEL} | device_map={device_map}")
>>>>>>> 712ea001c4db72213d1f7679e9523872a5095070
