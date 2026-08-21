lms server start

lms load openai/gpt-oss-20b \
  --gpu max \
  --context-length 8192 \
  --parallel 1 \
  --identifier openai/gpt-oss-20b \
  -y

lms load qwen/qwen3.5-9b \
  --gpu max \
  --context-length 8192 \
  --parallel 1 \
  --identifier qwen/qwen3.5-9b \
  -y

lms load deepseek/deepseek-r1-distill-qwen-14b \
  --gpu max \
  --context-length 8192 \
  --parallel 1 \
  --identifier deepseek/deepseek-r1-distill-qwen-14b \
  -y

lms unload <current-model>
