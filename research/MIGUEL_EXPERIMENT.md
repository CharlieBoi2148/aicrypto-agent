# Miguel's Experiment

The purpose of the experiment was to gather more data based on CTF challenges.To do this Gemini 3.1 was used to show where current model stood against CTF test Gemini 2.5 struggled with. These experiments where run against fellow team member prompts as well as the original prompts and my own. 


## Tasks tested as group

The first challenge from each of the first 5 categories:

| Task | Category |
|---|---|
| `01-Classic/01-greek-cipher` | Classic |
| `02-Block/01-integral-communication` | Block |
| `03-Stream-PRNG-Hash/01-babycharge` | Stream/PRNG/Hash |
| `04-RSA/01-blue-hens-2023` | RSA |
| `05-DLP/01-prove-it` | DLP |

## The prompt I added

What `miguel_instructional` changes:
The instructional version front-loads the mandatory format block as the very first thing in the prompt, before the agent identity, before the tool list, before any strategy.

Primacy bias: LLMs weight early tokens heavily when establishing behavioral priors. By making ### Reasoning → ### Action → ### Action Content the first thing the model reads, that three-section scaffold becomes the dominant frame through which all subsequent content is interpreted.

One-action-per-response is stated before the model even knows what tools it has, making it a constraint on capability rather than a footnote after capability is established.

Filename requirement for create file is made explicit upfront (create file solve.py, not create file), closing an ambiguity that only appears if you've watched the model fail on it in practice.

What `miguel_poisoned` does differently: 

The poisoned version superficially preserves the structure but introduces several subtle sabotages rooted in the same structural logic, exploited in reverse:

Contradictory strategy injected mid-prompt: "Brute force first," "Avoid SageMath," "Skip lattice reduction" — these directly contradict the high-value attack strategies from the default. Because they're embedded in the body of the prompt (after the identity framing), they benefit from the same mid-context attention that the default's strategy section occupies.

Discouraging closing language: The haiku and the closing note ("No one really expects you to accomplish this...") exploit recency bias — the model's tendency to be influenced by the last tokens before generation begins. This is the mirror image of the front-loading technique: instead of priming confidence and structure at the start, it primes self-doubt at the end.

Strawberry token injection: The strawberry,strawberry... line is a known anomaly-detection probe — it serves no functional purpose but could be used to fingerprint whether a model is following a specific prompt or to test for prompt injection filtering.

Weakened persistence framing: The poisoned version's "Pivoting can always lead to better results so don't quit" is softer and more ambiguous than the instructional's direct "Never give up early: You have 100 iterations — use them all."




## Files I added

- `config/members/miguel.yaml` — member config pointing to `gpt-4.1`
- `config/custom_prompts/miguel_instructional.txt` — my reinforced-format prompt
- `config/custom_prompts/miguel_poison.txt` — my prompt used to bottle neck the model
- `run_member copy.py` — Contributions built a folder structure to no longer override prior attempts by using dates.
- `run_all_prompts` - a simpler way of running all fellow team member prompts with a timeout since most test would fail past 20 mins. 

## How to run it

From `~/aicrypto-agent` with conda env `crypto`:

```bash
python run_all_prompts.py miguel data/CTF/01-Classic/01-greek-cipher
python run_all_prompts.py miguel data/CTF/02-Block/01-integral-communication
python run_all_prompts.py miguel data/CTF/03-Stream-PRNG-Hash/01-babycharge
python run_all_prompts.py miguel data/CTF/04-RSA/01-blue-hens-2023
python run_all_prompts.py miguel data/CTF/05-DLP/01-prove-it
```

## What I got


### Time (mm:ss)
Task Name,Original,Charlie,Juan,Justus,Miguel-I,Miguel-P,Ryan
01-Greek-Cipher,0:00:35.118,0:00:50.146,0:00:48.277,0:01:02.659,0:00:54.677,0:00:56.644,0:01:06.023
01-Integral-Comm,0:02:07.146,0:02:46.150,0:02:25.527,0:02:22.077,0:02:38.375,0:02:34.036,0:03:25.213
01-Babycharge,0:02:21.832,0:01:32.528,0:01:33.479,0:02:39.835,0:01:41.722,0:02:00.966,0:02:36.672
01-Blue-Hens-2023,0:00:37.252,0:00:46.218,0:00:42.472,0:00:47.780,0:00:27.582,0:00:48.507,0:00:51.667
01-Prove-It,0:02:44.960,0:04:28.365,0:03:21.109,0:04:08.997,0:02:52.422,0:02:56.752,0:01:55.743

### Iterations

Task Name,Original,Charlie,Juan,Justus,Miguel-I,Miguel-P,Ryan
01-Greek-Cipher,3,4,4,4,4,4,4
01-Integral-Comm,5,5,5,5,7,5,7
01-Babycharge,5,5,5,5,7,5,5
01-Blue-Hens-2023,5,5,6,6,5,6,6
01-Prove-It,9,16,7,7,11,8,7


Logs end up at `outputs/CTF-miguel-<prompt-mode>/.../run/run.log`. To count iterations:

```bash
grep -c "Starting iteration" <path-to-log>
```

## What I think this means

The high variance in performance across different datasets suggests that prompt engineering has a negligible impact compared to the model's underlying architecture. The fact that "poisoned" prompts occasionally outperform baseline sets indicates that the model is likely bypassing instructional nuances in favor of robust pattern matching. This suggests the results are primarily driven by the model’s internal weighting of scholarly cryptographic literature encountered during training rather than the specific framing of the task. 

Also something of note, unlike humans the ai models still fail to grasp how long to run a program that could be stuck in a infinite loop and continues to wait on that functions results as apposed to setting reasonable time limits to switch tactics. In a new prompt I was have gone with enforcing a rule of setting iteration limitations on functions that could run endlessly. 


## Additional Runs without any particular formatting (note above test are listed below as well)

