"""
Query and visualize model evaluation results from PostgreSQL database
"""

import argparse
import pandas as pd
from datetime import datetime, timedelta
import json
from scripts.db_utils import get_db_connection


def display_latest_runs(limit: int = 10):
    """Display latest model training runs"""
    with get_db_connection() as db:
        sql = """
        SELECT 
            run_id,
            model_name,
            model_version,
            model_stage,
            trained_at,
            metadata->>'model_type' as model_type
        FROM model_runs
        ORDER BY trained_at DESC
        LIMIT %s
        """
        
        with db.conn.cursor() as cur:
            cur.execute(sql, (limit,))
            rows = cur.fetchall()
            
            if rows:
                df = pd.DataFrame(rows, columns=[
                    'Run ID', 'Model Name', 'Version', 'Stage', 'Trained At', 'Type'
                ])
                print("\n" + "="*100)
                print(f"LATEST MODEL RUNS (Last {limit})")
                print("="*100)
                print(df.to_string(index=False))
                print("="*100 + "\n")
            else:
                print("No model runs found in database")


def display_run_metrics(run_id: str):
    """Display detailed metrics for a specific run"""
    with get_db_connection() as db:
        # Get run info
        sql_run = "SELECT * FROM model_runs WHERE run_id = %s"
        with db.conn.cursor() as cur:
            cur.execute(sql_run, (run_id,))
            run = cur.fetchone()
            
            if not run:
                print(f"Run {run_id} not found")
                return
        
        # Get metrics
        sql_metrics = """
        SELECT metric_name, metric_value, metric_type 
        FROM model_metrics 
        WHERE run_id = %s
        ORDER BY metric_type, metric_name
        """
        with db.conn.cursor() as cur:
            cur.execute(sql_metrics, (run_id,))
            metrics = cur.fetchall()
        
        # Get hyperparameters
        sql_params = """
        SELECT param_name, param_value 
        FROM model_hyperparameters 
        WHERE run_id = %s
        """
        with db.conn.cursor() as cur:
            cur.execute(sql_params, (run_id,))
            params = cur.fetchall()
        
        print("\n" + "="*100)
        print(f"MODEL RUN DETAILS: {run_id}")
        print("="*100)
        print(f"Model: {run[2]} (Version: {run[3]}, Stage: {run[4]})")
        print(f"Trained: {run[5]}")
        
        if metrics:
            print("\nMETRICS:")
            print("-" * 60)
            for metric in metrics:
                print(f"  [{metric[2]}] {metric[0]}: {metric[1]:.4f}")
        
        if params:
            print("\nHYPERPARAMETERS:")
            print("-" * 60)
            for param in params:
                print(f"  {param[0]}: {param[1]}")
        
        print("="*100 + "\n")


def display_performance_trend(model_name: str, metric_name: str = 'r2_score', days: int = 30):
    """Display performance trend over time"""
    with get_db_connection() as db:
        sql = """
        SELECT 
            mr.trained_at,
            mr.model_version,
            mm.metric_value
        FROM model_runs mr
        JOIN model_metrics mm ON mr.run_id = mm.run_id
        WHERE mr.model_name = %s 
        AND mm.metric_name = %s
        AND mr.trained_at > %s
        ORDER BY mr.trained_at ASC
        """
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with db.conn.cursor() as cur:
            cur.execute(sql, (model_name, metric_name, cutoff_date))
            rows = cur.fetchall()
            
            if rows:
                df = pd.DataFrame(rows, columns=['Trained At', 'Version', metric_name])
                print("\n" + "="*100)
                print(f"PERFORMANCE TREND: {model_name} - {metric_name} (Last {days} days)")
                print("="*100)
                print(df.to_string(index=False))
                print("="*100)
                
                # Calculate statistics
                values = [row[2] for row in rows]
                print(f"\nStatistics:")
                print(f"  Mean: {sum(values)/len(values):.4f}")
                print(f"  Min: {min(values):.4f}")
                print(f"  Max: {max(values):.4f}")
                print(f"  Latest: {values[-1]:.4f}")
                
                # Trend
                if len(values) > 1:
                    trend = "↑ Improving" if values[-1] > values[0] else "↓ Declining"
                    change = ((values[-1] - values[0]) / values[0] * 100)
                    print(f"  Trend: {trend} ({change:+.2f}%)")
                print()
            else:
                print(f"No data found for {model_name} - {metric_name} in last {days} days")


def display_alerts(severity: str = None, limit: int = 20):
    """Display recent alerts"""
    with get_db_connection() as db:
        sql = """
        SELECT 
            id,
            run_id,
            alert_type,
            severity,
            message,
            created_at,
            resolved
        FROM model_alerts
        WHERE 1=1
        """
        params = []
        
        if severity:
            sql += " AND severity = %s"
            params.append(severity)
        
        sql += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        with db.conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            
            if rows:
                df = pd.DataFrame(rows, columns=[
                    'ID', 'Run ID', 'Type', 'Severity', 'Message', 'Created', 'Resolved'
                ])
                print("\n" + "="*100)
                print(f"ALERTS {f'({severity} SEVERITY)' if severity else ''}")
                print("="*100)
                print(df.to_string(index=False))
                print("="*100 + "\n")
            else:
                print("No alerts found")


