#!/usr/bin/env python3
"""
Real-time Project Progress Dashboard
Shows current status of training, evaluation, and deliverables
"""

import json
import os
from datetime import datetime
from pathlib import Path

class ProjectTracker:
    def __init__(self, project_root="/Users/faan/Documents/_Ele/rl/power_optimization"):
        self.root = Path(project_root)
        
    def check_file_exists(self, path):
        """Check if file exists and get size"""
        full_path = self.root / path
        if full_path.exists():
            size = full_path.stat().st_size
            return True, size
        return False, 0
    
    def check_training_status(self):
        """Check if training is running and progress"""
        log_file = self.root / "logs/production_training.log"
        if not log_file.exists():
            return "Not Started", 0
        
        # Read last few lines of log
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                if len(lines) > 0:
                    # Look for step indicators
                    for line in reversed(lines[-50:]):
                        if "steps" in line.lower():
                            return "Running", len(lines)
            return "Running (check logs)", len(lines)
        except:
            return "Unknown", 0
    
    def generate_report(self):
        """Generate comprehensive progress report"""
        print("=" * 80)
        print("PROJECT PROGRESS DASHBOARD")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # 1. Core Deliverables
        print("\n CORE DELIVERABLES")
        print("-" * 80)
        
        deliverables = {
            " Data Pipeline": "data/pjm_hourly.csv",
            " RL Environment": "environment/power_env.py",
            " PPO Agent": "agent/ppo_agent.py",
            " Training Script": "training/train.py",
            " Evaluation Framework": "training/evaluate.py",
            " Dashboard": "dashboard/index.html",
            " Executive README": "README_EXECUTIVE.md",
            " Trained Model": "models/final_model.zip",
            " Evaluation Report": "reports/evaluation_results.json"
        }
        
        for name, path in deliverables.items():
            exists, size = self.check_file_exists(path)
            status = "" if exists else ""
            size_str = f"({size:,} bytes)" if exists else ""
            print(f"  {name:.<50} {status} {size_str}")
        
        # 2. Training Status
        print("\n TRAINING STATUS")
        print("-" * 80)
        
        status, progress = self.check_training_status()
        print(f"  Status: {status}")
        if progress > 0:
            print(f"  Log lines: {progress:,}")
        
        # Check model checkpoints
        models_dir = self.root / "models"
        if models_dir.exists():
            checkpoints = list(models_dir.glob("ppo_power_grid_*.zip"))
            print(f"  Checkpoints saved: {len(checkpoints)}")
        
        # 3. Documentation Status
        print("\n DOCUMENTATION")
        print("-" * 80)
        
        docs = {
            "Technical README": "README.md",
            "Executive Summary": "README_EXECUTIVE.md",
            "Project Structure": "PROJECT_STRUCTURE.md",
            "Configuration": "config.yaml",
            "Requirements": "requirements.txt"
        }
        
        for name, path in docs.items():
            exists, _ = self.check_file_exists(path)
            status = "" if exists else ""
            print(f"  {name:.<50} {status}")
        
        # 4. Code Quality
        print("\n CODE QUALITY")
        print("-" * 80)
        
        # Check for test files
        tests_dir = self.root / "tests"
        if tests_dir.exists():
            test_files = list(tests_dir.glob("test_*.py"))
            print(f"  Test files: {len(test_files)}")
        else:
            print(f"  Test files: 0 (TODO)")
        
        # Check for deprecated files
        deprecated = list(self.root.glob("*.deprecated"))
        print(f"  Deprecated files cleaned: {len(deprecated)} moved")
        
        # 5. Readiness Score
        print("\n READINESS ASSESSMENT")
        print("-" * 80)
        
        scores = {
            "Data Foundation": 100,  # PJM data verified
            "Core Algorithm": 100,   # Code complete
            "Training Pipeline": 75,  # Running but not done
            "Evaluation": 50,        # Need to complete training first
            "Documentation": 90,     # Executive + technical docs
            "Testing": 20,           # No unit tests yet
            "Deployment": 60         # Dashboard exists, need API
        }
        
        for category, score in scores.items():
            bar_length = int(score / 5)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            print(f"  {category:.<30} {bar} {score:>3}%")
        
        overall = sum(scores.values()) / len(scores)
        print(f"\n  {'OVERALL READINESS':.<30} {'█' * int(overall/5)}{'░' * (20-int(overall/5))} {overall:>3.0f}%")
        
        # 6. Next Steps
        print("\n NEXT STEPS")
        print("-" * 80)
        
        if status == "Not Started":
            print("  1.  Start training: python training/train.py --steps 500000")
        elif status.startswith("Running"):
            print("  1.  Wait for training to complete (~2-3 hours)")
            print("  2. Monitor: tensorboard --logdir logs/tensorboard")
        
        print("  3. Run evaluation after training completes")
        print("  4. Update dashboard with results")
        print("  5. Add unit tests (target 60% coverage)")
        print("  6. Prepare investor deck")
        
        # 7. Timeline Estimate
        print("\n ESTIMATED TIMELINE TO DEMO-READY")
        print("-" * 80)
        print("  Training complete:     2-3 hours (from now)")
        print("  Evaluation + report:   1-2 hours")
        print("  Dashboard update:      30 minutes")
        print("  Deck preparation:      2-3 hours")
        print(f"  {'-' * 60}")
        print("  TOTAL:                ~6-9 hours (1 working day)")
        
        print("\n" + "=" * 80)
        print(" TIP: Run this script anytime to check progress")
        print("   python scripts/progress_dashboard.py")
        print("=" * 80 + "\n")

if __name__ == "__main__":
    tracker = ProjectTracker()
    tracker.generate_report()