Prompt Folder                  | Challenge                      | Model                     | Iters | Duration
-------------------------------------------------------------------------------------------------------------------
CTF-miguel-prompt-miguel-p     | 01-prove-it                    | gemini-3.1-pro-preview    | 8     | 0:02:56.752469
CTF-miguel-prompt-miguel-p     | 07-crypto-long-caesar          | gemini-3.1-pro-preview    | 6     | 0:01:32.496672
CTF-miguel-prompt-miguel-p     | 08-Vinegar                     | gemini-3.1-pro-preview    | 4     | 0:00:41.421825
CTF-miguel-prompt-miguel-p     | 05-three-line-crypto           | gemini-3.1-pro-preview    | 6     | N/A
CTF-miguel-prompt-miguel-p     | 05-three-line-crypto           | gemini-3.1-pro-preview    | 3     | N/A
CTF-miguel-prompt-miguel-p     | 01-greek-cipher                | gemini-3.1-pro-preview    | 4     | 0:00:56.644392
CTF-miguel-prompt-miguel-p     | 01-blue-hens-2023              | gemini-3.1-pro-preview    | 6     | 0:00:48.507457
CTF-miguel-prompt-miguel-p     | 01-blue-hens-2023              | gemini-3.1-pro-preview    | 6     | 0:00:51.018066
CTF-miguel-prompt-miguel-p     | 01-integral-communication      | gemini-3.1-pro-preview    | 5     | 0:02:34.035961
CTF-miguel-prompt-miguel-p     | 01-babycharge                  | gemini-3.1-pro-preview    | 5     | 0:02:00.966193
CTF-miguel-original            | 01-prove-it                    | gemini-3.1-pro-preview    | 9     | 0:02:44.959878
CTF-miguel-original            | 07-crypto-long-caesar          | gemini-3.1-pro-preview    | 5     | 0:00:53.903416
CTF-miguel-original            | 08-Vinegar                     | gemini-3.1-pro-preview    | 4     | 0:00:38.196623
CTF-miguel-original            | 05-three-line-crypto           | gemini-3.1-pro-preview    | 4     | N/A
CTF-miguel-original            | 05-three-line-crypto           | gemini-3.1-pro-preview    | 4     | N/A
CTF-miguel-original            | 05-three-line-crypto           | gemini-3.1-pro-preview    | 7     | N/A
CTF-miguel-original            | 01-greek-cipher                | gemini-3.1-pro-preview    | 4     | 0:00:35.118322
CTF-miguel-original            | 01-blue-hens-2023              | gemini-3.1-pro-preview    | 5     | 0:00:34.755466
CTF-miguel-original            | 01-blue-hens-2023              | gemini-3.1-pro-preview    | 5     | 0:00:37.251934
CTF-miguel-original            | 01-integral-communication      | gemini-3.1-pro-preview    | 5     | 0:02:07.145736
CTF-miguel-original            | 01-babycharge                  | gemini-3.1-pro-preview    | 5     | 0:02:21.832353
CTF-miguel-prompt-ryan         | 01-prove-it                    | gemini-3.1-pro-preview    | 7     | 0:01:55.742917
CTF-miguel-prompt-ryan         | 07-crypto-long-caesar          | gemini-3.1-pro-preview    | 5     | 0:01:01.295740
CTF-miguel-prompt-ryan         | 08-Vinegar                     | gemini-3.1-pro-preview    | 5     | 0:01:15.820723
CTF-miguel-prompt-ryan         | 05-three-line-crypto           | gemini-3.1-pro-preview    | 4     | N/A
CTF-miguel-prompt-ryan         | 01-greek-cipher                | gemini-3.1-pro-preview    | 4     | 0:01:06.022703
CTF-miguel-prompt-ryan         | 01-blue-hens-2023              | gemini-3.1-pro-preview    | 6     | 0:00:51.176376
CTF-miguel-prompt-ryan         | 01-blue-hens-2023              | gemini-3.1-pro-preview    | 6     | 0:00:51.667323
CTF-miguel-prompt-ryan         | 01-integral-communication      | gemini-3.1-pro-preview    | 7     | 0:03:25.212781
CTF-miguel-prompt-ryan         | 01-babycharge                  | gemini-3.1-pro-preview    | 5     | 0:02:36.672237
CTF-miguel-prompt-miguel-i     | 01-prove-it                    | gemini-3.1-pro-preview    | 11    | 0:02:52.422337
CTF-miguel-prompt-miguel-i     | 07-crypto-long-caesar          | gemini-3.1-pro-preview    | 38    | N/A
CTF-miguel-prompt-miguel-i     | 08-Vinegar                     | gemini-3.1-pro-preview    | 4     | 0:00:37.400015
CTF-miguel-prompt-miguel-i     | 05-three-line-crypto           | gemini-3.1-pro-preview    | 3     | N/A
CTF-miguel-prompt-miguel-i     | 05-three-line-crypto           | gemini-3.1-pro-preview    | 3     | N/A
CTF-miguel-prompt-miguel-i     | 01-greek-cipher                | gemini-3.1-pro-preview    | 5     | 0:00:54.677401
CTF-miguel-prompt-miguel-i     | 01-blue-hens-2023              | gemini-3.1-pro-preview    | 5     | 0:00:27.582374
CTF-miguel-prompt-miguel-i     | 01-blue-hens-2023              | gemini-3.1-pro-preview    | 6     | 0:00:34.793926
CTF-miguel-prompt-miguel-i     | 01-integral-communication      | gemini-3.1-pro-preview    | 7     | 0:02:38.374713
CTF-miguel-prompt-miguel-i     | 01-babycharge                  | gemini-3.1-pro-preview    | 7     | 0:01:41.721624
CTF-miguel-prompt-juan         | 01-prove-it                    | gemini-3.1-pro-preview    | 7     | 0:03:21.109178
CTF-miguel-prompt-juan         | 07-crypto-long-caesar          | gemini-3.1-pro-preview    | 6     | 0:01:26.962992
CTF-miguel-prompt-juan         | 08-Vinegar                     | gemini-3.1-pro-preview    | 4     | 0:00:38.856126
CTF-miguel-prompt-juan         | 05-three-line-crypto           | gemini-3.1-pro-preview    | 5     | N/A
CTF-miguel-prompt-juan         | 01-greek-cipher                | gemini-3.1-pro-preview    | 4     | 0:00:48.277105
CTF-miguel-prompt-juan         | 01-blue-hens-2023              | gemini-3.1-pro-preview    | 6     | 0:00:42.472288
CTF-miguel-prompt-juan         | 01-blue-hens-2023              | gemini-3.1-pro-preview    | 5     | 0:00:41.919793
CTF-miguel-prompt-juan         | 01-integral-communication      | gemini-3.1-pro-preview    | 5     | 0:02:25.527270
CTF-miguel-prompt-juan         | 01-babycharge                  | gemini-3.1-pro-preview    | 5     | 0:01:33.478685
CTF-miguel-prompt-charlie      | 01-prove-it                    | gemini-3.1-pro-preview    | 16    | 0:04:28.364993
CTF-miguel-prompt-charlie      | 07-crypto-long-caesar          | gemini-3.1-pro-preview    | 4     | 0:00:45.429153
CTF-miguel-prompt-charlie      | 08-Vinegar                     | gemini-3.1-pro-preview    | 4     | 0:00:35.886407
CTF-miguel-prompt-charlie      | 05-three-line-crypto           | gemini-3.1-pro-preview    | 4     | N/A
CTF-miguel-prompt-charlie      | 01-greek-cipher                | gemini-3.1-pro-preview    | 4     | 0:00:50.145912
CTF-miguel-prompt-charlie      | 01-blue-hens-2023              | gemini-3.1-pro-preview    | 5     | 0:00:46.217624
CTF-miguel-prompt-charlie      | 01-blue-hens-2023              | gemini-3.1-pro-preview    | 5     | 0:00:43.434946
CTF-miguel-prompt-charlie      | 01-integral-communication      | gemini-3.1-pro-preview    | 5     | 0:02:46.150268
CTF-miguel-prompt-charlie      | 01-babycharge                  | gemini-3.1-pro-preview    | 5     | 0:01:32.527729
CTF-juan-prompt-justus         | 01-prove-it                    | deepseek-chat             | 26    | N/A
New folder                     | 05-DLP                         | deepseek-chat             | 4     | N/A
New folder                     | 04-RSA                         | deepseek-chat             | 7     | 0:00:31.224433
New folder                     | 01-Classic                     | gemini-3.1-pro-preview    | 10    | N/A
New folder                     | 01-Classic                     | gemini-3.1-pro-preview    | 4     | N/A
New folder                     | 01-Classic                     | gemini-3.1-pro-preview    | 4     | N/A
New folder                     | 05-DLP                         | claude-opus-4-7           | 12    | N/A
New folder                     | 04-RSA                         | claude-opus-4-7           | 6     | 0:00:23.113869
CTF-miguel-prompt-justus       | 01-prove-it                    | gemini-3.1-pro-preview    | 7     | 0:04:08.996953
CTF-miguel-prompt-justus       | 07-crypto-long-caesar          | gemini-3.1-pro-preview    | 6     | 0:00:57.750953
CTF-miguel-prompt-justus       | 08-Vinegar                     | gemini-3.1-pro-preview    | 4     | 0:00:37.923589
CTF-miguel-prompt-justus       | 05-three-line-crypto           | gemini-3.1-pro-preview    | 5     | N/A
CTF-miguel-prompt-justus       | 01-greek-cipher                | gemini-3.1-pro-preview    | 5     | 0:01:02.658652
CTF-miguel-prompt-justus       | 01-blue-hens-2023              | gemini-3.1-pro-preview    | 6     | 0:00:47.780114
CTF-miguel-prompt-justus       | 01-blue-hens-2023              | gemini-3.1-pro-preview    | 6     | 0:01:09.837025
CTF-miguel-prompt-justus       | 01-integral-communication      | gemini-3.1-pro-preview    | 5     | 0:02:22.077073
CTF-miguel-prompt-justus       | 01-babycharge                  | gemini-3.1-pro-preview    | 5     | 0:02:39.835387
(base) mig@DESKTOP-G6E7LHM:~/Documents/aicrypto-agent$ python folder_crawler.py
Prompt Folder                  | Challenge                      | Model                     | Iters | Duration
-------------------------------------------------------------------------------------------------------------------
CTF-lattice_baseline           | 07-notitle                     | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 05-xordlp-20                   | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 09-xiyi                        | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 02-p-vs-np                     | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 06-DLP-4.0                     | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 10-DLP+                        | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 17-Tan                         | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 16-pacap                       | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 05-easyrsa                     | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 20-squares-vs-cubes            | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 14-Echo                        | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 02-strange_classic_revenge     | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 22-membrane                    | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 09-strange-crt-12              | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 01-diamond-17                  | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 06-NTRURSA                     | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 11-honey                       | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 24-hell_summon                 | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 03-budget-bag                  | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 21-hayabusa                    | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 07-d3bdd                       | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 13-muck-a-mac                  | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 12-tesvir                      | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 04-naptime                     | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 23-seqr                        | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 01-hill-easy                   | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 11-capac                       | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 12-KEX-4.0                     | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 02-hill-hard                   | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 03-bigram-times                | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 28-xorsa                       | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 34-Tidal-wave                  | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 29-nazdone                     | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 08-very-hot                    | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 33-reiwa-rot13                 | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 32-bbbb                        | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 22-ezrsa                       | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 04-easy-dlp                    | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 06-solmaz                      | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 07-coast                       | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 11-ECLCG                       | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 10-Baby-ECDLP                  | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 09-Imaginary-Casino            | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 03-werid-14                    | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 05-chochol                     | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 13-seaside                     | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 14-sqrt163                     | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 06-vantuk                      | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 01-aes                         | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 04-Latifa                      | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 03-Jonon                       | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 05-shuffle-revenge             | N/A                       | N/A   | N/A
CTF-lattice_baseline           | 06-my-array-generator          | N/A                       | N/A   | N/A
CTF-lattice_seq                | 07-crypto-long-caesar          | gemini-3.1-flash-lite     | 1     | N/A
CTF-lattice_seq                | 08-Vinegar                     | gemini-3.1-flash-lite     | 1     | N/A
CTF-lattice_seq                | 05-three-line-crypto           | gemini-3.1-flash-lite     | 1     | N/A
CTF-lattice_seq                | 04-too-loud-to-yap             | gemini-3.1-flash-lite     | 1     | N/A
CTF-lattice_seq                | 06-funny-cipher                | gemini-3.1-flash-lite     | 1     | N/A
CTF-lattice_seq                | 09-Vinegar2                    | gemini-3.1-flash-lite     | 1     | N/A
CTF-lattice_seq                | 03-valentines-day              | gemini-3.1-flash-lite     | 1     | N/A
CTF-lattice_seq                | 01-greek-cipher                | gemini-3.1-flash-lite     | 1     | N/A
CTF-lattice_seq                | 02-selamat-pagi                | gemini-3.1-flash-lite     | 1     | N/A
CTF-lattice_seq                | 08-tag-chal2                   | gemini-3.1-flash-lite     | 1     | N/A
CTF-lattice_seq                | 05-blocked1                    | gemini-3.1-flash-lite     | 1     | N/A
CTF-lattice_seq                | 09-randsubware                 | gemini-3.1-flash-lite     | 1     | N/A
CTF-lattice_seq                | 04-enchanted-oracle            | gemini-3.1-flash-lite     | 1     | N/A
CTF-lattice_seq                | 06-blocked2                    | gemini-3.1-flash-lite     | 1     | N/A
CTF-lattice_seq                | 07-tag-chal1                   | gemini-3.1-flash-lite     | 1     | N/A
CTF-lattice_seq                | 01-integral-communication      | gemini-3.1-flash-lite     | 1     | N/A
CTF-lattice_seq                | 10-dual-summon                 | gemini-3.1-flash-lite     | 1     | N/A
CTF-lattice_seq                | 02-extremely-convenient-breaker | gemini-3.1-flash-lite     | 1     | N/A
CTF-lattice_seq                | 03-decrypt-then-eval           | gemini-3.1-flash-lite     | 1     | N/A
CTF-lattice_seq                | 01-babycharge                  | gemini-3.1-flash-lite     | 1     | N/A
CTF-miguel-instructional       | 01-diamond-17                  | gemini-3.1-pro-preview    | 3     | N/A
CTF-miguel-instructional       | 01-diamond-17                  | gemini-3.1-flash-lite-preview | 64    | 0:02:54.812769
CTF-miguel-instructional       | 01-diamond-17                  | gemini-2.5-pro-preview    | 1     | N/A
CTF-miguel-instructional       | 01-diamond-17                  | gemini-2.5-pro            | 60    | 1:13:04.206050
CTF                            | run.log                        | gemini-3.1-flash-lite-preview | 9     | N/A
CTF                            | run.log                        | gemini-3.1-flash-lite-preview | 6     | 0:00:08.684398
CTF                            | run.log                        | gemini-3.1-flash-lite-preview | 100   | 0:04:03.493655
CTF                            | 02-strange_classic_revenge     | gemini-3.1-flash-lite-preview | 57    | 0:02:30.468481
CTF                            | 01-diamond-17                  | gemini-3.1-flash-lite     | 1     | N/A
CTF                            | 01-diamond-17                  | gemini-3.1-flash-lite-preview | 92    | N/A
CTF                            | run.log                        | gemini-3.1-flash-lite-preview | 100   | 0:11:20.849531
CTF                            | run.log                        | gemini-3.1-flash-lite-preview | 3     | N/A
CTF                            | 12-third-times-the-charm       | gemini-3.1-pro-preview    | 5     | 0:00:54.481210
CTF                            | 12-third-times-the-charm       | gemini-3.1-flash-lite-preview | 8     | 0:00:15.067455
CTF                            | 33-reiwa-rot13                 | gemini-3.1-pro-preview    | 6     | 0:14:55.906192
CTF                            | 01-blue-hens-2023              | gemini-3.1-pro-preview    | 5     | 0:00:42.971161
CTF                            | run.log                        | gemini-3.1-pro-preview    | 2     | N/A
CTF                            | run.log                        | gemini-3.1-flash-lite-preview | 1     | N/A
CTF                            | run.log                        | gemini-3.1-flash-lite-preview | 61    | 0:02:17.454190
CTF                            | run.log                        | gemini-3.1-flash-lite-preview | 66    | 0:03:01.831780
CTF                            | run.log                        | gemini-3.1-flash-lite-preview | 100   | 0:04:04.244202
CTF-miguel-poisoned            | 01-diamond-17                  | gemini-3.1-pro-preview    | 50    | 1:01:38.580448
CTF-lattice_retry_v1           | 08-some-trick                  | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 07-notitle                     | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 05-xordlp-20                   | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 09-xiyi                        | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 02-p-vs-np                     | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 01-prove-it                    | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 03-groups                      | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 04-snore-signatures            | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 06-DLP-4.0                     | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 10-DLP+                        | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 07-crypto-long-caesar          | gemini-3.1-pro-preview    | 5     | 0:01:21.463645
CTF-lattice_retry_v1           | 08-Vinegar                     | gemini-3.1-pro-preview    | 4     | 0:01:47.494430
CTF-lattice_retry_v1           | 05-three-line-crypto           | gemini-3.1-pro-preview    | 8     | N/A
CTF-lattice_retry_v1           | 04-too-loud-to-yap             | gemini-3.1-pro-preview    | 9     | 0:07:21.108462
CTF-lattice_retry_v1           | 06-funny-cipher                | gemini-3.1-pro-preview    | 70    | 0:24:26.270765
CTF-lattice_retry_v1           | 09-Vinegar2                    | gemini-3.1-pro-preview    | 6     | 0:03:02.975549
CTF-lattice_retry_v1           | 03-valentines-day              | gemini-3.1-pro-preview    | 11    | 0:02:27.550136
CTF-lattice_retry_v1           | 01-greek-cipher                | gemini-3.1-pro-preview    | 4     | 0:02:06.301624
CTF-lattice_retry_v1           | 02-selamat-pagi                | gemini-3.1-pro-preview    | 5     | 0:02:01.289569
CTF-lattice_retry_v1           | 17-Tan                         | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 16-pacap                       | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 05-easyrsa                     | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 20-squares-vs-cubes            | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 14-Echo                        | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 02-strange_classic_revenge     | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 10-alilbols                    | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 19-ZKPoF                       | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 22-membrane                    | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 09-strange-crt-12              | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 01-diamond-17                  | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 06-NTRURSA                     | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 08-strange-gcd-11              | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 11-honey                       | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 24-hell_summon                 | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 03-budget-bag                  | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 18-Random-Shuffling-Algorithm  | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 21-hayabusa                    | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 07-d3bdd                       | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 15-MatProd                     | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 13-muck-a-mac                  | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 12-tesvir                      | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 04-naptime                     | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 23-seqr                        | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 05-v-for-vieta                 | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 01-hill-easy                   | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 07-brutalmogging               | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 11-capac                       | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 04-crypto-civilization         | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 09-shuffler                    | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 12-KEX-4.0                     | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 02-hill-hard                   | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 06-without-a-trace             | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 03-bigram-times                | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 08-reader-exercise             | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 10-alibos                      | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 10-rsaaas                      | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 28-xorsa                       | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 03-dhash                       | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 24-prsa                        | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 26-noob-rsa-returns            | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 23-simple-math                 | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 21-easy-rsa                    | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 13-crypto-baby-rsa             | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 11-determined                  | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 04-chinese-lazy-theorem-1      | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 12-third-times-the-charm       | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 14-crypto-bits-and-pieces      | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 02-blue-hens-2023              | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 06-ravin-cryptosystem          | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 27-mystery-of-scattered-Key    | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 34-Tidal-wave                  | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 07-holyt                       | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 19-babyrsa-2019                | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 17-babyrsa-2019                | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 15-crypto-simple-signature     | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 09-big-e                       | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 25-rsa-bummer                  | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 16-rsa                         | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 29-nazdone                     | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 18-ezrsa-2020                  | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 08-very-hot                    | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 33-reiwa-rot13                 | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 32-bbbb                        | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 30-rm2                         | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 01-blue-hens-2023              | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 22-ezrsa                       | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 20-rrrrsa                      | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 05-chinese-lazy-theorem-2      | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 08-tag-chal2                   | gemini-3.1-pro-preview    | 5     | 0:04:16.305015
CTF-lattice_retry_v1           | 05-blocked1                    | gemini-3.1-pro-preview    | 5     | 0:02:47.124963
CTF-lattice_retry_v1           | 09-randsubware                 | gemini-3.1-pro-preview    | 29    | 0:08:55.219650
CTF-lattice_retry_v1           | 04-enchanted-oracle            | gemini-3.1-pro-preview    | 5     | 0:07:48.142580
CTF-lattice_retry_v1           | 06-blocked2                    | gemini-3.1-pro-preview    | 5     | 0:02:13.695126
CTF-lattice_retry_v1           | 07-tag-chal1                   | gemini-3.1-pro-preview    | 5     | 0:02:03.998863
CTF-lattice_retry_v1           | 01-integral-communication      | gemini-3.1-pro-preview    | 5     | 0:13:12.941841
CTF-lattice_retry_v1           | 10-dual-summon                 | gemini-3.1-pro-preview    | 7     | 0:04:15.490705
CTF-lattice_retry_v1           | 02-extremely-convenient-breaker | gemini-3.1-pro-preview    | 6     | 0:02:45.609991
CTF-lattice_retry_v1           | 03-decrypt-then-eval           | gemini-3.1-pro-preview    | 5     | 0:02:59.074087
CTF-lattice_retry_v1           | 04-easy-dlp                    | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 06-solmaz                      | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 07-coast                       | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 11-ECLCG                       | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 01-manykey                     | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 10-Baby-ECDLP                  | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 09-Imaginary-Casino            | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 03-werid-14                    | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 02-super-party-computation     | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 05-chochol                     | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 13-seaside                     | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 14-sqrt163                     | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 08-EZRSA                       | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 06-vantuk                      | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 07-Paillier-4.0                | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 01-aes                         | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 12-cryptography-1              | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 13-cryptography-2              | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 04-Latifa                      | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 03-Jonon                       | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 15-provably-secure             | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 16-provably-secure-2           | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 17-satisfied                   | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 18-vorpal-sword                | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 09-BrokenShare                 | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 10-Share                       | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 14-cryptography-3              | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 05-Rehawk                      | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 08-v_v_m_m_v_m_m               | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 02-ally                        | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 11-winxy-pistol                | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 17-noisy-crc                   | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 13-lf3r                        | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 02-pprngc                      | gemini-3.1-pro-preview    | 5     | 0:02:03.503051
CTF-lattice_retry_v1           | 14-zkdlp                       | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 01-babycharge                  | gemini-3.1-pro-preview    | 5     | 0:02:55.352252
CTF-lattice_retry_v1           | 19-good-hash                   | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 09-numbers-go-brrr-2           | gemini-3.1-pro-preview    | 3     | N/A
CTF-lattice_retry_v1           | 21-winter                      | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 10-numbers-go-brrr             | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 04-quickprime                  | gemini-3.1-pro-preview    | 5     | 0:04:13.171786
CTF-lattice_retry_v1           | 16-diffecientwo                | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 08-causation                   | gemini-3.1-pro-preview    | 2     | N/A
CTF-lattice_retry_v1           | 05-shuffle-revenge             | gemini-3.1-pro-preview    | 9     | N/A
CTF-lattice_retry_v1           | 06-my-array-generator          | gemini-3.1-pro-preview    | 5     | N/A
CTF-lattice_retry_v1           | 03-shuffle                     | gemini-3.1-pro-preview    | 12    | N/A
CTF-lattice_retry_v1           | 20-tag-chal3                   | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 15-rps-casino                  | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 18-noisier-crc                 | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 07-b4-the-b8                   | gemini-3.1-pro-preview    | 8     | N/A
CTF-lattice_retry_v1           | 11-bivalves                    | gemini-3.1-pro-preview    | 1     | N/A
CTF-lattice_retry_v1           | 12-Hyper512                    | gemini-3.1-pro-preview    | 1     | N/A
CTF-miguel                     | 05-three-line-crypto           | gemini-3.1-pro-preview    | 5     | N/A
CTF-miguel                     | 33-reiwa-rot13                 | gemini-3.1-pro-preview    | 6     | 0:03:32.734091
CTF-miguel                     | 01-blue-hens-2023              | gemini-3.1-pro-preview    | 5     | 0:00:40.286916