def display_feature_importance(run_id: str, top_n: int = 10):
    """Display top feature importance for a run"""
    with get_db_connection() as db:
        sql = """
        SELECT feature_name, importance_score, rank
        FROM feature_importance
        WHERE run_id = %s
        ORDER BY rank
        LIMIT %s
        """
        
        with db.conn.cursor() as cur:
            cur.execute(sql, (run_id, top_n))
            rows = cur.fetchall()
            
            if rows:
                df = pd.DataFrame(rows, columns=['Feature', 'Importance', 'Rank'])
                print("\n" + "="*80)
                print(f"TOP {top_n} FEATURE IMPORTANCE: {run_id}")
                print("="*80)
                print(df.to_string(index=False))
                print("="*80 + "\n")
            else:
                print(f"No feature importance data found for run {run_id}")


def compare_runs(run_id1: str, run_id2: str):
    """Compare two model runs"""
    with get_db_connection() as db:
        sql = """
        SELECT 
            mr.run_id,
            mr.model_version,
            mr.trained_at,
            mm.metric_name,
            mm.metric_value
        FROM model_runs mr
        JOIN model_metrics mm ON mr.run_id = mm.run_id
        WHERE mr.run_id IN (%s, %s) AND mm.metric_type = 'test'
        ORDER BY mr.run_id, mm.metric_name
        """
        
        with db.conn.cursor() as cur:
            cur.execute(sql, (run_id1, run_id2))
            rows = cur.fetchall()
            
            if rows:
                print("\n" + "="*100)
                print(f"MODEL COMPARISON")
                print("="*100)
                
                # Group by run_id
                run1_data = [r for r in rows if r[0] == run_id1]
                run2_data = [r for r in rows if r[0] == run_id2]
                
                if run1_data and run2_data:
                    print(f"\nRun 1: {run_id1}")
                    print(f"  Version: {run1_data[0][1]}, Trained: {run1_data[0][2]}")
                    for r in run1_data:
                        print(f"  {r[3]}: {r[4]:.4f}")
                    
                    print(f"\nRun 2: {run_id2}")
                    print(f"  Version: {run2_data[0][1]}, Trained: {run2_data[0][2]}")
                    for r in run2_data:
                        print(f"  {r[3]}: {r[4]:.4f}")
                    
                    # Calculate improvements
                    print("\nIMPROVEMENTS (Run 2 vs Run 1):")
                    for i, r1 in enumerate(run1_data):
                        if i < len(run2_data):
                            r2 = run2_data[i]
                            if r1[3] == r2[3]:  # Same metric
                                diff = r2[4] - r1[4]
                                pct = (diff / r1[4] * 100) if r1[4] != 0 else 0
                                symbol = "↑" if diff > 0 else "↓"
                                print(f"  {r1[3]}: {symbol} {diff:+.4f} ({pct:+.2f}%)")
                
                print("="*100 + "\n")
            else:
                print("No data found for comparison")


def export_to_csv(output_file: str = 'model_results.csv'):
    """Export all results to CSV"""
    with get_db_connection() as db:
        sql = """
        SELECT 
            mr.run_id,
            mr.model_name,
            mr.model_version,
            mr.model_stage,
            mr.trained_at,
            mm.metric_name,
            mm.metric_value,
            mm.metric_type
        FROM model_runs mr
        LEFT JOIN model_metrics mm ON mr.run_id = mm.run_id
        ORDER BY mr.trained_at DESC, mm.metric_name
        """
        
        df = pd.read_sql(sql, db.conn)
        df.to_csv(output_file, index=False)
        print(f"✓ Exported {len(df)} rows to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Query model evaluation results from database')
    parser.add_argument('--action', required=True, 
                       choices=['runs', 'metrics', 'trend', 'alerts', 'features', 'compare', 'export'],
                       help='Action to perform')
    parser.add_argument('--run-id', help='MLflow run ID')
    parser.add_argument('--run-id2', help='Second run ID for comparison')
    parser.add_argument('--model-name', default='car_price_predictor', help='Model name')
    parser.add_argument('--metric', default='r2_score', help='Metric name')
    parser.add_argument('--severity', choices=['HIGH', 'MEDIUM', 'LOW'], help='Alert severity')
    parser.add_argument('--limit', type=int, default=10, help='Number of results')
    parser.add_argument('--days', type=int, default=30, help='Number of days for trend')
    parser.add_argument('--output', default='model_results.csv', help='Output file for export')
    
    args = parser.parse_args()
    
    if args.action == 'runs':
        display_latest_runs(args.limit)
    
    elif args.action == 'metrics':
        if not args.run_id:
            print("Error: --run-id required")
            return
        display_run_metrics(args.run_id)
        display_feature_importance(args.run_id, args.limit)
    
    elif args.action == 'trend':
        display_performance_trend(args.model_name, args.metric, args.days)
    
    elif args.action == 'alerts':
        display_alerts(args.severity, args.limit)
    
    elif args.action == 'features':
        if not args.run_id:
            print("Error: --run-id required")
            return
        display_feature_importance(args.run_id, args.limit)
    
    elif args.action == 'compare':
        if not args.run_id or not args.run_id2:
            print("Error: --run-id and --run-id2 required")
            return
        compare_runs(args.run_id, args.run_id2)
    
    elif args.action == 'export':
        export_to_csv(args.output)


if __name__ == "__main__":
    main()
