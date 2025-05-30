"""
Tests for Monitoring Stack Configuration (Prometheus, Grafana, Alerting)
"""
import pytest
import yaml
import json
from pathlib import Path
import re

def load_yaml(file_path):
    with open(file_path) as f:
        return yaml.safe_load(f)

def load_json(file_path):
    with open(file_path) as f:
        return json.load(f)

class TestPrometheusConfig:
    @pytest.fixture
    def prometheus_config(self):
        return load_yaml('../monitoring/prometheus.yml')

    def test_global_config(self, prometheus_config):
        """Test Prometheus global configuration"""
        global_config = prometheus_config['global']
        assert 'scrape_interval' in global_config
        assert 'evaluation_interval' in global_config
        assert isinstance(global_config['scrape_interval'], str)
        assert isinstance(global_config['evaluation_interval'], str)

    def test_scrape_configs(self, prometheus_config):
        """Test scrape configurations for all components"""
        scrape_configs = prometheus_config['scrape_configs']
        required_jobs = [
            'aetheros_agents',
            'deep_eval',
            'aethero_mem',
            'langgraph'
        ]
        
        job_names = [config['job_name'] for config in scrape_configs]
        assert all(job in job_names for job in required_jobs)
        
        for config in scrape_configs:
            assert 'static_configs' in config
            assert 'metrics_path' in config
            assert 'scheme' in config

    def test_alerting_config(self, prometheus_config):
        """Test alerting configuration"""
        alerting = prometheus_config['alerting']
        assert 'alertmanagers' in alerting
        assert len(alerting['alertmanagers']) > 0
        assert 'static_configs' in alerting['alertmanagers'][0]

    def test_rule_files(self, prometheus_config):
        """Test rule files configuration"""
        assert 'rule_files' in prometheus_config
        assert 'aetheros_rules.yml' in prometheus_config['rule_files']

class TestGrafanaDashboards:
    @pytest.fixture
    def dashboard_config(self):
        return load_json('../monitoring/grafana_dashboards.json')

    def test_dashboard_structure(self, dashboard_config):
        """Test Grafana dashboard structure"""
        assert 'panels' in dashboard_config
        assert 'templating' in dashboard_config
        assert 'time' in dashboard_config
        assert isinstance(dashboard_config['panels'], list)

    def test_required_panels(self, dashboard_config):
        """Test presence of required dashboard panels"""
        required_panels = [
            'Agent Performance Overview',
            'Reflection Metrics',
            'Memory System Metrics',
            'Pipeline Execution'
        ]
        
        panel_titles = [panel.get('title', '') for panel in dashboard_config['panels']]
        assert all(title in panel_titles for title in required_panels)

    def test_panel_datasources(self, dashboard_config):
        """Test panel datasource configurations"""
        for panel in dashboard_config['panels']:
            if 'panels' in panel:  # Row with sub-panels
                for sub_panel in panel['panels']:
                    if 'datasource' in sub_panel:
                        assert sub_panel['datasource'] == 'Prometheus'
            elif 'datasource' in panel:  # Direct panel
                assert panel['datasource'] == 'Prometheus'

    def test_dashboard_refresh(self, dashboard_config):
        """Test dashboard refresh settings"""
        assert 'refresh' in dashboard_config
        assert dashboard_config['refresh'] == '5s'

class TestAlertingRules:
    @pytest.fixture
    def rules_config(self):
        return load_yaml('../monitoring/aetheros_rules.yml')

    def test_rules_structure(self, rules_config):
        """Test alerting rules structure"""
        assert 'groups' in rules_config
        assert len(rules_config['groups']) > 0
        assert 'rules' in rules_config['groups'][0]

    def test_required_alerts(self, rules_config):
        """Test presence of required alert rules"""
        required_alerts = [
            'AgentDown',
            'HighAgentLatency',
            'LowReflectionQuality',
            'HighMemoryLatency',
            'LowPipelineSuccessRate'
        ]
        
        alert_names = []
        for group in rules_config['groups']:
            for rule in group['rules']:
                if 'alert' in rule:
                    alert_names.append(rule['alert'])
        
        assert all(alert in alert_names for alert in required_alerts)

    def test_alert_configurations(self, rules_config):
        """Test alert rule configurations"""
        for group in rules_config['groups']:
            for rule in group['rules']:
                if 'alert' in rule:
                    assert 'expr' in rule
                    assert 'for' in rule
                    assert 'labels' in rule
                    assert 'annotations' in rule
                    assert 'severity' in rule['labels']
                    assert 'summary' in rule['annotations']
                    assert 'description' in rule['annotations']

    def test_alert_expressions(self, rules_config):
        """Test alert rule expressions"""
        for group in rules_config['groups']:
            for rule in group['rules']:
                if 'alert' in rule:
                    # Verify PromQL syntax
                    expr = rule['expr']
                    assert isinstance(expr, (str, float, int))
                    if isinstance(expr, str):
                        # Basic PromQL syntax check
                        assert re.search(r'[a-zA-Z_:][a-zA-Z0-9_:]*', expr)

def test_monitoring_integration():
    """Test monitoring component integration"""
    prometheus_config = load_yaml('../monitoring/prometheus.yml')
    rules_config = load_yaml('../monitoring/aetheros_rules.yml')
    dashboard_config = load_json('../monitoring/grafana_dashboards.json')
    
    # Verify metrics consistency
    metrics = set()
    
    # Extract metrics from rules
    for group in rules_config['groups']:
        for rule in group['rules']:
            if 'expr' in rule:
                # Extract metric names from PromQL expressions
                matches = re.findall(r'[a-zA-Z_:][a-zA-Z0-9_:]*{', rule['expr'])
                metrics.update(match[:-1] for match in matches)
    
    # Verify metrics are scraped
    for scrape_config in prometheus_config['scrape_configs']:
        job_name = scrape_config['job_name']
        if job_name.startswith('aetheros_'):
            # Job should collect metrics used in rules
            relevant_metrics = {m for m in metrics 
                              if m.startswith(job_name.replace('aetheros_agents', 'aetheros_'))}
            assert len(relevant_metrics) > 0
    
    # Verify dashboard uses available metrics
    for panel in dashboard_config['panels']:
        if 'panels' in panel:  # Row with sub-panels
            for sub_panel in panel['panels']:
                if 'targets' in sub_panel:
                    for target in sub_panel['targets']:
                        if 'expr' in target:
                            # Extract metric names from panel queries
                            matches = re.findall(r'[a-zA-Z_:][a-zA-Z0-9_:]*{', target['expr'])
                            panel_metrics = {match[:-1] for match in matches}
                            assert panel_metrics.issubset(metrics)

if __name__ == '__main__':
    pytest.main(['-v', __file__])
