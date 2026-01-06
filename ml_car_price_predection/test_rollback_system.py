#!/usr/bin/env python
"""
Quick Test Suite for Model Rollback System
Verify that all components are working correctly
"""

import sys
import os
import logging

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_database_connection():
    """Test 1: Database connection"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Database Connection")
    logger.info("="*80)
    
    try:
        from db_utils import ModelEvaluationDB
        
        with ModelEvaluationDB() as db:
            logger.info("✓ Database connection successful")
            
            # Test list models
            models = db.get_model_history(limit=1)
            if models:
                logger.info(f"✓ Found {len(models)} model(s)")
            else:
                logger.warning("⚠️  No models found (expected if just starting)")
        
        return True
    
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False


def test_monitoring_functions():
    """Test 2: Monitoring functions"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Monitoring Functions")
    logger.info("="*80)
    
    try:
        from db_utils import ModelEvaluationDB
        
        with ModelEvaluationDB() as db:
            # Test check_performance_degradation
            result = db.check_performance_degradation(threshold_percent=5.0)
            
            logger.info("✓ check_performance_degradation() works")
            logger.info(f"  Degraded: {result.get('degraded', 'N/A')}")
            logger.info(f"  R² Change: {result.get('r2_change_percent', 'N/A')}%")
            
            # Test get_model_history
            history = db.get_model_history(limit=5)
            logger.info(f"✓ get_model_history() works - found {len(history)} models")
            
            if len(history) >= 2:
                # Test compare_models
                comparison = db.compare_models(
                    history[0]['model_version'],
                    history[1]['model_version']
                )
                logger.info("✓ compare_models() works")
                logger.info(f"  Degraded: {comparison.get('degraded', 'N/A')}")
        
        return True
    
    except Exception as e:
        logger.error(f"✗ Monitoring functions failed: {e}")
        return False


def test_monitor_class():
    """Test 3: ModelMonitor class"""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: ModelMonitor Class")
    logger.info("="*80)
    
    try:
        from monitor_model_performance import ModelMonitor
        
        monitor = ModelMonitor(auto_rollback=False)
        
        # Test get_model_history
        history = monitor.get_model_history(limit=3)
        logger.info(f"✓ ModelMonitor.get_model_history() works - found {len(history)} models")
        
        # Test check_and_respond (without auto-rollback)
        result = monitor.check_and_respond()
        logger.info(f"✓ ModelMonitor.check_and_respond() works")
        logger.info(f"  Status: {result.get('status', 'N/A')}")
        
        monitor.close()
        return True
    
    except Exception as e:
        logger.error(f"✗ ModelMonitor class failed: {e}")
        return False


def test_quick_reference():
    """Test 4: Quick reference tool"""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: Quick Reference Tool")
    logger.info("="*80)
    
    try:
        # Try importing (script-style test)
        import quick_rollback_ref
        logger.info("✓ quick_rollback_ref.py imports successfully")
        
        # Test functions exist
        assert hasattr(quick_rollback_ref, 'quick_status')
        assert hasattr(quick_rollback_ref, 'quick_degradation_check')
        assert hasattr(quick_rollback_ref, 'quick_rollback')
        
        logger.info("✓ All quick reference functions exist")
        return True
    
    except Exception as e:
        logger.error(f"✗ Quick reference test failed: {e}")
        return False


def test_documentation():
    """Test 5: Documentation files exist"""
    logger.info("\n" + "="*80)
    logger.info("TEST 5: Documentation Files")
    logger.info("="*80)
    
    docs = [
        'MODEL_ROLLBACK_GUIDE.md',
        'ROLLBACK_IMPLEMENTATION_SUMMARY.md',
        'ROLLBACK_EXAMPLES.md',
        'COMPLETE_ROLLBACK_SYSTEM.md'
    ]
    
    try:
        all_exist = True
        for doc in docs:
            path = os.path.join(os.path.dirname(__file__), doc)
            if os.path.exists(path):
                size = os.path.getsize(path)
                logger.info(f"✓ {doc} ({size/1024:.1f} KB)")
            else:
                logger.warning(f"✗ {doc} not found")
                all_exist = False
        
        return all_exist
    
    except Exception as e:
        logger.error(f"✗ Documentation check failed: {e}")
        return False


def test_airflow_dag():
    """Test 6: Airflow DAG"""
    logger.info("\n" + "="*80)
    logger.info("TEST 6: Airflow Integration")
    logger.info("="*80)
    
    try:
        dag_path = os.path.join(
            os.path.dirname(__file__),
            'airflow', 'dags', 'model_monitoring_dag.py'
        )
        
        if os.path.exists(dag_path):
            with open(dag_path, 'r') as f:
                content = f.read()
                
            # Check for key elements
            checks = {
                'DAG definition': 'DAG(' in content,
                'PythonOperator': 'PythonOperator' in content,
                'check_model_performance': 'check_model_performance' in content,
                'Task dependencies': '>>' in content,
            }
            
            all_ok = True
            for check_name, check_result in checks.items():
                status = "✓" if check_result else "✗"
                logger.info(f"{status} {check_name}")
                all_ok = all_ok and check_result
            
            return all_ok
        else:
            logger.warning(f"✗ Airflow DAG not found at {dag_path}")
            return False
    
    except Exception as e:
        logger.error(f"✗ Airflow DAG test failed: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    logger.info("\n")
    logger.info("╔" + "="*78 + "╗")
    logger.info("║" + " "*20 + "MODEL ROLLBACK SYSTEM - TEST SUITE" + " "*25 + "║")
    logger.info("╚" + "="*78 + "╝")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Monitoring Functions", test_monitoring_functions),
        ("Monitor Class", test_monitor_class),
        ("Quick Reference", test_quick_reference),
        ("Documentation", test_documentation),
        ("Airflow Integration", test_airflow_dag),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"\nUnexpected error in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info("="*80)
    logger.info(f"TOTAL: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 ALL TESTS PASSED! System is ready for use.")
        return True
    else:
        logger.warning(f"\n⚠️  {total - passed} test(s) failed. Please review above.")
        return False


def print_quick_start():
    """Print quick start guide"""
    logger.info("\n" + "="*80)
    logger.info("QUICK START GUIDE")
    logger.info("="*80)
    
    commands = {
        "Check for degradation": 
            "python scripts/monitor_model_performance.py --check",
        
        "Quick rollback": 
            "python scripts/monitor_model_performance.py --rollback-previous",
        
        "View status": 
            "python scripts/monitor_model_performance.py --status",
        
        "Interactive menu": 
            "python quick_rollback_ref.py",
        
        "Compare versions": 
            "python scripts/monitor_model_performance.py --compare v1 v2",
    }
    
    for description, command in commands.items():
        logger.info(f"\n{description}:")
        logger.info(f"  $ {command}")
    
    logger.info("\n" + "="*80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test model rollback system")
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--test', choices=[
        'database', 'monitoring', 'monitor', 'reference', 'docs', 'airflow'
    ], help='Run specific test')
    
    args = parser.parse_args()
    
    if args.test:
        test_map = {
            'database': test_database_connection,
            'monitoring': test_monitoring_functions,
            'monitor': test_monitor_class,
            'reference': test_quick_reference,
            'docs': test_documentation,
            'airflow': test_airflow_dag,
        }
        success = test_map[args.test]()
    else:
        success = run_all_tests()
        print_quick_start()
    
    sys.exit(0 if success else 1)
