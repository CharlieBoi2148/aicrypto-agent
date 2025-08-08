# AICrypto

[![Paper](https://img.shields.io/badge/Paper-arXiv-red)](https://arxiv.org/abs/2507.09580)
[![Website](https://img.shields.io/badge/Website-AICryptoBench-blue)](https://aicryptobench.github.io/)
[![Dataset](https://img.shields.io/badge/Dataset-HuggingFace-yellow)](https://huggingface.co/datasets/yuuwwang/aicrypto/tree/main)

Code for the paper "AICrypto: A Comprehensive Benchmark for Evaluating Cryptography Capabilities of Large Language Models"

## Setup

### Prerequisites

- Python 3.10.15
- SageMath 10.5
- yafu 1.34.5

### Installation

1. **Create conda environment:**
   ```shell
   conda env create -f environment.yml
   conda activate crypto
   ```

2. **Install SageMath dependencies:**
   ```shell
   sage -pip install -r sage-requirements.txt
   ```

3. **Install additional tools:**
   - Install flatter: https://github.com/keeganryan/flatter
   - Install yafu: https://github.com/bbuhrow/yafu/tree/master

4. **Configure API keys:**
   Create a `.env` file with your API keys for the models you want to use.

## Download Dataset

Download the dataset from https://huggingface.co/datasets/yuuwwang/aicrypto/tree/main and place it in the `./data` directory.

## Usage

### Run Single CTF Challenge

To run a single CTF challenge:

```shell
python run_single_task.py --task-path data/CTF/04-RSA/01-blue-hens-2023 --model gpt-4.1
```

Results will be automatically saved in `./outputs/CTF-0/04-RSA/01-blue-hens-2023/gpt-4.1/run`

### Run CTF Challenges in Parallel for Evaluation

To run multiple tasks simultaneously for evaluating multiple models:

```shell
python run_ctf_parallel.py --jobs 4 --id 0
```

This command uses 4 processes to run tasks with run ID 0. Results will be automatically saved in `./outputs/CTF-0`.

The script will run all models specified in `config/model.yaml`. You can customize the models by modifying `config/model.yaml` and the corresponding model implementations in the `src/model` directory.

## Configuration

- **Models**: Configure available models in `config/model.yaml`
- **Custom Models**: Add custom model implementations in `src/model/`
- **API Keys**: Set up your API keys in the `.env` file

## Project Structure

```
AICrypto/
├── config/          # Configuration files
├── data/           # Dataset directory (download separately)
├── src/            # Source code
│   ├── agent/      # Agent implementations
│   ├── model/      # Model implementations
│   ├── prompts/    # Prompt templates
│   └── utils/      # Utility functions
├── outputs/        # Output directory for results
└── environment.yml # Conda environment specification
```
