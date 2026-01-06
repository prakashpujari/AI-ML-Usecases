#!/usr/bin/env python
"""
Quick Reference: Model Rollback Operations
Fast access to common rollback commands and checks
"""

import sys
import os

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from db_utils import ModelEvaluationDB
from scripts.monitor_model_performance import ModelMonitor


def quick_status():
    """Show quick model status"""
    print("\n" + "="*80)
    print("📊 QUICK MODEL STATUS")
    print("="*80)
    
    with ModelEvaluationDB() as db:
        history = db.get_model_history(limit=3)
        
        for i, model in enumerate(history):
            prod = "🚀 PRODUCTION" if model['is_production'] else "TEST"
            print(f"\n{i+1}. {prod}")
            print(f"   Version: {model['model_version']}")
            print(f"   R² Score: {model['r2_score']:.4f}")
            print(f"   RMSE: {model['rmse_score']:.2f}")
            print(f"   Size: {model['size_mb']} MB")
            print(f"   Created: {model['created_at']}")


def quick_degradation_check():
    """Quick degradation check"""
    print("\n" + "="*80)
    print("🔍 DEGRADATION CHECK")
    print("="*80)
    
    with ModelEvaluationDB() as db:
        result = db.check_performance_degradation(threshold_percent=5.0)
        
        if result.get('degraded'):
            print("\n⚠️  DEGRADATION DETECTED!")
            print(f"R² Change: {result['r2_change_percent']:.2f}%")
            print(f"RMSE Change: {result['rmse_change_percent']:.2f}%")
            print(f"Threshold: {result['threshold_percent']}%")
            print(f"\nCurrent: v{result['current_version']}")
            print(f"Previous: v{result['previous_version']}")
        else:
            print("\n✓ No degradation detected")
            print(f"R² Change: {result['r2_change_percent']:.2f}%")
            print(f"RMSE Change: {result['rmse_change_percent']:.2f}%")


def quick_rollback():
    """Quick rollback to previous version"""
    print("\n" + "="*80)
    print("🔄 QUICK ROLLBACK")
    print("="*80)
    
    with ModelEvaluationDB() as db:
        success = db.rollback_production_model()
        
        if success:
            print("\n✓ Rollback successful!")
            print("  Model reverted to previous version")
        else:
            print("\n✗ Rollback failed!")
            print("  Please check database connection")


def menu():
    """Interactive menu"""
    while True:
        print("\n" + "="*80)
        print("🎯 MODEL ROLLBACK QUICK REFERENCE")
        print("="*80)
        print("\n1. Show model status")
        print("2. Check degradation")
        print("3. Quick rollback")
        print("4. Full monitoring (with auto-rollback)")
        print("5. Manual rollback to specific version")
        print("6. Compare two versions")
        print("7. Show model history")
        print("8. Exit")
        
        choice = input("\nSelect option (1-8): ").strip()
        
        if choice == '1':
            quick_status()
        
        elif choice == '2':
            quick_degradation_check()
        
        elif choice == '3':
            confirm = input("\n⚠️  Really rollback to previous version? (yes/no): ").strip().lower()
            if confirm == 'yes':
                quick_rollback()
            else:
                print("Cancelled")
        
        elif choice == '4':
            print("\n🚀 Starting full monitoring...")
            monitor = ModelMonitor(auto_rollback=True)
            result = monitor.check_and_respond()
            monitor.close()
        
        elif choice == '5':
            version = input("\nEnter target version (e.g., 20260105_143022): ").strip()
            confirm = input(f"Rollback to v{version}? (yes/no): ").strip().lower()
            if confirm == 'yes':
                with ModelEvaluationDB() as db:
                    success = db.rollback_production_model(target_version=version)
                    if success:
                        print(f"✓ Rolled back to v{version}")
                    else:
                        print(f"✗ Failed to rollback to v{version}")
            else:
                print("Cancelled")
        
        elif choice == '6':
            v1 = input("Enter first version: ").strip()
            v2 = input("Enter second version: ").strip()
            with ModelEvaluationDB() as db:
                comparison = db.compare_models(v1, v2)
                if comparison:
                    print(f"\n📊 COMPARISON RESULTS")
                    print(f"  Current: v{comparison['current_version']}")
                    print(f"    R²: {comparison['r2_current']:.4f}")
                    print(f"  Previous: v{comparison['previous_version']}")
                    print(f"    R²: {comparison['r2_previous']:.4f}")
                    print(f"  Change: {comparison['r2_change']:.4f}")
                    print(f"  Degraded: {'Yes' if comparison['degraded'] else 'No'}")
        
        elif choice == '7':
            limit = input("\nHow many versions to show? (default 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10
            with ModelEvaluationDB() as db:
                history = db.get_model_history(limit=limit)
                print(f"\n📜 MODEL HISTORY (Last {limit} versions)")
                for i, model in enumerate(history, 1):
                    prod = "🚀" if model['is_production'] else "  "
                    print(f"{prod} {i}. v{model['model_version']}")
                    print(f"      R²={model['r2_score']:.4f}, Size={model['size_mb']}MB")
        
        elif choice == '8':
            print("\nGoodbye! 👋")
            break
        
        else:
            print("Invalid option. Please select 1-8")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Quick reference for model rollback operations"
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show model status'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check degradation'
    )
    parser.add_argument(
        '--rollback',
        action='store_true',
        help='Quick rollback to previous version'
    )
    parser.add_argument(
        '--monitor',
        action='store_true',
        help='Run full monitoring'
    )
    parser.add_argument(
        '--interactive',
        '-i',
        action='store_true',
        help='Interactive menu (default)'
    )
    
    args = parser.parse_args()
    
    # If no arguments, show interactive menu
    if not any(vars(args).values()):
        menu()
    else:
        if args.status:
            quick_status()
        if args.check:
            quick_degradation_check()
        if args.rollback:
            quick_rollback()
        if args.monitor:
            monitor = ModelMonitor(auto_rollback=True)
            monitor.check_and_respond()
            monitor.close()
        if args.interactive:
            menu()
