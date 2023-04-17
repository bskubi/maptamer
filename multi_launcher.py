import gptner

gptner.run_multiple_gpt_instances("multi_launcher.bash", "multi_launcher_instance.py", "results/aliases.csv", "multi_launcher_instance", "results/aliases", 3)
print("Done running")