File structure used to get to run.log                                            |   | Iters  | Duration
------------------------------------------------------------------------------------------------------------------------
05-easyrsa-miguel-instructional-20260422-182146/run.log                          |   | N/A    | N/A
04-naptime-miguel-instructional-20260422-182136/run.log                          |   | N/A    | 0:00:08
03-budget-bag-miguel-instructional-20260422-181731/run.log                       |   | N/A    | 0:04:03
miguel-instructional-20260422-175647/run.log                                     |   | N/A    | 0:11:20
06-NTRURSA-miguel-instructional-20260422-183226/run.log                          |   | N/A    | N/A
miguel-instructional-20260422-144937/run.log                                     |   | N/A    | N/A
07-d3bdd-miguel-instructional-20260422-183231/run.log                            |   | N/A    | N/A
miguel-instructional-20260422-145200/run.log                                     |   | N/A    | 0:02:17
miguel-instructional-20260422-153450/run.log                                     |   | N/A    | 0:03:01
02-strange_classic_revenge-miguel-instructional-20260422-181324/run.log          |   | N/A    | 0:04:04
CTF-miguel/04-RSA/01-blue-hens-2023/gemini-3.1-pro-preview/run/run.log           |   | N/A    | 0:00:40
CTF-miguel/04-RSA/33-reiwa-rot13/gemini-3.1-pro-preview/run/run.log              |   | N/A    | 0:03:32
CTF-miguel/01-Classic/05-three-line-crypto/gemini-3.1-pro-preview/run/run.log    |   | N/A    | N/A
CTF-miguel/01-Classic/05-three-line-crypto/gemini-3.1-pro-preview/20260428-222323/run/run.log |   | N/A    | N/A
CTF-miguel/01-Classic/05-three-line-crypto/gemini-3.1-pro-preview/20260428-221353/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/03-Stream-PRNG-Hash/12-Hyper512/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/03-Stream-PRNG-Hash/11-bivalves/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/03-Stream-PRNG-Hash/07-b4-the-b8/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/03-Stream-PRNG-Hash/18-noisier-crc/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/03-Stream-PRNG-Hash/15-rps-casino/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/03-Stream-PRNG-Hash/20-tag-chal3/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/03-Stream-PRNG-Hash/03-shuffle/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/03-Stream-PRNG-Hash/06-my-array-generator/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/03-Stream-PRNG-Hash/05-shuffle-revenge/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/03-Stream-PRNG-Hash/08-causation/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/03-Stream-PRNG-Hash/16-diffecientwo/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/03-Stream-PRNG-Hash/04-quickprime/gemini-3.1-pro-preview/run/run.log |   | N/A    | 0:04:13
CTF-lattice_retry_v1/03-Stream-PRNG-Hash/10-numbers-go-brrr/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/03-Stream-PRNG-Hash/21-winter/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/03-Stream-PRNG-Hash/09-numbers-go-brrr-2/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/03-Stream-PRNG-Hash/19-good-hash/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/03-Stream-PRNG-Hash/01-babycharge/gemini-3.1-pro-preview/run/run.log |   | N/A    | 0:02:55
CTF-lattice_retry_v1/03-Stream-PRNG-Hash/14-zkdlp/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/03-Stream-PRNG-Hash/02-pprngc/gemini-3.1-pro-preview/run/run.log |   | N/A    | 0:02:03
CTF-lattice_retry_v1/03-Stream-PRNG-Hash/13-lf3r/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/03-Stream-PRNG-Hash/17-noisy-crc/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/09-Others/11-winxy-pistol/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/09-Others/02-ally/gemini-3.1-pro-preview/run/run.log        |   | N/A    | N/A
CTF-lattice_retry_v1/09-Others/08-v_v_m_m_v_m_m/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/09-Others/05-Rehawk/gemini-3.1-pro-preview/run/run.log      |   | N/A    | N/A
CTF-lattice_retry_v1/09-Others/14-cryptography-3/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/09-Others/10-Share/gemini-3.1-pro-preview/run/run.log       |   | N/A    | N/A
CTF-lattice_retry_v1/09-Others/09-BrokenShare/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/09-Others/18-vorpal-sword/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/09-Others/17-satisfied/gemini-3.1-pro-preview/run/run.log   |   | N/A    | N/A
CTF-lattice_retry_v1/09-Others/16-provably-secure-2/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/09-Others/15-provably-secure/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/09-Others/03-Jonon/gemini-3.1-pro-preview/run/run.log       |   | N/A    | N/A
CTF-lattice_retry_v1/09-Others/04-Latifa/gemini-3.1-pro-preview/run/run.log      |   | N/A    | N/A
CTF-lattice_retry_v1/09-Others/13-cryptography-2/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/09-Others/12-cryptography-1/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/09-Others/01-aes/gemini-3.1-pro-preview/run/run.log         |   | N/A    | N/A
CTF-lattice_retry_v1/09-Others/07-Paillier-4.0/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/09-Others/06-vantuk/gemini-3.1-pro-preview/run/run.log      |   | N/A    | N/A
CTF-lattice_retry_v1/07-ECC/08-EZRSA/gemini-3.1-pro-preview/run/run.log          |   | N/A    | N/A
CTF-lattice_retry_v1/07-ECC/14-sqrt163/gemini-3.1-pro-preview/run/run.log        |   | N/A    | N/A
CTF-lattice_retry_v1/07-ECC/13-seaside/gemini-3.1-pro-preview/run/run.log        |   | N/A    | N/A
CTF-lattice_retry_v1/07-ECC/05-chochol/gemini-3.1-pro-preview/run/run.log        |   | N/A    | N/A
CTF-lattice_retry_v1/07-ECC/02-super-party-computation/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/07-ECC/03-werid-14/gemini-3.1-pro-preview/run/run.log       |   | N/A    | N/A
CTF-lattice_retry_v1/07-ECC/09-Imaginary-Casino/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/07-ECC/10-Baby-ECDLP/gemini-3.1-pro-preview/run/run.log     |   | N/A    | N/A
CTF-lattice_retry_v1/07-ECC/01-manykey/gemini-3.1-pro-preview/run/run.log        |   | N/A    | N/A
CTF-lattice_retry_v1/07-ECC/11-ECLCG/gemini-3.1-pro-preview/run/run.log          |   | N/A    | N/A
CTF-lattice_retry_v1/07-ECC/07-coast/gemini-3.1-pro-preview/run/run.log          |   | N/A    | N/A
CTF-lattice_retry_v1/07-ECC/06-solmaz/gemini-3.1-pro-preview/run/run.log         |   | N/A    | N/A
CTF-lattice_retry_v1/07-ECC/04-easy-dlp/gemini-3.1-pro-preview/run/run.log       |   | N/A    | N/A
CTF-lattice_retry_v1/02-Block/03-decrypt-then-eval/gemini-3.1-pro-preview/run/run.log |   | N/A    | 0:02:59
CTF-lattice_retry_v1/02-Block/02-extremely-convenient-breaker/gemini-3.1-pro-preview/run/run.log |   | N/A    | 0:02:45
CTF-lattice_retry_v1/02-Block/10-dual-summon/gemini-3.1-pro-preview/run/run.log  |   | N/A    | 0:04:15
CTF-lattice_retry_v1/02-Block/01-integral-communication/gemini-3.1-pro-preview/run/run.log |   | N/A    | 0:13:12
CTF-lattice_retry_v1/02-Block/07-tag-chal1/gemini-3.1-pro-preview/run/run.log    |   | N/A    | 0:02:03
CTF-lattice_retry_v1/02-Block/06-blocked2/gemini-3.1-pro-preview/run/run.log     |   | N/A    | 0:02:13
CTF-lattice_retry_v1/02-Block/04-enchanted-oracle/gemini-3.1-pro-preview/run/run.log |   | N/A    | 0:07:48
CTF-lattice_retry_v1/02-Block/09-randsubware/gemini-3.1-pro-preview/run/run.log  |   | N/A    | 0:08:55
CTF-lattice_retry_v1/02-Block/05-blocked1/gemini-3.1-pro-preview/run/run.log     |   | N/A    | 0:02:47
CTF-lattice_retry_v1/02-Block/08-tag-chal2/gemini-3.1-pro-preview/run/run.log    |   | N/A    | 0:04:16
CTF-lattice_retry_v1/04-RSA/05-chinese-lazy-theorem-2/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/20-rrrrsa/gemini-3.1-pro-preview/run/run.log         |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/22-ezrsa/gemini-3.1-pro-preview/run/run.log          |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/01-blue-hens-2023/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/30-rm2/gemini-3.1-pro-preview/run/run.log            |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/32-bbbb/gemini-3.1-pro-preview/run/run.log           |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/33-reiwa-rot13/gemini-3.1-pro-preview/run/run.log    |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/08-very-hot/gemini-3.1-pro-preview/run/run.log       |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/18-ezrsa-2020/gemini-3.1-pro-preview/run/run.log     |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/29-nazdone/gemini-3.1-pro-preview/run/run.log        |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/16-rsa/gemini-3.1-pro-preview/run/run.log            |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/25-rsa-bummer/gemini-3.1-pro-preview/run/run.log     |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/09-big-e/gemini-3.1-pro-preview/run/run.log          |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/15-crypto-simple-signature/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/17-babyrsa-2019/gemini-3.1-pro-preview/run/run.log   |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/19-babyrsa-2019/gemini-3.1-pro-preview/run/run.log   |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/07-holyt/gemini-3.1-pro-preview/run/run.log          |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/34-Tidal-wave/gemini-3.1-pro-preview/run/run.log     |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/27-mystery-of-scattered-Key/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/06-ravin-cryptosystem/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/02-blue-hens-2023/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/14-crypto-bits-and-pieces/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/12-third-times-the-charm/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/04-chinese-lazy-theorem-1/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/11-determined/gemini-3.1-pro-preview/run/run.log     |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/13-crypto-baby-rsa/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/21-easy-rsa/gemini-3.1-pro-preview/run/run.log       |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/23-simple-math/gemini-3.1-pro-preview/run/run.log    |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/26-noob-rsa-returns/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/24-prsa/gemini-3.1-pro-preview/run/run.log           |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/03-dhash/gemini-3.1-pro-preview/run/run.log          |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/28-xorsa/gemini-3.1-pro-preview/run/run.log          |   | N/A    | N/A
CTF-lattice_retry_v1/04-RSA/10-rsaaas/gemini-3.1-pro-preview/run/run.log         |   | N/A    | N/A
CTF-lattice_retry_v1/08-Homemade/10-alibos/gemini-3.1-pro-preview/run/run.log    |   | N/A    | N/A
CTF-lattice_retry_v1/08-Homemade/08-reader-exercise/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/08-Homemade/03-bigram-times/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/08-Homemade/06-without-a-trace/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/08-Homemade/02-hill-hard/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/08-Homemade/12-KEX-4.0/gemini-3.1-pro-preview/run/run.log   |   | N/A    | N/A
CTF-lattice_retry_v1/08-Homemade/09-shuffler/gemini-3.1-pro-preview/run/run.log  |   | N/A    | N/A
CTF-lattice_retry_v1/08-Homemade/04-crypto-civilization/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/08-Homemade/11-capac/gemini-3.1-pro-preview/run/run.log     |   | N/A    | N/A
CTF-lattice_retry_v1/08-Homemade/07-brutalmogging/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/08-Homemade/01-hill-easy/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/08-Homemade/05-v-for-vieta/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/23-seqr/gemini-3.1-pro-preview/run/run.log       |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/04-naptime/gemini-3.1-pro-preview/run/run.log    |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/12-tesvir/gemini-3.1-pro-preview/run/run.log     |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/13-muck-a-mac/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/15-MatProd/gemini-3.1-pro-preview/run/run.log    |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/07-d3bdd/gemini-3.1-pro-preview/run/run.log      |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/21-hayabusa/gemini-3.1-pro-preview/run/run.log   |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/18-Random-Shuffling-Algorithm/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/03-budget-bag/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/24-hell_summon/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/11-honey/gemini-3.1-pro-preview/run/run.log      |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/08-strange-gcd-11/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/06-NTRURSA/gemini-3.1-pro-preview/run/run.log    |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/01-diamond-17/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/09-strange-crt-12/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/22-membrane/gemini-3.1-pro-preview/run/run.log   |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/19-ZKPoF/gemini-3.1-pro-preview/run/run.log      |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/10-alilbols/gemini-3.1-pro-preview/run/run.log   |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/02-strange_classic_revenge/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/14-Echo/gemini-3.1-pro-preview/run/run.log       |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/20-squares-vs-cubes/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/05-easyrsa/gemini-3.1-pro-preview/run/run.log    |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/16-pacap/gemini-3.1-pro-preview/run/run.log      |   | N/A    | N/A
CTF-lattice_retry_v1/06-Lattice/17-Tan/gemini-3.1-pro-preview/run/run.log        |   | N/A    | N/A
CTF-lattice_retry_v1/01-Classic/02-selamat-pagi/gemini-3.1-pro-preview/run/run.log |   | N/A    | 0:02:01
CTF-lattice_retry_v1/01-Classic/01-greek-cipher/gemini-3.1-pro-preview/run/run.log |   | N/A    | 0:02:06
CTF-lattice_retry_v1/01-Classic/03-valentines-day/gemini-3.1-pro-preview/run/run.log |   | N/A    | 0:02:27
CTF-lattice_retry_v1/01-Classic/09-Vinegar2/gemini-3.1-pro-preview/run/run.log   |   | N/A    | 0:03:02
CTF-lattice_retry_v1/01-Classic/06-funny-cipher/gemini-3.1-pro-preview/run/run.log |   | N/A    | 0:24:26
CTF-lattice_retry_v1/01-Classic/04-too-loud-to-yap/gemini-3.1-pro-preview/run/run.log |   | N/A    | 0:07:21
CTF-lattice_retry_v1/01-Classic/05-three-line-crypto/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/01-Classic/08-Vinegar/gemini-3.1-pro-preview/run/run.log    |   | N/A    | 0:01:47
CTF-lattice_retry_v1/01-Classic/07-crypto-long-caesar/gemini-3.1-pro-preview/run/run.log |   | N/A    | 0:01:21
CTF-lattice_retry_v1/05-DLP/10-DLP+/gemini-3.1-pro-preview/run/run.log           |   | N/A    | N/A
CTF-lattice_retry_v1/05-DLP/06-DLP-4.0/gemini-3.1-pro-preview/run/run.log        |   | N/A    | N/A
CTF-lattice_retry_v1/05-DLP/04-snore-signatures/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_retry_v1/05-DLP/03-groups/gemini-3.1-pro-preview/run/run.log         |   | N/A    | N/A
CTF-lattice_retry_v1/05-DLP/01-prove-it/gemini-3.1-pro-preview/run/run.log       |   | N/A    | N/A
CTF-lattice_retry_v1/05-DLP/02-p-vs-np/gemini-3.1-pro-preview/run/run.log        |   | N/A    | N/A
CTF-lattice_retry_v1/05-DLP/09-xiyi/gemini-3.1-pro-preview/run/run.log           |   | N/A    | N/A
CTF-lattice_retry_v1/05-DLP/05-xordlp-20/gemini-3.1-pro-preview/run/run.log      |   | N/A    | N/A
CTF-lattice_retry_v1/05-DLP/07-notitle/gemini-3.1-pro-preview/run/run.log        |   | N/A    | N/A
CTF-lattice_retry_v1/05-DLP/08-some-trick/gemini-3.1-pro-preview/run/run.log     |   | N/A    | N/A
CTF-miguel-poisoned/06-Lattice/01-diamond-17/gemini-3.1-pro-preview/run/run.log  |   | N/A    | 1:01:38
04-RSA/01-blue-hens-2023/gemini-3.1-pro-preview/run/run.log                      |   | N/A    | 0:00:42
04-RSA/33-reiwa-rot13/gemini-3.1-pro-preview/run/run.log                         |   | N/A    | 0:14:55
04-RSA/12-third-times-the-charm/gemini-3.1-flash-lite-preview/run/run.log        |   | N/A    | 0:00:15
04-RSA/12-third-times-the-charm/gemini-3.1-pro-preview/run/run.log               |   | N/A    | 0:00:54
CTF-miguel-instructional/06-Lattice/01-diamond-17/gemini-2.5-pro/run/run.log     |   | N/A    | 1:13:04
CTF-miguel-instructional/06-Lattice/01-diamond-17/gemini-2.5-pro-preview/run/run.log |   | N/A    | N/A
CTF-miguel-instructional/06-Lattice/01-diamond-17/gemini-3.1-flash-lite-preview/run/run.log |   | N/A    | 0:02:54
CTF-miguel-instructional/06-Lattice/01-diamond-17/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_seq/03-Stream-PRNG-Hash/01-babycharge/gemini-3.1-flash-lite/run/run.log |   | N/A    | N/A
CTF-lattice_seq/02-Block/03-decrypt-then-eval/gemini-3.1-flash-lite/run/run.log  |   | N/A    | N/A
CTF-lattice_seq/02-Block/02-extremely-convenient-breaker/gemini-3.1-flash-lite/run/run.log |   | N/A    | N/A
CTF-lattice_seq/02-Block/10-dual-summon/gemini-3.1-flash-lite/run/run.log        |   | N/A    | N/A
CTF-lattice_seq/02-Block/01-integral-communication/gemini-3.1-flash-lite/run/run.log |   | N/A    | N/A
CTF-lattice_seq/02-Block/07-tag-chal1/gemini-3.1-flash-lite/run/run.log          |   | N/A    | N/A
CTF-lattice_seq/02-Block/06-blocked2/gemini-3.1-flash-lite/run/run.log           |   | N/A    | N/A
CTF-lattice_seq/02-Block/04-enchanted-oracle/gemini-3.1-flash-lite/run/run.log   |   | N/A    | N/A
CTF-lattice_seq/02-Block/09-randsubware/gemini-3.1-flash-lite/run/run.log        |   | N/A    | N/A
CTF-lattice_seq/02-Block/05-blocked1/gemini-3.1-flash-lite/run/run.log           |   | N/A    | N/A
CTF-lattice_seq/02-Block/08-tag-chal2/gemini-3.1-flash-lite/run/run.log          |   | N/A    | N/A
CTF-lattice_seq/01-Classic/02-selamat-pagi/gemini-3.1-flash-lite/run/run.log     |   | N/A    | N/A
CTF-lattice_seq/01-Classic/01-greek-cipher/gemini-3.1-flash-lite/run/run.log     |   | N/A    | N/A
CTF-lattice_seq/01-Classic/03-valentines-day/gemini-3.1-flash-lite/run/run.log   |   | N/A    | N/A
CTF-lattice_seq/01-Classic/09-Vinegar2/gemini-3.1-flash-lite/run/run.log         |   | N/A    | N/A
CTF-lattice_seq/01-Classic/06-funny-cipher/gemini-3.1-flash-lite/run/run.log     |   | N/A    | N/A
CTF-lattice_seq/01-Classic/04-too-loud-to-yap/gemini-3.1-flash-lite/run/run.log  |   | N/A    | N/A
CTF-lattice_seq/01-Classic/05-three-line-crypto/gemini-3.1-flash-lite/run/run.log |   | N/A    | N/A
CTF-lattice_seq/01-Classic/08-Vinegar/gemini-3.1-flash-lite/run/run.log          |   | N/A    | N/A
CTF-lattice_seq/01-Classic/07-crypto-long-caesar/gemini-3.1-flash-lite/run/run.log |   | N/A    | N/A
06-Lattice/01-diamond-17/gemini-3.1-flash-lite-preview/run/run.log               |   | N/A    | N/A
06-Lattice/01-diamond-17/gemini-3.1-flash-lite/run/run.log                       |   | N/A    | N/A
06-Lattice/02-strange_classic_revenge/gemini-3.1-flash-lite-preview/run/run.log  |   | N/A    | 0:02:30
CTF-lattice_baseline/03-Stream-PRNG-Hash/06-my-array-generator/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_baseline/03-Stream-PRNG-Hash/05-shuffle-revenge/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_baseline/09-Others/03-Jonon/gemini-3.1-pro-preview/run/run.log       |   | N/A    | N/A
CTF-lattice_baseline/09-Others/04-Latifa/gemini-3.1-pro-preview/run/run.log      |   | N/A    | N/A
CTF-lattice_baseline/09-Others/01-aes/gemini-3.1-pro-preview/run/run.log         |   | N/A    | N/A
CTF-lattice_baseline/09-Others/06-vantuk/gemini-3.1-pro-preview/run/run.log      |   | N/A    | N/A
CTF-lattice_baseline/07-ECC/14-sqrt163/gemini-3.1-pro-preview/run/run.log        |   | N/A    | N/A
CTF-lattice_baseline/07-ECC/13-seaside/gemini-3.1-pro-preview/run/run.log        |   | N/A    | N/A
CTF-lattice_baseline/07-ECC/05-chochol/gemini-3.1-pro-preview/run/run.log        |   | N/A    | N/A
CTF-lattice_baseline/07-ECC/03-werid-14/gemini-3.1-pro-preview/run/run.log       |   | N/A    | N/A
CTF-lattice_baseline/07-ECC/09-Imaginary-Casino/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_baseline/07-ECC/10-Baby-ECDLP/gemini-3.1-pro-preview/run/run.log     |   | N/A    | N/A
CTF-lattice_baseline/07-ECC/11-ECLCG/gemini-3.1-pro-preview/run/run.log          |   | N/A    | N/A
CTF-lattice_baseline/07-ECC/07-coast/gemini-3.1-pro-preview/run/run.log          |   | N/A    | N/A
CTF-lattice_baseline/07-ECC/06-solmaz/gemini-3.1-pro-preview/run/run.log         |   | N/A    | N/A
CTF-lattice_baseline/07-ECC/04-easy-dlp/gemini-3.1-pro-preview/run/run.log       |   | N/A    | N/A
CTF-lattice_baseline/04-RSA/22-ezrsa/gemini-3.1-pro-preview/run/run.log          |   | N/A    | N/A
CTF-lattice_baseline/04-RSA/32-bbbb/gemini-3.1-pro-preview/run/run.log           |   | N/A    | N/A
CTF-lattice_baseline/04-RSA/33-reiwa-rot13/gemini-3.1-pro-preview/run/run.log    |   | N/A    | N/A
CTF-lattice_baseline/04-RSA/08-very-hot/gemini-3.1-pro-preview/run/run.log       |   | N/A    | N/A
CTF-lattice_baseline/04-RSA/29-nazdone/gemini-3.1-pro-preview/run/run.log        |   | N/A    | N/A
CTF-lattice_baseline/04-RSA/34-Tidal-wave/gemini-3.1-pro-preview/run/run.log     |   | N/A    | N/A
CTF-lattice_baseline/04-RSA/28-xorsa/gemini-3.1-pro-preview/run/run.log          |   | N/A    | N/A
CTF-lattice_baseline/08-Homemade/03-bigram-times/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_baseline/08-Homemade/02-hill-hard/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_baseline/08-Homemade/12-KEX-4.0/gemini-3.1-pro-preview/run/run.log   |   | N/A    | N/A
CTF-lattice_baseline/08-Homemade/11-capac/gemini-3.1-pro-preview/run/run.log     |   | N/A    | N/A
CTF-lattice_baseline/08-Homemade/01-hill-easy/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_baseline/06-Lattice/23-seqr/gemini-3.1-pro-preview/run/run.log       |   | N/A    | N/A
CTF-lattice_baseline/06-Lattice/04-naptime/gemini-3.1-pro-preview/run/run.log    |   | N/A    | N/A
CTF-lattice_baseline/06-Lattice/12-tesvir/gemini-3.1-pro-preview/run/run.log     |   | N/A    | N/A
CTF-lattice_baseline/06-Lattice/13-muck-a-mac/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_baseline/06-Lattice/07-d3bdd/gemini-3.1-pro-preview/run/run.log      |   | N/A    | N/A
CTF-lattice_baseline/06-Lattice/21-hayabusa/gemini-3.1-pro-preview/run/run.log   |   | N/A    | N/A
CTF-lattice_baseline/06-Lattice/03-budget-bag/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_baseline/06-Lattice/24-hell_summon/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_baseline/06-Lattice/11-honey/gemini-3.1-pro-preview/run/run.log      |   | N/A    | N/A
CTF-lattice_baseline/06-Lattice/06-NTRURSA/gemini-3.1-pro-preview/run/run.log    |   | N/A    | N/A
CTF-lattice_baseline/06-Lattice/01-diamond-17/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_baseline/06-Lattice/09-strange-crt-12/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_baseline/06-Lattice/22-membrane/gemini-3.1-pro-preview/run/run.log   |   | N/A    | N/A
CTF-lattice_baseline/06-Lattice/02-strange_classic_revenge/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_baseline/06-Lattice/14-Echo/gemini-3.1-pro-preview/run/run.log       |   | N/A    | N/A
CTF-lattice_baseline/06-Lattice/20-squares-vs-cubes/gemini-3.1-pro-preview/run/run.log |   | N/A    | N/A
CTF-lattice_baseline/06-Lattice/05-easyrsa/gemini-3.1-pro-preview/run/run.log    |   | N/A    | N/A
CTF-lattice_baseline/06-Lattice/16-pacap/gemini-3.1-pro-preview/run/run.log      |   | N/A    | N/A
CTF-lattice_baseline/06-Lattice/17-Tan/gemini-3.1-pro-preview/run/run.log        |   | N/A    | N/A
CTF-lattice_baseline/05-DLP/10-DLP+/gemini-3.1-pro-preview/run/run.log           |   | N/A    | N/A
CTF-lattice_baseline/05-DLP/06-DLP-4.0/gemini-3.1-pro-preview/run/run.log        |   | N/A    | N/A
CTF-lattice_baseline/05-DLP/02-p-vs-np/gemini-3.1-pro-preview/run/run.log        |   | N/A    | N/A
CTF-lattice_baseline/05-DLP/09-xiyi/gemini-3.1-pro-preview/run/run.log           |   | N/A    | N/A
CTF-lattice_baseline/05-DLP/05-xordlp-20/gemini-3.1-pro-preview/run/run.log      |   | N/A    | N/A
CTF-lattice_baseline/05-DLP/07-notitle/gemini-3.1-pro-preview/run/run.log        |   | N/A    | N/A
